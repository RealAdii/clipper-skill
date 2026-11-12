# usage: drive_upload.py <work dir>
# Makes a Drive folder named after plan.title, uploads the full episode and every clip, shares each
# "anyone with the link", and records links in <work>/links.json. Rerunning skips files already uploaded.
import json, os, sys, urllib.error, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import work, plan
from gdrive import token, call, share_anyone

CHUNK = 32 * 1024 * 1024
w = work(sys.argv)
p = plan(w)
tok = token()
lp = os.path.join(w, "links.json")
links = json.load(open(lp, encoding="utf-8")) if os.path.exists(lp) else {}
save = lambda: json.dump(links, open(lp, "w", encoding="utf-8"), indent=1)


def upload(path, name, folder_id):
    size = os.path.getsize(path)
    init = call(tok, "POST", "https://www.googleapis.com/upload/drive/v3/files?uploadType=resumable&fields=id,webViewLink",
                {"name": name, "parents": [folder_id]},
                {"X-Upload-Content-Type": "video/mp4", "X-Upload-Content-Length": str(size)}, raw=True)
    session = init.headers["Location"]
    sent = 0
    with open(path, "rb") as f:
        while sent < size:
            chunk = f.read(CHUNK)
            end = sent + len(chunk) - 1
            req = urllib.request.Request(session, data=chunk, method="PUT", headers={
                "Content-Length": str(len(chunk)), "Content-Range": f"bytes {sent}-{end}/{size}"})
            try:
                with urllib.request.urlopen(req) as r:
                    return json.loads(r.read())
            except urllib.error.HTTPError as e:
                if e.code != 308:
                    raise
            sent = end + 1
            print(f"  {name} {sent * 100 // size}%", flush=True)


if "folder_id" not in links:
    f = call(tok, "POST", "https://www.googleapis.com/drive/v3/files?fields=id,webViewLink",
             {"name": p["title"], "mimeType": "application/vnd.google-apps.folder"})
    share_anyone(tok, f["id"])
    links.update(folder=f["webViewLink"], folder_id=f["id"])
    save()
print("folder:", links["folder"])

files = []
if p.get("episode") and os.path.exists(os.path.join(w, "full_episode.mp4")):
    files.append((os.path.join(w, "full_episode.mp4"), p["slug"] + "_full_episode.mp4", "episode"))
for c in p["clips"]:
    f = os.path.join(w, "clips", c["name"] + ".mp4")
    if not os.path.exists(f):
        sys.exit(f"missing clip {c['name']}, run cut.py")
    files.append((f, c["name"] + ".mp4", c["name"]))
for path, name, key in files:
    if key in links:
        print("skip (already uploaded)", name)
        continue
    print("uploading", name, flush=True)
    r = upload(path, name, links["folder_id"])
    share_anyone(tok, r["id"])
    links[key] = r["webViewLink"]
    save()
print("done, links in", lp)
