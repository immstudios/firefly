from firefly.common import *
from firefly.widgets import *
from firefly.view import *

__all__ = ["FireflySubclipsView"]

DEFAULT_HEADER_DATA = [
        "mark_in",
        "mark_out",
        "title",
    ]

header_format = {
        "mark_in" : "In",
        "mark_out" : "Out",
        "title" : "Title",
    }

colw = {
        "mark_in" : 120,
        "mark_out" : 120,
        "title" : 300,
    }


class SubclipsModel(FireflyViewModel):
    def __init__(self, *args, **kwargs):
        super(SubclipsModel, self).__init__(*args, **kwargs)
        self.header_data = DEFAULT_HEADER_DATA

    def headerData(self, col, orientation=Qt.Horizontal, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return header_format[self.header_data[col]]
        return None

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        row = index.row()
        obj = self.object_data[row]
        key = self.header_data[index.column()]
        if role == Qt.DisplayRole:
            return meta_types[obj].show(obj[key])
        return None

    def load(self, **kwargs):
        self.beginResetModel()
        if self.parent().current_asset:
            self.object_data = self.parent().current_asset["subclips"]
            self.object_data.sort(key=lambda row: row["mark_in"])
        else:
            self.object_data = []
        self.endResetModel()


class FireflySubclipsView(FireflyView):
    def __init__(self, parent):
        super(FireflySubclipsView, self).__init__(parent)
        self.model = SubclipsModel(self)
        self.setModel(self.model)
        for i, h in enumerate(self.model.header_data):
            if h in colw :
                self.horizontalHeader().resizeSection(i, colw[h])
        self.horizontalHeader().setStretchLastSection(True)

    def load(self):
        self.model.load()

    @property
    def current_asset(self):
        return self.parent().current_asset
