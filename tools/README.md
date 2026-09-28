# tools — 자극물 편입 · 생성 · 점검

필요: `python3`, `ffmpeg`, `numpy`(편입 때만, `pip3 install numpy`). 저장소 어디서 실행해도 됩니다.

```
받은 폴더 ──ingest_assets.py──▶ _source/video/ ──build_assets.py──▶ deploy/assets/  ──check_assets.py──▶ 점검
```

## 1. 새 영상 편입 — `ingest_assets.py`

```bash
python3 tools/ingest_assets.py "받은폴더"            # 미리보기: 무엇이 어느 문항으로 가는지 출력
python3 tools/ingest_assets.py "받은폴더" --apply    # _source/video/<form>/<persona>/ 로 이동
python3 tools/ingest_assets.py "받은폴더" --form avatar --persona young_woman   # 추정이 틀릴 때
```

- form · persona 는 폴더명/파일명(`avatar_youngwoman`, `human_middle_man`, `아바타_중년` 등)에서 추정합니다.
- **질문 영상은 파일 번호를 믿지 않습니다.** 영상 속 음성을 `deploy/assets/audio/voice/<persona>/*.mp3` 와
  파형으로 대조해 문항을 정합니다. 실제로 0926 배치에서 젊은여 2↔3, 젊은남 번호가 뒤섞여 있었습니다.
  일치도 0.85 미만이거나 2순위와 0.10 이상 차이 나지 않으면 옮기지 않고 보고만 합니다.
- 영상 길이가 음성과 0.3초 이상 다르면 ⚠ 로 표시합니다 (끝 무음 패딩 등).
- 파일명에 `blink` / `깜빡` / `wait` / `replay` 가 있으면 **다시듣기 대기 클립** → `wait.mp4`.
- 파일명에 `silence` / `idle` / `침묵` / `대기` 가 있으면 답변 대기 클립이며, 끝 번호(1~4)가 이어 붙이는 순서입니다.
- 기존 파일을 덮어쓰게 되면 기존 파일은 `_to_delete/replaced/<날짜>/` 로 옮깁니다.

## 2. 배포용 파일 생성 — `build_assets.py`

```bash
python3 tools/build_assets.py                       # 미리보기
python3 tools/build_assets.py --apply               # 원본 해상도 그대로 (재인코딩 없이 faststart 만)
python3 tools/build_assets.py --apply --height 720  # 720p 재인코딩 (용량 약 1/6)
python3 tools/build_assets.py --apply --only avatar/young_woman
```

- 질문 영상 → `deploy/assets/video/<form>/<persona>/<key>.mp4`
- 답변 대기 클립(있는 것만, 1~4개) → 질문 영상 색에 맞춰 보정 후 이어 붙여 `idle.mp4` (24fps, 클립 경계 키프레임, 소리 제거)
- 다시듣기 대기 클립 → 같은 보정으로 `wait.mp4`
- 이어 붙이는 순서를 바꾸려면 `_source/video/<form>/<persona>/order.txt` 에 `1 3 2 4` 처럼 적습니다.
  질문 영상이 아직 없으면 보정 없이 만들고, 질문 영상이 들어오면 다음 실행 때 자동으로 다시 만듭니다.
- `idle.mp4` 첫 프레임 → `deploy/assets/persona/<form>_<persona>.jpg`
- 새로 만든 게 있으면 `deploy/index.html` 의 `ASSET_VERSION` 을 갱신합니다 (브라우저 캐시 무효화).
- 입력 파일(이름·크기·수정시각)과 해상도가 지난번과 같으면 건너뜁니다. 클립을 빼거나 바꿔도 알아서 다시 만듭니다. 강제로 다시: `--force`

## 3. 조건별 점검 — `check_assets.py`

```bash
python3 tools/check_assets.py
```

index.html 과 같은 규칙으로 12개 배정 버킷이 각각 영상 모드 · 사진 모드 · 오브 · 실행 불가 중
어디에 해당하는지 출력합니다. 필수 에셋이 빠진 조건이 있으면 종료 코드 1.
**본실험 전에는 사진 모드와 실행 불가가 모두 0** 이어야 합니다.

## 폐기한 도구

`clean_idle.py`(25초 대기 영상의 입 벌림 구간 제거)와 이전 `ingest_assets.py`(파일 번호로 문항 추정)는
`_to_delete/tools_old/` 로 옮겼습니다.
