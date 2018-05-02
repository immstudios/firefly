import pprint

from .common import *
from .modules import *
from .menu import create_menu
from .listener import SeismicListener

__all__ = ["FireflyMainWidget", "FireflyMainWindow"]

class FireflyMainWidget(QWidget):
    def __init__(self, main_window):
        super(FireflyMainWidget, self).__init__(main_window)
        self.main_window = main_window

        self.browser = BrowserModule(self)
        self.detail = DetailModule(self)
        self.scheduler = SchedulerModule(self)
        self.rundown = RundownModule(self)

        self.tabs = QTabWidget(self)
        self.tabs.addTab(self.detail, "Detail")
        self.tabs.addTab(self.scheduler, "Scheduler")
        self.tabs.addTab(self.rundown, "Rundown")

        self.main_splitter = QSplitter(Qt.Horizontal)
        self.main_splitter.addWidget(self.browser)
        self.main_splitter.addWidget(self.tabs)

        self.main_window.add_subscriber(self.detail, ["objects_changed"])
        self.main_window.add_subscriber(self.browser, ["objects_changed"])
        self.main_window.add_subscriber(self.rundown, ["objects_changed", "rundown_changed", "playout_status"])

        create_menu(self.main_window)

        layout = QVBoxLayout()
        layout.addWidget(self.main_splitter)
        self.setLayout(layout)

    @property
    def app(self):
        return self.main_window.app




class FireflyMainWindow(MainWindow):
    def __init__(self, parent, MainWidgetClass):
        self.subscribers = []

        super(FireflyMainWindow, self).__init__(parent, MainWidgetClass)


        logging.handlers = [self.log_handler]
        self.listener = SeismicListener(
                config["site_name"],
                config["seismic_addr"],
                int(config["seismic_port"])
            )

        self.seismic_timer = QTimer(self)
        self.seismic_timer.timeout.connect(self.on_seismic_timer)
        self.seismic_timer.start(40)
        self.load_default_state()

        self.id_channel = min(config["playout_channels"].keys())
        self.set_channel(self.id_channel)
        logging.info("[MAIN WINDOW] Firefly is ready")


    def load_default_state(self):
        self.showMaximized()
        one_third = self.width() / 3
        self.main_widget.main_splitter.setSizes([one_third, one_third*2])

    @property
    def browser(self):
        return self.main_widget.browser

    @property
    def scheduler(self):
        return self.main_widget.scheduler

    @property
    def rundown(self):
        return self.main_widget.rundown

    @property
    def detail(self):
        return self.main_widget.detail

    def focus(self, obj):
        if type(obj) == list:
            obj = obj[0]
        if obj.object_type == "item":
            obj = obj.asset
        self.detail.focus(obj)

    #
    # Menu actions
    #

    def new_asset(self):
        pass

    def clone_asset(self):
        pass

    def logout(self):
        pass

    def exit(self):
        self.close()

    def search_assets(self):
        self.browser.search_box.setFocus()
        self.browser.search_box.selectAll()

    def now(self):
        self.show_rundown()
        self.rundown.go_now()

    def set_channel(self, id_channel):
        for action in self.menu_channel.actions():
            if action.id_channel == id_channel:
                action.setChecked(True)
        self.scheduler.set_channel(id_channel)
        self.rundown.set_channel(id_channel)
        self.id_channel = id_channel

    def show_detail(self):
        if self.main_widget.tabs.currentIndex() == 0:
            self.detail.switch_tabs()
        else:
            self.main_widget.tabs.setCurrentIndex(0)

    def show_scheduler(self):
        self.main_widget.tabs.setCurrentIndex(1)

    def show_rundown(self):
        self.main_widget.tabs.setCurrentIndex(2)

    def refresh(self):
        self.rundown.load()
        self.scheduler.load()
        self.browser.load()

    #
    # Messaging
    #

    def on_seismic_timer(self):
        try:
            message = self.listener.queue.pop(0)
        except IndexError:
            pass
        else:
            self.seismic_handler(message)

    def add_subscriber(self, module, methods):
        self.subscribers.append([module, methods])

    def seismic_handler(self, message):
        if message.method == "objects_changed" and message.data["object_type"] == "asset":
            logging.info("Requesting new data for objects {}".format(message.data["objects"]))
            now = time.time()
            asset_cache.request([[aid, now] for aid in message.data["objects"]])

        for module, methods in self.subscribers:
            if message.method in methods:
                module.seismic_handler(message)
