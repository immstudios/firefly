import time
import json
import functools

from nxtools import logging, log_traceback

from firefly.core.common import config, NebulaResponse
from firefly.common import CLIENT_ID
from firefly.objects import asset_cache
from firefly.version import FIREFLY_VERSION
from firefly.qt import (
    QApplication,
    QNetworkAccessManager,
    QNetworkRequest,
    QUrl,
)


class NebulaAPI:
    def __init__(self):
        self.manager = None
        self.queries = []

    def run(self, endpoint: str, callback, **kwargs):
        if self.manager is None:
            self.manager = QNetworkAccessManager()

        is_async = " async" if callback == -1 else ""
        logging.info(f"Executing {endpoint} request{is_async}")

        endpoint = "/api/" + endpoint
        data = json.dumps(kwargs).encode("ascii")
        access_token = config.get("session_id")
        authorization = bytes(f"Bearer {access_token}", "ascii")
        user_agent = bytes(f"firefly/{FIREFLY_VERSION}", "ascii")

        request = QNetworkRequest(QUrl(config["hub"] + endpoint))
        request.setRawHeader(b"Content-Type", b"application/json")
        request.setRawHeader(b"User-Agent", user_agent)
        request.setRawHeader(b"Authorization", authorization)
        request.setRawHeader(b"X-Client-Id", bytes(CLIENT_ID, "ascii"))

        try:
            query = self.manager.post(request, data)
            if callback != -1:
                query.finished.connect(functools.partial(self.handler, query, callback))
            self.queries.append(query)
        except Exception:
            log_traceback()
            if callback:
                r = NebulaResponse(400, "Unable to send request")
                if callback == -1:
                    return r
                else:
                    callback(r)
            return

        if callback == -1:
            while not query.isFinished():
                time.sleep(0.0001)
                QApplication.processEvents()
            return self.handler(query, -1)

    def handler(self, response, callback):
        status = response.attribute(QNetworkRequest.HttpStatusCodeAttribute)
        bytes_string = response.readAll()
        data = str(bytes_string, "utf-8")
        if not data:
            return NebulaResponse(500, "Empty response")

        payload = json.loads(data)
        message = payload.get("detail", "")
        payload.pop("detail", None)

        result = NebulaResponse(status, message, **payload)
        self.queries.remove(response)
        if callback and callback != -1:
            callback(result)
        return result

    def __getattr__(self, endpoint: str):
        def wrapper(callback=-1, **kwargs):
            return self.run(endpoint, callback, **kwargs)

        return wrapper


api = NebulaAPI()
asset_cache.api = api
