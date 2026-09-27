#!/usr/bin/env python3
"""_source/video/ 의 원본으로 deploy/ 가 실제로 쓰는 파일을 만든다.

  python3 tools/build_assets.py                       # 무엇을 만들지만 출력
  python3 tools/build_assets.py --apply               # 원본 해상도 그대로 (재인코딩 없음)
  python3 tools/build_assets.py --apply --height 720  # 720p 로 재인코딩 (용량 약 1/6)
  python3 tools/build_assets.py --apply --only human/young_man   # 일부만

만드는 것 (form = human | avatar, persona = middle_man | young_woman | young_man)
  deploy/assets/video/<form>/<persona>/<key>.mp4   말하는 영상 (key = intro, 1-1 … 3-2)
  deploy/assets/video/<form>/<persona>/idle.mp4    대기 영상 = idle_1→2→3→4 를 이어 붙임, 소리 트랙 제거
  deploy/assets/persona/<form>_<persona>.jpg       idle.mp4 첫 프레임 (블러 화면 · 사진 모드용)

대기 클립 4개는 시작·끝 프레임이 같게 제작되어 있어 이어 붙이고 반복 재생해도 튀지 않는다.
모든 mp4 는 faststart(moov 앞쪽)로 저장해 브라우저가 다 받기 전에 재생을 시작할 수 있게 한다.
결과가 원본보다 새것이고 설정(해상도)이 같으면 건너뛴다. 전부 다시 만들려면 --force.
"""
import argparse, os, sys, glob, json, subprocess, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC  = os.path.join(ROOT, "_source", "video")
OUT  = os.path.join(ROOT, "deploy", "assets", "video")
IMG  = os.path.join(ROOT, "deploy", "assets", "persona")
STAMP = os.path.join(OUT, ".build.json")
KEYS = ["intro", "1-1", "1-2", "2-1", "2-2", "3-1", "3-2"]

def ff(*args):
    r = subprocess.run(["ffmpeg", "-v", "error", "-y", *args], capture_output=True, text=True)
    if r.returncode: raise RuntimeError(r.stderr.strip()[-400:])

def stale(out, ins, force):
    return force or not os.path.exists(out) or os.path.getmtime(out) < max(os.path.getmtime(i) for i in ins)

def vopts(height):
    if not height: return ["-c:v", "copy"]
    w = round(height * 16 / 9 / 2) * 2
    return ["-vf", f"scale={w}:{height},setsar=1", "-c:v", "libx264", "-preset", "medium",
            "-crf", "23", "-pix_fmt", "yuv420p"]

def build_talk(src, out, height):
    ff("-i", src, *vopts(height), "-c:a", "copy", "-movflags", "+faststart", out)

def build_idle(clips, out, height):
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as t:
        for c in clips: t.write("file '%s'\n" % c.replace("'", "'\\''"))
        lst = t.name
    try:
        ff("-f", "concat", "-safe", "0", "-i", lst, *vopts(height), "-an", "-movflags", "+faststart", out)
    finally:
        os.unlink(lst)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--height", type=int, default=0, help="0 = 원본 유지(기본), 720 등 = 재인코딩")
    ap.add_argument("--only", help="예: human 또는 human/young_man")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()

    prev = json.load(open(STAMP)) if os.path.exists(STAMP) else {}
    force = a.force or prev.get("height", 0) != a.height
    if force and prev and prev.get("height", 0) != a.height:
        print(f"해상도 설정이 바뀌어({prev.get('height') or '원본'} → {a.height or '원본'}) 전부 다시 만듭니다.\n")

    jobs = []
    for pdir in sorted(glob.glob(os.path.join(SRC, "*", "*"))):
        form, persona = pdir.split(os.sep)[-2:]
        if a.only and not f"{form}/{persona}".startswith(a.only): continue
        od = os.path.join(OUT, form, persona)
        for k in KEYS:
            s = os.path.join(pdir, k + ".mp4")
            if os.path.exists(s):
                o = os.path.join(od, k + ".mp4")
                if stale(o, [s], force): jobs.append(("talk", [s], o))
        clips = [os.path.join(pdir, f"idle_{i}.mp4") for i in (1, 2, 3, 4)]
        have = [c for c in clips if os.path.exists(c)]
        if have and len(have) < 4:
            print(f"  ⚠ {form}/{persona}: 대기 클립 {len(have)}/4 개뿐이라 idle.mp4 를 만들지 않습니다")
        if len(have) == 4:
            o = os.path.join(od, "idle.mp4")
            if stale(o, clips, force): jobs.append(("idle", clips, o))
            j = os.path.join(IMG, f"{form}_{persona}.jpg")
            if stale(j, clips, force): jobs.append(("still", [o], j))

    if not jobs:
        print("모두 최신입니다."); return
    for kind, ins, out in jobs:
        print(f"  {kind:5s} → {os.path.relpath(out, ROOT)}")
    if not a.apply:
        print(f"\n(미리보기 {len(jobs)}건. 만들려면 --apply)"); return

    for kind, ins, out in jobs:
        os.makedirs(os.path.dirname(out), exist_ok=True)
        if kind == "talk":  build_talk(ins[0], out, a.height)
        if kind == "idle":  build_idle(ins, out, a.height)
        if kind == "still": ff("-i", ins[0], "-frames:v", "1", "-q:v", "3", out)
        print(f"  ✓ {os.path.relpath(out, ROOT)}")
    if not a.only: json.dump({"height": a.height}, open(STAMP, "w"))
    print("\n다음 단계: python3 tools/check_assets.py")

if __name__ == "__main__":
    main()
