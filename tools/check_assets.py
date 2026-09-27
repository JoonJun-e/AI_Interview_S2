#!/usr/bin/env python3
"""조건별로 실험을 돌릴 수 있는 상태인지 점검한다.

  python3 tools/check_assets.py

index.html 의 판정 규칙을 그대로 따른다.
  · x 조건      : mp3 만 있으면 된다 (오브)
  · avatar/human: 해당 조건의 영상이 전부 있어야 영상 모드,
                  하나라도 없으면 그 조건 전체가 사진+mp3 모드로 내려간다.
"""
import os, sys, subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = os.path.join(ROOT, "deploy/assets")
PER  = ["middle_man","young_woman","young_man"]
KEYS = ["intro","1-1","1-2","2-1","2-2","3-1","3-2"]
LBL  = {"middle_man":"중년남","young_woman":"젊은여","young_man":"젊은남"}
QA   = {"intro":"middle_man","1-1":"middle_man","1-2":"middle_man",
        "2-1":"young_woman","2-2":"young_woman","3-1":"young_man","3-2":"young_man"}

def ex(*p): return os.path.exists(os.path.join(A, *p))

def cond_assets(agents, form, solo=None):
    """그 조건이 필요로 하는 (mp3, 사진, 영상) 경로"""
    mp3 = [("audio/voice/%s/%s.mp3" % (QA[k] if agents==3 else solo, k)) for k in KEYS]
    if form == "x": return mp3, [], []
    seats = PER if agents==3 else [solo]
    img = ["persona/%s_%s.jpg" % (form, p) for p in seats]
    vid = [("video/%s/%s/%s.mp4" % (form, QA[k] if agents==3 else solo, k)) for k in KEYS]
    vid += ["video/%s/%s/idle.mp4" % (form, p) for p in seats]
    vid += ["video/%s/%s/wait.mp4" % (form, p) for p in seats]
    return mp3, img, vid

def main():
    print("== 공통 에셋 ==")
    for t, ps in [("음성 mp3", ["audio/voice/%s/%s.mp3"%(p,k) for p in PER for k in KEYS]),
                  ("사진",     ["persona/%s_%s.jpg"%(f,p) for f in ("human","avatar") for p in PER]),
                  ("사전안내", ["audio/notice/single.mp3","audio/notice/multi.mp3"])]:
        miss=[x for x in ps if not ex(x)]
        print("  %-10s %2d/%-2d %s"%(t, len(ps)-len(miss), len(ps), "OK" if not miss else "누락: "+", ".join(miss)))

    print("\n== 조건별 실행 가능 여부 ==")
    rows=[]
    for agents in (1,3):
        for form in ("x","avatar","human"):
            solos = PER if agents==1 else [None]
            for solo in solos:
                mp3,img,vid = cond_assets(agents, form, solo)
                m3=[p for p in mp3 if not ex(p)]; mi=[p for p in img if not ex(p)]; mv=[p for p in vid if not ex(p)]
                name = "%s / %s%s" % ("single" if agents==1 else "multi ", form,
                                      "" if agents==3 else " / "+LBL[solo])
                if m3 or mi:
                    state = "실행 불가"; note = "필수 누락 %d개" % (len(m3)+len(mi))
                elif form == "x":
                    state = "오브";      note = ""
                elif mv:
                    state = "사진 모드"; note = "영상 %d/%d 누락" % (len(mv), len(vid))
                else:
                    state = "영상 모드"; note = ""
                rows.append((name, state, note))
    w=max(len(r[0]) for r in rows)
    for name, state, note in rows:
        print("  %-*s  %-9s %s" % (w, name, state, note))
    bad=[r for r in rows if r[1]=="실행 불가"]
    photo=[r for r in rows if r[1]=="사진 모드"]
    print("\n  영상 모드 %d · 오브 %d · 사진 모드 %d · 실행 불가 %d"
          %(sum(1 for r in rows if r[1]=="영상 모드"), sum(1 for r in rows if r[1]=="오브"),
            len(photo), len(bad)))
    if photo: print("  ※ 사진 모드 조건이 남아 있으면 조건 간 자극 종류가 달라집니다.")
    sys.exit(1 if bad else 0)

if __name__ == "__main__":
    main()
