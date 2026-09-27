#!/usr/bin/env python3
"""대기(idle) 영상에서 입을 벌리는 구간을 잘라내고 이어 붙인다.

  python3 tools/clean_idle.py                       # 전체 idle 검사 (드라이런)
  python3 tools/clean_idle.py --apply               # 적용
  python3 tools/clean_idle.py human/middle_man --apply

동작
  1. 시간축 표준편차로 눈(깜빡임) 위치를 찾고, 그 아래 26~40px 에서 입술선을 잡는다.
  2. 입술선 주변 좁은 띠에서 '입 벌림 두께'와 프레임간 변화량을 재고,
     둘 중 하나라도 기준을 넘으면 그 구간을 버린다 (앞뒤 여유 프레임 포함).
  3. 남은 구간을 이어 붙이되, 경계 ±30프레임을 훑어 화면이 가장 비슷한 지점에서 하드컷한다.
     크로스페이드는 입술이 이중으로 겹쳐 보여 쓰지 않는다.
  4. 원본은 _archive/idle_original/ 에 보관하고, 검수용 몽타주를 남긴다.

※ 3~4단계 결과는 반드시 눈으로 확인할 것. 몽타주 경로를 마지막에 출력한다.
"""
import sys, os, json, subprocess, shlex
import numpy as np, cv2

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VID  = os.path.join(ROOT, "deploy/assets/video")
ARCH = os.path.join(ROOT, "_archive/idle_original")
OUTD = os.path.join(ROOT, "_archive/idle_check")
FPS, SC = 25, 3

def find_idles(filt=None):
    out=[]
    for form in ("human","avatar"):
        for per in ("middle_man","young_woman","young_man"):
            p = os.path.join(VID, form, per, "idle.mp4")
            tag = "%s/%s" % (form, per)
            if os.path.exists(p) and (not filt or filt in tag): out.append((tag, p))
    return out

def scan_small(path):
    """1패스 : 축소 프레임만 모은다 (눈·입 위치 탐색과 이음새 비교용)."""
    cap=cv2.VideoCapture(path); small=[]
    while True:
        ok,f=cap.read()
        if not ok: break
        gr=cv2.cvtColor(f,cv2.COLOR_BGR2GRAY)
        small.append(cv2.resize(gr,(gr.shape[1]//SC, gr.shape[0]//SC)))
    cap.release()
    return np.stack(small).astype(np.float32)

def scan_band(path, my):
    """2패스 : 입술 주변 띠만 원본 해상도로 모은다 (전 프레임을 들고 있지 않는다)."""
    Y0,Y1,X0,X1 = (my-8)*SC,(my+8)*SC,298*SC,342*SC
    cap=cv2.VideoCapture(path); band=[]
    while True:
        ok,f=cap.read()
        if not ok: break
        band.append(cv2.cvtColor(f[Y0:Y1, X0:X1], cv2.COLOR_BGR2GRAY))
    cap.release()
    return np.stack(band).astype(np.float32)

def locate_mouth(S):
    sd = S.std(axis=0); H,W = sd.shape
    y0,y1 = int(H*0.15), int(H*0.50); x0,x1 = int(W*0.44), int(W*0.56)
    eye = y0 + int(np.argmax(sd[y0:y1, x0:x1].sum(axis=1)))     # 깜빡임이 가장 큰 행 = 눈
    win = range(eye+26, eye+40)
    my = list(win)[int(np.argmax([sd[y, 290:350].sum() for y in win]))]
    return eye, my

def features(B):
    ap = np.array([((np.abs(b-np.percentile(b,75))>34).mean(axis=1)>0.25).sum() for b in B], float)
    d  = np.concatenate([[0], np.abs(np.diff(B,axis=0)).mean(axis=(1,2))])
    return ap, d

def plan(ap, d, T, fa=0.35, pd=96, DIL=9, minseg=38):
    N=len(ap)
    a_thr = np.percentile(ap,50) + fa*(np.percentile(ap,99)-np.percentile(ap,50))
    bad = (ap>a_thr) | (d>np.percentile(d,pd))
    m = np.zeros(N,bool)
    for i in np.where(bad)[0]: m[max(0,i-DIL):min(N,i+DIL+1)] = True
    segs=[]; s=None
    for i in range(N):
        if not m[i] and s is None: s=i
        if (m[i] or i==N-1) and s is not None:
            e = i if m[i] else i+1
            if e-s>=minseg: segs.append([s,e])
            s=None
    for k in range(len(segs)-1):                       # 이음새 최적화
        aE,bS = segs[k][1], segs[k+1][0]; best=None
        for de in range(-30,1):
            for ds in range(0,31):
                e,s2 = aE+de, bS+ds
                if e-segs[k][0]<25 or segs[k+1][1]-s2<25: continue
                c=float(np.abs(T[e-1]-T[s2]).mean())
                if best is None or c<best[0]: best=(c,e,s2)
        if best: segs[k][1],segs[k+1][0] = best[1],best[2]
    if segs:                                           # 루프 이음새
        best=None
        for ds in range(0,13):
            for de in range(-12,1):
                s0,e0 = segs[0][0]+ds, segs[-1][1]+de
                if e0-s0<50: continue
                c=float(np.abs(T[e0-1]-T[s0]).mean())
                if best is None or c<best[0]: best=(c,s0,e0)
        if best: segs[0][0],segs[-1][1] = best[1],best[2]
    joins=[round(float(np.abs(T[segs[k][1]-1]-T[segs[k+1][0]]).mean()),2) for k in range(len(segs)-1)]
    seam = round(float(np.abs(T[segs[-1][1]-1]-T[segs[0][0]]).mean()),2) if segs else 0
    return segs, joins, seam, m.sum()

def encode(src, segs, dst):
    parts=[]; labs=[]
    for i,(a,b) in enumerate(segs):
        parts.append("[0:v]trim=start_frame=%d:end_frame=%d,setpts=PTS-STARTPTS[v%d]"%(a,b,i)); labs.append("[v%d]"%i)
    fc=";".join(parts)+";"+"".join(labs)+"concat=n=%d:v=1:a=0,format=yuv420p[v]"%len(segs)
    cmd=('ffmpeg -v error -y -i %s -filter_complex %s -map "[v]" -an '
         '-c:v libx264 -profile:v main -preset medium -r %d -b:v 2600k %s'
         %(shlex.quote(src), shlex.quote(fc), FPS, shlex.quote(dst)))
    r=subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if r.returncode: raise RuntimeError(r.stderr[-500:])

def montage(path, my, out):
    cap=cv2.VideoCapture(path); crops=[]; i=0
    while True:
        ok,f=cap.read()
        if not ok: break
        if i%3==0: crops.append((i, f[(my-11)*SC:(my+11)*SC, 294*SC:346*SC]))
        i+=1
    cap.release()
    if not crops: return
    ch,cw=crops[0][1].shape[:2]; cols=16; rows=int(np.ceil(len(crops)/cols))
    M=np.full((rows*(ch+12), cols*cw,3),255,np.uint8)
    for k,(idx,c) in enumerate(crops):
        r,cc=divmod(k,cols)
        M[r*(ch+12)+12:r*(ch+12)+12+ch, cc*cw:(cc+1)*cw]=c
        cv2.putText(M,str(idx),(cc*cw+2,r*(ch+12)+9),cv2.FONT_HERSHEY_SIMPLEX,0.28,(0,0,0),1)
    cv2.imwrite(out, M)

def main():
    args=[a for a in sys.argv[1:] if not a.startswith("--")]
    apply = "--apply" in sys.argv
    filt = args[0] if args else None
    todo = find_idles(filt)
    if not todo: print("대상 idle.mp4 없음"); return
    os.makedirs(ARCH, exist_ok=True); os.makedirs(OUTD, exist_ok=True)
    for tag, path in todo:
        S = scan_small(path)
        eye, my = locate_mouth(S)
        B = scan_band(path, my)
        ap, d = features(B)
        del B
        segs, joins, seam, cut = plan(ap, d, S)
        dur_in = len(S)/FPS; dur_out = sum(e-s for s,e in segs)/FPS
        if dur_in < 20:
            print("%-22s 길이가 %.1f초 — 이미 처리된 파일로 보입니다. 건너뜁니다."%(tag, dur_in)); continue
        print("%-22s 눈 y=%d 입 y=%d | %.1f초 → %.1f초 (제거 %.1f초, %d구간)"
              %(tag, eye, my, dur_in, dur_out, cut/FPS, len(segs)))
        print("%-22s 이음비용 %s · 루프이음새 %.2f  %s"
              %("", joins, seam, "" if all(j<4 for j in joins) and seam<4 else "← 이음새 티날 수 있음"))
        if dur_out < 8:
            print("%-22s *** 남는 길이가 8초 미만 — 적용하지 않음 (수동 확인 필요) ***"%""); continue
        if not apply: continue
        tmp = os.path.join(OUTD, tag.replace("/","_")+"_new.mp4")
        encode(path, segs, tmp)
        orig = os.path.join(ARCH, tag.replace("/","_")+"_idle_orig.mp4")
        if not os.path.exists(orig): os.replace(path, orig)
        else: os.remove(path)
        os.replace(tmp, path)
        montage(path, my, os.path.join(OUTD, tag.replace("/","_")+"_check.png"))
        print("%-22s 적용 완료 · 검수 몽타주 %s"%("", os.path.relpath(
              os.path.join(OUTD, tag.replace("/","_")+"_check.png"), ROOT)))
    if apply:
        print("\n검수 몽타주를 반드시 눈으로 확인하세요 — 입 벌린 프레임이 남아 있으면 임계값을 낮춰 재실행합니다.")

if __name__ == "__main__":
    main()
