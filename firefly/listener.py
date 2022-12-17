import json
import queue
import time
import websocket

from nxtools import logging, log_traceback

from firefly.core.common import config
from firefly.common import CLIENT_ID
from firefly.qt import QThread


if config.get("debug"):
    websocket.enableTrace(True)


class SeismicMessage:
    def __init__(self, **payload):
        self.timestamp = time.time()
        self.site_name = config.get("site_name")
        self.host = payload.get("host", "server")
        self.method = payload.get("topic", "unknown")
        payload.pop("topic", None)
        payload.pop("host", None)
        self.data = payload

    def __repr__(self):
        return f"<SeismicMessage {self.method}>"


class SeismicListener(QThread):
    def __init__(self):
        QThread.__init__(self, None)
        self.site_name = config["site_name"]
        self.should_run = True
        self.active = False
        self.last_msg = time.time()
        self.queue = queue.Queue()
        self.start()

    def run(self):
        addr = config["hub"].replace("http", "ws", 1) + "/ws"
        while self.should_run:
            logging.debug(f"[LISTENER] Connecting to {addr}", handlers=False)
            self.halted = False
            self.ws = websocket.WebSocketApp(
                addr,
                on_open=self.on_open,
                on_message=self.on_message,
                on_error=self.on_error,
                on_close=self.on_close,
            )
            self.ws.run_forever()
            self.active = False

        logging.debug("[LISTENER] halted", handlers=False)
        self.halted = True

    def on_open(self, *args):
        logging.goodnews("[LISTENER] connected", handlers=False)
        self.ws.send(
            json.dumps(
                {
                    "topic": "auth",
                    "token": config.get("session_id"),
                    "subscribe": ["*"],
                }
            )
        )

    def on_message(self, *args):
        data = args[-1]
        if not self.active:
            logging.goodnews("[LISTENER] Got first message!", handlers=False)
            self.active = True
        try:
            original_payload = json.loads(data)
            message = SeismicMessage(**original_payload)
        except Exception:
            log_traceback(handlers=False)
            logging.debug(f"[LISTENER] Malformed message: {data}", handlers=False)
            return

        self.last_msg = time.time()

        if message.data and message.data.get("initiator", None) == CLIENT_ID:
            return

        self.queue.put(message)

    def on_error(self, *args):
        error = args[-1]
        logging.error(error, handlers=False)

    def on_close(self, *args):
        self.active = False
        if self.should_run:
            logging.warning("[LISTENER] connection interrupted", handlers=False)

    def halt(self):
        logging.debug("[LISTENER] Shutting down")
        self.should_run = False
        self.ws.close()
