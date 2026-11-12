# clipper

A Claude Code skill that turns a long interview, podcast or X broadcast into a pack of post-ready clips:

1. download the source (X, YouTube, anything yt-dlp reads, or a local file)
2. transcribe it locally with MLX Whisper (large-v3-turbo)
3. Claude reads the transcript and picks the clips, with captions in house style
4. cut every clip with ffmpeg, then QA each boundary by transcribing its first and last 5 s
5. package everything into a folder and zip on the Desktop
6. upload the videos to Google Drive, shared "anyone with the link"
7. build a Google Doc with the captions, timestamps and a link for every clip

Built from the Eli Ben-Sasson clip packs (The Block, Oct 2026, and "What If Bitcoin Can't Survive Quantum?", Nov 2026).

## install

```bash
git clone https://github.com/RealAdii/clipper-skill ~/clipper-skill
ln -s ~/clipper-skill/clipper ~/.claude/skills/clipper
```

Then in Claude Code: "clip this <url>" or `/clipper <url>`.

## needs

- macOS on Apple Silicon (MLX)
- `ffmpeg`, `yt-dlp` (`brew install ffmpeg yt-dlp`)
- `gcloud` logged in with Drive access for the upload step: `gcloud auth login --enable-gdrive-access`
- `clipper/scripts/setup.sh` builds a venv with `mlx-whisper` on first run

See [clipper/SKILL.md](clipper/SKILL.md) for the full flow.
