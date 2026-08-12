# 화면 이미지 넣는 곳

노션 `자극물 앞뒤 플로우 추가` 문서의 이미지를 아래 이름으로 저장하면
해당 화면에 자동으로 표시됩니다. 파일이 없으면 코드로 만든 화면이 그대로 나옵니다.

| 파일명 | 표시 위치 |
|---|---|
| `intro_single.png` | 실험 안내 화면 (Single agent) |
| `intro_multi.png`  | 실험 안내 화면 (Multi agent) |
| `result_single.png` | 결과 화면 (Single agent) |
| `result_multi.png`  | 결과 화면 (Multi agent) |

`assets/screens/` 와 `deploy/assets/screens/` **양쪽에 넣어야** 로컬·배포 모두 반영됩니다.

## 평가 중 화면은?

노션의 평가중 GIF 6종은 사용하지 않습니다. 대신 **면접 화면을 그대로 유지한 채**
배경을 흐리게 하고 "AI 면접관이 지원자님의 답변을 평가하고 있습니다" 오버레이를
15초간 띄웁니다. 면접관 대기 영상이 뒤에서 계속 재생되므로 자극물 디자인이 그대로 이어집니다.
