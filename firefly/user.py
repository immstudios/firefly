from typing import Any


class FireflyUser:
    def __init__(self):
        self.meta = {}

    def __str__(self):
        return self.meta.get("login", "Anonymous")

    def __getitem__(self, key: str) -> Any:
        return self.meta.get(key)

    def update(self, meta: dict[str, Any]) -> None:
        self.meta.update(meta)

    def can(self, action: str, value: Any = None, anyval=False) -> bool:
        return True

        if self["is_admin"]:
            return True
        key = f"can/{action}"
        if not self[key]:
            return False
        if anyval:
            return True
        return self[key] is True or (type(self[key]) == list and value in self[key])


user = FireflyUser()
