r"""safe_edit — 볼트의 기존 파일을 한 번에 안전하게 고친다.

AI 에이전트의 파일 편집 도구는 가끔 끝부분을 잘라 먹거나, 줄바꿈 방식을 바꾸거나, 사람이 그사이 고친 판을 덮어쓴다.
이 도구는 그 세 가지를 막는다: 판본 확인 → 전부 아니면 전무 치환 → 쓰기 후 검증.

사용(의존성 없음, Python 3.8+):
  python safe_edit.py <spec.json> [--dry-run] [--root <볼트 루트>]

spec.json — 객체 하나 또는 객체 리스트(파일별로 차례 처리, 실패하면 거기서 멈춘다):
  {"file": "볼트 루트 기준 경로",
   "edits": [{"old": "찾을 글", "new": "바꿀 글", "count": 1}],   # count 기본 1, "all"이면 1건 이상 전부
   "append": "끝에 덧붙일 글",                                    # 선택
   "create": true, "content": "새 파일 내용",                      # 새 파일. 이미 있으면 거부
   "expect_md5": "앞 8자 이상",                                    # 선택. 현재 판과 다르면 중단
   "allow_protected": false}                                       # .protected 목록 대상 수정 허용

동작:
  1. 볼트 밖 경로는 거부한다. 볼트 루트의 `.protected`(한 줄에 경로 접두어 하나)에 걸리면 allow_protected 없이는 거부한다.
  2. 현재 md5·수정시각을 출력하고, expect_md5가 다르면 중단한다.
  3. 줄바꿈(CRLF·LF)과 BOM을 판별해 보존한다 — spec의 \n은 파일 방식으로 맞춘다.
  4. 치환 건수가 count와 다르면 아무것도 쓰지 않는다.
  5. git이 추적하지 않는 파일이면 쓰기 전에 `.backup/YYYYMMDD-HHMMSS_파일명`으로 사본을 남긴다.
  6. .py·.json은 쓰기 전에 구문을 검사한다. 같은 폴더 임시 파일에 쓴 뒤 교체하고, 다시 읽어 바이트 일치·줄바꿈 불변을 확인한다.
  7. 결과를 한 줄 JSON으로 출력한다.

종료 코드: 0 성공, 1 입력·일치 오류(쓰지 않음), 2 쓰기 후 검증 실패(백업·git으로 되돌린다).
"""
import ast, hashlib, json, os, pathlib, shutil, subprocess, sys, time

BOM = b"\xef\xbb\xbf"


def md5(b):
    return hashlib.md5(b).hexdigest()


def protected(rel, root):
    p = pathlib.Path(root, ".protected")
    if not p.exists():
        return None
    rel = rel.replace("\\", "/")
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and rel.startswith(line.rstrip("/")):
            return line
    return None


def tracked(path, root):
    try:
        r = subprocess.run(["git", "ls-files", "--error-unmatch", str(path)], cwd=root,
                           capture_output=True)
        return r.returncode == 0
    except FileNotFoundError:
        return False


def style_of(raw):
    body = raw[len(BOM):] if raw.startswith(BOM) else raw
    return ("CRLF" if b"\r\n" in body else "LF"), raw.startswith(BOM)


def syntax_ok(path, text):
    if path.suffix == ".py":
        ast.parse(text)
    elif path.suffix == ".json":
        json.loads(text)


def apply(spec, root, dry):
    rel = spec["file"]
    rootp = pathlib.Path(root).resolve()
    path = (rootp / rel).resolve()
    res = {"file": rel}
    if rootp not in path.parents:
        return 1, {**res, "error": "볼트 밖 경로"}
    hit = protected(rel, root)
    if hit and not spec.get("allow_protected"):
        return 1, {**res, "error": f".protected 대상({hit}) — allow_protected 필요"}

    if spec.get("create"):
        if path.exists():
            return 1, {**res, "error": "이미 있음 — create 거부"}
        new_text, nl, bom, before = spec["content"], "LF", False, None
    else:
        if not path.exists():
            return 1, {**res, "error": "파일 없음"}
        raw = path.read_bytes()
        before = {"bytes": len(raw), "md5": md5(raw)[:8],
                  "mtime": time.strftime("%Y-%m-%d %H:%M", time.localtime(path.stat().st_mtime))}
        exp = spec.get("expect_md5")
        if exp and not md5(raw).startswith(exp):
            return 1, {**res, "before": before, "error": "판본 불일치 — 그사이 바뀐 판 위에서 다시 작업"}
        nl, bom = style_of(raw)
        text = (raw[len(BOM):] if bom else raw).decode("utf-8")
        sep = "\r\n" if nl == "CRLF" else "\n"
        for e in spec.get("edits", []):
            old, new = e["old"].replace("\n", sep), e["new"].replace("\n", sep)
            n = text.count(old)
            want = e.get("count", 1)
            if (want == "all" and n < 1) or (want != "all" and n != want):
                return 1, {**res, "before": before, "error": f"치환 건수 {n} ≠ 기대 {want}", "old": e["old"][:80]}
            text = text.replace(old, new)
        if "append" in spec:
            add = spec["append"].replace("\n", sep)
            if text and not text.endswith(sep):
                text += sep
            text += add
        new_text = text
    res["before"] = before

    try:
        syntax_ok(path, new_text)
    except Exception as ex:  # noqa: BLE001
        return 1, {**res, "error": f"구문 오류 — 쓰지 않음: {ex}"}

    data = (BOM if bom else b"") + new_text.encode("utf-8")
    if dry:
        return 0, {**res, "dry_run": True, "after_bytes": len(data)}

    if not spec.get("create") and not tracked(path, root):
        bdir = rootp / ".backup"
        bdir.mkdir(exist_ok=True)
        shutil.copy2(path, bdir / f"{time.strftime('%Y%m%d-%H%M%S')}_{path.name}")
        res["backup"] = True

    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp_safe_edit")
    tmp.write_bytes(data)
    os.replace(tmp, path)

    back = path.read_bytes()
    ok = back == data and style_of(back)[0] == nl
    res.update({"after": {"bytes": len(back), "md5": md5(back)[:8]}, "newline": nl, "verified": ok,
                "tail": new_text.splitlines()[-2:]})
    return (0 if ok else 2), res


def main(argv):
    args = argv[1:]
    dry = "--dry-run" in args
    root = os.getcwd()
    if "--root" in args:
        root = args[args.index("--root") + 1]
    pos = [a for i, a in enumerate(args) if not a.startswith("--") and (i == 0 or args[i - 1] != "--root")]
    if not pos:
        print(__doc__)
        return 1
    specs = json.loads(pathlib.Path(pos[0]).read_text(encoding="utf-8"))
    specs = specs if isinstance(specs, list) else [specs]
    for s in specs:
        rc, res = apply(s, root, dry)
        print(json.dumps({**res, "ok": rc == 0}, ensure_ascii=False))
        if rc:
            return rc
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
