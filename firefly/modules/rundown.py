import time
import datetime
import functools

from firefly import *
from firefly.dialogs.event import EventDialog
from firefly.dialogs.send_to import SendToDialog

from .rundown_utils import *
from .rundown_mcr import MCR
from .rundown_cg import CG
from .rundown_view import RundownView


class RundownModule(BaseModule):
    def __init__(self, parent):
        super(RundownModule, self).__init__(parent)
        self.start_time = day_start(time.time(), self.playout_config["day_start"])

        self.current_item = False
        self.cued_item = False
        self.last_search = ""

        self.view = RundownView(self)
        self.mcr = MCR(self)
        self.cg = CG(self)

        self.toolbar = rundown_toolbar(self)
        self.items_toolbar = items_toolbar(self)

        layout = QVBoxLayout()
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(2)
        layout.addWidget(self.toolbar, 0)
        layout.addWidget(self.items_toolbar, 0)
        layout.addWidget(self.mcr)
        layout.addWidget(self.cg)
        layout.addWidget(self.view, 1)

        self.setLayout(layout)

        self.update_header()
        self.load()

    @property
    def can_edit(self):
        return user.has_right("rundown_edit", self.id_channel)

    @property
    def can_schedule(self):
        return user.has_right("scheduler_edit", self.id_channel)

    def load(self, **kwargs):
        do_update_header = False
        if "start_time" in kwargs and kwargs["start_time"] != self.start_time:
            do_update_header = True
            self.start_time = kwargs["start_time"]
        if "id_channel" in kwargs and kwargs["id_channel"] != self.id_channel:
            do_update_header = True
            self.id_channel = kwargs["id_channel"]
        self.view.load()
        if do_update_header:
            self.update_header()
        if not "event" in kwargs:
            return

        event = kwargs["event"]
        for i, r in enumerate(self.view.model().object_data):
            if event.id == r.id and r.object_typei == "event":
                self.view.scrollTo(
                        self.view.model().index(i, 0, QModelIndex()),
                        QAbstractItemView.PositionAtTop
                    )
                break


    def refresh(self, reset=False):
        selection = []
        #for idx in self.view.selectionModel().selectedIndexes():
        #    if self.model.object_data[idx.row()].id:
        #        selection.append([self.model.object_data[idx.row()].object_type, self.model.object_data[idx.row()].id])

        self.load()

        #item_selection = QItemSelection()
        #for i, row in enumerate(self.model.object_data):
        #    if [row.object_type, row.id] in selection:
        #       i1 = self.model.index(i, 0, QModelIndex())
        #       i2 = self.model.index(i, len(self.model.header_data)-1, QModelIndex())
        #       item_selection.select(i1,i2)
        #self.view.focus_enabled = False
        #self.view.selectionModel().select(item_selection, QItemSelectionModel.ClearAndSelect)
        #self.view.focus_enabled = True

    def update_header(self):
        ch = self.playout_config["title"]
        t = datetime.date.fromtimestamp(self.start_time)
        if t < datetime.date.today():
            s = " color='red'"
        elif t > datetime.date.today():
            s = " color='green'"
        else:
            s = ""
        t = t.strftime("%A %Y-%m-%d")
        self.parent().setWindowTitle("Rundown {}".format(t))
        self.channel_display.setText("<font{}>{}</font> - {}".format(s, t, ch))


    #
    # Actions
    #

    def set_channel(self, id_channel):
        if self.id_channel != id_channel:
            self.id_channel = id_channel
            self.refresh()
            if self.cg:
                self.cg.load_plugins(id_channel)

            if self.mcr:
                can_mcr = has_right("mcr", self.id_channel)
                self.mcr.btn_take.setEnabled(can_mcr)
                self.mcr.btn_freeze.setEnabled(can_mcr)
                self.mcr.btn_retake.setEnabled(can_mcr)
                self.mcr.btn_abort.setEnabled(can_mcr)


    def on_day_prev(self):
        self.load(start_time=self.start_time - (3600*24))

    def on_day_next(self):
        self.load(start_time=self.start_time + (3600*24))

    def on_now(self):
        if not (self.start_time + 86400 > time.time() > self.start_time):
            self.load(start_time=day_start(
                        time.time(),
                        self.playout_config["day_start"]
                    )
                )

        for i,r in enumerate(self.view.model().object_data):
            if self.current_item == r.id and r.object_type=="item":
                self.view.scrollTo(self.view.model().index(i, 0, QModelIndex()), QAbstractItemView.PositionAtTop  )
                break

    def on_calendar(self):
        y, m, d = get_date()
        if not y:
            return
        hh, mm = self.playout_config["day_start"]
        dt = datetime.datetime(y,m,d,hh,mm)
        self.load(start_time=time.mktime(dt.timetuple()))

    def on_toggle_mcr(self):
        if self.mcr:
            if self.mcr.isVisible():
                self.mcr.hide()
            else:
                self.mcr.show()

    def on_toggle_cg(self):
        if self.cg and has_right("cg", self.id_channel):
            if self.cg.isVisible():
                self.cg.hide()
            else:
                self.cg.show()

    def on_toggle_tools(self):
        if self.items_toolbar.isVisible():
            self.items_toolbar.hide()
        else:
            self.items_toolbar.show()

    #
    # Search rundown
    #

    def on_find(self):
        text, result = QInputDialog.getText(
                self,
                "Rundown search",
                "Enter your blabla:",
                text=self.last_search
            )
        if result and text:
            self.do_find(text)
        else:
            self.last_search = ""

    def on_find_next(self):
        if self.last_search:
            self.do_find(self.last_search)
        else:
            self.on_find()

    def do_find(self, search_string, start_row=-1):
        self.last_search = search_string
        search_string = search_string.lower()
        if start_row == -1:
            for idx in self.view.selectionModel().selectedIndexes():
                if idx.row() > start_row:
                    start_row = idx.row()
        start_row += 1
        for i, row in enumerate(self.model.object_data[start_row:]):
            for key in ["title", "identifier/main"]:
                if str(row[key]).lower().find(search_string) > -1:
                    selection = QItemSelection()
                    i1 = self.view.model().index(i + start_row, 0, QModelIndex())
                    i2 = self.view.model().index(i + start_row, len(self.view.model().header_data)-1, QModelIndex())
                    self.view.scrollTo(i1 , QAbstractItemView.PositionAtTop  )
                    selection.select(i1, i2)
                    self.view.selectionModel().select(selection, QItemSelectionModel.ClearAndSelect)
                    break
            else:
                continue
            break
        else:
            logging.warnings("Not found: {}".format(self.last_search))
            self.view.clearSelection()

    #
    # Messaging
    #

    def seismic_handler(self, message):
        if message.method == "playout_status":
            if message.data["id_channel"] != self.id_channel:
                return

            if message.data["current_item"] != self.current_item:
                self.current_item = message.data["current_item"]
                self.view.model().refresh_items([self.current_item])

            if message.data["cued_item"] != self.cued_item:
                self.cued_item = message.data["cued_item"]
                self.refresh(reset=True)

            if self.mcr:
                self.mcr.seismic_handler(message)

        elif message.method == "objects_changed" and message.data["object_type"] == "event":
            my_name = self.parent().objectName()

            for id_event in message.data["objects"]:#
                if message.data.get("sender", False) != my_name and id_event in self.view.model().event_ids :
                    self.refresh()
                    break
