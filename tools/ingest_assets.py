#!/usr/bin/env python3
"""새로 받은 면접관 영상 묶음을 _source/video/ 에 편입한다.

  python3 tools/ingest_assets.py <폴더>                  # 무엇을 어디로 옮길지만 출력
  python3 tools/ingest_assets.py <폴더> --apply          # 실제로 옮김
  python3 tools/ingest_assets.py <폴더> --form avatar --persona young_woman   # 추정이 틀릴 때 지정

▸ 말하는 영상(질문 낭독)은 **파일 번호를 믿지 않는다.**
  제작 사이트에서 받은 번호가 문항 순서와 다른 경우가 실제로 있었다(젊은여 2↔3, 젊은남 뒤섞임).
  그래서 영상 속 음성을 deploy/assets/audio/voice/<persona>/<key>.mp3 와 파형으로 대조해
  어느 문항인지 정한다. 일치도가 낮거나 애매하면 옮기지 않고 보고만 한다.

▸ 대기(청취) 클립은 파일명에 silence / idle / 침묵 / 대기 가 들어간 것.
  끝 번호 1~4 가 그대로 이어 붙이는 순서가 된다 → _source/video/<form>/<persona>/idle_<n>.mp4

옮긴 뒤에는 tools/build_assets.py 로 deploy/ 용 파일을 만든다.
이미 있는 파일을 덮어쓰게 되면 기존 파일은 _to_delete/replaced/<날짜>/ 로 옮긴다.
필요: ffmpeg, numpy
"""
import argparse, os, re, sys, glob, shutil, subprocess, datetime
try:
    import numpy as np
except ImportError:
    sys.exit("numpy 가 필요합니다:  pip3 install numpy")

ROOT  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC   = os.path.join(ROOT, "_source", "video")
VOICE = os.path.join(ROOT, "deploy", "assets", "audio", "voice")
TRASH = os.path.join(ROOT, "_to_delete", "replaced", datetime.date.today().isoformat())
KEYS  = ["intro", "1-1", "1-2", "2-1", "2-2", "3-1", "3-2"]
MIN_R, MIN_GAP = 0.85, 0.10          # 파형 일치도 하한 · 2순위와의 최소 차이

FORM_HINTS    = [("avatar", ["avatar", "아바타"]), ("human", ["human", "사람", "실사"])]
PERSONA_HINTS = [("middle_man",  ["middle", "oldman", "중년"]),
                 ("young_woman", ["woman", "여"]),          # woman 을 man 보다 먼저 본다
                 ("young_man",   ["man", "남"])]
IDLE_WORDS = ["silence", "idle", "침묵", "대기"]

def guess(text, hints):
    t = text.lower()
    for name, words in hints:
        if any(w in t for w in words): return name
    return None

def guess_persona(text):
    t = text.lower()
    for w in ("human", "avatar"): t = t.replace(w, " ")     # 'human' 안의 'man' 오인 방지
    return guess(t, PERSONA_HINTS)

def envelope(path, sr=4000):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(sr),
                          "-f", "s16le", "-"], capture_output=True).stdout
    x = np.frombuffer(raw, np.int16).astype(np.float32)
    n = len(x) // 40
    e = np.abs(x[:n * 40]).reshape(n, 40).mean(1)          # 100 Hz 포락선
    return (e - e.mean()) / (e.std() + 1e-9)

def xcorr(a, b):
    n = len(a) + len(b)
    c = np.fft.irfft(np.fft.rfft(a, n) * np.conj(np.fft.rfft(b, n)), n)
    return float(c.max() / min(len(a), len(b)))

def probe(path):
    """(해상도·fps 문자열, 길이 초)"""
    q = lambda *e: subprocess.run(["ffprobe", "-v", "error", *e, "-of", "csv=p=0", path],
                                  capture_output=True, text=True).stdout.strip()
    try: dur = float(q("-show_entries", "format=duration"))
    except ValueError: dur = 0.0
    try:
        w, h, fr = q("-select_streams", "v:0", "-show_entries", "stream=width,height,r_frame_rate").split(",")
        num, den = fr.split("/")
        return f"{w}x{h} {round(int(num)/int(den))}fps", dur
    except ValueError:
        return "audio", dur

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("folder"); ap.add_argument("--form"); ap.add_argument("--persona")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    folder = os.path.abspath(a.folder)
    files = sorted(f for f in glob.glob(os.path.join(folder, "**", "*.mp4"), recursive=True))
    if not files: sys.exit("mp4 파일이 없습니다: " + folder)

    name = os.path.basename(folder)
    form = a.form or guess(name, FORM_HINTS) or guess(files[0], FORM_HINTS)
    persona = a.persona or guess_persona(name) or guess_persona(os.path.basename(files[0]))
    if form not in ("avatar", "human") or persona not in ("middle_man", "young_woman", "young_man"):
        sys.exit(f"form/persona 를 추정하지 못했습니다 (form={form}, persona={persona}). "
                 "--form avatar|human --persona middle_man|young_woman|young_man 로 지정하세요.")
    print(f"== {name}  →  form={form}  persona={persona}\n")

    idle, talk = [], []
    for f in files:
        (idle if any(w in os.path.basename(f).lower() for w in IDLE_WORDS) else talk).append(f)

    plan, problems = [], []
    # 대기 클립
    for f in idle:
        m = re.findall(r"(\d+)", os.path.splitext(os.path.basename(f))[0])
        n = int(m[-1]) if m else None
        spec, dur = probe(f)
        if n not in (1, 2, 3, 4):
            problems.append(f"대기 클립 번호(1~4)를 읽지 못함: {os.path.basename(f)}"); continue
        plan.append((f, f"idle_{n}.mp4", f"대기 {n}번  {spec} {dur:.2f}s"))

    # 말하는 영상 : 파형 대조
    if talk:
        voices = {k: envelope(os.path.join(VOICE, persona, k + ".mp3")) for k in KEYS
                  if os.path.exists(os.path.join(VOICE, persona, k + ".mp3"))}
        vdur = {k: probe(os.path.join(VOICE, persona, k + ".mp3"))[1] for k in voices}
        scores = {f: {k: xcorr(envelope(f), v) for k, v in voices.items()} for f in talk}
        pairs = sorted(((s, f, k) for f, d in scores.items() for k, s in d.items()), reverse=True)
        used_f, used_k = set(), set()
        for s, f, k in pairs:
            if f in used_f or k in used_k: continue
            others = sorted((v for kk, v in scores[f].items() if kk != k), reverse=True)
            gap = s - (others[0] if others else 0)
            spec, dur = probe(f)
            if s < MIN_R or gap < MIN_GAP:
                problems.append(f"{os.path.basename(f)}: 문항을 확정 못함 (최고 {k} r={s:.2f}, 차이 {gap:.2f})")
                used_f.add(f); continue
            used_f.add(f); used_k.add(k)
            dd = dur - vdur[k]
            note = f"r={s:.2f}  {spec} {dur:.2f}s" + (f"  ⚠ 음성보다 {dd:+.2f}s" if abs(dd) > 0.3 else "")
            plan.append((f, f"{k}.mp4", note))
        for f in talk:
            if f not in used_f: problems.append(f"{os.path.basename(f)}: 매칭되는 문항 없음")

    dest_dir = os.path.join(SRC, form, persona)
    for f, dst, note in sorted(plan, key=lambda p: p[1]):
        exists = os.path.exists(os.path.join(dest_dir, dst))
        print(f"  {os.path.basename(f):40s} → {dst:10s} {note}{'  (기존 파일 교체)' if exists else ''}")
    missing = [k for k in KEYS if k + ".mp4" not in {p[1] for p in plan}
               and not os.path.exists(os.path.join(dest_dir, k + ".mp4"))]
    if talk and missing: print("\n  아직 없는 문항:", ", ".join(missing))
    if problems:
        print("\n  ⚠ 옮기지 않은 파일"); [print("   -", p) for p in problems]

    if not a.apply:
        print("\n(미리보기입니다. 실제로 옮기려면 --apply)"); return
    os.makedirs(dest_dir, exist_ok=True)
    for f, dst, _ in plan:
        target = os.path.join(dest_dir, dst)
        if os.path.exists(target):
            bk = os.path.join(TRASH, form, persona); os.makedirs(bk, exist_ok=True)
            shutil.move(target, os.path.join(bk, dst))
        shutil.move(f, target)
    print(f"\n{len(plan)}개 편입 완료 → {os.path.relpath(dest_dir, ROOT)}")
    print("다음 단계: python3 tools/build_assets.py --apply")

if __name__ == "__main__":
    main()
