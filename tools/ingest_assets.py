#!/usr/bin/env python3
"""새 자극물 배치를 정규 경로로 편입한다.

  python3 tools/ingest_assets.py <배치폴더> [--apply]

--apply 없이 실행하면 무엇을 어디로 옮길지만 출력한다(드라이런).

정규 경로
  deploy/assets/persona/<form>_<persona>.jpg          1672x941 JPEG q92
  deploy/assets/video/<form>/<persona>/<key>.mp4      intro 1-1 1-2 2-1 2-2 3-1 3-2 idle

배치마다 파일명 규칙이 달라서, 파일명에 들어 있는 단서로 form/persona/key 를 추정한다.
추정이 안 되는 파일은 건드리지 않고 목록으로 보고한다.
"""
import sys, os, re, shutil, subprocess, unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PERSONA_DIR = os.path.join(ROOT, "deploy/assets/persona")
VIDEO_DIR   = os.path.join(ROOT, "deploy/assets/video")
ARCHIVE     = os.path.join(ROOT, "_archive")

FORM = [("avatar", ["avatar", "아바타"]),
        ("human",  ["human", "사람", "실사"])]
PERSONA = [("middle_man",  ["middle_man","middle-man","middleaged","middle aged","중년"]),
           ("young_woman", ["young_woman","young-woman","젊은_여","젊은 여","여성","woman"]),
           ("young_man",   ["young_man","young-man","젊은_남","젊은 남","남성","man"])]
KEYS = ["intro","1-1","1-2","2-1","2-2","3-1","3-2"]
# 숫자 접두사 규칙 : 0=자기소개, 1~6=문제1~6
NUMKEY = {"0":"intro","1":"1-1","2":"1-2","3":"2-1","4":"2-2","5":"3-1","6":"3-2"}

def norm(s):
    return unicodedata.normalize("NFC", s).lower()

def pick(name, table):
    n = norm(name)
    hits = [(key, max(len(t) for t in toks if t in n))
            for key, toks in table if any(t in n for t in toks)]
    if not hits: return None
    return max(hits, key=lambda h: h[1])[0]          # 가장 구체적인 단서 우선

def pick_key(name):
    n = norm(name)
    if "silence" in n or "idle" in n or "waiting" in n or "대기" in n: return "idle"
    if "자기소개" in n or "intro" in n: return "intro"
    m = re.search(r'(?<!\d)([1-3])[-_]([1-2])(?!\d)', n)
    if m: return "%s-%s" % m.groups()
    m = re.search(r'문제\s*([1-6])', n)
    if m: return NUMKEY[m.group(1)]
    m = re.search(r'(?:^|[^0-9])([0-6])(?:[^0-9]|$)', os.path.basename(n))
    if m: return NUMKEY[m.group(1)]
    return None

def main():
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)
    src = sys.argv[1]; apply = "--apply" in sys.argv
    if not os.path.isdir(src):
        print("폴더 없음:", src); sys.exit(1)

    plans, skipped = [], []
    for dirpath, _, files in os.walk(src):
        for f in files:
            if f.startswith("."): continue
            p = os.path.join(dirpath, f)
            ext = os.path.splitext(f)[1].lower()
            rel = os.path.relpath(p, src)
            form = pick(rel, FORM); per = pick(rel, PERSONA)
            if ext in (".png", ".jpg", ".jpeg"):
                if not (form and per): skipped.append((rel, "form/persona 추정 실패")); continue
                plans.append(("img", p, os.path.join(PERSONA_DIR, "%s_%s.jpg" % (form, per))))
            elif ext in (".mp4", ".mov", ".m4v"):
                key = pick_key(rel)
                if not (form and per and key):
                    skipped.append((rel, "form/persona/key 추정 실패 (%s/%s/%s)" % (form, per, key))); continue
                plans.append(("vid", p, os.path.join(VIDEO_DIR, form, per, "%s.mp4" % key)))
            else:
                skipped.append((rel, "대상 아님"))

    print("== 편입 계획 (%s) ==" % ("적용" if apply else "드라이런"))
    for kind, s, d in sorted(plans, key=lambda x: x[2]):
        mark = "덮어씀" if os.path.exists(d) else "신규  "
        print("  [%s] %s  %s  <-  %s" % (kind, mark, os.path.relpath(d, ROOT), os.path.relpath(s, src)))
    if skipped:
        print("\n== 건너뜀 ==")
        for rel, why in skipped: print("  %-50s %s" % (rel, why))
    if not apply:
        print("\n적용하려면 --apply 를 붙여 다시 실행하세요."); return

    os.makedirs(os.path.join(ARCHIVE, "replaced"), exist_ok=True)
    import cv2
    for kind, s, d in plans:
        os.makedirs(os.path.dirname(d), exist_ok=True)
        if os.path.exists(d):                                  # 기존본 보관
            shutil.move(d, os.path.join(ARCHIVE, "replaced",
                        os.path.basename(os.path.dirname(d)) + "_" + os.path.basename(d)))
        if kind == "img":
            im = cv2.imread(s)
            cv2.imwrite(d, im, [cv2.IMWRITE_JPEG_QUALITY, 92])
        else:
            shutil.copy2(s, d)
    print("\n%d개 편입 완료. 원본은 그대로 두었습니다." % len(plans))

    # 규격 일치 확인
    sizes = {}
    for f in sorted(os.listdir(PERSONA_DIR)):
        if f.endswith(".jpg"):
            im = cv2.imread(os.path.join(PERSONA_DIR, f))
            sizes.setdefault(im.shape[:2], []).append(f)
    print("\n== 사진 규격 ==")
    for sz, fs in sizes.items(): print("  %s : %d장" % (sz, len(fs)))
    if len(sizes) > 1: print("  *** 규격이 섞여 있습니다 — 자극 통제에 문제가 됩니다 ***")

if __name__ == "__main__":
    main()
