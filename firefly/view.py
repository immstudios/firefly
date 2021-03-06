from .common import *
from .widgets import *

from pprint import pformat

__all__ = ["FireflyViewModel", "FireflySortModel", "FireflyView", "format_header", "format_description"]

def format_header(key):
    return meta_types[key].header()

def format_description(key):
    return meta_types[key].description()

class FireflyViewModel(QAbstractTableModel):
    def __init__(self, parent):
        super(FireflyViewModel, self).__init__(parent)
        self.object_data = []
        self.header_data = []
        self.changed_objects = []

    def rowCount(self, parent):
        return len(self.object_data)

    def columnCount(self, parent):
        return len(self.header_data)

    def headerData(self, col, orientation=Qt.Horizontal, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                return format_header(self.header_data[col])
            elif role == Qt.ToolTipRole:
                desc = format_description(self.header_data[col])
                return "<p>{}</p>".format(desc) if desc else None
        return None

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        row = index.row()
        obj = self.object_data[row]
        key = self.header_data[index.column()]

        if role == Qt.DisplayRole:
            return obj.format_display(key, model=self)
        elif role == Qt.ForegroundRole:
            color = obj.format_foreground(key, model=self)
            return QColor(color) if color else None
        elif role == Qt.BackgroundRole:
            color = obj.format_background(key, model=self)
            return QColor(color) if color else None
        elif role == Qt.DecorationRole:
            return pix_lib[obj.format_decoration(key, model=self)]
        elif role == Qt.FontRole:
            font = obj.format_font(key, model=self)
            return fonts[font]
        elif role == Qt.ToolTipRole:
            if config.get("debug", False):
                r = pformat(obj.meta)
                if obj.object_type == "item":
                    r += "\n\n" + pformat(obj.asset.meta) if obj.asset else ""
                return r
            else:
                return obj.format_tooltip(key, model=self)
        return None


    def setData(self, index, data, role=False):
        key = self.header_data[index.column()]
        id_object = self.object_data[index.row()].id
        self.object_data[index.row()][key] = data

        if not id_object in self.changed_objects:
            self.changed_objects.append(id_object)

        self.model.dataChanged.emit(index, index)
        self.update()

        self.refresh()
        return True

    def refresh(self):
        pass


class FireflySortModel(QSortFilterProxyModel):
    def __init__(self, model):
        super(FireflySortModel, self).__init__()
        self.setSourceModel(model)
        self.setDynamicSortFilter(True)
        self.setSortLocaleAware(True)

    @property
    def object_data(self):
       return self.sourceModel().object_data

    def mimeData(self, indexes):
        return self.sourceModel().mimeData([self.mapToSource(idx) for idx in indexes ])


class FireflyView(QTableView):
    def __init__(self, parent):
        super(FireflyView, self).__init__(parent)
        self.verticalHeader().setVisible(False)
        self.setWordWrap(False)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setSelectionMode(self.ExtendedSelection)
        self.setShowGrid(False)
        self.setAlternatingRowColors(True)
        self.selected_objects = []
        self.focus_enabled = True

    @property
    def main_window(self):
        return self.parent().main_window
