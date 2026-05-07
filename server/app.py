import json
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, jsonify, request

from server.config import CHAT_LIST_LIMIT, CHAT_STORE_PATH, PORT

app = Flask(__name__)


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    return response


def _options_response():
    return ("", 204)


class ChatStore:
    def __init__(self, path: str) -> None:
        self.path = Path(path)
        self.messages = []
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            data = json.loads(self.path.read_text())
        except json.JSONDecodeError:
            return
        if isinstance(data, list):
            self.messages = data

    def append(self, message: dict) -> None:
        self.messages.append(message)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as handle:
            handle.write(json.dumps(self.messages, ensure_ascii=False, indent=2))

    def tail(self, limit: int) -> list:
        if limit <= 0:
            return []
        return self.messages[-limit:]


chat_store = ChatStore(CHAT_STORE_PATH)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _handle_calc(op: str, params: list) -> dict:
    if not isinstance(params, list) or len(params) != 2:
        return {"ok": False, "error": "invalid_params"}

    try:
        a = float(params[0])
        b = float(params[1])
    except (TypeError, ValueError):
        return {"ok": False, "error": "invalid_number"}

    if op == "add":
        result = a + b
    elif op == "sub":
        result = a - b
    elif op == "mul":
        result = a * b
    elif op == "div":
        if b == 0:
            return {"ok": False, "error": "division_by_zero"}
        result = a / b
    else:
        return {"ok": False, "error": "invalid_operation"}

    return {"ok": True, "result": result}


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"ok": True})


@app.route("/api/calc", methods=["POST", "OPTIONS"])
def calc():
    if request.method == "OPTIONS":
        return _options_response()

    data = request.get_json(silent=True) or {}
    op = data.get("op")
    params = data.get("params")

    if not op or not isinstance(params, list) or len(params) != 2:
        return jsonify({"ok": False, "error": "invalid_request"}), 400

    return jsonify(_handle_calc(op, params))


@app.route("/api/chat/send", methods=["POST", "OPTIONS"])
def chat_send():
    if request.method == "OPTIONS":
        return _options_response()

    data = request.get_json(silent=True) or {}
    user = data.get("user")
    msg = data.get("msg")

    if not user or not msg:
        return jsonify({"ok": False, "error": "invalid_request"}), 400

    record = {"user": str(user), "msg": str(msg), "ts": _now_iso()}
    chat_store.append(record)
    return jsonify({"ok": True})


@app.route("/api/chat/list", methods=["GET", "OPTIONS"])
def chat_list():
    if request.method == "OPTIONS":
        return _options_response()

    try:
        limit = int(request.args.get("limit", CHAT_LIST_LIMIT))
    except ValueError:
        limit = CHAT_LIST_LIMIT

    return jsonify({"ok": True, "messages": chat_store.tail(limit)})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
