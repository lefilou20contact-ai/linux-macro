#!/usr/bin/env python3

import json
import os
import secrets
import socket
import subprocess
import threading
import time
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

CONFIG_FILE = BASE_DIR / "config.json"
DEVICE_FILE = BASE_DIR / "device.json"
MACROS_FILE = BASE_DIR / "macros.json"


# =====================================================
# OUTILS
# =====================================================

def load_json(path, default):

    try:

        with open(
            path,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)

    except Exception:

        return default


def save_json(path, data):

    temporary = path.with_suffix(
        path.suffix + ".tmp"
    )

    with open(
        temporary,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            indent=4,
            ensure_ascii=False
        )

    temporary.replace(path)


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


# =====================================================
# RESEAU
# =====================================================

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


# =====================================================
# CORS
# =====================================================

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


# =====================================================
# JSON RESPONSE
# =====================================================

def send_json(
    handler,
    data,
    status=200
):

    body = json.dumps(
        data,
        ensure_ascii=False
    ).encode("utf-8")


    handler.send_response(
        status
    )


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


    handler.wfile.write(
        body
    )


# =====================================================
# VERIFICATION CODE
# =====================================================

def verify_device(data):

    code =
        str(
            data.get(
                "code",
                ""
            )
        ).strip()


    return secrets.compare_digest(
        code,
        str(
            DEVICE.get(
                "code",
                ""
            )
        )
    )


# =====================================================
# ACTIONS
# =====================================================

def run_command(
    command
):

    subprocess.Popen(
        command,
        shell=True,
        start_new_session=True
    )


def open_application(
    value
):

    subprocess.Popen(
        value,
        shell=True,
        start_new_session=True
    )


def open_file(
    value
):

    subprocess.Popen(
        [
            "xdg-open",
            os.path.expanduser(
                value
            )
        ],
        start_new_session=True
    )


def open_url(
    value
):

    subprocess.Popen(
        [
            "xdg-open",
            value
        ],
        start_new_session=True
    )


def keyboard_action(
    value
):

    if not shutil_available(
        "xdotool"
    ):

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


def type_text(
    value
):

    if not shutil_available(
        "xdotool"
    ):

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


def mouse_action(
    value
):

    if not shutil_available(
        "xdotool"
    ):

        raise RuntimeError(
            "xdotool n'est pas installé."
        )


    mapping = {

        "left_click":
            "1",

        "right_click":
            "3",

        "double_click":
            "1"

    }


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


    if value == "double_click":

        time.sleep(
            0.08
        )

        subprocess.run(
            [
                "xdotool",
                "click",
                button
            ],
            check=True
        )


def shutil_available(
    command
):

    import shutil

    return shutil.which(
        command
    ) is not None


# =====================================================
# EXECUTION MACRO
# =====================================================

def execute_action(
    action
):

    action_type =
        action.get(
            "type"
        )


    value =
        action.get(
            "value",
            ""
        )


    if action_type == "wait":

        milliseconds =
            int(
                action.get(
                    "ms",
                    500
                )
            )


        time.sleep(
            milliseconds / 1000
        )

        return


    if action_type == "open_app":

        open_application(
            value
        )

        return


    if action_type == "open_file":

        open_file(
            value
        )

        return


    if action_type == "open_url":

        open_url(
            value
        )

        return


    if action_type == "command":

        if not action.get(
            "approved",
            False
        ):

            raise RuntimeError(
                "Commande refusée : confirmation nécessaire."
            )


        run_command(
            value
        )

        return


    if action_type == "key":

        keyboard_action(
            value
        )

        return


    if action_type == "text":

        type_text(
            value
        )

        return


    if action_type == "mouse":

        mouse_action(
            value
        )

        return


    raise RuntimeError(
        "Action inconnue : " +
        str(action_type)
    )


def execute_macro(
    macro
):

    for action in macro.get(
        "actions",
        []
    ):

        execute_action(
            action
        )


# =====================================================
# GITHUB
# =====================================================

def sync_github():

    url =
        CONFIG.get(
            "github_raw_url",
            ""
        ).strip()


    if not url:

        raise RuntimeError(
            "github_raw_url n'est pas configuré."
        )


    request =
        urllib.request.Request(
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

        content =
            response.read()


    data =
        json.loads(
            content.decode(
                "utf-8"
            )
        )


    if not isinstance(
        data,
        list
    ):

        raise RuntimeError(
            "macros.json doit contenir une liste."
        )


    global MACROS

    MACROS = data


    save_json(
        MACROS_FILE,
        MACROS
    )


# =====================================================
# SERVEUR
# =====================================================

class FilouHandler(
    BaseHTTPRequestHandler
):


    def log_message(
        self,
        format,
        *args
    ):

        print(
            "[Filou]",
            format % args
        )


    def do_OPTIONS(
        self
    ):

        self.send_response(
            204
        )

        add_cors(
            self
        )

        self.end_headers()


    def read_json_body(
        self
    ):

        length =
            int(
                self.headers.get(
                    "Content-Length",
                    "0"
                )
            )


        if length > 1024 * 1024:

            raise RuntimeError(
                "Requête trop volumineuse."
            )


        body =
            self.rfile.read(
                length
            )


        return json.loads(
            body.decode(
                "utf-8"
            )
        )


    def do_GET(
        self
    ):

        parsed =
            urllib.parse.urlparse(
                self.path
            )


        path =
            parsed.path


        if path == "/api/info":

            send_json(
                self,
                {
                    "name":
                        DEVICE.get(
                            "name"
                        ),

                    "id":
                        DEVICE.get(
                            "name"
                        ),

                    "ip":
                        get_local_ip(),

                    "port":
                        CONFIG.get(
                            "port"
                        )
                }
            )

            return


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


    def do_POST(
        self
    ):

        parsed =
            urllib.parse.urlparse(
                self.path
            )


        path =
            parsed.path


        try:

            data =
                self.read_json_body()

        except Exception as error:

            send_json(
                self,
                {
                    "error":
                        "JSON invalide : " +
                        str(error)
                },
                400
            )

            return


        # ---------------------------------------------
        # CONNEXION
        # ---------------------------------------------

        if path == "/api/connect":

            if not verify_device(
                data
            ):

                send_json(
                    self,
                    {
                        "error":
                            "Code appareil incorrect."
                    },
                    403
                )

                return


            requested_name =
                str(
                    data.get(
                        "name",
                        DEVICE.get(
                            "name"
                        )
                    )
                ).strip()


            if requested_name:

                DEVICE["name"] =
                    requested_name

                save_json(
                    DEVICE_FILE,
                    DEVICE
                )


            send_json(
                self,
                {
                    "ok":
                        True,

                    "name":
                        DEVICE["name"],

                    "ip":
                        get_local_ip(),

                    "port":
                        CONFIG["port"]
                }
            )

            return


        # ---------------------------------------------
        # MACROS
        # ---------------------------------------------

        if path == "/api/macros":

            global MACROS

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


            MACROS =
                data


            save_json(
                MACROS_FILE,
                MACROS
            )


            send_json(
                self,
                {
                    "ok":
                        True
                }
            )

            return


        # ---------------------------------------------
        # EXECUTION
        # ---------------------------------------------

        if path.startswith(
            "/api/run/"
        ):

            macro_id =
                urllib.parse.unquote(
                    path[
                        len("/api/run/") :
                    ]
                )


            macro =
                next(
                    (
                        item
                        for item in MACROS
                        if item.get(
                            "id"
                        ) == macro_id
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
                        "ok":
                            True
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


        # ---------------------------------------------
        # SYNCHRONISATION GITHUB
        # ---------------------------------------------

        if path == "/api/sync":

            try:

                sync_github()


                send_json(
                    self,
                    {
                        "ok":
                            True,

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


        send_json(
            self,
            {
                "error":
                    "Route inconnue."
            },
            404
        )


# =====================================================
# DEMARRAGE
# =====================================================

def main():

    port =
        int(
            CONFIG.get(
                "port",
                8765
            )
        )


    server =
        ThreadingHTTPServer(
            (
                "0.0.0.0",
                port
            ),
            FilouHandler
        )


    ip =
        get_local_ip()


    print()
    print(
        "========================================"
    )

    print(
        "       FILOU MACRO SYSTEM V1"
    )

    print(
        "========================================"
    )

    print()

    print(
        "PC : http://" +
        ip +
        ":" +
        str(port)
    )

    print(
        "Code appareil : " +
        str(
            DEVICE.get(
                "code"
            )
        )
    )

    print()

    print(
        "Le serveur fonctionne sur le réseau local."
    )

    print(
        "CTRL+C pour arrêter."
    )

    print()


    server.serve_forever()


if __name__ == "__main__":

    main()
print("Appareil :",device["id"])
print("Code     :",device["pair_code"])
print("Token    :",device["token"])
print(f"Agent    : http://127.0.0.1:{port}")
ThreadingHTTPServer(("127.0.0.1",port),H).serve_forever()
