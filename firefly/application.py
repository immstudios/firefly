import sys

from .common import *

from .dialogs.site_select import SiteSelectDialog
from .dialogs.login import LoginDialog

from .main_window import FireflyMainWindow, FireflyMainWidget


def check_login():
    user_meta = api.get_user()
    if user_meta:
        return user_meta
    dlg = LoginDialog()
    dlg.exec_()
    return dlg.result


class FireflyApplication(Application):
    def __init__(self, **kwargs):
        super(FireflyApplication, self).__init__(name="firefly", title="Firefly")
        self.splash = QSplashScreen(pix_lib['splash'])
        self.splash.show()

        # Which site we are running

        i = 0
        if "sites" in config:
            if len(config["sites"]) > 1:
                dlg = SiteSelect(None, config["sites"])
                i = dlg.exec_()
            else:
                i = 0
        config.update(config["sites"][i])

        # Login

        api._settings["hub"] = config["hub"]
        try:
            api.set_auth(open("auth.key").read())
        except FileNotFoundError:
            pass
        except Exception:
            log_traceback()

        user_meta = check_login()
        if not user_meta:
            logging.error("Unable to log in")
            sys.exit(0)
        user.meta = user_meta

        # Load settings and show main window
        self.splash_message("Loading site settings...")
        self.load_settings()
        self.splash_message("Loading asset cache...")
        asset_cache.load()
        self.splash_message("Loading user workspace...")
        self.main_window = FireflyMainWindow(self, FireflyMainWidget)


    def start(self):
        self.splash.hide()
        self.exec_()
        self.on_exit()

    def on_exit(self):
        asset_cache.save()
        if not self.main_window.listener:
            return
        self.main_window.listener.halt()
        i = 0
        while not self.main_window.listener.halted:
            time.sleep(.1)
            if i > 30:
                logging.warning("Unable to shutdown listener. Forcing quit", handlers=False)
                sys.exit(1)
            i+=1
        with open("auth.key", "w") as f:
            f.write(api.auth_key)
        sys.exit(0)


    def splash_message(self, msg):
        self.splash.showMessage(
                msg,
                alignment=Qt.AlignBottom|Qt.AlignLeft,
                color=Qt.white
            )

    def load_settings(self):
        self.splash_message("Loading site settings")
        result = api.settings()
        if result.is_error:
            QMessageBox.critical(self.splash, "Error", result.message)
            critical_error("Unable to load site settings")

        config.update(result.data)

        # Fix indices
        for config_group in [
                    "storages",
                    "playout_channels",
                    "ingest_channels",
                    "folders",
                    "views"
                ]:
            ng = {}
            for id in config[config_group]:
                ng[int(id)] = config[config_group][id]
            config[config_group] = ng
