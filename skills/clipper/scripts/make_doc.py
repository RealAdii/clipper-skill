# usage: make_doc.py <work dir> [--no-upload]
# Builds doc.html from plan.json + links.json and uploads it as a Google Doc in the Drive folder, shared
# "anyone with the link". Rerunning updates the same doc. --no-upload only writes doc.html for review.
import html, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import work, plan, mmss, duration, no_dashes

w = work(sys.argv)
p = plan(w)
dry = "--no-upload" in sys.argv
lp = os.path.join(w, "links.json")
links = json.load(open(lp)) if os.path.exists(lp) else {}
if not dry and "folder_id" not in links:
    sys.exit("no Drive folder yet, run drive_upload.py first")

paras = lambda t: "".join(f"<p>{html.escape(x)}</p>" for x in t.split("\n\n") if x.strip())


def link(key, label):
    url = links.get(key)
    if not url:
        return f"<p>{html.escape(label)} (link after upload)</p>"
    return f'<p><a href="{html.escape(url)}">{html.escape(label)}</a></p>'


def length(path):
    return mmss(duration(path)) if os.path.exists(path) else "?"


ep = p.get("episode")
trim = (ep or {}).get("trim_start") or 0.0
parts = [f"<h1>{html.escape(p['title'])}</h1>", link("folder", "drive folder with every video")]
if p.get("source_url"):
    parts.append(f'<p><a href="{html.escape(p["source_url"])}">original source</a></p>')
if ep:
    parts += ["<h2>full episode</h2>",
              link("episode", f"watch the full episode ({length(os.path.join(w, 'full_episode.mp4'))})")]
    if ep.get("caption"):
        parts += ["<h3>caption</h3>", paras(ep["caption"])]
    if ep.get("timestamps"):
        parts += ["<h3>timestamps</h3>",
                  "".join(f"<p>{html.escape(t)} {html.escape(l)}</p>" for t, l in ep["timestamps"])]
parts.append("<h2>clips</h2>")
for i, c in enumerate(p["clips"], 1):
    d = length(os.path.join(w, "clips", c["name"] + ".mp4"))
    where = f"at {mmss(max(0.0, c['start'] - trim))} in the episode" if ep else f"at {mmss(c['start'])} in the source"
    parts.append(f"<h3>{i}. {html.escape(c.get('title') or c['name'])} ({d}, {where})</h3>")
    if c.get("caption"):
        parts.append(paras(c["caption"]))
    parts.append(link(c["name"], f"watch clip {i}"))
body = "<html><head><meta charset=\"utf-8\"></head><body>" + "".join(parts) + "</body></html>"
no_dashes(body, "doc.html")
open(os.path.join(w, "doc.html"), "w").write(body)
print("wrote", os.path.join(w, "doc.html"))
if dry:
    sys.exit(0)

from gdrive import token, call, share_anyone
tok = token()
B = "clipperboundary"
if links.get("doc_id"):
    call(tok, "PATCH", f"https://www.googleapis.com/upload/drive/v3/files/{links['doc_id']}?uploadType=media",
         body.encode(), {"Content-Type": "text/html; charset=UTF-8"})
    print("updated doc:", links["doc"])
    sys.exit(0)
meta = {"name": p["title"], "mimeType": "application/vnd.google-apps.document", "parents": [links["folder_id"]]}
payload = (f"--{B}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n{json.dumps(meta)}\r\n"
           f"--{B}\r\nContent-Type: text/html; charset=UTF-8\r\n\r\n{body}\r\n--{B}--").encode()
f = call(tok, "POST", "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart&fields=id,webViewLink",
         payload, {"Content-Type": f"multipart/related; boundary={B}"})
share_anyone(tok, f["id"])
links.update(doc=f["webViewLink"], doc_id=f["id"])
json.dump(links, open(lp, "w"), indent=1)
print("doc:", f["webViewLink"])
