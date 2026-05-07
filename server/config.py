import os
from pathlib import Path


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
REQUEST_TIMEOUT = float(os.getenv("REQUEST_TIMEOUT", "10"))
CHAT_LIST_LIMIT = int(os.getenv("CHAT_LIST_LIMIT", "50"))
CHAT_STORE_PATH = os.getenv("CHAT_STORE_PATH", "server/messages/messages.json")
PORT = int(os.getenv("PORT", "5000"))
