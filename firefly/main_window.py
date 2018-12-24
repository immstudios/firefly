from .common import *
from .modules import *
from .menu import create_menu
from .listener import SeismicListener

__all__ = ["FireflyMainWidget", "FireflyMainWindow"]

class FireflyMainWidget(QWidget):
    def __init__(self, main_window):
        super(FireflyMainWidget, self).__init__(main_window)
        self.main_window = main_window
        current_tab = self.main_window.app_state.get("current_module",0)
        self.tabs = QTabWidget(self)

        self.browser = self.detail = self.rundown = self.scheduler = self.jobs = False

        # MAM modules

        self.browser = BrowserModule(self)
        self.detail = DetailModule(self)
        self.tabs.addTab(self.detail, "DETAIL")

        self.main_window.add_subscriber(self.browser, ["objects_changed"])
        self.main_window.add_subscriber(self.detail, ["objects_changed"])

        # Jobs modul

        if config["actions"]:
            self.jobs = JobsModule(self)
            self.tabs.addTab(self.jobs, "JOBS")
            self.main_window.add_subscriber(self.jobs, ["job_progress"])

        # Channel control modules

        if config["playout_channels"]:
            if user.has_right("scheduler_view", anyval=True) or user.has_right("scheduler_edit", anyval=True):
                self.scheduler = SchedulerModule(self)
                self.main_window.add_subscriber(self.scheduler, ["objects_changed"])
                self.tabs.addTab(self.scheduler, "SCHEDULER")

            if user.has_right("rundown_view", anyval=True) or user.has_right("rundown_edit", anyval=True):
                self.rundown = RundownModule(self)
                self.main_window.add_subscriber(self.rundown, ["objects_changed", "rundown_changed", "playout_status", "job_progress"])
                self.tabs.addTab(self.rundown, "RUNDOWN")

        # Layout

        self.main_splitter = QSplitter(Qt.Horizontal)
        self.main_splitter.addWidget(self.browser)
        self.main_splitter.addWidget(self.tabs)

        create_menu(self.main_window)

        layout = QVBoxLayout()
        layout.addWidget(self.main_splitter)
        self.setLayout(layout)

        if current_tab:
            self.switch_tab(current_tab)
        else:
            self.on_switch_tab()

        self.tabs.currentChanged.connect(self.on_switch_tab)

    @property
    def app(self):
        return self.main_window.app

    @property
    def current_module(self):
        return self.tabs.currentWidget()

    def switch_tab(self, module):
        for i in range(self.tabs.count()):
            if (type(module) == int and module == i) or self.tabs.widget(i) == module:
                self.tabs.setCurrentIndex(i)

    def on_switch_tab(self, index=None):
        if self.current_module == self.detail:
            self.detail.detail_tabs.on_switch()
        else:
            # Disable proxy loading if player is not focused
            self.detail.detail_tabs.on_switch(-1)

        if self.current_module == self.rundown:
            if self.rundown.mcr and self.rundown.mcr.isVisible():
                self.rundown.mcr.request_display_resize = True
            # Refresh rundown on focus
            self.rundown.load()

        if self.current_module == self.jobs:
            self.jobs.load()

        self.main_window.app_state["current_module"] = self.tabs.currentIndex()


class FireflyMainWindow(MainWindow):
    def __init__(self, parent, MainWidgetClass):
        self.subscribers = []
        super(FireflyMainWindow, self).__init__(parent, MainWidgetClass)
        self.setWindowIcon(QIcon(get_pix("icon")))

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


        for id_channel in config["playout_channels"]:
            if user.has_right("rundown_view", id_channel) \
              or user.has_right("rundown_edit", id_channel) \
              or user.has_right("scheduler_view", id_channel) \
              or user.has_right("scheduler_edit", id_channel):
                self.id_channel = min(config["playout_channels"].keys())
                self.set_channel(self.id_channel)
                break
        logging.info("[MAIN WINDOW] Firefly is ready")


    def load_default_state(self):
        self.showMaximized()
        one_third = self.width() / 3
        self.main_widget.main_splitter.setSizes([one_third, one_third*2])

    @property
    def current_module(self):
        return self.main_widget.current_module

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

    @property
    def jobs(self):
        return self.main_widget.jobs

    def focus(self, obj):
        if type(obj) == list:
            obj = obj[0]
        if obj.object_type == "item":
            obj = obj.asset
        self.detail.focus(obj)
        if self.scheduler:
            self.scheduler.focus(obj)

    #
    # Menu actions
    #

    def new_asset(self):
        self.detail.new_asset()

    def clone_asset(self):
        self.detail.clone_asset()

    def logout(self):
        api.logout()
        self.close()

    def exit(self):
        self.close()

    def search_assets(self):
        self.browser.search_box.setFocus()
        self.browser.search_box.selectAll()

    def now(self):
        if config["playout_channels"] and (user.has_right("rundown_view", self.id_channel) or user.has_right("rundown_edit", self.id_channel)):
            self.show_rundown()
            self.rundown.go_now()

    def refresh_plugins(self):
        self.rundown.plugins.load()

    def set_channel(self, id_channel):
        if config["playout_channels"]:
            for action in self.menu_scheduler.actions():
                if hasattr(action, "id_channel") and action.id_channel == id_channel:
                    action.setChecked(True)
            if self.scheduler:
                self.scheduler.set_channel(id_channel)
            if self.rundown:
                self.rundown.set_channel(id_channel)
            self.id_channel = id_channel

    def show_detail(self):
        if self.main_widget.tabs.currentIndex() == 0:
            self.detail.switch_tabs()
        else:
            self.main_widget.tabs.setCurrentIndex(0)

    def show_scheduler(self):
        if config["playout_channels"] and (user.has_right("scheduler_view", self.id_channel) or user.has_right("scheduler_edit", self.id_channel)):
            self.main_widget.switch_tab(self.scheduler)

    def show_rundown(self):
        if config["playout_channels"] and (user.has_right("rundown_view", self.id_channel) or user.has_right("rundown_edit", self.id_channel)):
            self.main_widget.switch_tab(self.rundown)

    def refresh(self):
        self.browser.load()
        if config["playout_channels"]:
            if self.rundown:
                self.rundown.load()
            if self.scheduler:
                self.scheduler.load()

    def export_template(self):
        self.scheduler.export_template()

    def import_template(self):
        self.scheduler.import_template()

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
