# gaeguri-instagram

@gaeguribhai (Gaeguri Bhai) 릴스 자동 업로드. 매일 밤 10시 무렵(KST, 인도 저녁 6시 30분)에 그날 날짜의 릴스를 올려요.

- `schedule.json`: 게시 일정과 캡션. `"approved": true`인 것만 올라가요.
- `media/reels/`: 영상 (raw.githubusercontent.com 주소로 인스타가 가져가요).
- `published.json`: 올라간 게시물 기록 (같은 영상이 두 번 올라가지 않게).
- `check` 워크플로: schedule.json이 바뀌면 다음 게시물을 공개 없이 미리 만들어 봐서 문제가 없는지 확인해요.

필요한 Secrets (Settings → Secrets and variables → Actions): `IG_ACCESS_TOKEN`, `IG_USER_ID`.
Instagram 로그인 토큰(IGAA...)이면 60일마다 만료되니 `GH_PAT`(이 저장소 Secrets 읽기·쓰기 fine-grained 토큰)을 넣으면 매달 1일·15일 자동 갱신돼요.
