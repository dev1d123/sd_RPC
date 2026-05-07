"""Legacy entrypoint for the RPC client API.

This keeps the original filename, but runs the new Flask API
implementation under server/app.py so you can keep using the same file.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from server.app import app
from server.config import PORT


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
