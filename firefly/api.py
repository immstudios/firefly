__all__ = ["api"]

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
    QUrlQuery,
    QUrl,
)


class NebulaAPI:
    def __init__(self):
        self.manager = None
        self.queries = []

    def run(self, method, callback, **kwargs):
        if self.manager is None:
            self.manager = QNetworkAccessManager()

        logging.debug(
            "Executing {}{} query".format("" if callback == -1 else "async ", method)
        )
        kwargs["session_id"] = config["session_id"]
        kwargs["initiator"] = CLIENT_ID

        if method in ["ping", "login", "logout"]:
            method = "/" + method
            mime = "application/x-www-form-urlencoded"
            post_data = QUrlQuery()
            for key in kwargs:
                post_data.addQueryItem(key, kwargs[key])
            data = post_data.toString(
                QUrl.ComponentFormattingOption.FullyEncoded
            ).encode("ascii")
        else:
            method = "/api/" + method
            mime = "application/json"
            data = json.dumps(kwargs).encode("ascii")

        request = QNetworkRequest(QUrl(config["hub"] + method))
        request.setHeader(QNetworkRequest.KnownHeaders.ContentTypeHeader, mime)
        request.setHeader(
            QNetworkRequest.KnownHeaders.UserAgentHeader,
            f"nebula-firefly/{FIREFLY_VERSION}",
        )

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
        bytes_string = response.readAll()
        data = str(bytes_string, "ascii")
        if not data:
            return NebulaResponse(500, "Empty response")
        try:
            result = NebulaResponse(**json.loads(data))
        except Exception:
            result = NebulaResponse(500, "Unable to parse response")
        self.queries.remove(response)
        if callback and callback != -1:
            callback(result)
        return result

    def __getattr__(self, method_name):
        def wrapper(callback=-1, **kwargs):
            return self.run(method_name, callback, **kwargs)

        return wrapper


api = NebulaAPI()
asset_cache.api = api
