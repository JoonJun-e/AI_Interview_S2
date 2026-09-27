# tools — 자극물 교체 도구

자극물 배치가 들어올 때마다 파일명 규칙이 달라져서, 편입·정리·점검을 스크립트로 고정해 둡니다.
모든 스크립트는 저장소 어디서 실행해도 됩니다.

## 새 배치 편입

```bash
python3 tools/ingest_assets.py "deploy/assets/새배치폴더"          # 무엇을 어디로 옮길지만 출력
python3 tools/ingest_assets.py "deploy/assets/새배치폴더" --apply  # 실제 편입
```

파일명/폴더명에 든 단서로 form(human·avatar) · persona(중년남·젊은여·젊은남) · key 를 추정합니다.
`사람_중년_남성.png`, `avatar-young-man-3/avatar-young-man-3.mp4`, `human-middle-man-silence.mp4`
같은 형태를 모두 인식하고, **추정이 안 되면 건드리지 않고 목록으로 보고**합니다.

- 사진은 JPEG q92 로 변환해 `persona/<form>_<persona>.jpg` 에 넣고, 6장 규격이 섞였는지 확인합니다.
- 영상은 `video/<form>/<persona>/<key>.mp4` 에 넣습니다. key = intro · 1-1 · 1-2 · 2-1 · 2-2 · 3-1 · 3-2 · idle
- 덮어쓰는 기존 파일은 `_archive/replaced/` 로 옮깁니다.

## 대기 영상 입 벌림 제거

```bash
python3 tools/clean_idle.py                      # 전체 검사만
python3 tools/clean_idle.py --apply              # 적용
python3 tools/clean_idle.py human/middle_man --apply
```

무음으로 만든 idle 영상에도 입이 움직이는 구간이 섞여 들어옵니다. 그 구간을 잘라내고
**자세가 가장 비슷한 프레임에서 하드컷**으로 이어 붙입니다. 크로스페이드는 입술이 이중으로
겹쳐 보여 쓰지 않습니다(실제로 겪은 문제입니다).

- 원본은 `_archive/idle_original/` 에 보관합니다.
- 남는 길이가 8초 미만이면 적용하지 않고 보고만 합니다.
- 25초보다 짧은 파일은 이미 처리된 것으로 보고 건너뜁니다.
- **적용 후 `_archive/idle_check/*_check.png` 를 반드시 눈으로 확인하세요.**
  입 벌린 프레임이 남아 있으면 `plan()` 의 `fa`(기본 0.35)를 낮춰 재실행합니다.

## 조건별 점검

```bash
python3 tools/check_assets.py
```

index.html 과 같은 규칙으로 12개 배정 버킷이 각각 영상 모드 · 사진 모드 · 오브 · 실행 불가
중 어디에 해당하는지 출력합니다. 필수 에셋이 빠진 조건이 있으면 종료 코드 1 을 냅니다.
