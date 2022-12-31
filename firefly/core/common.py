import os
import sys
import json
import hashlib
import socket

from http import HTTPStatus
from nxtools import PLATFORM, logging, log_traceback, critical_error


logging.show_time = True
logging.user = "nebula"


if PLATFORM == "windows":
    def ismount(path):
        """Check if a path is a mounted mount point."""
        return True
else:
    from posixpath import ismount


class Storage:
    def __init__(self, id, **kwargs):
        self.id = int(id)
        self.settings = kwargs

    def __getitem__(self, key):
        return self.settings[key]

    def __repr__(self):
        r = f"storage ID:{self.id}"
        if self.get("title"):
            r += f" ({self['title']})"
        return r

    def get(self, key, default=None):
        return self.settings.get(key, default)

    @property
    def title(self):
        if "title" in self.settings:
            return self.settings["title"]
        return "Storage {}".format(self.id)

    @property
    def local_path(self):
        if str(self.id) in config.get("alt_storages", []):
            alt_storage_config = config["alt_storages"][str(self.id)]
            if config.get("id_service", -1) in alt_storage_config.get("services", []):
                return alt_storage_config["path"]

        if self["protocol"] == "local":
            return self["path"]
        elif PLATFORM == "unix":
            return os.path.join("/mnt/{}_{:02d}".format(config["site_name"], self.id))
        return ""

    def __len__(self):
        if self["protocol"] == "local" and os.path.isdir(self["path"]):
            return True
        return (
            os.path.isdir(self.local_path)
            and ismount(self.local_path)
            and len(os.listdir(self.local_path)) != 0
        )


class UnknownStorage:
    def __init__(self, id, **kwargs):
        self.id = int(id)
        self.title = "Unknown storage {}".format(self.id)

    def __repr__(self):
        return self.title

    def __getitem__(self, key):
        return False

    @property
    def local_path(self):
        return ""

    def __len__(self):
        return 0


class Storages:
    def __getitem__(self, key):
        if key not in config["storages"]:
            return UnknownStorage(key)
        return Storage(key, **config["storages"][key])

    def __iter__(self):
        return config["storages"].__iter__()

    def items(self):
        return [(id_storage, self[id_storage]) for id_storage in config["storages"]]


storages = Storages()
