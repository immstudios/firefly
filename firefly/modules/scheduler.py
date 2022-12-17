import os
import datetime

from nxtools import log_traceback, xml, logging

from firefly.api import api
from firefly.core.enum import ObjectStatus, ContentType, MediaType, JobState
from firefly.common import pixlib
from firefly.objects import Event, Item
from firefly.base_module import BaseModule
from firefly.widgets import ToolBarStretcher, ChannelDisplay
from firefly.qt import (
    Qt,
    QToolButton,
    QIcon,
    QDrag,
    QMimeData,
    QToolBar,
    QAction,
    QVBoxLayout,
    QFileDialog,
    QApplication,
)

from .scheduler_model import SchedulerCalendar
from .scheduler_utils import dump_template

assert ObjectStatus and ContentType and MediaType and JobState


# Backwards compatibility
OFFLINE = 0
ONLINE = 1
CREATING = 2  # File exists, but was changed recently.
TRASHED = 3  # File has been moved to trash location.
ARCHIVED = 4  # File has been moved to archive location.
RESET = 5  # Reset metadata action has been invoked.
CORRUPTED = 6
REMOTE = 7
UNKNOWN = 8
AIRED = 9  # Auxiliary value.
ONAIR = 10
RETRIEVING = 11
AUDIO = 1
VIDEO = 2
IMAGE = 3
TEXT = 4
DATABROADCASTING = 5
INTERSTITIAL = 6
EDUCATION = 7
APPLICATION = 8
GAME = 9
PACKAGE = 10
PENDING = 0
IN_PROGRESS = 1
COMPLETED = 2
FAILED = 3
ABORTED = 4
RESTART = 5
SKIPPED = 6
VIRTUAL = 0
FILE = 1
URI = 2


EMPTY_EVENT_DATA = '[{"id" : 0, "title" : "Empty event"}]'.encode("ascii")


class EmptyEventButton(QToolButton):
    def __init__(self, parent):
        super(EmptyEventButton, self).__init__()
        self.pressed.connect(self.startDrag)
        self.setIcon(QIcon(pixlib["empty-event"]))
        self.setToolTip("Drag this to scheduler to create empty event.")

    def startDrag(self):
        drag = QDrag(self)
        mimeData = QMimeData()
        mimeData.setData("application/nx.event", EMPTY_EVENT_DATA)
        drag.setMimeData(mimeData)
        if drag.exec(Qt.DropAction.CopyAction):
            pass  # nejak to rozumne ukoncit


def scheduler_toolbar(wnd):
    toolbar = QToolBar(wnd)

    action_week_prev = QAction(QIcon(pixlib["previous"]), "&Previous week", wnd)
    action_week_prev.setShortcut("Alt+Left")
    action_week_prev.setStatusTip("Go to previous week")
    action_week_prev.triggered.connect(wnd.on_week_prev)
    toolbar.addAction(action_week_prev)

    action_refresh = QAction(QIcon(pixlib["refresh"]), "&Refresh", wnd)
    action_refresh.setStatusTip("Refresh scheduler")
    action_refresh.triggered.connect(wnd.load)
    toolbar.addAction(action_refresh)

    action_week_next = QAction(QIcon(pixlib["next"]), "&Next week", wnd)
    action_week_next.setShortcut("Alt+Right")
    action_week_next.setStatusTip("Go to next week")
    action_week_next.triggered.connect(wnd.on_week_next)
    toolbar.addAction(action_week_next)

    # TODO
    #    toolbar.addSeparator()
    #
    #    wnd.action_show_runs = QAction(QIcon(pixlib["show-runs"]), '&Show runs', wnd)
    #    wnd.action_show_runs.setStatusTip('Show runs')
    #    wnd.action_show_runs.setCheckable(True)
    #    toolbar.addAction(wnd.action_show_runs)

    toolbar.addSeparator()
    toolbar.addWidget(EmptyEventButton(wnd))
    toolbar.addWidget(ToolBarStretcher(wnd))
    wnd.channel_display = ChannelDisplay()
    toolbar.addWidget(wnd.channel_display)

    return toolbar


class SchedulerModule(BaseModule):
    def __init__(self, parent):
        super(SchedulerModule, self).__init__(parent)
        toolbar = scheduler_toolbar(self)
        self.calendar = SchedulerCalendar(self)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        layout.addWidget(toolbar, 0)
        layout.addWidget(self.calendar, 1)

        self.setLayout(layout)

    def export_template(self):
        data = dump_template(self.calendar)
        try:
            if not os.path.exists("templates"):
                os.makedirs("templates")
        except Exception:
            log_traceback()
        save_file_path = QFileDialog.getSaveFileName(
            self,
            "Save scheduler template",
            os.path.abspath("templates"),
            "Templates (*.xml)",
        )[0]
        if os.path.splitext(save_file_path)[1].lower() != ".xml":
            save_file_path += ".xml"
        try:
            with open(save_file_path, "wb") as save_file:
                save_file.write(data.encode("utf-8"))
        except Exception:
            log_traceback()

    def import_template(self, day_offset=0):
        try:
            if not os.path.exists("templates"):
                os.makedirs("templates")
        except Exception:
            log_traceback()
        file_path = QFileDialog.getOpenFileName(
            self, "Open template", os.path.abspath("templates"), "Templates (*.xml)"
        )[0]

        if not file_path:
            return

        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            feed = open(file_path, "rb").read().decode("utf-8")
            data = xml(feed)
        except Exception:
            QApplication.restoreOverrideCursor()
            log_traceback()
            return
        ch, cm = self.calendar.day_start
        events = []
        try:
            for day_index, day in enumerate(data.findall("day")):
                day_start = self.calendar.week_start_time + (3600 * 24 * day_index)
                for event_data in day.findall("event"):
                    hh, mm = [int(x) for x in event_data.attrib["time"].split(":")]

                    clock_offset = (hh * 3600) + (mm * 60) - (ch * 3600) - (cm * 60)
                    if (hh * 3600) + (mm * 60) < (ch * 3600) - (cm * 60):
                        clock_offset += 24 * 3600

                    start_time = day_start + clock_offset + (day_offset * 3600 * 24)

                    event = Event(meta={"start": start_time})
                    for m in event_data.findall("meta"):
                        key = m.attrib["key"]
                        value = m.text
                        if value:
                            event[key] = value

                    items_data = event_data.find("items")
                    if items_data is not None:
                        event.meta["_items"] = []
                        for ipos, item_data in enumerate(items_data.findall("item")):
                            item = Item()
                            item["position"] = ipos + 1
                            for kv in item_data.findall("meta"):
                                item[kv.attrib["key"]] = kv.text
                            event.meta["_items"].append(item.meta)

                    events.append(event.meta)
                if day_offset:  # Importing single day.
                    break
        except Exception:
            QApplication.restoreOverrideCursor()
            log_traceback("Unable to parse template:")
            return
        if not events:
            QApplication.restoreOverrideCursor()
            return
        response = api.schedule(id_channel=self.id_channel, events=events)
        QApplication.restoreOverrideCursor()
        if not response:
            logging.error(response.message)
        else:
            logging.info(response.message)
        self.load()

    def load(self, *args, **kwargs):
        self.calendar.load(*args, **kwargs)
        date = datetime.date.fromtimestamp(self.calendar.week_start_time)
        week_no = date.isocalendar()[1]
        header = f"Week {week_no} - {self.playout_config.name}"
        self.channel_display.setText(header)

    def on_week_prev(self):
        self.load(self.calendar.week_start_time - (3600 * 24 * 7))

    def on_week_next(self):
        self.load(self.calendar.week_start_time + (3600 * 24 * 7))

    def focus(self, objects):
        return
        # TODO
        if self.action_show_runs.isChecked():
            ...
            # asset_ids = [obj.id for obj in objects if obj.object_type == "asset"]
            # if not asset_ids:
            #    return
            # res, data = query(
            #     "get_runs", id_channel=self.id_channel, asset_ids=asset_ids
            # )
            # if success(res):
            #    self.calendar.focus_data = data["data"]
            #     self.calendar.update()

    def open_rundown(self, ts, event=False):
        self.main_window.main_widget.rundown.load(start_time=ts, event=event)
        self.main_window.main_widget.switch_tab(
            self.main_window.main_widget.rundown, perform_on_switch_tab=False
        )

    def set_channel(self, id_channel):
        # TODO: is this used? may be removed?
        pass

    def on_channel_changed(self):
        logging.debug(f"[SCHEDULER] setting channel to {self.id_channel}")
        self.load()

    def refresh_events(self, events):
        for id_event in events:
            if id_event in self.calendar.event_ids:
                logging.debug(
                    f"[SCHEDULER] Event id {id_event} has been changed."
                    "Reloading calendar"
                )
                self.load()
                break

    def seismic_handler(self, data):
        if data.method == "objects_changed" and data.data["object_type"] == "event":
            self.refresh_events(data.data["objects"])
