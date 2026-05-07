# Run locally

## 1) Activate venv

```
source .venv/bin/activate
```

## 2) Install dependencies

```
pip install -r worker/requirements.txt -r server/requirements.txt
```

## 3) Start services (separate terminals)

Client:
```
cd client
python -m http.server 3000
```

Worker:
```
python worker/worker.py
```

API:
```
python server/amqpstorm_threaded_rpc_client.py
```

## 4) Open UI

```
http://localhost:3000
```

# .env template

Create a `.env` file at the project root and fill your real credentials.

```
# RabbitMQ
RABBITMQ_URL=amqps://yzwbrtzl:QHboniYygEgy60ulVJ1EH6pgJovt_yc-@jackal.rmq.cloudamqp.com/yzwbrtzl
RPC_QUEUE=rpc_queue



# API server
PORT=5000
REQUEST_TIMEOUT=10
CHAT_LIST_LIMIT=50

# Worker storage
CHAT_STORE_PATH=server/messages/messages.json
