# 면접관 영상 파일 규칙

포맷: MP4 (H.264 + AAC), 1920×1080 · 16:9. 질문 음성은 영상에 포함되어 있으면 됩니다.

## 면접관 배정

| 면접관 | 인물 | 화면 좌석 | 담당 문항 |
|---|---|---|---|
| 면접관 1 | 중년 남자 | 가운데 | 자기소개, 1-1, 1-2 |
| 면접관 2 | 일반 여자 | 오른쪽 | 2-1, 2-2 |
| 면접관 3 | 일반 남자 | 왼쪽 | 3-1, 3-2 |

## 폴더 구조

```
assets/video/
├── human/
│   ├── Multi/    ← 사람 형태 · 면접관 3명   (완료)
│   └── single/   ← 사람 형태 · 면접관 1명   (준비 중)
└── avatar/
    ├── Multi/    ← 아바타 · 면접관 3명      (완료)
    └── single/   ← 아바타 · 면접관 1명      (완료)
```

폴더명 대소문자(`Multi` / `single`)를 그대로 지켜 주세요.

## Multi agent — 완료 (human · avatar 모두)

| 문항 | 면접관 | human | avatar |
|---|---|---|---|
| 자기소개 | 1 | `multi0-0.mp4` | `avatar-m0-0.mp4` |
| 1-1 | 1 | `multi1-1.mp4` | `avatar-m1-1.mp4` |
| 1-2 | 1 | `multi1-2.mp4` | `avatar-m1-2.mp4` |
| 2-1 | 2 | `multi2-1.mp4` | `avatar-m2-1.mp4` |
| 2-2 | 2 | `multi2-2.mp4` | `avatar-m2-2.mp4` |
| 3-1 | 3 | `Multi3-1.mp4` | `avatar-m3-1.mp4` |
| 3-2 | 3 | `Multi3-2.mp4` | `avatar-m3-2.mp4` |
| 대기 | 1 | `M1-waiting.mp4` | `avatar-m-1-waiting.mp4` |
| 대기 | 2 | `M2-waiting.mp4` | `avatar-m-2-waiting.mp4` |
| 대기 | 3 | `M3-waiting.mp4` | `avatar-m-3-waiting.mp4` |

대기 영상은 25.7초, 무한 반복 재생됩니다.

## Single agent

`avatar/single/` 는 완료, `human/single/` 은 준비 중입니다. **두 폴더의 파일명은 동일합니다.**

| 문항 | 파일명 |
|---|---|
| 자기소개 | `single0-0.mp4` |
| 1-1 | `single1-1.mp4` |
| 1-2 | `single1-2.mp4` |
| 2-1 | `single2-1.mp4` |
| 2-2 | `single2-2.mp4` |
| 3-1 | `single3-1.mp4` |
| 3-2 | `single3-2.mp4` |
| 대기 | `single-waiting.mp4` |

`human/single/` 에 위 8개를 넣기만 하면 코드 수정 없이 동작합니다.
이름을 다르게 쓰고 싶으면 `index.html` 의 `MEDIA` 설정만 고치면 됩니다.

## 대기 스틸 (자동 생성)

`still_a1.jpg` `still_a2.jpg` `still_a3.jpg` (Multi), `still_single.jpg` (single)
— 각 대기 영상의 첫 프레임입니다. 대기 영상 로드 전이나 재생 실패 시 표시되는 예비 이미지이며,
없으면 `assets/human_multi_*.png` 등 기존 사진으로 대체됩니다.

## 형태 없음(Agent X) 조건 음성

영상 대신 아래 오디오를 사용합니다. (이미 배치 완료)

```
assets/audio/Multi agent/M0_자기소개.mp3, M1-1_문제.mp3 … M3-2_문제.mp3
assets/audio/Single agent/S0_자기소개.mp3, S1-1_문제.mp3 … S3-2_문제.mp3
```

## 아바타 조건 제작 시

`assets/video/avatar/` 에 위 ①②와 **똑같은 파일명**으로 넣으면 코드 수정 없이 동작합니다.
스틸은 넣지 않아도 되며, 없을 경우 `assets/avatar_multi_1~3.png` 크롭 이미지가 대신 표시됩니다.
