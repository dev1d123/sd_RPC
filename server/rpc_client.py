import threading
import uuid
from time import sleep
import pika


class RpcClient:
    """Asynchronous RPC client with a dedicated response thread."""

    def __init__(self, rpc_queue: str, rabbitmq_url: str = "") -> None:
        self.rpc_queue = rpc_queue
        self._responses = {}
        self._lock = threading.Lock()

        if rabbitmq_url:
            params = pika.URLParameters(rabbitmq_url)
            self.connection = pika.BlockingConnection(params)
        else:
            self.connection = pika.BlockingConnection()

        self.channel = self.connection.channel()
        result = self.channel.queue_declare(queue="", exclusive=True)
        self.callback_queue = result.method.queue

        self.channel.basic_consume(
            queue=self.callback_queue,
            on_message_callback=self._on_response,
            auto_ack=True,
        )

        thread = threading.Thread(target=self._process_data_events, daemon=True)
        thread.start()

    def _process_data_events(self) -> None:
        while True:
            with self._lock:
                self.connection.process_data_events(time_limit=1)
            sleep(0.05)

    def _on_response(self, ch, method, props, body) -> None:
        self._responses[props.correlation_id] = body

    def send_request(self, payload: str) -> str:
        corr_id = str(uuid.uuid4())
        self._responses[corr_id] = None
        with self._lock:
            self.channel.basic_publish(
                exchange="",
                routing_key=self.rpc_queue,
                properties=pika.BasicProperties(
                    reply_to=self.callback_queue,
                    correlation_id=corr_id,
                ),
                body=payload,
            )
        return corr_id

    def wait_for_response(self, corr_id: str, timeout: float) -> bytes | None:
        elapsed = 0.0
        step = 0.05
        while elapsed < timeout:
            response = self._responses.get(corr_id)
            if response is not None:
                self._responses.pop(corr_id, None)
                return response
            sleep(step)
            elapsed += step
        return None
