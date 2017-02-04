from firefly import *

__all__ = ["PlaceholderDialog", "SubclipSelectDialog"]

ITEM_ROLES = {
    "studio" : [["title", "Studio"], ["duration", 300], ["article", ""]],
    "placeholder" : [["title", "Placeholder"], ["duration", 3600] ],
}


class PlaceholderDialog(QDialog):
    def __init__(self,  parent, item_role):
        super(PlaceholderDialog, self).__init__(parent)
        self.setWindowTitle("Rundown placeholder")

        self.ok = False

        toolbar = QToolBar(self)
        toolbar.setMovable(False)
        toolbar.setFloatable(False)
        toolbar.addWidget(ToolBarStretcher(toolbar))

        action_accept = QAction(QIcon(pixlib["accept"]), 'Accept changes', self)
        action_accept.setShortcut('Ctrl+S')
        action_accept.triggered.connect(self.on_accept)
        toolbar.addAction(action_accept)

        keys =  [[key, {"default":default}] for key, default in ITEM_ROLES[item_role]]
        self.form = MetaEditor(parent, keys)

        layout = QVBoxLayout()
        layout.addWidget(toolbar, 0)
        layout.addWidget(self.form, 1)
        self.setLayout(layout)

        self.setModal(True)
        self.setStyleSheet(base_css)
        self.setMinimumWidth(400)

    @property
    def meta(self):
        return self.form.meta

    def on_accept(self):
        self.ok = True
        self.close()



class SubclipSelectDialog(QDialog):
    def __init__(self,  parent, asset):
        super(SubclipSelectDialog, self).__init__(parent)
        self.setModal(True)
        self.setStyleSheet(base_css)
        self.setWindowTitle("Select {} subclip to use".format(asset))
        self.ok = False

        layout = QVBoxLayout()

        btn = QPushButton("Entire clip")
        btn.clicked.connect(functools.partial(self.on_submit, "", [asset["mark_in"],asset["mark_out"]]))
        layout.addWidget(btn)

        subclips = asset.meta.get("subclips", {})
        for subclip in sorted(subclips):
            marks = subclips[subclip]
            btn = QPushButton(subclip)
            btn.clicked.connect(functools.partial(self.on_submit, subclip, marks))
            layout.addWidget(btn)

        self.setLayout(layout)


    def on_submit(self, clip, marks):
        self.marks = [float(mark) for mark in marks]
        self.clip = clip
        self.ok = True
        self.close()


