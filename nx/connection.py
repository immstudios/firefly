import json
import hashlib
import socket
import getpass
import requests

from .core import *

__all__ = ["api"]

DEFAULT_PORT = 443
DEFAULT_SSL = True


class ApiResult():
    def __init__(self, **kwargs):
        self.data = {}
        self.data.update(kwargs)

    @property
    def response(self):
        return self.get("response", 500)

    @property
    def message(self):
        return self.get("message", "Invalid data")

    @property
    def is_success(self):
        return self.response < 400

    @property
    def is_error(self):
        return self.response >= 400

    def get(self, key, default=False):
        return self.data.get(key, default)

    def __getitem__(self, key):
        return self.data[key]



class NebulaApi():
    def __init__(self, **kwargs):
        self.settings = kwargs
        self.cookies = requests.cookies.RequestsCookieJar()

    def get_user(self):
        try:
            response = requests.post(
                    self.settings["host"] + "/ping",
                    cookies=self.cookies
                )
            self.cookies = response.cookies
            result = json.loads(response.text)
        except:
            log_traceback()
            return False
        if result["response"] >= 400:
            return False
        return User(meta=result["user"])

    @property
    def auth_key(self):
        return self.cookies.get("session_id", "0")

    def set_auth(self, key):
        self.cookies["session_id"] = key

    def login(self, login, password):
        data = {"login" : login, "password" : password, "api" : 1}
        print (data)
        response = requests.post(self.settings["host"] + "/login", data)
        self.cookies = response.cookies
        data = json.loads(response.text)
        print ("RESPONSE:",  data)
        return ApiResult(**data)


    def run(self, method, **kwargs):
        response = requests.post(
                self.settings["host"] + "/api/" + method,
                data=json.dumps(kwargs),
                cookies=self.cookies
            )
        self.cookies = response.cookies
        data = json.loads(response.text)
        return ApiResult(**data)

    def __getattr__(self, method_name):
        def wrapper(**kwargs):
            return self.run(method_name, **kwargs)
        return wrapper


api = NebulaApi()
