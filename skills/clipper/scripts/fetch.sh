#!/bin/zsh
# usage: fetch.sh <url or local file> <work dir>
# Local files are symlinked as source.<ext>. URLs go through yt-dlp (CLIPPER_COOKIES=chrome if a login is needed).
SRC="$1"; WORK="$2"
[ -z "$SRC" ] || [ -z "$WORK" ] && { echo "usage: fetch.sh <url|file> <work dir>"; exit 1; }
mkdir -p "$WORK"; WORK=$(cd "$WORK" && pwd)
rm -f "$WORK"/source.*(N)
if [ -f "$SRC" ]; then
  ABS=$(cd "$(dirname "$SRC")" && pwd)/$(basename "$SRC")
  ln -s "$ABS" "$WORK/source.${SRC:e:l}"
  echo "$ABS" > "$WORK/source_ref.txt"
else
  COOK=(); [ -n "$CLIPPER_COOKIES" ] && COOK=(--cookies-from-browser "$CLIPPER_COOKIES")
  yt-dlp --no-warnings $COOK -f "bv*[ext=mp4]+ba[ext=m4a]/bv*+ba/b" --merge-output-format mp4 \
    -o "$WORK/source.%(ext)s" "$SRC" || exit 1
  echo "$SRC" > "$WORK/source_ref.txt"
fi
F=("$WORK"/source.*(N)); F=${F[1]}
[ -e "$F" ] || { echo "no source file landed in $WORK"; exit 1; }
ffmpeg -hide_banner -i "$F" 2>&1 | grep -E "Duration|Stream #" | sed 's/^ *//'
ls -lhL "$F" | awk '{print "size: " $5}'
echo "source: $F"
