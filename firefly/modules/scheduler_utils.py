import re
from firefly import *

COLOR_CALENDAR_BACKGROUND = QColor("#161616")
COLOR_DAY_BACKGROUND = QColor("#323232")

TIME_PENS = [
        (60 , QPen( QColor("#999999"), 2 , Qt.SolidLine )),
        (15 , QPen( QColor("#999999"), 1 , Qt.SolidLine )),
        (5  , QPen( QColor("#444444"), 1 , Qt.SolidLine ))
    ]


RUN_PENS = [
    QPen( QColor("#dddd00"), 2 , Qt.SolidLine ),
    QPen( QColor("#dd0000"), 2 , Qt.SolidLine )
    ]


SECS_PER_DAY = 3600 * 24
MINS_PER_DAY = 60 * 24
SECS_PER_WEEK = SECS_PER_DAY * 7
SAFE_OVERRUN = 5 # Do not warn if overrun < 5 mins

CLOCKBAR_WIDTH = 45


def suggested_duration(dur):
    adur = int(dur) + 360
    g = adur % 300
    return adur - g + 300 if g > 150 else adur -g

def text_shorten(text, font, target_width):
    fm = QFontMetrics(font)
    exps =  [r"\W|_", r"[a-z]([aáeéěiíoóuůú])", r"[a-z]", r"."]
    r = exps.pop(0)
    text = text[::-1]
    while fm.width(text) > target_width:
        text, n = re.subn(r, "", text, 1)
        if n == 0:
            r = exps.pop(0)
    return text[::-1]

