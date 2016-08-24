import math

from firefly_common import *
from firefly_widgets import *

PROGRESS_BAR_RESOLUTION = 2000


class OnAirButton(QPushButton):
    def __init__(self, title, parent=None, on_click=False):
        super(OnAirButton, self).__init__(parent)
        self.setText(title)

        if title == "Freeze":
            bg_col = "qlineargradient(x1: 0, y1: 0,    x2: 0, y2: 1,  stop: 0 #c01616, stop: 1 #941010);"
            self.setToolTip("Pause/unpause current clip")
        elif title == "Take":
            bg_col = "qlineargradient(x1: 0, y1: 0,    x2: 0, y2: 1,  stop: 0 #16c316, stop: 1 #109410);"
            self.setToolTip("Start cued clip")
        else:
            bg_col = "qlineargradient(x1: 0, y1: 0,    x2: 0, y2: 1,  stop: 0 #787878, stop: 1 #565656);"
        self.setStyleSheet("OnAirButton{font-size:16px; font-weight: bold; font-family: Arial; color: #eeeeee; border:  1px raised #323232;  width:80px; height:30px; background: %s }  OnAirButton:pressed {border-style: inset;} "%bg_col)

        if on_click:
            self.clicked.connect(on_click)

class OnAirLabel(QLabel):
    def __init__(self,head, default, parent=None, tcolor="#eeeeee"):
        super(OnAirLabel,self).__init__(parent)
        self.head = head
        self.setStyleSheet("background-color: #161616; padding:5px; margin:3px; font:16px; font-weight: bold; color : {}; width:160px".format(tcolor))
        #self.setMinimumWidth(160)

    def set_text(self,text):
       self.setText("%s: %s"%(self.head,text))




class OnAir(QWidget):
    def __init__(self, parent):
        super(OnAir, self).__init__(parent)

        self.pos = 0
        self.dur = 0
        self.current  = "(loading)"
        self.cued     = "(loading)"
        self.request_time = 0
        self.paused = False
        self.stopped = True
        self.local_request_time = time.time()

        self.fps = 25.0

        self.parent().setWindowTitle("On air ctrl")

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(PROGRESS_BAR_RESOLUTION)

        self.btn_take    = OnAirButton(u"Take",   self, self.on_take)
        self.btn_freeze  = OnAirButton(u"Freeze", self, self.on_freeze)
        self.btn_retake  = OnAirButton(u"Retake", self, self.on_retake)
        self.btn_abort   = OnAirButton(u"Abort",  self, self.on_abort)

        can_mcr = has_right("mcr", self.parent().id_channel)
        self.btn_take.setEnabled(can_mcr)
        self.btn_freeze.setEnabled(can_mcr)
        self.btn_retake.setEnabled(can_mcr)
        self.btn_abort.setEnabled(can_mcr)

        self.btn_take.setShortcut("F9")
        self.btn_freeze.setShortcut("F10")
        self.btn_retake.setShortcut("F11")
        self.btn_abort.setShortcut("F12")

        btns_layout = QHBoxLayout()

        btns_layout.addStretch(1)
        btns_layout.addWidget(self.btn_take ,0)
        btns_layout.addWidget(self.btn_freeze ,0)
        btns_layout.addWidget(self.btn_retake,0)
        btns_layout.addWidget(self.btn_abort,0)
        btns_layout.addStretch(1)

        self.display_clock   = OnAirLabel("CLK", "--:--:--:--")
        self.display_pos     = OnAirLabel("POS", "--:--:--:--")

        self.display_current = OnAirLabel("CUR","(no clip)", tcolor="#cc0000")
        self.display_cued    = OnAirLabel("NXT","(no clip)", tcolor="#00cc00")

        self.display_rem     = OnAirLabel("REM","(unknown)")
        self.display_dur     = OnAirLabel("DUR", "--:--:--:--")

        info_layout = QGridLayout()
        info_layout.setContentsMargins(0,0,0,0)
        info_layout.setSpacing(2)

        info_layout.addWidget(self.display_clock,   0, 0)
        info_layout.addWidget(self.display_pos,     1, 0)

        info_layout.addWidget(self.display_current, 0, 1)
        info_layout.addWidget(self.display_cued,    1, 1)

        info_layout.addWidget(self.display_rem,     0, 2)
        info_layout.addWidget(self.display_dur,     1, 2)

        info_layout.setColumnStretch(1,1)

        layout = QVBoxLayout()
        layout.addLayout(info_layout,0)
        layout.addStretch(1)
        layout.addWidget(self.progress_bar,0)
        layout.addLayout(btns_layout,0)
        self.setLayout(layout)

        self.display_timer = QTimer(self)
        self.display_timer.timeout.connect(self.update_display)
        self.display_timer.start(40)

    @property
    def route(self):
        return "play{}".format(self.parent().id_channel)

    def on_take(self, evt=False):
        query("take", self.route, id_channel=self.parent().id_channel)

    def on_freeze(self, evt=False):
        query("freeze", self.route, id_channel=self.parent().id_channel)

    def on_retake(self, evt=False):
        query("retake", self.route, id_channel=self.parent().id_channel)

    def on_abort(self, evt=False):
        query("abort", self.route, id_channel=self.parent().id_channel)

    def getState(self):
        state = {}
        state["class"] = "onair"
        return state

    def setState(self, state):
        pass


    def seismic_handler(self, data):
        status = data.data
        self.pos = status["position"] + (1/self.fps)
        self.request_time = status["request_time"]
        self.paused = status["paused"]
        self.stopped = status["stopped"]
        self.local_request_time = time.time()

        if self.dur !=  status["duration"]:
            self.dur = status["duration"]
            self.display_dur.set_text(f2tc(self.dur, self.fps))

        if self.current != status["current_title"]:
            self.current = status["current_title"]
            self.display_current.set_text(self.current)

        if self.cued != status["cued_title"]:
            self.cued = status["cued_title"]
            self.display_cued.set_text(self.cued)


    def update_display(self):
            adv = time.time() - self.local_request_time

            rtime = self.request_time+adv
            rpos = self.pos

            if not (self.paused or self.stopped):
                rpos += adv * self.fps

            clock = time.strftime("%H:%M:%S:{:02d}", time.localtime(rtime)).format(int(25*(rtime-math.floor(rtime))))
            self.display_clock.set_text(clock)
            self.display_pos.set_text(f2tc(min(self.dur, rpos), self.fps))

            rem = self.dur - rpos
            t = f2tc(max(0, rem), self.fps)
            if rem < 250:
                self.display_rem.set_text("<font color='red'>{}</font>".format(t))
            else:
                self.display_rem.set_text(t)

            try:
                ppos = int((rpos/self.dur) * PROGRESS_BAR_RESOLUTION)
            except ZeroDivisionError:
                return

            self.progress_bar.setValue(ppos)
