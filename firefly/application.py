import sys
import locale

from .common import *

from .dialogs.site_select import SiteSelectDialog
from .dialogs.login import LoginDialog

from .main_window import FireflyMainWindow, FireflyMainWidget


def check_login(wnd):
    data = api.get_user()
    user_meta = data.get("data", False)
    if user_meta:
        return user_meta
    if data["response"] > 403:
        QMessageBox.critical(
                wnd,
                "Error {}".format(data["response"]),
                data["message"]
            )
        return False
    dlg = LoginDialog()
    dlg.exec_()
    return dlg.result


class FireflyApplication(Application):
    def __init__(self, **kwargs):
        super(FireflyApplication, self).__init__(name="firefly", title="Firefly")
        locale.setlocale(locale.LC_NUMERIC, 'C')
        self.splash = QSplashScreen(pix_lib['splash'])
        self.splash.show()

        # Which site we are running

        i = 0
        if "sites" in config:
            if len(config["sites"]) > 1:
                dlg = SiteSelectDialog(None, config["sites"])
                i = dlg.exec_()
            else:
                i = 0
        config.update(config["sites"][i])

        self.app_state_path = os.path.join(app_dir, "{}-{}.appstate".format(app_settings["name"], config["site_name"]))

        # Login

        api._settings["hub"] = config["hub"]
        try:
            api.set_auth(open("auth.key").read())
        except FileNotFoundError:
            pass
        except Exception:
            log_traceback()

        user_meta = check_login(self.splash)
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
        with open("auth.key", "w") as f:
            f.write(api.auth_key)
        self.main_window.listener.halt()
        i = 0
        while not self.main_window.listener.halted:
            time.sleep(.1)
            if i > 10:
                logging.warning("Unable to shutdown listener. Forcing quit", handlers=False)
                sys.exit(0)
            i+=1
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
                    "views",
                    "actions",
                ]:
            ng = {}
            for id in config[config_group]:
                ng[int(id)] = config[config_group][id]
            config[config_group] = ng
#        config["playout_channels"] = {} #testing CMS MODE
