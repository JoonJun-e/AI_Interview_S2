#!/usr/bin/env python3
"""_source/video/ 의 원본으로 deploy/ 가 실제로 쓰는 파일을 만든다.

  python3 tools/build_assets.py                       # 무엇을 만들지만 출력
  python3 tools/build_assets.py --apply               # 원본 해상도 그대로 (재인코딩 없음)
  python3 tools/build_assets.py --apply --height 720  # 720p 로 재인코딩 (용량 약 1/6)
  python3 tools/build_assets.py --apply --only human/young_man   # 일부만

만드는 것 (form = human | avatar, persona = middle_man | young_woman | young_man)
  deploy/assets/video/<form>/<persona>/<key>.mp4   말하는 영상 (key = intro, 1-1 … 3-2)
  deploy/assets/video/<form>/<persona>/idle.mp4    답변 대기 = 있는 idle_N 을 번호순(또는 order.txt 순서)으로 이어 붙임, 소리 제거
  deploy/assets/video/<form>/<persona>/wait.mp4    듣기 대기(눈 깜빡임) = blink_1→blink_2… 를 이어 붙인 loop, 소리 제거
  deploy/assets/persona/<form>_<persona>.jpg       idle.mp4 첫 프레임 (블러 화면 · 사진 모드용)

대기 클립 4개는 시작·끝 프레임이 같게 제작되어 있어 이어 붙이고 반복 재생해도 튀지 않는다.
대기 클립은 질문 영상보다 약간 밝게 나와 있어서, 질문 영상이 있으면 그 색에 맞춰(채널별 밝기·대비)
보정한 뒤 이어 붙인다. 그래야 질문 → 대기로 넘어갈 때 화면 밝기가 튀지 않는다.
idle.mp4 는 24fps 로 다시 인코딩하고 클립 경계(121프레임마다)에 키프레임을 둔다 —
index.html 이 다시 듣기 구간에서 특정 클립 시작점으로 정확히 이동하기 위해서다.
무언가 새로 만들면 index.html 의 ASSET_VERSION 을 갱신해 브라우저 캐시(1년)를 무효화한다.
모든 mp4 는 faststart(moov 앞쪽)로 저장해 브라우저가 다 받기 전에 재생을 시작할 수 있게 한다.
입력 파일(이름·크기·수정시각)과 해상도가 지난번과 같으면 건너뛴다. 전부 다시 만들려면 --force.
"""
import argparse, os, re, sys, glob, json, subprocess, tempfile, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC  = os.path.join(ROOT, "_source", "video")
OUT  = os.path.join(ROOT, "deploy", "assets", "video")
IMG  = os.path.join(ROOT, "deploy", "assets", "persona")
STAMP = os.path.join(OUT, ".build.json")
HTML  = os.path.join(ROOT, "deploy", "index.html")
CLIP_FRAMES, IDLE_FPS = 121, 24          # 대기 클립 1개 = 24fps × 121프레임 (index.html IDLE_CLIP_SEC 와 같아야 함)
KEYS = ["intro", "1-1", "1-2", "2-1", "2-2", "3-1", "3-2"]

def ff(*args):
    r = subprocess.run(["ffmpeg", "-v", "error", "-y", *args], capture_output=True, text=True)
    if r.returncode: raise RuntimeError(r.stderr.strip()[-400:])

SIGS = {}   # 결과 파일별 입력 서명 (.build.json 에 저장) — 입력이 바뀌거나 빠져도 다시 만든다
def sig(ins, height):
    return [height] + [[os.path.relpath(i, ROOT), os.path.getsize(i), int(os.path.getmtime(i))] for i in ins]
def stale(out, ins, force, height=0):
    key = os.path.relpath(out, ROOT)
    return force or not os.path.exists(out) or SIGS.get(key) != sig(ins, height)

def vopts(height):
    if not height: return ["-c:v", "copy"]
    w = round(height * 16 / 9 / 2) * 2
    return ["-vf", f"scale={w}:{height},setsar=1", "-c:v", "libx264", "-preset", "medium",
            "-crf", "23", "-pix_fmt", "yuv420p"]

def build_talk(src, out, height):
    ff("-i", src, *vopts(height), "-c:a", "copy", "-movflags", "+faststart", out)

def rgb_stats(path, sseof=None):
    """첫 프레임(또는 끝에서 sseof 초) 의 채널별 평균·표준편차"""
    a = ["ffmpeg", "-v", "error"] + (["-sseof", str(sseof)] if sseof else []) + \
        ["-i", path, "-frames:v", "1", "-vf", "scale=320:180", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    x = subprocess.run(a, capture_output=True).stdout
    import numpy as np
    x = np.frombuffer(x, np.uint8).astype(np.float32).reshape(-1, 3)
    return x.mean(0), x.std(0)

def color_match(talks, clips):
    """대기 클립 → 질문 영상 색으로 맞추는 채널별 gain·offset. 질문 영상이 없으면 None"""
    if not talks: return None
    try:
        import numpy as np
    except ImportError:
        print("  ⚠ numpy 가 없어 색 보정을 건너뜁니다 (pip3 install numpy)"); return None
    tm, ts = np.mean([rgb_stats(t)[0] for t in talks], 0), np.mean([rgb_stats(t)[1] for t in talks], 0)
    im, is_ = np.mean([rgb_stats(c)[0] for c in clips], 0), np.mean([rgb_stats(c)[1] for c in clips], 0)
    g = ts / is_; o = tm - g * im
    return [(round(float(g[i]), 4), round(float(o[i]), 2)) for i in range(3)]

def build_idle(clips, out, height, cm, cap=True):
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as t:
        for c in clips: t.write("file '%s'\n" % c.replace("'", "'\\''"))
        lst = t.name
    vf = []
    if cm:
        vf.append("lutrgb=" + ":".join(f"{ch}='clip(val*{g}+{o},0,255)'" for ch, (g, o) in zip("rgb", cm)))
    if height:
        w = round(height * 16 / 9 / 2) * 2
        vf.append(f"scale={w}:{height},setsar=1")
    vf.append("format=yuv420p")
    try:
        ff("-f", "concat", "-safe", "0", "-i", lst, "-vf", ",".join(vf), "-r", str(IDLE_FPS),
           "-c:v", "libx264", "-preset", "medium", "-crf", "18",
           "-g", str(CLIP_FRAMES), "-keyint_min", str(CLIP_FRAMES), "-sc_threshold", "0",
           *(["-frames:v", str(CLIP_FRAMES * len(clips))] if cap else []),
           "-an", "-movflags", "+faststart", out)
    finally:
        os.unlink(lst)

def bump_asset_version():
    v = time.strftime("%Y%m%d%H%M")
    s = open(HTML, encoding="utf-8").read()
    s2, n = re.subn(r'const ASSET_VERSION\s*=\s*"[^"]*"', f'const ASSET_VERSION = "{v}"', s)
    if n:
        open(HTML, "w", encoding="utf-8").write(s2); print(f"  ✓ index.html ASSET_VERSION = {v}")
    else:
        print("  ⚠ index.html 에서 ASSET_VERSION 을 찾지 못했습니다")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--height", type=int, default=0, help="0 = 원본 유지(기본), 720 등 = 재인코딩")
    ap.add_argument("--only", help="예: human 또는 human/young_man")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()

    prev = json.load(open(STAMP)) if os.path.exists(STAMP) else {}
    SIGS.update(prev.get("sigs", {}))
    force = a.force

    jobs = []
    for pdir in sorted(glob.glob(os.path.join(SRC, "*", "*"))):
        form, persona = pdir.split(os.sep)[-2:]
        if a.only and not f"{form}/{persona}".startswith(a.only): continue
        od = os.path.join(OUT, form, persona)
        H = a.height
        for k in KEYS:
            s_ = os.path.join(pdir, k + ".mp4")
            if os.path.exists(s_):
                o = os.path.join(od, k + ".mp4")
                if stale(o, [s_], force, H): jobs.append(("talk", [s_], o))
        talks = [os.path.join(pdir, k + ".mp4") for k in KEYS if os.path.exists(os.path.join(pdir, k + ".mp4"))]
        # 이어 붙일 순서: order.txt (예: "1 3 2 4") 가 있으면 그 순서, 없으면 번호순
        of = os.path.join(pdir, "order.txt")
        order = [int(x) for x in open(of).read().split()] if os.path.exists(of) else [1, 2, 3, 4]
        clips = [c for c in (os.path.join(pdir, f"idle_{i}.mp4") for i in order) if os.path.exists(c)]
        if clips and len(clips) < 4:
            print(f"  ⚠ {form}/{persona}: 대기 클립 {len(clips)}/4 개로 idle.mp4 를 만듭니다 "
                  f"({', '.join(os.path.basename(c) for c in clips)})")
        if clips:
            o = os.path.join(od, "idle.mp4")
            if stale(o, clips + talks, force, H): jobs.append(("idle", (clips, talks), o))
            j = os.path.join(IMG, f"{form}_{persona}.jpg")
            if stale(j, clips + talks, force, H): jobs.append(("still", [o], j, clips + talks))
        # 다시듣기·듣기 대기(눈 깜빡임) : blink_1, blink_2 … 를 이어 붙여 wait.mp4. 없으면 예전 wait.mp4 한 개
        blinks = sorted(glob.glob(os.path.join(pdir, "blink_*.mp4")))
        w = os.path.join(pdir, "wait.mp4")
        wsrc = blinks or ([w] if os.path.exists(w) else [])
        if wsrc:
            o = os.path.join(od, "wait.mp4")
            if stale(o, wsrc + talks, force, H): jobs.append(("wait", (wsrc, talks), o))
        elif clips:
            print(f"  ⚠ {form}/{persona}: wait.mp4(다시듣기 대기 클립)가 없습니다")

    if not jobs:
        print("모두 최신입니다."); return
    for job in jobs:
        print(f"  {job[0]:5s} → {os.path.relpath(job[2], ROOT)}")
    if not a.apply:
        print(f"\n(미리보기 {len(jobs)}건. 만들려면 --apply)"); return

    for job in jobs:
        kind, ins, out = job[:3]
        os.makedirs(os.path.dirname(out), exist_ok=True)
        if kind == "talk":
            build_talk(ins[0], out, a.height); srcs = ins
        if kind in ("idle", "wait"):
            cm = color_match(ins[1], ins[0])
            build_idle(ins[0], out, a.height, cm, cap=(kind == "idle" or "blink_" in os.path.basename(ins[0][0])))
            print("    색 보정 (R,G,B gain·offset):" if cm else "    색 보정 없음 (질문 영상이 아직 없음 — 들어오면 다시 만들어짐)", cm or "")
            srcs = ins[0] + ins[1]
        if kind == "still":
            ff("-i", ins[0], "-frames:v", "1", "-q:v", "3", out); srcs = job[3]
        SIGS[os.path.relpath(out, ROOT)] = sig(srcs, a.height)
        print(f"  ✓ {os.path.relpath(out, ROOT)}")
    json.dump({"height": a.height, "sigs": SIGS}, open(STAMP, "w"), ensure_ascii=False, indent=0)
    bump_asset_version()
    print("\n다음 단계: python3 tools/check_assets.py")

if __name__ == "__main__":
    main()
