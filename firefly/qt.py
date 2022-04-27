import os

from nxtools import logging, log_traceback

from PySide6.QtCore import (
    QSettings,
    QUrlQuery,
    QUrl,
    QTimer,
    QEvent,
    QThread,
    QModelIndex,
    QItemSelection,
    QItemSelectionModel,
    QDate,
    QMimeData,
    QAbstractTableModel,
    QSortFilterProxyModel,
    QRect,
)

from PySide6.QtGui import (
    Qt,
    QFont,
    QPixmap,
    QIcon,
    QColor,
    QAction,
    QFontDatabase,
    QBrush,
    QPalette,
    QFontMetrics,
    QActionGroup,
    QDrag,
    QPainter,
    QLinearGradient,
    QPen,
)

from PySide6.QtWidgets import (
    QDialog,
    QLineEdit,
    QPushButton,
    QFormLayout,
    QMessageBox,
    QApplication,
    QVBoxLayout,
    QMenu,
    QWidget,
    QLabel,
    QSizePolicy,
    QGridLayout,
    QTextEdit,
    QSpinBox,
    QCheckBox,
    QColorDialog,
    QHBoxLayout,
    QComboBox,
    QAbstractItemDelegate,
    QStyle,
    QStyleOptionMenuItem,
    QStyleOptionComboBox,
    QStylePainter,
    QAbstractItemView,
    QInputDialog,
    QToolBar,
    QCalendarWidget,
    QToolButton,
    QProgressBar,
    QTabWidget,
    QDialogButtonBox,
    QTableView,
    QFileDialog,
    QScrollArea,
    QFrame,
    QSlider,
    QMainWindow,
    QSplitter,
    QSplashScreen,
)

from PySide6.QtNetwork import (
    QNetworkAccessManager,
    QNetworkRequest,
)


app_dir = os.getcwd()


class AppSettings:
    def __init__(self):
        self.data = {"name": "qtapp"}

    def get(self, key, default=False):
        return self.data.get(key, default)

    def update(self, data):
        return self.data.update(data)

    def __setitem__(self, key, value):
        self.data[key] = value

    def __getitem__(self, key):
        if key == "title":
            return self.get(key, self.data["name"])
        return self.data[key]


app_settings = AppSettings()
logging.name = app_settings["name"]


def get_app_state(path):
    return QSettings(path, QSettings.Format.IniFormat)


#
# Skin
#

app_skin = ""
skin_path = os.path.join(app_dir, "skin.css")
if os.path.exists(skin_path):
    try:
        app_skin = open(skin_path).read()
    except Exception:
        log_traceback("Unable to read stylesheet")
