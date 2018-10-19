import math
import functools

from firefly import *

from .jobs_model import *

class SearchWidget(QLineEdit):
    def __init__(self, parent):
        super(QLineEdit, self).__init__()

    def keyPressEvent(self, event):
        if event.key() in [Qt.Key_Return,Qt.Key_Enter]:
            self.parent().parent().load()
        elif event.key() == Qt.Key_Escape:
            self.line_edit.setText("")
        elif event.key() == Qt.Key_Down:
            self.parent().parent().view.setFocus()
        QLineEdit.keyPressEvent(self, event)




class JobsModule(BaseModule):
    def __init__(self, parent):
        super(JobsModule, self).__init__(parent)

        self.view = FireflyJobsView(self)

        toolbar = QToolBar()

        btn_active = QPushButton("ACTIVE")
        btn_active.setCheckable(True)
        btn_active.setChecked(True)
        btn_active.setAutoExclusive(True)
        btn_active.clicked.connect(functools.partial(self.set_view, "active"))
        toolbar.addWidget(btn_active)

        btn_finished = QPushButton("FINISHED")
        btn_finished.setCheckable(True)
        btn_finished.setAutoExclusive(True)
        btn_finished.clicked.connect(functools.partial(self.set_view, "finished"))
        toolbar.addWidget(btn_finished)

        btn_failed = QPushButton("FAILED")
        btn_failed.setCheckable(True)
        btn_failed.setAutoExclusive(True)
        btn_failed.clicked.connect(functools.partial(self.set_view, "failed"))
        toolbar.addWidget(btn_failed)

        toolbar.addWidget(ToolBarStretcher(self))

        layout = QVBoxLayout()
        layout.setContentsMargins(0,0,0,0)
        layout.addWidget(toolbar, 0)
        layout.addWidget(self.view, 1)
        self.setLayout(layout)
        self.set_view("active")


    @property
    def model(self):
        return self.view.model

    def load(self, **kwargs):
        self.view.model.load(**kwargs)

    def set_view(self, id_view="active"):
        self.id_view = id_view
        self.load(view=id_view)

    def seismic_handler(self, message):
        if self.main_window.current_module != self.main_window.jobs:
            return

        if self.id_view != "active":
            return

        d = message.data

        do_reload = False
        for row in self.view.model.object_data:
            if row["id"] == d.get("id", False):
                #TODO: emit change row instead reset model
                self.view.model.beginResetModel()
                row["message"] = d["message"]
                row["progress"] = d["progress"]
                self.view.model.endResetModel()
                if row["status"] != d.get("status", False):
                    do_reload = True
                break
        else:
            do_reload = True

        if do_reload:
            self.view.model.load()
