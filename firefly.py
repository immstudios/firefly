#!/usr/bin/env python3

import os
import sys

from firefly import *

class Firefly(QMainWindow):
    def __init__(self, parent):
        super(Firefly, self).__init__()
        self.setWindowTitle("{}@{} - {}".format(user["login"], config["site_name"], VERSION_INFO))
        self.setWindowIcon(QIcon(":/images/firefly.ico"))
        self.parent = parent

        self.docks = []

        create_menu(self)
        self.setTabPosition(Qt.AllDockWidgetAreas, QTabWidget.North)
        self.setDockNestingEnabled(True)
        self.setStyleSheet(base_css)

        settings = ffsettings()

        self.on_change_channel(1) # todo: Load default from settings
        self.workspace_locked = settings.value("main_window/locked", False)

        for dock_key in settings.allKeys():
            if not dock_key.startswith("docks/"):
                continue
            dock_data = settings.value(dock_key)
            parent.splash_message("Loading {} {}".format(dock_data["class"], dock_data["object_name"]))
            self.create_dock(dock_data["class"], state=dock_data, show=False)

        if settings.contains("main_window/pos"):
            self.move(settings.value("main_window/pos"))

        if settings.contains("main_window/size"):
            self.resize(settings.value("main_window/size"))
            self.size_helper = self.size()

        if settings.contains("main_window/state"):
            self.restoreState(settings.value("main_window/state"))

        if self.workspace_locked:
            self.lock_workspace()
        else:
            self.unlock_workspace()

        if not settings.contains("main_window/pos") or (settings.contains("main_window/maximized") and int(settings.value("main_window/maximized"))):
            self.showMaximized()
        else:
            self.show()

        for dock in self.docks:
            dock.show()

        self.subscribers = {}
        self.seismic_timer = QTimer(self)
        self.seismic_timer.timeout.connect(self.on_seismic_timer)
        self.seismic_timer.start(40)



    def resizeEvent(self, evt):
        if not self.isMaximized():
            self.size_helper = evt.size()


    def create_dock(self, widget_class, state={}, show=True, one_instance=False):
        widget, right = {
                "browser"      : [Browser, False],
                "scheduler"    : [Scheduler, "scheduler_view"],
                "rundown"      : [Rundown, "rundown_view"],
                "preview"      : [Preview, False],
                "detail"       : [Detail, False]
                }[widget_class]

        if right and not has_right(right):
            logging.warning("Not authorised to show {}".format(widget_class))
            return

        create = True
        if one_instance:
            for dock in self.docks:
                if dock.class_ == widget_class:
                    if dock.class_ == "detail":
                        if dock.hasFocus():
                            dock.main_widget.switch_tabs()
                        else:
                            dock.main_widget.switch_tabs(0)
                    dock.raise_()
                    dock.setFocus()
                    return dock

        # Create new dock
        QApplication.processEvents()
        QApplication.setOverrideCursor(Qt.WaitCursor)

        self.docks.append(BaseDock(self, widget, state))
        if self.workspace_locked:
            self.docks[-1].setAllowedAreas(Qt.NoDockWidgetArea)
        else:
            self.docks[-1].setAllowedAreas(Qt.AllDockWidgetAreas)
        if show:
            self.docks[-1].setFloating(True)
            self.docks[-1].show()

        qr = self.docks[-1].frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.docks[-1].move(qr.topLeft())

        # populate dock with asset data from cache
        self.push_asset_data(self.docks[-1])

        QApplication.restoreOverrideCursor()
        return self.docks[-1]



    def lock_workspace(self):
        for dock in self.docks:
            if dock.isFloating():
                dock.setAllowedAreas(Qt.NoDockWidgetArea)
            else:
                dock.setTitleBarWidget(QWidget())
        self.workspace_locked = True

    def unlock_workspace(self):
        wdgt = QDockWidget().titleBarWidget()
        for dock in self.docks:
            dock.setAllowedAreas(Qt.AllDockWidgetAreas)
            if not dock.isFloating():
                dock.setTitleBarWidget(wdgt)
        self.workspace_locked = False



    def closeEvent(self, event):
        settings = ffsettings()

        settings.remove("main_window")
        settings.setValue("main_window/state", self.saveState())

        settings.setValue("main_window/pos", self.pos())
        settings.setValue("main_window/size", self.size_helper)
        settings.setValue("main_window/maximized", int(self.isMaximized()))
        settings.setValue("main_window/locked", int(self.workspace_locked))

        settings.remove("docks")
        for dock in self.docks:
            dock.save()

        asset_cache.save()

    def on_dock_destroyed(self):
        for i, dock in enumerate(self.docks):
            try:
                a = dock.objectName()
            except:
                del(self.docks[i])

    def focus(self, objects):
        for d in self.docks:
            if d.class_ in ["preview", "detail", "scheduler"] and objects:
                d.main_widget.focus(objects)

    def focus_rundown(self, id_channel, date, event=False):
        dock = self.create_dock("rundown", state={}, show=True, one_instance=True)
        dock.main_widget.load(id_channel, date, event)

    def on_search(self):
        for d in self.docks:
            if d.class_ == "browser":
                d.main_widget.search_box.setFocus()
                d.main_widget.search_box.selectAll()

    def on_now(self):
        dock = self.create_dock("rundown", state={}, show=True, one_instance=True)
        dock.main_widget.on_now()


    #
    # Menu actions
    #

    # FILE

    def on_new_asset(self):
        dock = self.create_dock("detail", state={}, show=True, one_instance=True)
        dock.main_widget.new_asset()

    def on_clone_asset(self):
        dock = self.create_dock("detail", state={}, show=True, one_instance=True)
        dock.main_widget.clone_asset()

    def on_dlg_system(self):
        self.sys_dlg = SystemDialog(self)
        self.sys_dlg.exec_()

    def on_logout(self):
        api.logout()
        self.close()

    def on_exit(self):
        with open("auth.key", "w") as f:
            f.write(api.auth_key)
        self.close()

    # VIEW

    def on_wnd_browser(self):
        self.create_dock("browser")

    def on_wnd_preview(self):
        self.create_dock("preview", one_instance=True)

    def on_wnd_scheduler(self):
        self.create_dock("scheduler", one_instance=True)

    def on_wnd_rundown(self):
        self.create_dock("rundown", one_instance=True)

    def on_lock_workspace(self):
        if self.workspace_locked:
            self.unlock_workspace()
        else:
            self.lock_workspace()

    def on_refresh(self):
        for dock in self.docks:
            dock.main_widget.refresh()

    def on_change_channel(self, id_channel):
        self.id_channel = id_channel
        for action in self.menu_channel.actions():
            if action.id_channel == id_channel:
                action.setChecked(True)
        for d in self.docks:
            if d.class_ in ["rundown", "scheduler"]:
                d.main_widget.set_channel(id_channel)

    def on_send_message(self):
        msg, ok = QInputDialog.getText(self, "Send message", "Text", QLineEdit.Normal)
        if ok and msg:
            api.message(message=msg)

    #
    # Status line
    #

    def log_handler(self, **kwargs):
        message_type = kwargs.get("message_type", INFO)
        message = kwargs.get("message", "")
        if not message:
            return
        if message_type == WARNING:
            QMessageBox.warning(self, "Warning", message)
        elif message_type== ERROR:
            QMessageBox.critical(self, "Error", message)
        else:
            self.statusBar().showMessage(message, 10000)

    #
    # Seismic
    #

    def on_seismic_timer(self):
        try:
            msg = self.parent.listener.queue.pop(0)
        except IndexError:
            pass
        else:
            self.handle_messaging(msg)

    def handle_messaging(self, data):
        if data.method == "objects_changed" and data.data["object_type"] == "asset":
            aids = [aid for aid in data.data["objects"] if aid in asset_cache.keys()]
            if aids:
                logging.info("{} has been changed by {}".format(asset_cache[aids[0]], data.data.get("user", "anonymous"))  )
                self.update_assets(aids)

        if data.method == "message" and data.data["sender"] != AUTH_KEY:
            QMessageBox.information(self, "Message", "Message from {}\n\n{}".format(data.data["from_user"],  data.data["message"]))
            return

        elif data.method == "firefly_shutdown":
            logging.warning("Remote shutdown")
            sys.exit(0)


        for dock in self.docks:
            if dock.class_ == "rundown" and data.method in ["playout_status", "job_progress", "objects_changed"]:
                pass
            elif dock.class_ in ["detail", "scheduler"] and data.method == "objects_changed":
                pass
            else:
                continue # cool construction, isn't it?

            dock.main_widget.seismic_handler(data)

        for subscriber in self.subscribers:
            if data.method in self.subscribers[subscriber]:
                subscriber(data)


    def subscribe(self, handler, *methods):
        """subscribe dialogs and other (non-dock) windows to seismic"""
        self.subscribers[handler] = methods

    def unsubscribe(self, handler):
        del self.subscribers[handler]

    #
    # Asset caching
    #

    def update_assets(self, asset_ids=[]):
       pass
        # Call this if you want to update asset cache
        #res, adata = query("get_assets", handler=self.update_assets_handler , asset_ids=asset_ids)
        #for dock in self.docks:
        #    self.push_asset_data(dock)

    def update_assets_handler(self, data):
        # Handler for asset data comming from get_assets query
        a = Asset(from_data=data)
        asset_cache[a.id] = a

    def push_asset_data(self, dock):
        # Push asset data to dock which need it
        if dock.class_ in ["rundown", "browser"]:
            dock.main_widget.model.refresh_assets(asset_cache.keys())


if __name__ == "__main__":
    app = Firestarter(Firefly)
    app.start()
