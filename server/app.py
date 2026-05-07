import json
from flask import Flask, jsonify, request

from server.config import CHAT_LIST_LIMIT, PORT, RABBITMQ_URL, REQUEST_TIMEOUT, RPC_QUEUE
from server.rpc_client import RpcClient

app = Flask(__name__)

rpc_client = RpcClient(rpc_queue=RPC_QUEUE, rabbitmq_url=RABBITMQ_URL)


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    return response


def _options_response():
    return ("", 204)


def _send_rpc(payload: dict):
    corr_id = rpc_client.send_request(json.dumps(payload))
    raw = rpc_client.wait_for_response(corr_id, REQUEST_TIMEOUT)
    if raw is None:
        return None, "timeout"
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8", errors="replace")
    try:
        return json.loads(raw), None
    except json.JSONDecodeError:
        return {"ok": False, "error": "bad_response", "raw": raw}, "bad_response"


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

    payload = {"action": "operacion", "op": op, "params": params}
    response, err = _send_rpc(payload)
    if err == "timeout":
        return jsonify({"ok": False, "error": "timeout"}), 504
    return jsonify(response)


@app.route("/api/chat/send", methods=["POST", "OPTIONS"])
def chat_send():
    if request.method == "OPTIONS":
        return _options_response()

    data = request.get_json(silent=True) or {}
    user = data.get("user")
    msg = data.get("msg")

    if not user or not msg:
        return jsonify({"ok": False, "error": "invalid_request"}), 400

    payload = {"action": "chat_send", "user": user, "msg": msg}
    response, err = _send_rpc(payload)
    if err == "timeout":
        return jsonify({"ok": False, "error": "timeout"}), 504
    return jsonify(response)


@app.route("/api/chat/list", methods=["GET", "OPTIONS"])
def chat_list():
    if request.method == "OPTIONS":
        return _options_response()

    try:
        limit = int(request.args.get("limit", CHAT_LIST_LIMIT))
    except ValueError:
        limit = CHAT_LIST_LIMIT

    payload = {"action": "chat_list", "limit": limit}
    response, err = _send_rpc(payload)
    if err == "timeout":
        return jsonify({"ok": False, "error": "timeout"}), 504
    return jsonify(response)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
