from functools import partial
from firefly.qt import *

class SiteSelectButton(QPushButton):
    pass

class SiteSelectDialog(QDialog):
    def __init__(self,  parent, sites=[]):
        super(SiteSelectDialog, self).__init__(parent)
        self.sites = sites
        self.setModal(True)
        self.setStyleSheet(base_css)
        self.setWindowTitle("Multiple sites are cofigured")
        self.setWindowIcon(QIcon(":/images/firefly.ico"))

        layout = QVBoxLayout()
        for i, site in enumerate(sites):
            btn_site = SiteSelectButton(site.get("site_title", False) or site["site_name"])
            btn_site.clicked.connect(partial(self.on_select, i))
            layout.addWidget(btn_site, 1)

            self.setLayout(layout)
            self.setMinimumWidth(400)

    def on_select(self, id_site):
        self.close()
        self.setResult(id_site)
