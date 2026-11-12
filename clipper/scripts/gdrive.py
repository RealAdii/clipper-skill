import json, subprocess, sys, urllib.error, urllib.parse, urllib.request

FIX = "run:  ! gcloud auth login --enable-gdrive-access   (then rerun this script)"


def token():
    try:
        t = subprocess.check_output(["gcloud", "auth", "print-access-token"], text=True,
                                    stderr=subprocess.DEVNULL).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        sys.exit("no gcloud login. " + FIX)
    try:
        info = json.loads(urllib.request.urlopen(
            "https://oauth2.googleapis.com/tokeninfo?access_token=" + urllib.parse.quote(t)).read())
    except urllib.error.HTTPError:
        sys.exit("gcloud token is invalid or expired. " + FIX)
    if "auth/drive" not in info.get("scope", ""):
        sys.exit("gcloud token has no Google Drive scope. " + FIX)
    return t


def call(tok, method, url, body=None, headers=None, raw=False):
    h = {"Authorization": "Bearer " + tok}
    h.update(headers or {})
    data = body if isinstance(body, (bytes, type(None))) else json.dumps(body).encode()
    if body is not None and not isinstance(body, bytes) and "Content-Type" not in h:
        h["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=h, method=method)
    r = urllib.request.urlopen(req)
    return r if raw else json.loads(r.read() or b"{}")


def share_anyone(tok, file_id):
    call(tok, "POST", f"https://www.googleapis.com/drive/v3/files/{file_id}/permissions",
         {"type": "anyone", "role": "reader"})
