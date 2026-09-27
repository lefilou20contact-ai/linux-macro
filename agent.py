#!/usr/bin/env python3

import json
import os
import secrets
import shutil
import socket
import subprocess
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

CONFIG_FILE = BASE_DIR / "config.json"
DEVICE_FILE = BASE_DIR / "device.json"
MACROS_FILE = BASE_DIR / "macros.json"


# ============================================================
# JSON
# ============================================================

def load_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception:
        return default


def save_json(path, data):
    temporary = path.with_suffix(path.suffix + ".tmp")

    with open(temporary, "w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            indent=4,
            ensure_ascii=False
        )

    temporary.replace(path)


# ============================================================
# CONFIGURATION
# ============================================================

CONFIG = load_json(
    CONFIG_FILE,
    {
        "port": 8765,
        "github_raw_url": ""
    }
)


DEVICE = load_json(
    DEVICE_FILE,
    {
        "name": "Filou PC",
        "code": secrets.token_urlsafe(12)
    }
)


if not DEVICE_FILE.exists():
    save_json(
        DEVICE_FILE,
        DEVICE
    )


MACROS = load_json(
    MACROS_FILE,
    []
)


# ============================================================
# IP LOCALE
# ============================================================

def get_local_ip():
    try:
        sock = socket.socket(
            socket.AF_INET,
            socket.SOCK_DGRAM
        )

        sock.connect(
            ("8.8.8.8", 80)
        )

        ip = sock.getsockname()[0]

        sock.close()

        return ip

    except Exception:
        return "127.0.0.1"


# ============================================================
# CORS
# ============================================================

def add_cors(handler):
    handler.send_header(
        "Access-Control-Allow-Origin",
        "*"
    )

    handler.send_header(
        "Access-Control-Allow-Methods",
        "GET, POST, OPTIONS"
    )

    handler.send_header(
        "Access-Control-Allow-Headers",
        "Content-Type"
    )


# ============================================================
# REPONSE JSON
# ============================================================

def send_json(handler, data, status=200):
    body = json.dumps(
        data,
        ensure_ascii=False
    ).encode("utf-8")

    handler.send_response(status)

    add_cors(handler)

    handler.send_header(
        "Content-Type",
        "application/json; charset=utf-8"
    )

    handler.send_header(
        "Content-Length",
        str(len(body))
    )

    handler.end_headers()

    handler.wfile.write(body)


# ============================================================
# VERIFICATION DU CODE APPAREIL
# ============================================================

def verify_device(data):
    code = str(
        data.get(
            "code",
            ""
        )
    ).strip()

    saved_code = str(
        DEVICE.get(
            "code",
            ""
        )
    ).strip()

    return secrets.compare_digest(
        code,
        saved_code
    )


# ============================================================
# OUTILS SYSTEME
# ============================================================

def command_exists(command):
    return shutil.which(command) is not None


# ============================================================
# OUVRIR APPLICATION
# ============================================================

def open_application(value):
    subprocess.Popen(
        value,
        shell=True,
        start_new_session=True
    )


# ============================================================
# OUVRIR FICHIER
# ============================================================

def open_file(value):
    subprocess.Popen(
        [
            "xdg-open",
            os.path.expanduser(value)
        ],
        start_new_session=True
    )


# ============================================================
# OUVRIR URL
# ============================================================

def open_url(value):
    subprocess.Popen(
        [
            "xdg-open",
            value
        ],
        start_new_session=True
    )


# ============================================================
# CLAVIER
# ============================================================

def keyboard_action(value):
    if not command_exists("xdotool"):
        raise RuntimeError(
            "xdotool n'est pas installé."
        )

    subprocess.run(
        [
            "xdotool",
            "key",
            value
        ],
        check=True
    )


# ============================================================
# TEXTE
# ============================================================

def type_text(value):
    if not command_exists("xdotool"):
        raise RuntimeError(
            "xdotool n'est pas installé."
        )

    subprocess.run(
        [
            "xdotool",
            "type",
            "--delay",
            "1",
            value
        ],
        check=True
    )


# ============================================================
# SOURIS
# ============================================================

def mouse_action(value):
    if not command_exists("xdotool"):
        raise RuntimeError(
            "xdotool n'est pas installé."
        )

    mapping = {
        "left_click": "1",
        "right_click": "3"
    }

    if value == "double_click":
        subprocess.run(
            [
                "xdotool",
                "click",
                "1"
            ],
            check=True
        )

        time.sleep(0.08)

        subprocess.run(
            [
                "xdotool",
                "click",
                "1"
            ],
            check=True
        )

        return

    button = mapping.get(
        value,
        "1"
    )

    subprocess.run(
        [
            "xdotool",
            "click",
            button
        ],
        check=True
    )


# ============================================================
# COMMANDE LINUX
# ============================================================

def run_command(command):
    subprocess.Popen(
        command,
        shell=True,
        start_new_session=True
    )


# ============================================================
# EXECUTER UNE ACTION
# ============================================================

def execute_action(action):
    action_type = action.get(
        "type"
    )

    value = action.get(
        "value",
        ""
    )

    # Attendre
    if action_type == "wait":
        milliseconds = int(
            action.get(
                "ms",
                500
            )
        )

        time.sleep(
            milliseconds / 1000
        )

        return

    # Application
    if action_type == "open_app":
        open_application(value)
        return

    # Fichier
    if action_type == "open_file":
        open_file(value)
        return

    # URL
    if action_type == "open_url":
        open_url(value)
        return

    # Commande
    if action_type == "command":

        if not action.get(
            "approved",
            False
        ):
            raise RuntimeError(
                "Commande refusée : confirmation nécessaire."
            )

        run_command(value)
        return

    # Touche
    if action_type == "key":
        keyboard_action(value)
        return

    # Texte
    if action_type == "text":
        type_text(value)
        return

    # Souris
    if action_type == "mouse":
        mouse_action(value)
        return

    raise RuntimeError(
        "Action inconnue : "
        + str(action_type)
    )


# ============================================================
# EXECUTER UNE MACRO
# ============================================================

def execute_macro(macro):
    actions = macro.get(
        "actions",
        []
    )

    for action in actions:
        execute_action(action)


# ============================================================
# SYNCHRONISATION GITHUB
# ============================================================

def sync_github():
    url = str(
        CONFIG.get(
            "github_raw_url",
            ""
        )
    ).strip()

    if not url:
        raise RuntimeError(
            "github_raw_url n'est pas configuré."
        )

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent":
                "FilouMacroSystem/1.0"
        }
    )

    with urllib.request.urlopen(
        request,
        timeout=10
    ) as response:

        content = response.read()

    data = json.loads(
        content.decode("utf-8")
    )

    if not isinstance(data, list):
        raise RuntimeError(
            "macros.json doit contenir une liste."
        )

    global MACROS

    MACROS = data

    save_json(
        MACROS_FILE,
        MACROS
    )


# ============================================================
# SERVEUR HTTP
# ============================================================

class FilouHandler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        print(
            "[Filou]",
            format % args
        )

    # --------------------------------------------------------
    # OPTIONS
    # --------------------------------------------------------

    def do_OPTIONS(self):
        self.send_response(204)

        add_cors(self)

        self.end_headers()

    # --------------------------------------------------------
    # LIRE JSON
    # --------------------------------------------------------

    def read_json_body(self):
        length = int(
            self.headers.get(
                "Content-Length",
                "0"
            )
        )

        if length > 1024 * 1024:
            raise RuntimeError(
                "Requête trop volumineuse."
            )

        body = self.rfile.read(
            length
        )

        return json.loads(
            body.decode("utf-8")
        )

    # --------------------------------------------------------
    # GET
    # --------------------------------------------------------

    def do_GET(self):

        path = self.path.split(
            "?",
            1
        )[0]

        # Informations
        if path == "/api/info":

            send_json(
                self,
                {
                    "name":
                        DEVICE.get(
                            "name"
                        ),

                    "ip":
                        get_local_ip(),

                    "port":
                        CONFIG.get(
                            "port",
                            8765
                        )
                }
            )

            return

        # Macros
        if path == "/api/macros":

            send_json(
                self,
                MACROS
            )

            return

        send_json(
            self,
            {
                "error":
                    "Route inconnue."
            },
            404
        )

    # --------------------------------------------------------
    # POST
    # --------------------------------------------------------

    def do_POST(self):

        path = self.path.split(
            "?",
            1
        )[0]

        try:
            data = self.read_json_body()

        except Exception as error:

            send_json(
                self,
                {
                    "error":
                        "JSON invalide : "
                        + str(error)
                },
                400
            )

            return

        # ----------------------------------------------------
        # CONNEXION
        # ----------------------------------------------------

        if path == "/api/connect":

            if not verify_device(data):

                send_json(
                    self,
                    {
                        "error":
                            "Code appareil incorrect."
                    },
                    403
                )

                return

            requested_name = str(
                data.get(
                    "name",
                    DEVICE.get(
                        "name"
                    )
                )
            ).strip()

            if requested_name:
                DEVICE["name"] = (
                    requested_name
                )

                save_json(
                    DEVICE_FILE,
                    DEVICE
                )

            send_json(
                self,
                {
                    "ok": True,
                    "name":
                        DEVICE["name"],
                    "ip":
                        get_local_ip(),
                    "port":
                        CONFIG.get(
                            "port",
                            8765
                        )
                }
            )

            return

        # ----------------------------------------------------
        # SAUVEGARDER MACROS
        # ----------------------------------------------------

        if path == "/api/macros":

            if not isinstance(
                data,
                list
            ):

                send_json(
                    self,
                    {
                        "error":
                            "Les macros doivent être une liste."
                    },
                    400
                )

                return

            global MACROS

            MACROS = data

            save_json(
                MACROS_FILE,
                MACROS
            )

            send_json(
                self,
                {
                    "ok": True
                }
            )

            return

        # ----------------------------------------------------
        # EXECUTER MACRO
        # ----------------------------------------------------

        if path.startswith(
            "/api/run/"
        ):

            macro_id = path[
                len("/api/run/"):
            ]

            macro = next(
                (
                    item
                    for item in MACROS
                    if item.get("id")
                    == macro_id
                ),
                None
            )

            if macro is None:

                send_json(
                    self,
                    {
                        "error":
                            "Macro introuvable."
                    },
                    404
                )

                return

            try:

                execute_macro(
                    macro
                )

                send_json(
                    self,
                    {
                        "ok": True
                    }
                )

            except Exception as error:

                send_json(
                    self,
                    {
                        "error":
                            str(error)
                    },
                    500
                )

            return

        # ----------------------------------------------------
        # SYNCHRONISATION GITHUB
        # ----------------------------------------------------

        if path == "/api/sync":

            try:

                sync_github()

                send_json(
                    self,
                    {
                        "ok": True,
                        "message":
                            "GitHub synchronisé."
                    }
                )

            except Exception as error:

                send_json(
                    self,
                    {
                        "error":
                            str(error)
                    },
                    500
                )

            return

        # ----------------------------------------------------
        # ROUTE INCONNUE
        # ----------------------------------------------------

        send_json(
            self,
            {
                "error":
                    "Route inconnue."
            },
            404
        )


# ============================================================
# DEMARRAGE
# ============================================================

def main():

    port = int(
        CONFIG.get(
            "port",
            8765
        )
    )

    server = ThreadingHTTPServer(
        (
            "0.0.0.0",
            port
        ),
        FilouHandler
    )

    ip = get_local_ip()

    print()
    print(
        "========================================"
    )
    print(
        "        FILOU MACRO SYSTEM V1"
    )
    print(
        "========================================"
    )
    print()

    print(
        "Adresse locale :"
    )

    print(
        "http://"
        + ip
        + ":"
        + str(port)
    )

    print()

    print(
        "Nom : "
        + str(
            DEVICE.get(
                "name"
            )
        )
    )

    print(
        "Code appareil : "
        + str(
            DEVICE.get(
                "code"
            )
        )
    )

    print()

    print(
        "Serveur actif sur le réseau local."
    )

    print(
        "CTRL+C pour arrêter."
    )

    print()

    server.serve_forever()


# ============================================================
# LANCEMENT
# ============================================================

if __name__ == "__main__":
    main()
