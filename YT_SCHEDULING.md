# YouTube scheduling procedure (needs the user's computer: Claude desktop app, built-in browser)

Queue: `yt_queue.json` — entries `{ep, date, title, desc, media, srt, status}`; `status` = `pending` -> `scheduled` (+ `video_id`).
Video + subtitle files are public at `https://raw.githubusercontent.com/seyoungk3030-dotcom/gaeguri-instagram/main/<media|srt>`.
The built-in browser (mcp__remote-devices__Claude_Browser__*) is signed in to YouTube Studio for channel UCSRpEJb17BwqbM6RAPizHJg.
It has NO file_upload tool: inject the file with JavaScript (fetch from raw.githubusercontent -> File -> DataTransfer -> input.files).

Step 0: run `python3 yt_plan.py` (assigns `date` + `time` to pending entries: 22:00 daily, plus a 01:00 KST second slot during the
2026-11-16..29 test; FEST episodes keep their date) and commit yt_queue.json if it changed.

For each pending entry, ordered by (date, time) (skip slots already in the past: mark them `skipped_past`):
1. navigate `https://studio.youtube.com/channel/UCSRpEJb17BwqbM6RAPizHJg/videos/upload?d=ud`, wait 4 s.
2. javascript_exec:
   ```js
   const inp=document.querySelector('input[type=file]'); const b=await (await fetch('RAW_URL_OF_MEDIA')).blob();
   const dt=new DataTransfer(); dt.items.add(new File([b],'gaeguri_epNNN.mp4',{type:'video/mp4'})); inp.files=dt.files;
   inp.dispatchEvent(new Event('change',{bubbles:true})); 'set '+b.size
   ```
   wait 5 s.
3. find "textbox" -> title box (`동영상을 설명하는 제목 추가…`) and description box (`시청자에게 동영상에 대해 설명해 주세요…`).
   Click title, key ctrl+a, type title. Click description, type desc. Verify with
   `[...document.querySelectorAll('#textbox')].map(e=>e.innerText).join('\n---\n')`.
4. find "고급 설정 표시" -> scroll_to + click. find "AI를 사용하지 않았습니다" -> click the radio. find "동영상 언어" (the generic one) -> click,
   wait 1 s, find "힌디어" -> click the first (not 로마자). Verify:
   `[document.querySelector('ytcp-form-language-input')?.innerText, document.querySelector('tp-yt-paper-radio-button[name=VIDEO_HAS_ALTERED_CONTENT_NO]')?.getAttribute('aria-checked')]`
   -> must be "동영상 언어\n힌디어", "true".
5. find `button "다음"` -> click it 3 times (2 s waits). Click (447,456) to expand 예약 (viewport 800x600). Screenshot.
6. Click the date field (~(130,388)) to open the calendar; if it did not open, click again. Screenshot, click the target day.
   If the month differs, use the calendar's next-month arrow (or type the date into the calendar's text field `YYYY. M. D.` + Enter).
7. Click the time field (~(266,388)), find the entry's time: `time` "22:00" -> "오후 10:00", "01:00" -> "오전 1:00" -> scroll_to + click.
   Zoom (60,360,480,420) to verify date + time.
8. Click 예약 (~(732,535)), wait 3 s, screenshot: the dialog must say "동영상 예약됨 … <date> <time>". Read the shorts link -> video id.
9. Subtitles: navigate `https://studio.youtube.com/video/<id>/translations`, wait 4 s, find `button "언어 추가"` -> click, find "타밀어" -> click,
   wait 2 s, click 수동 자막 추가 (~(437,482)), wait 2 s, click 파일 업로드 (~(120,160)), wait 1 s, then javascript_exec:
   ```js
   const ins=[...document.querySelectorAll('input[type=file]')]; const inp=ins[ins.length-1];
   const t=await (await fetch('RAW_URL_OF_SRT')).text(); const dt=new DataTransfer();
   dt.items.add(new File([t],'ta.srt',{type:'application/x-subrip'})); inp.files=dt.files; inp.dispatchEvent(new Event('change',{bubbles:true})); t.length
   ```
   wait 3 s, click 게시 (~(700,62)), check page text shows "타밀어 … 1개 게시됨". (An auto "영어" track may also appear — that is YouTube's auto caption, ignore.)
10. Set the entry `status: "scheduled"`, `video_id`. Commit + push yt_queue.json after every 3 videos.
If YouTube says the daily upload limit is reached, stop and leave the rest pending. Never delete or edit already-public videos.
