import functools
from firefly import *

from .rundown_model import RundownModel

class RundownView(FireflyView):
    def __init__(self, parent):
        super(RundownView, self).__init__(parent)
        self.activated.connect(self.on_activate)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setModel(RundownModel(self))

    @property
    def id_channel(self):
        return self.parent().id_channel

    @property
    def start_time(self):
        return self.parent().start_time

    def load(self):
        self.model().load()

    def selectionChanged(self, selected, deselected):
        rows = []
        self.selected_objects = []
        tot_dur = 0

        for idx in self.selectionModel().selectedIndexes():
            row = idx.row()
            if row in rows:
                continue
            rows.append(row)
            obj = self.model().object_data[row]
            self.selected_objects.append(obj)
            if obj.object_type in ["asset", "item"]:
                tot_dur += obj.duration

        if self.selected_objects and self.focus_enabled:
            self.parent().main_window.focus(self.selected_objects[0])
            if len(self.selected_objects) == 1 and self.selected_objects[0].object_type == "item" and self.selected_objects[0]["id_asset"]:
                asset = self.selected_objects[0].asset
                times = len([obj for obj in self.model().object_data if obj.object_type == "item" and obj["id_asset"] == asset.id])
                logging.info("{} is scheduled {}x in this rundown".format(asset, times))
            if len(self.selected_objects) > 1 and tot_dur:
                logging.info("{} objects selected. Total duration {}".format(len(self.selected_objects), s2time(tot_dur) ))

        super(FireflyView, self).selectionChanged(selected, deselected)


    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete:
            self.on_delete()
        FireflyView.keyPressEvent(self, event)


    ###################################################
    ## Rundown actions

    def contextMenuEvent(self, event):
        obj_set = list(set([itm.object_type for itm in self.selected_objects]))
        menu = QMenu(self)

        if len(obj_set) > 0:

            action_focus = QAction('&Focus', self)
            action_focus.setStatusTip('Focus selected object')
            action_focus.triggered.connect(self.on_focus)
            menu.addAction(action_focus)

            menu.addSeparator()


        if len(obj_set) == 1:
            if obj_set[0] == "item" and self.selected_objects[0]["id_asset"]:

                mode_menu = menu.addMenu("Run mode")

                action_mode_auto = QAction('&Auto', self)
                action_mode_auto.setStatusTip('Set run mode to auto')
                action_mode_auto.triggered.connect(functools.partial(self.on_set_mode, 0))
                mode_menu.addAction(action_mode_auto)

                action_mode_manual = QAction('&Manual', self)
                action_mode_manual.setStatusTip('Set run mode to manual')
                action_mode_manual.triggered.connect(functools.partial(self.on_set_mode, 1))
                mode_menu.addAction(action_mode_manual)

            elif obj_set[0] == "event" and len(self.selected_objects) == 1:
                mode_menu = menu.addMenu("Run mode")

                action_mode_auto = QAction('&Auto', self)
                action_mode_auto.setStatusTip('Set run mode to auto')
                action_mode_auto.setCheckable(True)
                action_mode_auto.setChecked(self.selected_objects[0]["run_mode"] == 0)
                action_mode_auto.triggered.connect(functools.partial(self.on_set_mode, 0))
                mode_menu.addAction(action_mode_auto)

                action_mode_manual = QAction('&Manual', self)
                action_mode_manual.setStatusTip('Set run mode to manual')
                action_mode_manual.setCheckable(True)
                action_mode_manual.setChecked(self.selected_objects[0]["run_mode"] == 1)
                action_mode_manual.triggered.connect(functools.partial(self.on_set_mode, 1))
                mode_menu.addAction(action_mode_manual)

                action_mode_soft = QAction('&Soft', self)
                action_mode_soft.setStatusTip('Set run mode to soft')
                action_mode_soft.setCheckable(True)
                action_mode_soft.setChecked(self.selected_objects[0]["run_mode"] == 2)
                action_mode_soft.triggered.connect(functools.partial(self.on_set_mode, 2))
                mode_menu.addAction(action_mode_soft)

                action_mode_hard = QAction('&Hard', self)
                action_mode_hard.setStatusTip('Set run mode to hard')
                action_mode_hard.setCheckable(True)
                action_mode_hard.setChecked(self.selected_objects[0]["run_mode"] == 3)
                action_mode_hard.triggered.connect(functools.partial(self.on_set_mode, 3))
                mode_menu.addAction(action_mode_hard)


        if "item" in obj_set:
            action_send_to = QAction('&Send to...', self)
            action_send_to.setStatusTip('Create action for selected asset(s)')
            action_send_to.triggered.connect(self.on_send_to)
            menu.addAction(action_send_to)


        if "event" in obj_set:
            action_solve = QAction('Solve', self)
            action_solve.setStatusTip('Solve selected event')
            action_solve.triggered.connect(self.on_solve_event)
            menu.addAction(action_solve)

        if len(obj_set) > 0:
            menu.addSeparator()

            action_delete = QAction('&Delete', self)
            action_delete.setStatusTip('Delete selected object')
            action_delete.triggered.connect(self.on_delete)
            menu.addAction(action_delete)

            if len(obj_set) == 1 and "event" in obj_set:
                action_edit = QAction('&Edit', self)
                action_edit.setStatusTip('Edit selected event')
                action_edit.triggered.connect(self.on_edit_event)
                menu.addAction(action_edit)

        menu.exec_(event.globalPos())


    def on_set_mode(self, mode):
        if not self.parent().can_edit:
            logging.error("You are not allowed to modify this rundown")
            return
        QApplication.processEvents()
        QApplication.setOverrideCursor(Qt.WaitCursor)
        stat, res = query("set_meta", object_type=self.selected_objects[0].object_type, objects=[obj.id for obj in self.selected_objects], data={"run_mode":mode})
        QApplication.restoreOverrideCursor()
        if not success(stat):
            logging.error(res)
        self.parent().refresh()
        self.selectionModel().clear()
        return

    def on_focus(self):
        pass

    def on_delete(self):
        items = list(set([obj.id for obj in self.selected_objects if obj.object_type == "item"]))
        events  = list(set([obj.id for obj in self.selected_objects if obj.object_type == "event"]))

        if items and not self.parent().can_edit:
            logging.error("You are not allowed to modify this rundown items")
            return
        elif events and not self.parent().can_schedule:
            logging.error("You are not allowed to modify this rundown blocks")
            return


        if events or len(items) > 10:
            ret = QMessageBox.question(self,
                "Delete",
                "Do you REALLY want to delete {} items and {} events?\nThis operation CANNOT be undone".format(len(items), len(events)),
                QMessageBox.Yes | QMessageBox.No
                )

            if ret != QMessageBox.Yes:
                return

        if items:
            QApplication.processEvents()
            QApplication.setOverrideCursor(Qt.WaitCursor)
            stat, res = query("del_items", items=items)
            QApplication.restoreOverrideCursor()
            if success(stat):
                logging.info("Item deleted: {}".format(res))
            else:
                logging.error(res)

        if events:
            QApplication.processEvents()
            QApplication.setOverrideCursor(Qt.WaitCursor)
            stat, res = query("set_events", delete=events)
            QApplication.restoreOverrideCursor()
            if success(stat):
                logging.info("Event deleted: {}".format(res))
            else:
                logging.error(res)

        self.parent().refresh()
        self.selectionModel().clear()


    def on_send_to(self):
        objs = set([obj for obj in self.selected_objects if obj.object_type == "item"])
        if not objs:
            logging.warning("No rundown item selected")
            return
        dlg = SendToDialog(self, objs)
        dlg.exec_()


    def on_edit_event(self):
        objs = [obj for obj in self.selected_objects if obj.object_type == "event"]
        dlg = EventDialog(self, event=objs[0])
        if dlg.exec_() == QDialog.Accepted:
            self.refresh()


    def on_solve_event(self):
        if not self.parent().can_edit:
            logging.error("You are not allowed to modify this rundown")
            return

        ret = QMessageBox.question(self,
            "Solve event",
            "Do you really want to (re)solve {}?\nThis operation cannot be undone.".format(self.selected_objects[0]),
            QMessageBox.Yes | QMessageBox.No
            )

        if ret == QMessageBox.Yes:
            QApplication.processEvents()
            QApplication.setOverrideCursor(Qt.WaitCursor)
            stat, res = query("dramatica",
                handler=self.parent().handle_message,
                id_channel=self.parent().id_channel,
                date=time.strftime("%Y-%m-%d", time.localtime(self.parent().start_time)),
                id_event =self.selected_objects[0].id,
                solve=True
                )
            QApplication.restoreOverrideCursor()
            if not success(stat):
                logging.error(res)
            self.parent().refresh()


    def on_activate(self, mi):
        obj = self.model().object_data[mi.row()]
        can_mcr = user.has_right("mcr", self.id_channel)
        if obj.object_type == "item" and self.mcr and self.mcr.isVisible() and can_mcr:
            stat, res = query("cue", self.mcr.route, id_channel=self.id_channel, id_item=obj.id)
            if not success(stat):
                logging.error(res)
            self.view.clearSelection()
        elif obj.object_type == "event" and has_right("scheduler_edit", self.id_channel):
            if self.model().header_data[mi.column()] == "rundown_symbol":
                obj["promoted"] = not obj["promoted"]
                stat, res = query("set_events",
                    id_channel=obj["id_channel"],
                    events=[obj.meta]
                    )
                self.refresh()
            else:
                self.view.on_edit_event()
