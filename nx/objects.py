import os
import time
import copy

from .core import *
from .core.base_objects import *
from .connection import *

__all__ = ["Asset", "Item", "Bin", "Event", "User", "anonymous"]


class FireflyObject(BaseObject):
    pass

class Asset(AssetMixIn, FireflyObject):
    pass

class Item(ItemMixIn, FireflyObject):
    pass

class Bin(BinMixIn, FireflyObject):
    pass

class Event(EventMixIn, FireflyObject):
    pass

class User(UserMixIn, FireflyObject):
    def has_right(self, key, val=True):
        if self["is_admin"]:
            return True
        key = "can/{}".format(key)
        if not self[key]:
            return False
        return self[key] == True or (type(self[key]) == list and val in self[key])

    def __getitem__(self, key):
        if self.meta.get("is_admin", False) and key.startswith("can/"):
            return True
        key = key.lower().strip()
        if not key in self.meta:
            return meta_types[key].default
        return self.meta[key]

anonymous = User(meta={
        "login" : "Anonymous"
    })
