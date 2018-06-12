#!/usr/bin/env python3

import sys
import time
import functools

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from .mpv import MPV
from nxtools import *


CHR_PLAY = "\u25B6"
CHR_PAUSE = "\u23F8"
CHR_PREV = "\u29CF"
CHR_NEXT = "\u29D0"
CHR_GO_IN = "\u291D"
CHR_GO_OUT = "\u291E"
CHR_MARK = "\u2B25"
CHR_CLEAR = "\u2B26"


class TimecodeWindow(QLineEdit):
    def __init__(self, parent=None):
        super(TimecodeWindow, self).__init__(parent)
        self.setText("00:00:00:00")
        self.setInputMask("99:99:99:99")

        fm = self.fontMetrics()
        w = fm.boundingRect(self.text()).width() + 16
        self.setMinimumWidth(w)
        self.setMaximumWidth(w)




def get_navbar(wnd):
    toolbar = QToolBar(wnd)

    wnd.action_frame_prev5 = QAction('Previous 5 frames', wnd)
    wnd.action_frame_prev5.setShortcut('1')
    wnd.action_frame_prev5.triggered.connect(wnd.on_5_prev)
    wnd.addAction(wnd.action_frame_prev5)

    wnd.action_frame_next5 = QAction('Next 5 frames', wnd)
    wnd.action_frame_next5.setShortcut('2')
    wnd.action_frame_next5.triggered.connect(wnd.on_5_next)
    wnd.addAction(wnd.action_frame_next5)


    wnd.action_clear_in = QAction(CHR_CLEAR, wnd)
    wnd.action_clear_in.setShortcut('d')
    wnd.action_clear_in.setStatusTip('Clear IN')
    wnd.action_clear_in.triggered.connect(wnd.on_clear_in)
    toolbar.addAction(wnd.action_clear_in)

    wnd.action_mark_in = QAction(CHR_MARK, wnd)
    wnd.action_mark_in.setShortcut('E')
    wnd.action_mark_in.setStatusTip('Mark IN')
    wnd.action_mark_in.triggered.connect(wnd.on_mark_in)
    toolbar.addAction(wnd.action_mark_in)

    wnd.action_goto_in = QAction(CHR_GO_IN, wnd)
    wnd.action_goto_in.setShortcut('Q')
    wnd.action_mark_in.setStatusTip('Go to selection start')
    wnd.action_goto_in.triggered.connect(wnd.on_go_in)
    toolbar.addAction(wnd.action_goto_in)

    wnd.action_frame_prev = QAction(CHR_PREV, wnd)
    wnd.action_frame_prev.setShortcut('3')
    wnd.action_frame_prev.setStatusTip('Go to previous frame')
    wnd.action_frame_prev.triggered.connect(wnd.on_frame_prev)
    toolbar.addAction(wnd.action_frame_prev)

    wnd.action_play = QAction(CHR_PLAY, wnd)
    wnd.action_play.setShortcut('Space')
    wnd.action_play.setStatusTip('Play/Pause')
    wnd.action_play.triggered.connect(wnd.on_pause)
    toolbar.addAction(wnd.action_play)

    wnd.action_frame_next = QAction(CHR_NEXT, wnd)
    wnd.action_frame_next.setShortcut('4')
    wnd.action_frame_next.setStatusTip('Go to next frame')
    wnd.action_frame_next.triggered.connect(wnd.on_frame_next)
    toolbar.addAction(wnd.action_frame_next)

    wnd.action_goto_out = QAction(CHR_GO_OUT, wnd)
    wnd.action_goto_out.setShortcut('W')
    wnd.action_goto_out.setStatusTip('Go to selection end')
    wnd.action_goto_out.triggered.connect(wnd.on_go_out)
    toolbar.addAction(wnd.action_goto_out)

    wnd.action_mark_out = QAction(CHR_NEXT, wnd)
    wnd.action_mark_out.setShortcut('R')
    wnd.action_mark_out.setStatusTip('Mark OUT')
    wnd.action_mark_out.triggered.connect(wnd.on_mark_out)
    toolbar.addAction(wnd.action_mark_out)

    wnd.action_clear_out = QAction(CHR_CLEAR, wnd)
    wnd.action_clear_out.setShortcut('f')
    wnd.action_clear_out.setStatusTip('Clear OUT')
    wnd.action_clear_out.triggered.connect(wnd.on_clear_out)
    toolbar.addAction(wnd.action_clear_out)

    return toolbar







class VideoPlayer(QWidget):
    def __init__(self, parent=None):
        super(VideoPlayer, self).__init__(parent)

        self.video_window = QWidget(self)
        self.video_window.setStyleSheet("background-color: #161616;")
        self.player = MPV(
                    keep_open=True,
                    wid=str(int(self.video_window.winId()))
                )

        self.position = 0
        self.duration = 0
        self.mark_in  = 0
        self.mark_out = 0
        self.fps = 25.0

        self.prev_position = 0
        self.prev_duration = 0
        self.prev_mark_in  = 0
        self.prev_mark_out = 0

        @self.player.property_observer('time-pos')
        def time_observer(_name, value):
            self.on_time_change(value)

        @self.player.property_observer('duration')
        def duration_observer(_name, value):
            self.on_duration_change(value)

        #
        # Displays
        #

        self.mark_in_display = TimecodeWindow(self)
        self.mark_in_display.setToolTip("Selection start")

        self.mark_out_display = TimecodeWindow(self)
        self.mark_out_display.setToolTip("Selection end")

        self.io_display = TimecodeWindow(self)
        self.io_display.setToolTip("Selection duration")
        self.io_display.setReadOnly(True)

        self.position_display = TimecodeWindow(self)
        self.position_display.setToolTip("Clip position")

        self.duration_display = TimecodeWindow(self)
        self.duration_display.setToolTip("Clip duration")
        self.duration_display.setReadOnly(True)

        #
        # Controls
        #

        self.timeline = QSlider(Qt.Horizontal)
        self.timeline.setRange(0, 0)
        self.timeline.sliderMoved.connect(self.on_timeline_seek)

        self.navbar = get_navbar(self)

        #
        # Layout
        #

        bottom_bar = QHBoxLayout()
        top_bar = QHBoxLayout()

        top_bar.addWidget(self.mark_in_display, 0)
        top_bar.addStretch(1)
        top_bar.addWidget(self.io_display, 0)
        top_bar.addStretch(1)
        top_bar.addWidget(self.mark_out_display, 0)

        bottom_bar.addWidget(self.position_display, 0)
        bottom_bar.addStretch(1)
        bottom_bar.addWidget(self.navbar, 0)
        bottom_bar.addStretch(1)
        bottom_bar.addWidget(self.duration_display, 0)

        layout = QVBoxLayout()
        layout.addLayout(top_bar)
        layout.addWidget(self.video_window)
        layout.addWidget(self.timeline)
        layout.addLayout(bottom_bar)

        self.setLayout(layout)
        self.navbar.setFocus(True)

        # Displays updater

        self.display_timer = QTimer()
        self.display_timer.timeout.connect(self.on_display_timer)
        self.display_timer.start(40)


    @property
    def frame_dur(self):
        return 1 / self.fps

    def load(self, path, mark_in=0, mark_out=0):
        self.player["pause"] = True
        self.player.play(path)
        self.mark_in = mark_in
        self.mark_out = mark_out

    def on_time_change(self, value):
        self.position = value

    def on_duration_change(self, value):
        if value:
            self.duration = value
            self.mark_out = self.mark_out or value - self.frame_dur
        else:
            self.duration = 0
            self.mark_out = 0

    def on_timeline_seek(self):
        self.player["pause"] = True
        self.player.seek(self.timeline.value() / 100.0, "absolute", "exact")

    def on_frame_next(self):
        self.player.frame_step()

    def on_frame_prev(self):
        self.player.frame_back_step()

    def on_5_next(self):
        self.player.seek(5*self.frame_dur, "relative", "exact")

    def on_5_prev(self):
        self.player.seek(-5*self.frame_dur, "relative", "exact")

    def on_go_in(self):
        self.seek(self.mark_in)

    def on_go_out(self):
        self.seek(self.mark_out)

    def on_mark_in(self):
        self.mark_in = self.position

    def on_mark_out(self):
        self.mark_out = self.position

    def on_clear_in(self):
        self.mark_in = 0

    def on_clear_out(self):
        self.mark_out = self.duration

    def seek(self, position):
        self.player.seek(position, "absolute", "exact")

    def on_pause(self):
        self.player["pause"] = not self.player["pause"]

    def on_display_timer(self):
        if self.position != self.prev_position and self.position is not None:
            self.position_display.setText(s2tc(self.position))
            self.timeline.setValue(int(self.position*100))
            self.prev_position = self.position

        if self.duration != self.prev_duration and self.position is not None:
            self.duration_display.setText(s2tc(self.duration))
            self.timeline.setMaximum(int(self.duration*100))
            self.prev_duration = self.duration

        if self.mark_in != self.prev_mark_in or self.mark_out != self.prev_mark_out:
            self.mark_in_display.setText(s2tc(self.mark_in))
            self.mark_out_display.setText(s2tc(self.mark_out))
            self.io_display.setText(s2tc(self.mark_out - self.mark_in + self.frame_dur))
            self.prev_mark_in = self.mark_in
            self.prev_mark_out = self.mark_out



if __name__ == "__main__":
    path = "https://sport5.nebulabroadcast.com/proxy/0001/1000.mp4"

    class Test(QMainWindow):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.player = VideoPlayer(self)
            self.setCentralWidget(self.player)
            self.player.load(path)

    app = QApplication(sys.argv)

    import locale
    locale.setlocale(locale.LC_NUMERIC, 'C')
    win = Test()
    win.show()
    sys.exit(app.exec_())
