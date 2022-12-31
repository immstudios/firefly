from nxtools import format_filesize, format_time, s2time, unaccent, logging

import firefly

from .common import storages
from .enum import ContentType, ObjectStatus, MediaType
from .meta_utils import shorten, tree_indent

#
# Formating helpers
#


def format_text(meta_type, value, **kwargs):
    result = kwargs.get("result", "alias")
    if result == "brief":
        return {"value": shorten(value, 100)}
    if result == "full":
        return {"value": value}
    return value


def format_integer(meta_type, value, **kwargs):
    result = kwargs.get("result", "alias")
    value = int(value)

    if not value:  # TODO: and meta_type.settings.get("hide_null", False):
        alias = ""

    elif meta_type.name == "file/size":
        alias = format_filesize(value)

    elif meta_type.name == "id_folder":
        if folder := firefly.settings.get_folder(value):
            alias = folder.name
        else:
            alias = f"Unknown folder ({value})"

    elif meta_type.name == "status":
        alias = ObjectStatus(value).name

    elif meta_type.name == "content_type":
        alias = ContentType(value).name

    elif meta_type.name == "media_type":
        alias = MediaType(value).name

    elif meta_type.name == "id_storage":
        alias = storages[value].__repr__().lstrip("storage ")

    else:
        alias = str(value)

    if result in ["brief", "full"]:
        return {"value": value, "alias": alias}
    return alias


def format_numeric(meta_type, value, **kwargs):
    if type(value) not in [int, float]:
        try:
            value = float(value)
        except ValueError:
            value = 0
    result = kwargs.get("result", "alias")
    alias = "{:.03f}".format(value)
    if result in ["brief", "full"]:
        return {"value": value, "alias": alias}
    return alias


def format_boolean(meta_type, value, **kwargs):
    value = int(value)
    result = kwargs.get("result", "alias")
    alias = ["no", "yes"][bool(value)]
    if result in ["brief", "full"]:
        return {"value": value, "alias": alias}
    return alias


def format_datetime(meta_type, value, **kwargs):
    result = kwargs.get("result", "alias")
    time_format = kwargs.get("format") or meta_type.format or "%Y-%m-%d %H:%M"
    alias = format_time(
        value,
        time_format,
        never_placeholder=kwargs.get("never_placeholder", "never"),
    )
    if result in ["brief", "full"]:
        return {"value": value, "alias": alias}
    return alias


def format_timecode(meta_type, value, **kwargs):
    result = kwargs.get("result", "alias")
    alias = s2time(value)
    if result in ["brief", "full"]:
        return {"value": value, "alias": alias}
    return alias


def format_regions(meta_type, value, **kwargs):
    result = kwargs.get("result", "alias")
    alias = "{} regions".format(len(value))
    if result in ["brief", "full"]:
        return {"value": value, "alias": alias}
    return alias


def format_fract(meta_type, value, **kwargs):
    result = kwargs.get("result", "alias")
    alias = value  # TODO
    if result in ["brief", "full"]:
        return {"value": value, "alias": alias}
    return alias


def format_select(meta_type, value, **kwargs):
    value = str(value)
    result = kwargs.get("result", "alias")

    cs = meta_type.csdata

    if result == "brief":
        return {"value": value, "alias": cs.title(value)}

    elif result == "full":
        result = []
        has_zero = has_selected = False
        # if (value not in cs.data) and (value in cs.csdata):
        #     adkey = [value]
        # else:
        adkey = []
        for csval in cs.data + adkey:
            if csval == "0":
                has_zero = True
            if value == csval:
                has_selected = True
            role = cs.role(csval)
            if role == "hidden":
                continue
            result.append(
                {
                    "value": csval,
                    "alias": cs.title(csval),
                    "description": cs.description(csval),
                    "selected": value == csval,
                    "role": role,
                    "indent": 0,
                }
            )
        if meta_type.mode == "tree":

            def sort_mode(x):
                return "".join([n.zfill(5) for n in x["value"].split(".")])

            result.sort(key=sort_mode)
            tree_indent(result)
        else:
            if meta_type.order == "alias":

                def sort_mode(x):
                    return unaccent(str(x["alias"]))

            else:

                def sort_mode(x):
                    return unaccent(str(x["value"]))

            result.sort(key=sort_mode)
        if not has_selected:
            if has_zero:
                result[0]["selected"] = True
            else:
                result.insert(
                    0, {"value": "", "alias": "", "selected": True, "role": "option"}
                )
        return result

    elif result == "description":
        return cs.description(value)

    else:  # alias
        return cs.title(value)


def format_list(meta_type, value, **kwargs):
    if type(value) == str:
        value = [value]
    elif type(value) != list:
        logging.warning("Unknown value {} for key {}".format(value, meta_type))
        value = []

    value = [str(v) for v in value]
    result = kwargs.get("result", "alias")

    cs = meta_type.csdata

    if result == "brief":
        return {
            "value": value,
            "alias": ", ".join([cs.title(v) for v in value]),
        }

    elif result == "full":
        result = []
        adkey = []
        # for v in value:
        #     if (v not in cs.data) and (v in cs.csdata):
        #         adkey.append(v)

        for csval in cs.data + adkey:
            role = cs.role(csval)
            if role == "hidden":
                continue
            result.append(
                {
                    "value": csval,
                    "alias": cs.title(csval),
                    "description": cs.description(csval),
                    "selected": csval in value,
                    "role": role,
                    "indent": 0,
                }
            )
        if meta_type.mode == "tree":

            def sort_mode(x):
                return "".join([n.zfill(3) for n in x["value"].split(".")])

            result.sort(key=sort_mode)
            tree_indent(result)
        else:
            if meta_type.order == "alias":

                def sort_mode(x):
                    return unaccent(str(x["alias"]))

            else:

                def sort_mode(x):
                    return unaccent(str(x["value"]))

            result.sort(key=sort_mode)
        return result

    elif result == "description":
        if len(value):
            return cs.description(value[0])
        return ""

    else:  # alias
        return ", ".join([cs.title(v) for v in value])


def format_color(meta_type, value, **kwargs):
    return = f"#{value:06X}"


humanizers = {
    -1: None,
    "string": format_text,
    "text": format_text,
    "integer": format_integer,
    "numeric": format_numeric,
    "boolean": format_boolean,
    "datetime": format_datetime,
    "timecode": format_timecode,
    "object": format_regions,
    "fraction": format_fract,
    "select": format_select,
    "list": format_list,
    "color": format_color,
}
