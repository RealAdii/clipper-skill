---
name: clipper
description: Turn a long interview, podcast, panel or X broadcast (Eli Ben-Sasson style) into a pack of topical, post-ready clips. Downloads the source (X, YouTube, any yt-dlp link, or a local file), transcribes it with MLX Whisper, picks the strongest moments, cuts clean clips on word boundaries, QA-checks every cut, packages everything into a folder (plus zip) on the Desktop, uploads the videos to Google Drive with public links, and builds a shareable Google Doc with captions, timestamps and a link for every clip. Use when the user says "clip this", "make clips from this interview", "cut eli's podcast into clips", "the clipping thing", "clip it and put it on drive", "make the clips doc", or pastes a video link or file and wants clips.
---

# clipper

The full pipeline we ran for Eli's The Block interview (Oct 26) and the "What If Bitcoin Can't Survive Quantum?" episode (Nov 3), as one repeatable flow.

```
source (url or file)
  -> fetch.sh        download to <work>/source.mp4
  -> transcribe.py   full.wav, segments.json, transcript.txt
  -> YOU             read the transcript, write plan.json (clips + captions)
  -> cut.py          clips/*.mp4 (and full_episode.mp4)
  -> check.py        head/tail transcripts, first/last frames, contact sheet
  -> words.py        word-level timing to fix any bad boundary, then re-cut
  -> package.py      ~/Desktop/<slug>/ + ~/Desktop/<slug>.zip
  -> drive_upload.py Drive folder, every video shared "anyone with link"
  -> make_doc.py     Google Doc with captions + links, shared, link printed
```

`S` below means this skill's `scripts/` directory. Every script takes the work dir as its first argument. Work dirs live in `~/liveclip/<slug>/`.

## 0. setup (once per machine)

```bash
PY=$(S/setup.sh)          # prints a python with mlx-whisper; reuses ~/liveclip/.venv if present
```

Needs `ffmpeg`, `yt-dlp` (brew), `gcloud` (for Drive), Apple Silicon (MLX). The whisper model is `mlx-community/whisper-large-v3-turbo` (downloads on first run, about 1.6 GB).

## 1. fetch

```bash
S/fetch.sh "<url or path>" ~/liveclip/<slug>
```

- Local file: symlinked as `source.<ext>`, nothing copied.
- URL: yt-dlp, best mp4. If X or YouTube wants a login, rerun with `CLIPPER_COOKIES=chrome`.
- X live broadcasts: the replay URL (`x.com/i/broadcasts/...`) works once the stream ends. For a stream that is still live, use `S/live/liveclip <url>` (rolling 20 min buffer into `~/liveclip/buf`) and `S/live/clip <seconds>` to grab the last N seconds.
- Prints duration, resolution and size. Sanity check it is the right video.

## 2. transcribe

```bash
$PY -I S/transcribe.py ~/liveclip/<slug>
```

Writes `segments.json` and `transcript.txt` with lines like `[12:34 754.2-760.9] text`. A 50 min episode takes a few minutes.

## 3. plan (this is the judgment step, do it yourself)

Read all of `transcript.txt`. Then write `<work>/plan.json`:

```json
{
  "slug": "eli-theblock-oct26",
  "title": "eli ben-sasson on the starting block (the block), oct 26",
  "source_url": "https://x.com/TheBlockCo/status/...",
  "speaker": "eli ben-sasson",
  "handles": "w/ @elibensasson @theblockco",
  "pad": [0.3, 0.8],
  "episode": {
    "trim_start": 29.0,
    "trim_end": null,
    "caption": "eli ben-sasson joins ... \n\n\"verbatim quote\"\n\nfull interview below, timestamps in the replies\n\nw/ @elibensasson",
    "timestamps": [["0:00", "intro"], ["5:26", "why starknet is researching its own l1"]]
  },
  "clips": [
    {
      "name": "01_l1_vote_93pct",
      "title": "the 93% l1 vote",
      "start": 379.04,
      "end": 433.85,
      "hook": "one line on what the clip is about",
      "caption": "x-ready post. context line\n\n\"verbatim quote from the clip\"\n\nw/ @elibensasson @theblockco"
    }
  ]
}
```

How to pick clips:

- One idea per clip, 30 s to 2 min. Usually 6 to 13 clips per hour of footage.
- Start on the first word of a complete thought (the question can be dropped if the answer stands alone). End on the full stop of the answer, never mid-sentence or on "and so...".
- Prefer moments with a quotable line, a strong claim, a number, or a clean analogy. Include the episode's own cold open as clip 01 if it has one.
- `name` is `NN_snake_case_topic`. Order by how strong the clip is, or by episode order if the user prefers.
- `start` / `end` are seconds in the source. `pad` adds pre-roll and tail at cut time (default 0.3 s and 0.8 s), so put the times on the words themselves.
- `episode` is optional. Set it to cut a trimmed full episode (drops pre-show dead air via `trim_start`). Timestamps are relative to the trimmed episode. Set `"episode": null` to skip it.

Caption rules (house style, non-negotiable):

- all lowercase, casual, the user's voice. No emojis, no hashtags, no corporate framing.
- Quotes are verbatim from the transcript (lowercased). Never invent or "clean up" a quote beyond dropping ums.
- No em dashes or en dashes anywhere. Use commas, colons, periods. The scripts assert this and will refuse to write.
- Tag the speaker and the show at the end (`w/ @handle @show`). Look up the show's real X handle if unsure.
- Flag profanity in the hook (for example "contains the f-word, check before posting from a brand account").

## 4. cut

```bash
$PY -I S/cut.py ~/liveclip/<slug>              # all clips + full episode
$PY -I S/cut.py ~/liveclip/<slug> --only 03_x  # re-cut one clip after fixing plan.json
```

H.264 CRF 18, AAC 160k, `+faststart`, short audio fades so cuts never click. Runs 3 encodes in parallel.

## 5. check (always, before showing anyone)

```bash
$PY -I S/check.py ~/liveclip/<slug>
```

Prints every clip's duration plus what is said in its first and last 5 s, and writes first/last frames and `check/contact.jpg`. Read the output and open the contact sheet. A clip passes when the head starts on a clean first word, and the tail ends on a finished sentence with no next speaker sneaking in.

To fix a boundary, get word timings around it:

```bash
$PY -I S/words.py ~/liveclip/<slug> 2604 10   # words between 2604 s and 2614 s, absolute times
```

Update `start`/`end` in plan.json, `cut.py --only <name>`, then `check.py --only <name>`. Repeat until every clip passes.

## 6. package to the desktop

```bash
$PY -I S/package.py ~/liveclip/<slug>            # -> ~/Desktop/<slug>/ and ~/Desktop/<slug>.zip
$PY -I S/package.py ~/liveclip/<slug> --dest ~/Downloads
```

The folder holds every clip, the full episode, `transcript.txt` and `clips.txt` (source times, lengths, hooks, captions). Use the folder name the user asks for (`--name "some folder"`).

## 7. upload to drive

Drive needs a gcloud login with Drive scope. The script checks first and stops with the fix if the token is missing or lacks Drive. Tell the user to run:

```
! gcloud auth login --enable-gdrive-access
```

Uploading makes the files public ("anyone with the link"). Confirm with the user before the first upload of a new pack.

```bash
python3 -I S/drive_upload.py ~/liveclip/<slug>
```

Creates a Drive folder named after `title`, uploads the full episode and every clip (resumable, 32 MB chunks), shares each publicly and records links in `<work>/links.json`. Safe to rerun: files already in links.json are skipped.

## 8. the doc

```bash
python3 -I S/make_doc.py ~/liveclip/<slug> --no-upload   # writes doc.html only, read it first
python3 -I S/make_doc.py ~/liveclip/<slug>               # creates the Google Doc in the folder, shares it, prints the link
```

The doc has: title, Drive folder link, original source link, the full episode (link, length, caption, timestamps), then one section per clip (title, length, where it sits in the episode, caption, link).

Before handing over the link, verify what a reader gets: export the doc as text (`https://docs.google.com/document/d/<id>/export?format=txt`) without auth and check that the links work anonymously and that no markup leaked through.

## 9. hand over

Reply with: the Desktop folder path, the zip path, the Doc link, the Drive folder link, and the clip list (name, length, one-line hook). Note anything the user should check (profanity, third-party footage rights).

## Past runs (for reference)

- `~/liveclip/theblock/`: Eli on The Block, 8 clips + full episode, Drive + Doc.
- `~/liveclip/btcquantum/`: Eli on "What If Bitcoin Can't Survive Quantum?", 13 clips, zip to Downloads, Drive.
