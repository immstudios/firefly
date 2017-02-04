import json
import requests

from nebulacore import *

__all__ = ["api"]

class APIResult(object):
    def __init__(self, **kwargs):
        self._data = {}
        self._data.update(kwargs)

    @property
    def response(self):
        return self.get("response", 500)

    @property
    def message(self):
        return self.get("message", "Invalid data")

    @property
    def data(self):
        return self.get("data", {})

    @property
    def is_success(self):
        return self.response < 400

    @property
    def is_error(self):
        return self.response >= 400

    def get(self, key, default=False):
        return self._data.get(key, default)

    def __getitem__(self, key):
        return self._data[key]



class NebulaAPI(object):
    def __init__(self, **kwargs):
        self._settings = kwargs
        self._cookies = requests.cookies.RequestsCookieJar()

    def get_user(self):
        try:
            response = requests.post(
                    self._settings["hub"] + "/ping",
                    cookies=self._cookies
                )
            self._cookies = response.cookies
            result = json.loads(response.text)
        except Exception:
            log_traceback()
            return False
        if result["response"] >= 400:
            return False
        if not result["user"]:
            return False
        return result["user"]

    @property
    def auth_key(self):
        return self._cookies.get("session_id", "0")

    def set_auth(self, key):
        self._cookies["session_id"] = key

    def login(self, login, password):
        data = {"login" : login, "password" : password, "api" : 1}
        response = requests.post(self._settings["hub"] + "/login", data)
        self._cookies = response.cookies
        data = json.loads(response.text)
        return APIResult(**data)

    def run(self, method, **kwargs):
        response = requests.post(
                self._settings["hub"] + "/api/" + method,
                data=json.dumps(kwargs),
                cookies=self._cookies

            )
        self._cookies = response.cookies
        data = json.loads(response.text)
        return APIResult(**data)

    def __getattr__(self, method_name):
        def wrapper(**kwargs):
            return self.run(method_name, **kwargs)
        return wrapper


api = NebulaAPI()
