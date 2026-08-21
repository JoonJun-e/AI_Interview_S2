# AI Interview S2

AI 면접관 형태(형태 없음 / 아바타 / 사람 형태) × 면접관 수(Single / Multi) **2×3 실험 자극물**.

브라우저에서만 동작하는 정적 웹앱입니다. 서버로 전송되는 데이터가 없으며,
답변 녹음과 로그는 참가자 브라우저 안에만 존재하고 종료 화면에서 직접 내려받습니다.

## 폴더 구조

```
AI_Interview_S2/
├── deploy/            ← 실제 프로그램 (배포 + 로컬 실행 공용)
│   ├── index.html         프로그램 본체 ★ 수정은 여기서만
│   ├── vercel.json        배포 설정
│   └── assets/            영상 · 음성 · 화면 자산 (720p)
├── start.command      ← Mac 실행 (deploy/ 를 서빙)
├── start_windows.bat  ← Windows 실행
├── server.ps1         ← Windows 내장 서버
├── backend/           ← 조건 자동 배정 + 녹음 수집 (Google Apps Script)
│   ├── Code.gs            스크립트 본문
│   └── README.md          설치 가이드
├── README.md
├── 실행방법.md
└── _archive/          ← Git 제외 · 없어도 프로그램은 동작함
```

## 조건 배정 · 녹음 수집

참가자에게 **링크 하나만** 배포하면 접속 시 참가자 번호가 자동 생성되고
인원이 가장 적은 조건에 배정됩니다. 조건은 URL에 노출되지 않습니다.
답변 녹음은 문항이 끝날 때마다 구글 드라이브로 자동 업로드됩니다.

- 배정 기록 · 로그 → [AI면접_배정기록](https://docs.google.com/spreadsheets/d/1mD3lP4jtQiDVYcUeQ6VJ_Br1i0qh9nthAOHOZ4UoZu0/edit)
- 녹음 파일 → [AI면접_녹음](https://drive.google.com/drive/folders/1QWtun8uh4Ow9lJMFcAx536DSJHVwP7fr)

`deploy/index.html` 의 `BACKEND_URL` 을 비우면 예전처럼 실험자 수동 선택 모드로 돌아갑니다.
자세한 내용은 `backend/README.md`.

| 구분 | 폴더 | 용량 | Git |
|---|---|---|---|
| **배포용** | `deploy/` + 실행 스크립트 + 문서 | 68MB | 포함 |
| **보관용** | `_archive/` | 621MB | 제외 |

### `_archive/` 안에 있는 것

| 폴더 | 내용 | 삭제해도 되나 |
|---|---|---|
| `original_1080p/` | 원본 1080p 영상·음성·이미지 | 재인코딩할 일이 없다면 가능 |
| `duplicate_backup/` | `original_1080p/video` 와 동일한 중복본 | **바로 삭제 권장 (298MB)** |
| `index.html.bak` | 재구성 전 최상위 index.html (deploy 본과 동일) | 가능 |

## Vercel 배포

1. 이 저장소를 Vercel 에서 Import
2. **Framework Preset**: `Other`
3. **Root Directory**: `deploy` ← 반드시 변경
4. Build/Output 설정은 비워 둠 (정적 사이트)
5. Deploy

## 로컬 실행

Mac 은 `start.command`, Windows 는 `start_windows.bat` 더블클릭.
`deploy/` 폴더를 `http://localhost:8000` 으로 서빙하므로 배포본과 완전히 동일하게 동작합니다.

카메라·마이크는 보안 정책상 `localhost` 또는 HTTPS 에서만 동작합니다.
`index.html` 을 그냥 더블클릭(`file://`)하면 작동하지 않습니다. 자세한 내용은 `실행방법.md`.

## 조건 설정

로그인 화면 하단의 실험자 설정에서 선택합니다.

| 형태 | Single | Multi |
|---|---|---|
| 형태 없음 | 원 1개 + 파동 (음성) | 원 3개 + 파동 (음성) |
| 아바타 | 아바타 1인 영상 | 아바타 3인 영상 |
| 사람 형태 | 실사 1인 영상 | 실사 3인 영상 |

면접관 배정 (Multi): 면접관 1(중년 남자) → 자기소개·1-1·1-2, 면접관 2(여자) → 2-1·2-2,
면접관 3(남자) → 3-1·3-2.

## 설정 변경 (`deploy/index.html` 상단 CONFIG)

| 항목 | 설명 |
|---|---|
| `QUESTIONS` | 문항 텍스트, 담당 면접관, 답변 제한시간 |
| `SURVEY_URL` | 종료 후 연결할 설문 주소 (비우면 안내만 표시) |
| `ENFORCE_MIN` | `true` 로 바꾸면 30초 전까지 [답변 완료] 버튼 잠금 (본실험용) |
| `REPLAY_WINDOW` | 다시 듣기 선택 시간 (기본 5초) |
| `SAVE_SECONDS` / `EVAL_SECONDS` | 저장 · 평가 화면 표시 시간 |
| `MEDIA` | 조건별 영상 파일 경로·이름 |
