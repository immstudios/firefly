from nebulacore import *
from nebulacore.base_objects import BaseObject

__all__ = ["FireflyObject"]

DEFAULT_TEXT_COLOR  = "#c0c0c0"
RUNDOWN_EVENT_BACKGROUND_COLOR = "#000000";

STATUS_FG_COLORS = {
    OFFLINE  : "#dd0000",
    ONLINE   : DEFAULT_TEXT_COLOR,
    CREATING : "#dddd00",
    TRASHED  : "#808080",
    ARCHIVED : "#808080",
    RESET    : "#dddd00",
}

class CellFormat(object):
    key = "none"
    def display(self, obj, **kwargs):
        return None

    def decoration(self, obj, **kwargs):
        return None

    def tooltip(self, obj, **kwargs):
        return None

    def statustip(self, obj, **kwargs):
        return self.tooltip(obj, **kwargs)

    def whatsthis(self, obj, **kwargs):
        return self.tooltip(obj, **kwargs)

    def background(self, obj, **kwargs):
        return None

    def foreground(self, obj, **kwargs):
        return None

#
# Cell formatters
#

class FormatFolder(CellFormat):
    key = "id_folder"
    def foreground(self, obj, **kwargs):
        return config["folders"][obj["id_folder"]]["color"]


class FormatContentType(CellFormat):
    key = "content_type"
    def decoration(self, obj, **kwargs):
        return ["text", "video", "audio", "image"][int(obj[self.key])]


class FormatPromoted(CellFormat):
    key = "promoted"
    def display(self, obj, **kwargs):
        return ""

    def decoration(self, obj, **kwargs):
        return ["star_disabled", "star_enabled"][int(obj[self.key])]



class FormatRundownStatus(CellFormat):
    key = "rundown_status"
    def display(self, obj, **kwargs):
        if obj.object_type != "item" or not obj["id_asset"]:
            return ""

        if obj["rundown_transfer_progress"] and float(obj["rundown_transfer_progress"]) == -1:
            return "PENDING"

        elif obj["rundown_transfer_progress"] and float(obj["rundown_transfer_progress"]) > -1:
            return "{:0.2f}%".format(float(obj["rundown_transfer_progress"]))

        return {
                -2 : "PART AIRED",
                -1 : "AIRED",
                0 : "OFFLINE",
                1 : "NOT SCHEDULED",
                2 : "READY"
                }.get(int(obj[self.key]), "UNKNOWN")

    def foreground(self, obj, **kwargs):
        return None
        if obj["rundown_transfer_progress"] and int(obj["rundown_transfer_progress"]) >= -1:
            return NXColors[ASSET_FG_CREATING]

        if obj.object_type == "item" and self["rundown_status"] == -1:
            return "#404040"

        if obj.object_type == "item":
            return [NXColors[ASSET_FG_OFFLINE],
                    NXColors[ASSET_FG_OFFLINE],
                    DEFAULT_TEXT_COLOR
                    ][int(obj[self.key])]


class FormatRundownDifference(CellFormat):
    key = "rundown_difference"
    def foreground(self, obj, **kwargs):
        if obj["rundown_broadcast"] and obj["rundown_scheduled"]:
            diff = obj["rundown_broadcast"] - obj["rundown_scheduled"]
            return ["#ff0000", "#00ff00"][diff >= 0]


class FormatRunMode(CellFormat):
    key = "run_mode"
    def display(self, obj, **kwargs):
        if obj.object_type == "item" and not obj["id_asset"]:
            return
        if obj[self.key] == 1:
            return "MANUAL"
        if obj[self.key] == 2:
            return "SOFT"
        elif obj[self.key] == 3:
            return "HARD"
        return "AUTO"


class FormatState(CellFormat):
    key = "qc/state"
    def decoration(self, obj, **kwargs):
        return {
                0 : "qc_new",
                1 : "qc_failed",
                2 : "qc_passed",
                3 : "qc_rejected",
                4 : "qc_approved"
                }[int(obj.meta.get(self.key, 0))]

    def foreground(self, obj, **kwargs):
        return {
                0 : None,
                1 : "#cc0000",
                2 : "#cccc00",
                3 : "#cc0000",
                4 : "#00cc00"
                }[int(obj.meta.get(self.key, 0))]


class FormatTitle(CellFormat):
    key = "title"
    def decoration(self, obj, **kwargs):
        if obj.object_type == "event":
            return ["star_disabled", "star_enabled"][int(obj["promoted"])]
        elif obj["status"] == ARCHIVED:
            return "archive"
        elif obj["status"] == TRASHED:
            return "trash"

        if obj.object_type == "item":
            if obj["id_folder"]:
                return "folder_" + str(obj["id_folder"])
            elif obj["item_role"] == "lead_in":
                return "mark_in"
            elif obj["item_role"] == "lead_out":
                return "mark_out"
            elif obj["item_role"] == "studio":
                return "talking_head"

    def foreground(self, obj, **kwargs):
        if obj.object_type in ["asset", "item"]:
            return STATUS_FG_COLORS[obj["status"]]

    def font(self, obj, **kwargs)
        if obj.object_type == "event":
            return "bold"
        elif obj.object_type == "item" and obj["id_asset"] == obj["rundown_event_asset"]:
            return "bold"


format_helpers_list = [
        FormatFolder,
        FormatContentType,
        FormatPromoted,
        FormatRundownStatus,
        FormatRundownDifference,
        FormatRunMode,
        FormatState,
        FormatTitle
    ]

format_helpers = {}

for h in format_helpers_list:
    helper = h()
    format_helpers[h.key] = helper


#
# Firefly object
#



class FireflyObject(BaseObject):
    def format_display(self, key, **kwargs):
        if key in format_helpers:
            val = format_helpers[key].display(self, **kwargs)
            if val is not None:
                return val
        return self.show(
                key,
                hide_null=True,
                shorten=100
            )

    def format_decoration(self, key, **kwargs):
        if key in format_helpers:
            return format_helpers[key].decoration(self, **kwargs)
        return None

    def format_background(self, key, **kwargs):
        model = kwargs.get("model")
        if self.object_type == "event":
            if model.__class__.__name__ == "RundownModel":
                return RUNDOWN_EVENT_BACKGROUND_COLOR
        if model and self.object_type == "item":
            if not self.id:
                return "#111140"
            elif model.cued_item == self.id:
                return "#059005"
            elif model.current_item == self.id:
                return "#900505"
            elif not self["id_asset"]:
                return "#121240"
        return None

    def format_foreground(self, key, **kwargs):
        if key in format_helpers:
            return format_helpers[key].foreground(self, **kwargs)

    def format_font(self, key, **kwargs):
        if key in format_helpers:
            return format_helpers[key].font(self, **kwargs)
        return None
