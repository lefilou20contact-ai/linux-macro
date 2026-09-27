#!/usr/bin/env python3
import json, os, secrets, subprocess, threading, time, urllib.request, webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

BASE = Path(__file__).resolve().parent
CONFIG = BASE / "config.json"
DEVICE = BASE / "device.json"
MACROS = BASE / "macros.json"

def read_json(path, default):
    try: return json.loads(path.read_text(encoding="utf-8"))
    except Exception: return default

config = read_json(CONFIG, {"port":8765, "github_raw_url":""})
device = read_json(DEVICE, {})
if not device.get("id"):
    device = {
        "id": "FILOU-" + secrets.token_hex(4).upper(),
        "pair_code": f"{secrets.randbelow(1000000):06d}",
        "token": secrets.token_urlsafe(32)
    }
    DEVICE.write_text(json.dumps(device, indent=2), encoding="utf-8")

def macros():
    return read_json(MACROS, [])

def run_action(a):
    typ = a.get("type")
    if typ == "wait":
        time.sleep(max(0, int(a.get("ms", 0))) / 1000)
    elif typ == "open_url":
        webbrowser.open(a["url"])
    elif typ == "launch":
        subprocess.Popen(a["command"], shell=True)
    elif typ == "open_file":
        subprocess.Popen(["xdg-open", os.path.expanduser(a["path"])])
    elif typ == "command":
        # Sensitive action: require explicit confirmation from the web UI.
        if not a.get("approved", False):
            raise PermissionError("Commande sensible non validée.")
        subprocess.Popen(a["command"], shell=True)
    elif typ == "text":
        # Clipboard is intentionally used rather than an unrestricted keyboard injector.
        text = str(a.get("text", ""))
        subprocess.run(["bash", "-lc", "command -v xclip >/dev/null && printf %s \"$1\" | xclip -selection clipboard || true", "--", text])
    else:
        raise ValueError("Action inconnue : " + str(typ))

def run_macro(m):
    for a in m.get("actions", []):
        run_action(a)

def sync():
    url = str(config.get("github_raw_url","")).strip()
    if not url: return {"ok":False,"message":"Aucune URL GitHub configurée."}
    try:
        req = urllib.request.Request(url, headers={"User-Agent":"FilouMacroSystem/1.0"})
        with urllib.request.urlopen(req, timeout=8) as r: raw = r.read()
        data = json.loads(raw.decode("utf-8"))
        if not isinstance(data, list): raise ValueError("macros.json doit être une liste.")
        tmp = MACROS.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(MACROS)
        return {"ok":True,"message":f"{len(data)} macro(s) synchronisée(s)."}
    except Exception as e:
        return {"ok":False,"message":str(e)}

class H(BaseHTTPRequestHandler):
    def send_json(self, code, obj):
        raw=json.dumps(obj,ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type","application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin","*")
        self.send_header("Access-Control-Allow-Headers","Content-Type,X-Filou-Token")
        self.send_header("Access-Control-Allow-Methods","GET,POST,OPTIONS")
        self.end_headers(); self.wfile.write(raw)
    def auth(self):
        return secrets.compare_digest(self.headers.get("X-Filou-Token",""),device["token"])
    def do_OPTIONS(self): self.send_json(204,{})
    def do_GET(self):
        if self.path=="/api/info":
            self.send_json(200,{"id":device["id"],"pair_code":device["pair_code"],"macros":len(macros())})
        elif self.path=="/api/macros": self.send_json(200,macros())
        else: self.send_json(404,{"error":"not_found"})
    def do_POST(self):
        if not self.auth(): self.send_json(403,{"error":"bad_token"}); return
        if self.path=="/api/sync": self.send_json(200,sync()); return
        if self.path.startswith("/api/run/"):
            mid=self.path.split("/api/run/",1)[1]
            m=next((x for x in macros() if x.get("id")==mid),None)
            if not m: self.send_json(404,{"error":"macro_not_found"}); return
            try:
                threading.Thread(target=run_macro,args=(m,),daemon=True).start()
                self.send_json(200,{"ok":True})
            except Exception as e: self.send_json(400,{"error":str(e)})
            return
        self.send_json(404,{"error":"not_found"})
    def log_message(self,*args): pass

port=int(config.get("port",8765))
print("Filou Macro System V1")
print("Appareil :",device["id"])
print("Code     :",device["pair_code"])
print("Token    :",device["token"])
print(f"Agent    : http://127.0.0.1:{port}")
ThreadingHTTPServer(("127.0.0.1",port),H).serve_forever()
