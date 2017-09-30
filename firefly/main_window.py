import pprint

from .common import *
from .modules import *
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

        self.main_window.add_subscriber(self.browser, ["objects_changed"])
        self.main_window.add_subscriber(self.rundown, ["objects_changed", "rundown_changed", "playout_status"])

        layout = QVBoxLayout()
        layout.addWidget(self.main_splitter)
        self.setLayout(layout)

    @property
    def app(self):
        return self.main_window.app




class FireflyMainWindow(MainWindow):
    def __init__(self, parent, MainWidgetClass):
        self.id_channel = min(config["playout_channels"].keys())

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
        logging.info("Firefly is ready")


    def load_default_state(self):
        self.showMaximized()
        one_third = self.width() / 3
        print (one_third)
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
        self.detail.focus([obj])

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
        for module, methods in self.subscribers:
            if message.method in methods:
                module.seismic_handler(message)
