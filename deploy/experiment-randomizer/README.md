# 6-condition Experiment Randomizer — condition 숨김 버전

한 개의 배포 링크로 참가자를 6개 조건에 자동 배정하는 작은 웹앱입니다.

## 참가자가 경험하는 흐름

1. 참가자가 공통 Vercel 링크 하나에 접속합니다.
2. 시스템이 브라우저용 임시 토큰을 생성합니다.
3. Supabase DB에서 현재 6개 조건의 배정 인원을 확인합니다.
4. 현재 인원이 가장 적은 조건들 중 하나를 무작위 선택합니다.
5. `P0001` 형태의 participant ID를 자동 생성하여 DB에 저장합니다.
6. 참가자를 해당 조건의 실험 페이지로 이동시킵니다.
7. 참가자 URL에는 participant ID만 표시됩니다.
8. condition은 Supabase DB 안에만 저장됩니다.
9. 같은 브라우저에서 공통 링크를 다시 열면 기존 배정을 그대로 사용합니다.

예를 들어 C4에 배정된 P0001 참가자라도 참가자에게 보이는 주소는 아래처럼 됩니다.

`https://실험주소.com/?participant_id=P0001`

**`condition=C4`는 주소에 나오지 않습니다.** 연구자는 Supabase에서 `P0001 → C4`를 확인합니다.

---

## 조건 코드 예시

- C1 = Single × Voice-only
- C2 = Single × Avatar
- C3 = Single × Human-like
- C4 = Multi × Voice-only
- C5 = Multi × Avatar
- C6 = Multi × Human-like

조건의 실제 의미는 자유롭게 바꿀 수 있습니다. 프로그램 내부에서는 C1~C6만 사용합니다.

---

# 처음부터 설치하는 방법

## STEP 1. 준비할 것

다음 세 가지가 필요합니다.

1. Supabase 계정
2. Vercel 계정
3. 실제 실험 조건별 URL 6개

GitHub를 이용하면 배포와 수정이 편하지만, 필수는 아닙니다.

---

## STEP 2. Supabase 프로젝트 만들기

1. Supabase에 로그인합니다.
2. 새 프로젝트(New project)를 만듭니다.
3. 프로젝트가 생성되면 왼쪽 메뉴에서 **SQL Editor**를 엽니다.
4. 이 폴더의 `supabase.sql` 파일을 엽니다.
5. 파일 내용을 처음부터 끝까지 복사합니다.
6. Supabase SQL Editor에 붙여넣습니다.
7. **Run**을 누릅니다.

성공하면 `experiment_assignments`라는 테이블과 `assign_participant` 함수가 생성됩니다.

---

## STEP 3. Supabase URL과 Secret key 확인

Supabase 프로젝트에서 **Connect** 또는 **Settings → API Keys**로 이동합니다.

다음 두 값을 준비합니다.

- Project URL: `https://xxxx.supabase.co`
- Secret key: 보통 `sb_secret_...` 형태

중요: **Secret key는 절대 index.html이나 공개 코드에 붙여넣지 마세요.** 이 프로젝트에서는 Vercel의 서버 환경변수로만 사용합니다.

---

## STEP 4. 조건별 실험 URL 6개 준비

예를 들어 다음과 같이 준비합니다.

- C1 → `https://example.com/single-voice`
- C2 → `https://example.com/single-avatar`
- C3 → `https://example.com/single-human`
- C4 → `https://example.com/multi-voice`
- C5 → `https://example.com/multi-avatar`
- C6 → `https://example.com/multi-human`

이 URL 자체에 `C1`, `C2`처럼 조건을 추측할 수 있는 이름이 들어 있으면 참가자가 주소창을 보고 조건을 짐작할 수 있습니다. 가능하면 조건 페이지 URL도 중립적인 이름을 사용하세요.

예:

- 권장: `/interview/a7f3`
- 비권장: `/condition-C4-multi-human`

---

## STEP 5. Vercel에 프로젝트 올리기

### GitHub를 사용하는 경우

1. 이 폴더 전체를 하나의 GitHub repository에 업로드합니다.
2. Vercel에 로그인합니다.
3. **Add New → Project**를 선택합니다.
4. 방금 만든 GitHub repository를 Import합니다.
5. Deploy하기 전에 또는 배포 후 Project Settings에서 환경변수를 등록합니다.

### 환경변수 8개

Vercel에서 **Project → Settings → Environment Variables**로 이동하여 아래 값을 등록합니다.

- `SUPABASE_URL`
- `SUPABASE_SECRET_KEY`
- `CONDITION_C1_URL`
- `CONDITION_C2_URL`
- `CONDITION_C3_URL`
- `CONDITION_C4_URL`
- `CONDITION_C5_URL`
- `CONDITION_C6_URL`

예:

`SUPABASE_URL = https://xxxx.supabase.co`

`SUPABASE_SECRET_KEY = sb_secret_xxxxxxxxx`

`CONDITION_C1_URL = https://example.com/interview/a1`

각 환경변수는 실제 값으로 바꾸어 입력합니다.

환경변수를 추가하거나 변경한 뒤에는 **Redeploy**해야 새 값이 기존 배포에 적용됩니다.

---

## STEP 6. 참가자에게 줄 링크

배포가 완료되면 Vercel이 다음과 같은 공통 주소를 만들어줍니다.

`https://your-project.vercel.app`

**참가자에게는 이 주소 하나만 배포합니다.**

참가자는 조건을 선택하지 않습니다. 접속하자마자 시스템이 자동으로 6개 조건 중 하나에 배정합니다.

---

## STEP 7. 배정 데이터 확인

Supabase에서 **Table Editor → experiment_assignments**를 엽니다.

예를 들어 다음과 같이 기록됩니다.

| participant_id | condition_code | assigned_at |
|---|---|---|
| P0001 | C4 | ... |
| P0002 | C1 | ... |
| P0003 | C6 | ... |

`browser_token`도 저장되지만 중복 배정을 막기 위한 내부 값이므로 일반적인 분석에서는 사용하지 않아도 됩니다.

따라서 실험 데이터에서 `participant_id=P0001`만 알면 Supabase에서 P0001을 찾아 실제 조건이 C4였음을 확인할 수 있습니다.

---

# 배정 방식

이 버전은 고정된 6명 단위 block randomization이 아니라 **현재 배정 인원이 가장 적은 조건 우선 + 동률일 경우 무작위 배정** 방식입니다.

예를 들어 현재 배정 수가 다음과 같다면:

`C1=20 / C2=20 / C3=19 / C4=20 / C5=19 / C6=20`

다음 참가자는 C3 또는 C5 중 하나에 랜덤으로 배정됩니다.

따라서 배정된 참가자의 수는 조건 간 거의 동일하게 유지됩니다.

주의: 이것은 **배정자 수**를 균형화합니다. 특정 조건에서 중도이탈자가 더 많이 발생하면 최종 완료자 수는 달라질 수 있습니다.

---

# 테스트 방법

실제 참가자를 모집하기 전에 다음을 확인하세요.

1. 공통 Vercel 링크에 접속합니다.
2. 조건 페이지로 자동 이동되는지 확인합니다.
3. 주소창에 `participant_id=P0001`처럼 ID만 보이는지 확인합니다.
4. 주소창 어디에도 `condition=C1` 같은 값이 없는지 확인합니다.
5. Supabase `experiment_assignments`에서 P0001의 condition이 저장되었는지 확인합니다.
6. 같은 브라우저에서 공통 링크에 다시 접속했을 때 같은 participant ID와 같은 조건으로 이동하는지 확인합니다.
7. 다른 브라우저 또는 시크릿 창으로 테스트해 새로운 ID가 생성되는지 확인합니다.

테스트 데이터를 삭제한 뒤 본 실험을 시작하고 싶다면 Table Editor에서 테스트 행을 삭제하면 됩니다. 본 실험 시작 직전에는 데이터가 비어 있는지 확인하세요.

---

# 참가자에게 condition을 더 확실하게 숨기려면

이 프로그램은 query parameter에서 condition을 제거합니다. 하지만 **실제 조건별 URL 자체가 조건을 드러내면** 참가자가 여전히 추측할 수 있습니다.

예를 들어 아래 주소는 피하는 것이 좋습니다.

`https://example.com/multi-human-condition`

아래처럼 중립적인 주소가 더 좋습니다.

`https://example.com/interview/x4q9`

또한 조건 페이지 화면의 개발자 도구나 소스 코드까지 완전히 숨기는 것은 별개의 보안 문제입니다. 일반적인 참가자 실험에서는 URL과 화면에 조건명을 노출하지 않는 정도로 충분한 경우가 많습니다.
