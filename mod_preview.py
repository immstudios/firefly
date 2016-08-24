from functools import partial

from firefly_common import *
from firefly_widgets import *

from dlg_subclips import SubclipsDialog
from nx.connection import DEFAULT_PORT, DEFAULT_SSL

T_MARK_IN  = 0
T_MARK_OUT = 1
T_POSITION = 2
T_DURATION = 3

class RegionBar(QWidget):
    def __init__(self,parent):
        super(RegionBar, self).__init__(parent)
        self.marks_color = QColor("#009fbc")
        self.setFixedHeight(3)
        self.data = [0,0,0,0]
        self.show()

    def mark_in(self, value=-1):
        return self._value(T_MARK_IN, value)

    def mark_out(self, value=-1):
        return self._value(T_MARK_OUT, value)

    def position(self, value=-1):
        return self._value(T_POSITION, value)

    def duration(self, value=-1):
        return self._value(T_DURATION, value)

    def _value(self, key, value):
        if value >= 0 and value != self.data[key]:
            self.data[key] = value
            self.update()
        return self.data[key]

    def paintEvent(self, event=False):
        qp = QPainter()
        qp.begin(self)
        self.drawRegion(qp)
        qp.end()

    def drawRegion(self, qp):
        duration = self.duration()
        if not duration:
            return
        mark_in = self.mark_in() or 0
        mark_out = self.mark_out() or duration
        w = self.width()
        h = self.height()
        x1 = (float(w) / duration) * (mark_in)
        x2 = (float(w) / duration) * (mark_out-mark_in)
        qp.setBrush(self.marks_color)
        qp.setPen(Qt.NoPen)
        qp.drawRect(x1, 1, x2, h-1)



def proxy_path(id_asset):
    host = config.get("media_host", False) or config.get("hive_host")
    port = config.get("media_port", False) or config.get("hive_port", DEFAULT_PORT)
    ssl  = config.get("media_ssl", False) or config.get("hive_ssl", DEFAULT_SSL)
    url  = "{}://{}:{}/proxy/{:04d}/{:d}.mp4".format(["http", "https"][ssl], host, port, int(id_asset/1000), id_asset)
    return QUrl(url)

def thumb_path(id_asset):
    host = config.get("media_host", False) or config["hive_host"]
    port = config.get("media_port", False) or config["hive_port"]
    url = "http://{}:{}/thumb/{:04d}/{:d}/{:d}m0.jpg".format(host, port, int(id_asset/1000), id_asset, id_asset)
    return url


def action_toolbar(wnd):
    toolbar = QToolBar(wnd)
    toolbar.setStyleSheet("background-color:transparent;")

    toolbar.addWidget(ToolBarStretcher(wnd))


    wnd.action_marks = QMenu("Save marks")
    wnd.action_marks.setStyleSheet(base_css)
    wnd.action_marks.menuAction().setIcon(QIcon(pixlib["save_marks"]))
    wnd.action_marks.menuAction().setShortcut('X')
    wnd.action_marks.menuAction().triggered.connect(wnd.on_save_marks)

    toolbar.addAction(wnd.action_marks.menuAction())

    action_create_subclip = QAction("Create subclip", wnd)
    action_create_subclip.setShortcut('C')
    action_create_subclip.triggered.connect(wnd.on_create_subclip)
    wnd.action_marks.addAction(action_create_subclip)

    action_manage_subclips = QAction("Manage subclips", wnd)
    action_manage_subclips.setShortcut('V')
    action_manage_subclips.triggered.connect(wnd.on_manage_subclips)
    wnd.action_marks.addAction(action_manage_subclips)

    toolbar.addWidget(ToolBarStretcher(wnd))
    return toolbar





def navigation_toolbar(wnd):
    action_goto_in = QAction('Go to IN', wnd)
    action_goto_in.setShortcut('Q')
    action_goto_in.triggered.connect(wnd.on_goto_in)
    wnd.addAction(action_goto_in)

    action_goto_out = QAction('Go to OUT', wnd)
    action_goto_out.setShortcut('W')
    action_goto_out.triggered.connect(wnd.on_goto_out)
    wnd.addAction(action_goto_out)

    action_shuttle_left = QAction('Shuttle left', wnd)
    action_shuttle_left.setShortcut('J')
    action_shuttle_left.triggered.connect(wnd.on_shuttle_left)
    wnd.addAction(action_shuttle_left)

    action_shuttle_pause = QAction('Shuttle right', wnd)
    action_shuttle_pause.setShortcut('K')
    action_shuttle_pause.triggered.connect(wnd.on_play)
    wnd.addAction(action_shuttle_pause)

    action_shuttle_right = QAction('Shuttle right', wnd)
    action_shuttle_right.setShortcut('L')
    action_shuttle_right.triggered.connect(wnd.on_shuttle_right)
    wnd.addAction(action_shuttle_right)

    action_frame_prev5 = QAction('Previous 5 frames', wnd)
    action_frame_prev5.setShortcut('1')
    action_frame_prev5.triggered.connect(partial(wnd.on_frame_step, -5))
    wnd.addAction(action_frame_prev5)

    action_frame_next5 = QAction('Next 5 frames', wnd)
    action_frame_next5.setShortcut('2')
    action_frame_next5.triggered.connect(partial(wnd.on_frame_step, 5))
    wnd.addAction(action_frame_next5)


    ################################################################

    toolbar = QToolBar(wnd)
    toolbar.setStyleSheet("background-color:transparent;")

    toolbar.addWidget(ToolBarStretcher(wnd))

    action_clear_in = QAction(QIcon(pixlib["clear_in"]), 'Clear IN', wnd)
    action_clear_in.setShortcut('d')
    action_clear_in.setStatusTip('Clear IN')
    action_clear_in.triggered.connect(wnd.on_clear_in)
    toolbar.addAction(action_clear_in)

    action_mark_in = QAction(QIcon(pixlib["mark_in"]), 'Mark IN', wnd)
    action_mark_in.setShortcut('E')
    action_mark_in.setStatusTip('Mark IN')
    action_mark_in.triggered.connect(wnd.on_mark_in)
    toolbar.addAction(action_mark_in)

    action_frame_prev = QAction(QIcon(pixlib["frame_prev"]), 'Previous frame', wnd)
    action_frame_prev.setShortcut('3')
    action_frame_prev.setStatusTip('Go to previous frame')
    action_frame_prev.triggered.connect(partial(wnd.on_frame_step, -1))
    toolbar.addAction(action_frame_prev)

    wnd.action_play = QAction(QIcon(pixlib["play"]), 'Play/Pause', wnd)
    wnd.action_play.setShortcut('Space')
    wnd.action_play.setStatusTip('Play/Pause')
    wnd.action_play.triggered.connect(wnd.on_play)
    toolbar.addAction(wnd.action_play)

    action_frame_next = QAction(QIcon(pixlib["frame_next"]), 'Next frame', wnd)
    action_frame_next.setShortcut('4')
    action_frame_next.setStatusTip('Go to next frame')
    action_frame_next.triggered.connect(partial(wnd.on_frame_step, 1))
    toolbar.addAction(action_frame_next)

    action_mark_out = QAction(QIcon(pixlib["mark_out"]), 'Mark OUT', wnd)
    action_mark_out.setShortcut('R')
    action_mark_out.setStatusTip('Mark OUT')
    action_mark_out.triggered.connect(wnd.on_mark_out)
    toolbar.addAction(action_mark_out)

    action_clear_out = QAction(QIcon(pixlib["clear_out"]), 'Clear OUT', wnd)
    action_clear_out.setShortcut('f')
    action_clear_out.setStatusTip('Clear OUT')
    action_clear_out.triggered.connect(wnd.on_clear_out)
    toolbar.addAction(action_clear_out)

    toolbar.addWidget(ToolBarStretcher(wnd))
    return toolbar


class VideoWidget(QVideoWidget):
    def __init__(self, parent):
        super(VideoWidget,self).__init__(parent)
        #self.setMinimumWidth(512)
        #self.setMinimumHeight(288)
        self.pix = pixlib["thumb_video"]

    def paintEvent(self, e):
        qp = QPainter()
        qp.begin(self)
        self.drawWidget(qp)
        qp.end()

    def drawWidget(self, qp):
        qp.setPen(Qt.NoPen)
        qp.setBrush(QColor("#000000"))
        qp.drawRect(0, 0, self.width(), self.height())
        x, y = int(self.width()/2), int(self.height()/2)
        x -= int(self.pix.width()/2)
        y -= int(self.pix.height()/2)
        qp.drawPixmap(x, y, self.pix)

    def load_thumb(self, id_asset, content_type):
        self.pix = pixlib[{
            VIDEO: "thumb_video",
            AUDIO: "thumb_audio",
            IMAGE: "thumb_image",
            TEXT : "thumb_text"
            }[int(content_type)]]
        self.update()

class Preview(BaseWidget):
    def __init__(self, parent):
        super(Preview, self).__init__(parent)
        parent.setWindowTitle("Asset preview")

        self.ddur  = NXE_timecode(self)
        self.dpos  = NXE_timecode(self)
        self.din   = NXE_timecode(self)
        self.dout  = NXE_timecode(self)

        self.din.setReadOnly(True) # FIX THIS
        self.dout.setReadOnly(True)

        self.position = self.mark_in = self.mark_out = self.fps = 0

        self.ddur.setReadOnly(True)
        self.dpos.setReadOnly(True)

        self.ddur.setStatusTip("Duration")
        self.dpos.setStatusTip("Position")
        self.din.setStatusTip ("Mark In")
        self.dout.setStatusTip("Mark Out")

        self.media_player = QMediaPlayer(self, QMediaPlayer.VideoSurface or QMediaPlayer.StreamPlayback)
        self.video_widget = VideoWidget(self)
        self.current_id = False

        self.region_bar = RegionBar(self)

        self.timeline = QSlider(Qt.Horizontal)
        self.timeline.setRange(0, 0)
        self.timeline.sliderMoved.connect(self.set_position)

        self.buttons_up = action_toolbar(self)
        self.buttons = navigation_toolbar(self)

        layout = QGridLayout()
        layout.setContentsMargins(0,0,0,0)
        layout.addWidget(self.din  , 0, 0)
        layout.addWidget(self.buttons_up , 0, 1)
        layout.addWidget(self.dout , 0, 2)

        layout.addWidget(self.video_widget ,1, 0, 1, -1)
        layout.addWidget(self.region_bar   ,2, 0, 1, -1)
        layout.addWidget(self.timeline     ,3, 0, 1, -1)

        layout.addWidget(self.dpos,    4,0)
        layout.addWidget(self.buttons, 4,1)
        layout.addWidget(self.ddur,    4,2)

        layout.setRowStretch(1,2)

        layout.setColumnStretch(0,0)
        layout.setColumnStretch(1,1)
        layout.setColumnStretch(2,0)

        self.setLayout(layout)

        self.media_player.setVideoOutput(self.video_widget)
        self.media_player.setNotifyInterval(40)
        self.media_player.stateChanged.connect(self.media_state_changed)
        self.media_player.positionChanged.connect(self.position_changed)
        self.media_player.durationChanged.connect(self.duration_changed)
        self.media_player.error.connect(self.handle_error)


    def save_state(self):
        state = {}
        return state

    def load_state(self, state):
        pass

    def media_state_changed(self, state):
        if self.media_player.state() == QMediaPlayer.PlayingState:
            self.action_play.setIcon(QIcon(pixlib["pause"]))
        else:
            self.action_play.setIcon(QIcon(pixlib["play"]))

    def position_changed(self, position):
        self.timeline.setValue(position)
        self.position = position / 1000.0
        self.update_displays()

    def update_displays(self):
        if self.fps:
            self.dpos.setText(s2tc(self.position, self.fps))
            self.din.setText(s2tc(self.mark_in, self.fps))
            self.dout.setText(s2tc(self.mark_out, self.fps))
        else:
            self.dpos.setText(s2time(self.position))
            self.din.setText(s2time(self.mark_in))
            self.dout.setText(s2time(self.mark_out))
            #TODO REMAINING DISPLAYS

        self.region_bar.mark_in(self.mark_in)
        self.region_bar.mark_out(self.mark_out)
        self.region_bar.position(self.position)


    def duration_changed(self, duration):
        self.timeline.setRange(0, duration)
        if self.fps:
            dstring = s2tc(duration/1000.0, self.fps)
        else:
            dstring = s2tc(duration/1000.0)
        self.ddur.setText(dstring)
        self.region_bar.duration(duration/1000.0)

    def get_position(self):
        return self.media_player.position()

    def set_position(self, position):
        if self.media_player.state() == QMediaPlayer.StoppedState:
            return
        self.media_player.setPosition(position)


    def handle_error(self):
        logging.error(self.media_player.errorString())

    ###############################################
    ## loading


    def load(self, obj):
        self.unload()
        id_asset = obj.id

        id_asset = obj.id if obj.object_type == "asset" else obj["id_asset"]
        if not id_asset:
            return

        try:
            if int(id_asset) < 1 or id_asset == self.current_id:
                return
        except:
            return

        self.current_object = obj
        self.current_id = id_asset

        try:
            self.fps = fract2float(self.current_object["video/fps"])
        except:
            self.fps = 0

        self.mark_in = self.current_object["mark_in"] or 0
        self.mark_out = self.current_object["mark_out"] or 0
        self.duration_changed(self.current_object["duration"]*1000)
        self.update_displays()


        self.video_widget.load_thumb(id_asset, obj["content_type"])
        self.action_play.setIcon(QIcon(pixlib["play"]))



    def unload(self):
        if self.media_player.state() in [QMediaPlayer.PlayingState,QMediaPlayer.PausedState]:
            self.media_player.stop()


    ###############################################
    ## navigation

    def on_frame_step(self, frames):
        if self.media_player.state() == QMediaPlayer.StoppedState:
            return
        fps = self.fps or 25.0 # default
        toffset = (frames / fps) * 1000
        self.media_player.pause()
        self.set_position(self.media_player.position()+toffset)


    def on_play(self):
        if not self.current_id:
            return

        if self.media_player.state() == QMediaPlayer.StoppedState:
            self.status("Loading. Please wait...")
            self.media_player.setMedia(QMediaContent(proxy_path(self.current_id)))
            self.media_player.play()
            self.media_player.setPlaybackRate(1.0)
            self.status("Playing")

        elif self.media_player.state() == QMediaPlayer.PlayingState:
            self.media_player.pause()
            self.status("Paused")
        else:
            self.media_player.play()
            self.media_player.setPlaybackRate(1.0)
            self.status("Playing")


    def on_shuttle_left(self):
        if self.media_player.state() == QMediaPlayer.StoppedState:
            return
        old_rate = self.media_player.playbackRate()
        new_rate = min(-.5, old_rate - 0.5)
        self.media_player.play()
        self.media_player.setPlaybackRate(new_rate)
        self.status("Playing {}x".format(self.media_player.playbackRate()))

    def on_shuttle_right(self):
        if self.media_player.state() == QMediaPlayer.StoppedState:
            return
        old_rate = self.media_player.playbackRate()
        new_rate = max(.5, old_rate + 0.5)
        self.media_player.play()
        self.media_player.setPlaybackRate(new_rate)
        self.status("Playing {}x".format(self.media_player.playbackRate()))

    def on_mark_in(self):
        self.mark_in = self.position
        self.update_displays()

    def on_mark_out(self):
        self.mark_out = self.position
        self.update_displays()

    def on_clear_in(self):
        self.mark_in = 0
        self.update_displays()

    def on_clear_out(self):
        self.mark_out = 0
        self.update_displays()

    def on_goto_in(self):
        self.set_position(self.mark_in*1000)

    def on_goto_out(self):
        self.set_position(self.mark_out*1000)



    def on_save_marks(self):
        if not self.current_object:
            return

        data = {}
        if self.current_object["mark_in"] != self.mark_in:
            data["mark_in"] = self.mark_in

        if self.current_object["mark_out"] != self.mark_out:
            data["mark_out"] = self.mark_out

        if data:
            res, data = query("set_meta", object_type=self.current_object.object_type, objects=[self.current_object.id], data=data)
            if success(res):
                self.status("Marks saved")
            else:
                self.status("Unable to set marks")
        else:
            self.status("Marks unchanged")


    def on_create_subclip(self):
        if not self.current_object or self.current_object.object_type != "asset":
            self.status("Only assets can have subclips")
            return

        text, result = QInputDialog.getText(self,
            "Create subclip",
            "Range {} to {} will be used to create subclip.\n\nEnter subclip name:".format(
                s2tc(self.mark_in, self.fps),
                s2tc(self.mark_out, self.fps)
                ))

        if result:
            subclips = self.current_object["subclips"] or {}
            subclips[text] = [self.mark_in, self.mark_out]
            res, data = query("set_meta", object_type=self.current_object.object_type, objects=[self.current_object.id], data={"subclips": subclips})
            if success(res):
                self.current_object["subclips"] = data["subclips"]


    def on_manage_subclips(self):
        if not self.current_object or self.current_object.object_type != "asset":
            return

        dlg = SubclipsDialog(None, asset=self.current_object)
        dlg.exec_()

        if dlg.selection:
            self.mark_in, self.mark_out = dlg.selection
            self.update_displays()


    def focus(self, objects):
        if len(objects) == 1 and objects[0].object_type in ["asset", "item"]:
            o = objects[0]
            self.load(o)
        else:
            self.unload()
