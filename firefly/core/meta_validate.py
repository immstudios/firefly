class NebulaInvalidValueError(Exception):
    pass


def validate_default(meta_type, value):
    if type(value) in [str, float, int, list, dict]:
        return value
    return str(value)


def validate_string(meta_type, value):
    return str(value).strip()


def validate_text(meta_type, value):
    return str(value).strip()


def validate_integer(meta_type, value):
    if not value:
        return 0
    try:
        value = int(value)
    except ValueError:
        raise NebulaInvalidValueError
    return value


def validate_numeric(meta_type, value):
    if type(value) in [int, float]:
        return value
    try:
        return float(value)
    except ValueError:
        raise NebulaInvalidValueError


def validate_boolean(meta_type, value):
    if value:
        return True
    return False


def validate_datetime(meta_type, value):
    return validate_numeric(meta_type, value)


def validate_timecode(meta_type, value):
    return validate_numeric(meta_type, value)


def validate_regions(meta_type, value):
    return value


def validate_fract(meta_type, value):
    value = value.replace(":", "/")
    split = value.split("/")
    try:
        assert len(split) == 2
        assert split[0].replace(".", "", 1).isdigit()
        assert split[1].isdigit()
    except AssertionError:
        raise NebulaInvalidValueError("Invalid fraction format")
    return value


def validate_select(meta_type, value):
    return str(value)


def validate_list(meta_type, value):
    return [str(v) for v in value] if type(value) == list else [str(value)]


def validate_color(meta_type, value):
    if not value:
        return 0
    if type(value) == int:
        return value
    if type(value) != str:
        return 0
    if value.startswith("#"):
        base = 16
        value = value.lstrip("#")
    else:
        base = 10
    try:
        value = int(value, base)
    except ValueError:
        raise NebulaInvalidValueError
    return value


validators = {
    "string": validate_string,
    "text": validate_text,
    "integer": validate_integer,
    "numeric": validate_numeric,
    "boolean": validate_boolean,
    "datetime": validate_datetime,
    "timecode": validate_timecode,
    "object": validate_regions,
    "fraction": validate_fract,
    "select": validate_select,
    "list": validate_list,
    "color": validate_color,
}
