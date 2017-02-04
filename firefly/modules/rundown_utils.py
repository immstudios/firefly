import datetime

from firefly import *



ITEM_BUTTONS = [
    {
        "icon"      : "placeholder",
        "title"     : "Placeholder",
        "tooltip"   : "Drag this to rundown to create placeholder",
        "item_role" : "placeholder",
    },

    {
        "icon"      : "talking_head",
        "title"     : "Studio",
        "tooltip"   : "Drag this to rundown to create studio placeholder",
        "item_role" : "studio",
    },

    {
        "icon"      : "mark_in",
        "title"     : "Lead-in",
        "tooltip"   : "Drag this to rundown to create Lead-in",
        "item_role" : "lead_in",
    },

    {
        "icon"      : "mark_out",
        "title"     : "Lead-out",
        "tooltip"   : "Drag this to rundown to create Lead-out",
        "item_role" : "lead_out",
    }
]


def get_date():
    class CalendarDialog(QDialog):
        def __init__(self):
            super(CalendarDialog, self).__init__()
            self.setWindowTitle('Calendar')
            self.date = False, False, False
            self.setModal(True)
            self.calendar = QCalendarWidget(self)
            self.calendar.setGridVisible(True)
            self.calendar.setFirstDayOfWeek(1)
            self.calendar.activated[QDate].connect(self.setDate)
            layout = QVBoxLayout()
            layout.addWidget(self.calendar)
            self.setLayout(layout)
            self.show()

        def setDate(self, date):
            self.date = (date.year(), date.month(), date.day())
            self.close()

    cal = CalendarDialog()
    cal.exec_()
    return cal.date


def day_start(ts, start):
    hh, mm = start
    r = ts - (hh*3600 + mm*60)
    dt = datetime.datetime.fromtimestamp(r).replace(
        hour = hh,
        minute = mm,
        second = 0
        )
    return time.mktime(dt.timetuple())


class ItemButton(QToolButton):
    def __init__(self, parent, config):
        super(ItemButton, self).__init__()
        self.button_config = config
        self.pressed.connect(self.startDrag)
        self.setIcon(QIcon(pixlib[self.button_config["icon"]]))
        self.setToolTip(self.button_config["tooltip"])

    def startDrag(self):
        item_data = [{
            "title" : self.button_config["title"],
            "item_role" : self.button_config["item_role"]
            }]
        drag = QDrag(self);
        mimeData = QMimeData()
        mimeData.setData(
           "application/nx.item",
           json.dumps(item_data)
           )
        drag.setMimeData(mimeData)
        if drag.exec_(Qt.CopyAction):
            pass # nejak to rozumne ukonc


def rundown_toolbar(wnd):
    action_find = QAction('Search rundown', wnd)
    action_find.setShortcut('Ctrl+F')
    action_find.triggered.connect(wnd.on_find)
    wnd.addAction(action_find)

    action_find_next = QAction('Search rundown', wnd)
    action_find_next.setShortcut('F3')
    action_find_next.triggered.connect(wnd.on_find_next)
    wnd.addAction(action_find_next)

    toolbar = QToolBar(wnd)

    action_day_prev = QAction(QIcon(pixlib["back"]), '&Previous day', wnd)
    action_day_prev.setShortcut('Alt+Left')
    action_day_prev.setStatusTip('Go to previous day')
    action_day_prev.triggered.connect(wnd.on_day_prev)
    toolbar.addAction(action_day_prev)

    action_now = QAction(QIcon(pixlib["now"]), '&Now', wnd)
    action_now.setStatusTip('Go to now')
    action_now.triggered.connect(wnd.on_now)
    toolbar.addAction(action_now)

    action_calendar = QAction(QIcon(pixlib["calendar"]), '&Calendar', wnd)
    action_calendar.setShortcut('Ctrl+D')
    action_calendar.setStatusTip('Open calendar')
    action_calendar.triggered.connect(wnd.on_calendar)
    toolbar.addAction(action_calendar)

    action_refresh = QAction(QIcon(pixlib["refresh"]), '&Refresh', wnd)
    action_refresh.setStatusTip('Refresh rundown')
    action_refresh.triggered.connect(wnd.refresh)
    toolbar.addAction(action_refresh)

    action_day_next = QAction(QIcon(pixlib["next"]), '&Next day', wnd)
    action_day_next.setShortcut('Alt+Right')
    action_day_next.setStatusTip('Go to next day')
    action_day_next.triggered.connect(wnd.on_day_next)
    toolbar.addAction(action_day_next)

    toolbar.addSeparator()

    action_toggle_mcr = QAction(QIcon(pixlib["onair"]), '&Playout controls', wnd)
    action_toggle_mcr.setStatusTip('Toggle playout controls')
    action_toggle_mcr.triggered.connect(wnd.on_toggle_mcr)
    toolbar.addAction(action_toggle_mcr)

    action_toggle_cg = QAction(QIcon(pixlib["cg"]), '&CG controls', wnd)
    action_toggle_cg.setShortcut('F4')
    action_toggle_cg.setStatusTip('Toggle CG controls')
    action_toggle_cg.triggered.connect(wnd.on_toggle_cg)
    toolbar.addAction(action_toggle_cg)


    action_toggle_tools = QAction(QIcon(pixlib["tools"]), '&Rundown tools', wnd)
    action_toggle_tools.setStatusTip('Toggle rundown tools')
    action_toggle_tools.triggered.connect(wnd.on_toggle_tools)
    toolbar.addAction(action_toggle_tools)

    toolbar.addWidget(ToolBarStretcher(wnd))

    wnd.channel_display = ChannelDisplay()
    toolbar.addWidget(wnd.channel_display)

    return toolbar



def items_toolbar(wnd):
    toolbar = QToolBar(wnd)
    for btn_config in ITEM_BUTTONS:
        toolbar.addWidget(ItemButton(wnd, btn_config))
    return toolbar
