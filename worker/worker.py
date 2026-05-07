import json
import os
from datetime import datetime, timezone
from pathlib import Path
import pika


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


BASE_DIR = Path(__file__).resolve().parent
_load_dotenv(BASE_DIR.parent / ".env")

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "")
RPC_QUEUE = os.getenv("RPC_QUEUE", "rpc_queue")
CHAT_STORE_PATH = os.getenv(
    "CHAT_STORE_PATH", str(BASE_DIR.parent / "server" / "messages" / "messages.json")
)


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


def _handle_calc(payload: dict) -> dict:
    op = payload.get("op")
    params = payload.get("params", [])
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


def _handle_chat_send(payload: dict) -> dict:
    user = payload.get("user")
    msg = payload.get("msg")
    if not user or not msg:
        return {"ok": False, "error": "invalid_message"}

    record = {"user": str(user), "msg": str(msg), "ts": _now_iso()}
    chat_store.append(record)
    return {"ok": True}


def _handle_chat_list(payload: dict) -> dict:
    limit = payload.get("limit", 50)
    try:
        limit = int(limit)
    except (TypeError, ValueError):
        limit = 50
    return {"ok": True, "messages": chat_store.tail(limit)}


def handle_request(body: bytes) -> dict:
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {"ok": False, "error": "invalid_json"}

    action = payload.get("action")
    if action == "operacion":
        return _handle_calc(payload)
    if action == "chat_send":
        return _handle_chat_send(payload)
    if action == "chat_list":
        return _handle_chat_list(payload)
    return {"ok": False, "error": "unknown_action"}


def main() -> None:
    if RABBITMQ_URL:
        params = pika.URLParameters(RABBITMQ_URL)
        connection = pika.BlockingConnection(params)
    else:
        connection = pika.BlockingConnection()

    channel = connection.channel()
    channel.queue_declare(queue=RPC_QUEUE)
    channel.basic_qos(prefetch_count=1)

    def on_request(ch, method, props, body):
        response = handle_request(body)
        ch.basic_publish(
            exchange="",
            routing_key=props.reply_to,
            properties=pika.BasicProperties(correlation_id=props.correlation_id),
            body=json.dumps(response).encode("utf-8"),
        )
        ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(queue=RPC_QUEUE, on_message_callback=on_request)
    channel.start_consuming()


if __name__ == "__main__":
    main()
