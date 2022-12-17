from typing import Any
from pydantic import BaseModel, Field


def find_by_id(array: list[dict[str, Any]], id: int) -> Any:
    for item in array:
        if item.id == id:
            return item
    return None


class SettingsModel(BaseModel):
    pass


class FolderField(SettingsModel):
    name: str
    mode: str | None = None
    format: str | None = None
    order: str | None = None
    filter: str | None = None


class FolderSettings(SettingsModel):
    id: int = Field(...)
    name: str = Field(...)
    color: str = Field(...)
    fields: list[FolderField] = Field(default_factory=list)
    links: list[Any] = Field(default_factory=list)


class ViewSettings(SettingsModel):
    id: int = Field(...)
    name: str = Field(...)
    position: int = Field(...)
    folders: list[int] = Field(default_factory=list)
    states: list[int] = Field(default_factory=list)
    columns: list[str] = Field(default_factory=list)
    conditions: list[str] = Field(default_factory=list)
    separator: bool = False


class PlayoutChannelSettings(SettingsModel):
    id: int = Field(...)
    name: str = Field(...)
    fps: float = Field(25.0)
    plugins: list[str] = Field(default_factory=list)
    solvers: list[str] = Field(default_factory=list)
    day_start: tuple[int, int] = Field((7, 0))
    rundown_columns: list[str] = Field(default_factory=list)
    fields: list[FolderField] = Field(default_factory=list)


class Settings(SettingsModel):
    folders: list[FolderSettings] = Field(default_factory=list)
    views: list[ViewSettings] = Field(default_factory=list)
    metatypes: dict[str, Any] = Field(default_factory=dict)
    cs: dict[str, Any] = Field(default_factory=dict)
    playout_channels: list[PlayoutChannelSettings] = Field(default_factory=list)

    def get_folder(self, id_folder: int) -> FolderSettings:
        return find_by_id(self.folders, id_folder)

    def get_view(self, id_view: int) -> ViewSettings:
        return find_by_id(self.views, id_view)

    def get_playout_channel(self, id_channel: int) -> PlayoutChannelSettings:
        return find_by_id(self.playout_channels, id_channel)


settings = Settings()


def update_settings(data: dict[str, Any]) -> None:
    """Update settings from a dict."""
    new_settings = Settings(**data)
    for key in new_settings.dict().keys():
        if key in settings.dict().keys():
            setattr(settings, key, getattr(new_settings, key))
