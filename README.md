# AI Interview S2

AI 면접관 **형태(형태 없음·오브 / 아바타 / 사람) × 면접관 수(Single / Multi)** 2×3 실험 자극물.
브라우저에서 동작하는 정적 웹앱이며, 조건 배정과 녹음 수집은 Google Apps Script 백엔드가 맡습니다.

## 폴더 구조

```
AI_Interview_s2/
├── deploy/                 ← 실제 프로그램 (Vercel 루트 · 로컬 실행 공용)  ★ 배포되는 것은 여기만
│   ├── index.html              프로그램 본체 — 코드 수정은 여기서만
│   ├── vercel.json             배포 설정 (캐시 · 카메라/마이크 권한)
│   └── assets/
│       ├── audio/notice/       사전 안내 음성 single.mp3 · multi.mp3
│       ├── audio/voice/        질문 음성 <persona>/<key>.mp3 (오브 조건 · 사진 모드용)
│       ├── persona/            정지 사진 <form>_<persona>.jpg        ┐ tools/build_assets.py 가
│       └── video/              면접관 영상 <form>/<persona>/*.mp4    ┘ _source/ 에서 생성
├── _source/                ← 영상 원본 (Git 제외) — 새 영상은 여기로 편입
├── _to_delete/             ← 버릴 파일 모음 (Git 제외) — 확인 후 폴더째 삭제
├── backend/                ← 조건 자동 배정 + 녹음 수집 (Apps Script)
├── tools/                  ← 자산 편입 · 생성 · 점검 스크립트
├── start.command           ← Mac 로컬 실행 (deploy/ 를 localhost:8000 으로 서빙)
├── start_windows.bat · server.ps1   ← Windows 로컬 실행
├── README.md · 실행방법.md
```

폴더별 자세한 규칙은 각 폴더의 README 를 보세요
(`deploy/assets/video/README.md`, `tools/README.md`, `backend/README.md`, `_source/README.md`).

## 자산 현황 (2026-09-28 기준)

| 형태 | 상태 |
|---|---|
| 형태 없음 (오브) | 완료 — 음성 mp3 21개 |
| 사람 | **완료** — 3인 × (질문 7 + 대기) 영상, 워터마크 제거본 |
| 아바타 | **완료** — 3인 × 질문 7 · 눈 깜빡임 · 대기 영상. 대기 클립은 3종(입 벌림 클립 제외, 교체본 대기) |

현재 상태는 언제든 `python3 tools/check_assets.py` 로 확인할 수 있습니다.

## 조건 · 면접관 배정

| 형태 | Single | Multi |
|---|---|---|
| 형태 없음 | 오브 1개 + 음성 | 오브 3개 + 음성 |
| 아바타 | 아바타 1인 영상 | 아바타 3인 영상 |
| 사람 | 실사 1인 영상 | 실사 3인 영상 |

- **Multi**: 면접관 1(중년 남, 왼쪽) → 자기소개·1-1·1-2 / 면접관 2(젊은 여, 가운데) → 2-1·2-2 / 면접관 3(젊은 남, 오른쪽) → 3-1·3-2
- **Single**: 배정된 페르소나 1명이 7문항 전부. Single 은 페르소나별로 나뉘어 **배정 버킷은 총 12개**입니다.
- 음성은 형태와 무관하게 동일한 녹음입니다.

## 조건 배정 · 데이터 수집

참가자에게 **링크 하나만** 배포하면 참가자 번호가 자동 생성되고 인원이 가장 적은 버킷에 배정됩니다.
조건은 URL에 드러나지 않습니다. 답변 녹음은 문항마다 구글 드라이브로 업로드되고,
배정·진행 로그는 스프레드시트에 쌓입니다. 종료 화면의 실험자용 메뉴에서도 로그 CSV·녹음을 받을 수 있습니다.

- 배정 기록 · 로그 → [AI면접_배정기록](https://docs.google.com/spreadsheets/d/1mD3lP4jtQiDVYcUeQ6VJ_Br1i0qh9nthAOHOZ4UoZu0/edit)
- 녹음 파일 → [AI면접_녹음](https://drive.google.com/drive/folders/1QWtun8uh4Ow9lJMFcAx536DSJHVwP7fr)
- 데모·테스트: 주소 뒤에 `?admin=1` → 조건 직접 선택

`deploy/index.html` 의 `BACKEND_URL` 을 비우면 실험자 수동 선택 모드로 돌아갑니다. 자세한 내용은 `backend/README.md`.

## 본실험 전 체크리스트 (`deploy/index.html` 상단 CONFIG)

| 항목 | 지금 (테스트) | 본실험 |
|---|---|---|
| `ENFORCE_MIN` — 30초 전 [답변 완료] 잠금 | `false` | **`true`** |
| `STICKY_ASSIGNMENT` — 같은 브라우저는 같은 조건 | `false` | **`true`** |
| `LOCK_UNTIL_NOTICE` — 안내 음성이 끝나야 다음으로 | `true` | `true` |
| `SURVEY_URL` — 종료 후 설문 주소 | 확인 | 확인 |

그리고 `python3 tools/check_assets.py` 결과에 **사진 모드 · 실행 불가가 0** 이어야 합니다.
백엔드는 12개 버킷 모두에 배정하므로, 아바타 영상이 없는 상태로 참가자를 받으면 아바타 조건 참가자는 사진 모드를 보게 됩니다.

그 밖의 설정: `QUESTIONS`(문항·담당 면접관·제한시간), `REPLAY_WINDOW`(다시 듣기 선택 5초), `SAVE_SECONDS`, `USE_VIDEO`.

## Vercel 배포

1. 저장소를 Vercel 에서 Import → **Framework Preset**: `Other`
2. **Root Directory**: `deploy` ← 반드시 변경. 빌드 설정은 비워 둠 (정적 사이트)
3. 이후에는 GitHub 에 푸시하면 자동 배포

## 로컬 실행

Mac 은 `start.command`, Windows 는 `start_windows.bat` 더블클릭 → `http://localhost:8000`.
카메라·마이크는 `localhost` 또는 HTTPS 에서만 동작하므로 `index.html` 을 직접 더블클릭하면 안 됩니다.
자세한 내용은 `실행방법.md`.

## 새 영상이 들어왔을 때

```bash
python3 tools/ingest_assets.py "받은폴더"            # 미리보기 — 파형 대조로 문항 자동 판별
python3 tools/ingest_assets.py "받은폴더" --apply    # _source/ 로 편입
python3 tools/build_assets.py --apply                # deploy/ 용 파일 생성 (필요하면 --height 720)
python3 tools/check_assets.py                        # 조건별 점검
```
