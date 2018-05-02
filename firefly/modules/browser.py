import math
import functools

from firefly import *
#from firefly.dialogs.send_to import SendToDialog
#from firefly.dialogs.batch import BatchDialog

from .browser_model import *




class SearchWidget(QLineEdit):
    def __init__(self, parent):
        super(QLineEdit, self).__init__()

    def keyPressEvent(self, event):
        if event.key() in [Qt.Key_Return,Qt.Key_Enter]:
            self.parent().parent().browse()
        elif event.key() == Qt.Key_Escape:
            self.line_edit.setText("")
        elif event.key() == Qt.Key_Down:
            self.parent().parent().view.setFocus()
        QLineEdit.keyPressEvent(self, event)


class BrowserModule(BaseModule):
    def __init__(self, parent):
        super(BrowserModule, self).__init__(parent)

#TODO: defaults from appstate
        self.search_query = {
                "view" : min(config["views"].keys())
            }

        self.search_box = SearchWidget(self)

        self.view = FireflyView(self)
        self.view.setSortingEnabled(True)
        self.view.clicked.connect(self.on_click)
        self.view.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.model       = BrowserModel(self)
        self.sort_model  = FireflySortModel(self.model)
        self.view.setModel(self.sort_model)

        action_clear = QAction(QIcon(pix_lib["search_clear"]), '&Clear search query', parent)
        action_clear.triggered.connect(self.on_clear)

        self.action_search = QMenu("Views")
        self.action_search.setStyleSheet(app_skin)
        self.action_search.menuAction().setIcon(QIcon(pix_lib["search"]))
        self.action_search.menuAction().triggered.connect(self.browse)
        self.load_view_menu()

        action_copy = QAction('Copy result', self)
        action_copy.setShortcut('CTRL+C')
        action_copy.triggered.connect(self.on_copy_result)
        self.addAction(action_copy)

        toolbar = QToolBar()
        toolbar.addWidget(self.search_box)
        toolbar.addAction(action_clear)
        toolbar.addAction(self.action_search.menuAction())

        layout = QVBoxLayout()
        layout.setContentsMargins(0,0,0,0)
        layout.addWidget(toolbar, 0)
        layout.addWidget(self.view, 1)
        self.setLayout(layout)
        self.browse()


    def load_view_menu(self):
        for id_view in sorted(
                    config["views"].keys(),
                    key=lambda k: config["views"][k]["position"]
                ):
            view = config["views"][id_view]
            if view["title"] == "-":
                self.action_search.addSeparator()
                continue
            action = QAction(view["title"], self, checkable=True)
            action.id_view = id_view
            action.triggered.connect(functools.partial(self.set_view, id_view))
            self.action_search.addAction(action)

#
# Do browse
#

    def browse(self, **kwargs):
        search_string = self.search_box.text()
        self.search_query["fulltext"] = search_string
        self.search_query.update(kwargs)
        self.model.browse(**self.search_query)

    def refresh(self):
        self.browse()

    def on_clear(self):
        self.search_box.setText("")
        self.browse(fulltext="")

    def set_view(self, id_view):
        self.browse(view=id_view)
        for action in self.action_search.actions():
            if not hasattr(action, "id_view"):
                continue
            if action.id_view == id_view:
                action.setChecked(True)
            else:
                action.setChecked(False)




    def hideEvent(self, event):
        pass

    def contextMenuEvent(self, event):
        if not self.view.selected_objects:
            return
        menu = QMenu(self)

        statuses = [obj["status"] for obj in self.view.selected_objects ]

        if len(statuses) == 1 and statuses[0] == TRASHED:
            action_untrash = QAction('Untrash', self)
            action_untrash.setStatusTip('Take selected asset(s) from trash')
            action_untrash.triggered.connect(self.on_untrash)
            menu.addAction(action_untrash)
        else:
            action_move_to_trash = QAction('Move to trash', self)
            action_move_to_trash.setStatusTip('Move selected asset(s) to trash')
            action_move_to_trash.triggered.connect(self.on_trash)
            menu.addAction(action_move_to_trash)

        if len(statuses) == 1 and statuses[0] == ARCHIVED:
            action_unarchive = QAction('Unarchive', self)
            action_unarchive.setStatusTip('Take selected asset(s) from archive')
            action_unarchive.triggered.connect(self.on_unarchive)
            menu.addAction(action_unarchive)
        else:
            action_move_to_archive = QAction('Move to archive', self)
            action_move_to_archive.setStatusTip('Move selected asset(s) to archive')
            action_move_to_archive.triggered.connect(self.on_archive)
            menu.addAction(action_move_to_archive)


        action_reset = QAction('Reset', self)
        action_reset.setStatusTip('Reload asset metadata')
        action_reset.triggered.connect(self.on_reset)
        menu.addAction(action_reset)

        menu.addSeparator()

        action_send_to = QAction('&Send to...', self)
        action_send_to.setStatusTip('Create action for selected asset(s)')
        action_send_to.triggered.connect(self.on_send_to)
        menu.addAction(action_send_to)

        if config["rights"]["is_admin"].lower() == "true":
            action_batch = QAction('&Batch ops', self)
            action_batch.setStatusTip('Batch operations')
            action_batch.triggered.connect(self.on_batch)
            menu.addAction(action_batch)

        menu.addSeparator()

        action_columns = QAction('Choose columns', self)
        action_columns.setStatusTip('Choose header columns')
        action_columns.triggered.connect(self.on_choose_columns)
        menu.addAction(action_columns)

        menu.exec_(event.globalPos())


    def on_send_to(self):
        dlg = SendTo(self, self.view.selected_objects)
        dlg.exec_()


    def on_reset(self):
        stat, res = query("set_meta", objects=[obj.id for obj in self.view.selected_objects if obj["status"] not in [ARCHIVED, TRASHED, RESET]], data={"status" : RESET} )


    def on_trash(self):
        ret = QMessageBox.question(self,
            "Trash",
            "Do you really want to trash {} selected asset(s)?".format(len(self.view.selected_objects)),
            QMessageBox.Yes | QMessageBox.No
            )
        if ret == QMessageBox.Yes:
            stat, res = query("trash", objects=[obj.id for obj in self.view.selected_objects if obj["status"] not in [ARCHIVED, TRASHED]])


    def on_untrash(self):
        objs = [obj.id for obj in self.view.selected_objects if obj["status"] in [TRASHED]]
        if objs:
            stat, res = query("untrash", objects=objs)

    def on_archive(self):
        ret = QMessageBox.question(self,
            "Archive",
            "Do you really want to move {} selected asset(s) to archive?".format(len(self.view.selected_objects)),
            QMessageBox.Yes | QMessageBox.No
            )
        if ret == QMessageBox.Yes:
            stat, res = query("archive", objects=[obj.id for obj in self.view.selected_objects if obj["status"] not in [ARCHIVED, TRASHED]])

    def on_unarchive(self):
        objs = [obj.id for obj in self.view.selected_objects if obj["status"] in [ARCHIVED]]
        if objs:
            stat, res = query("unarchive", objects=objs)

    def on_batch(self):
        dlg = BatchDialog(self, self.view.selected_objects)
        dlg.exec_()

    def on_choose_columns(self):
        pass #TODO

    def on_copy_result(self):
        result = ""
        for obj in self.view.selected_objects:
            result += "{}\n".format("\t".join([obj.format_display(key) or "" for key in self.model.header_data]))
        clipboard = QApplication.clipboard();
        clipboard.setText(result)

    def on_click(self, index):
        rows = []
        self.view.selected_objects = []

        tot_dur = 0
        for idx in self.view.selectionModel().selectedIndexes():
            row = self.sort_model.mapToSource(idx).row()
            if row in rows:
                continue
            rows.append(row)
            obj = self.model.object_data[row]
            self.view.selected_objects.append(obj)
            if obj.object_type in ["asset", "item"]:
                tot_dur += obj.duration

        days = math.floor(tot_dur / (24*3600))
        durstr = "{} days {}".format(days, s2time(tot_dur)) if days else s2time(tot_dur)

        if self.view.selected_objects:
            self.main_window.focus(self.view.selected_objects[0])
            if len(self.view.selected_objects) > 1 and tot_dur:
                logging.debug("{} objects selected. Total duration {}".format(len(self.view.selected_objects), durstr ))
