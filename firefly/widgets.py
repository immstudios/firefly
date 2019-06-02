import time
import copy
import functools

from nx import *

from nebulacore.meta_format import format_select

from .common import *
from .dialogs.text_editor import TextEditorDialog
from .multiselect import CheckComboBox


class ChannelDisplay(QLabel):
    pass

class ToolBarStretcher(QWidget):
    def __init__(self, parent):
        super(ToolBarStretcher, self).__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)

class ActionButton(QPushButton):
    pass

#
# Metadata editor widgets
#

class FireflyNotImplementedEditor(QLabel):
    def __init__(self, parent, **kwargs):
        super(FireflyNotImplementedEditor, self).__init__(parent)
        self.val = None

    def set_value(self, value):
        self.setText(str(value))
        self.val = value
        self.default = value

    def get_value(self):
        return self.val

    def setReadOnly(self, *args, **kwargs):
        pass


class FireflyString(QLineEdit):
    def __init__(self, parent, **kwargs):
        super(FireflyString, self).__init__(parent)
        self.default = self.get_value()

    def set_value(self, value):
        if value == self.get_value():
            return
        self.setText(str(value))
        self.default = self.get_value()

    def get_value(self):
        return self.text()


class FireflyText(QTextEdit):
    def __init__(self, parent, **kwargs):
        super(FireflyText, self).__init__(parent)
        fixed_font = QFontDatabase.systemFont(QFontDatabase.FixedFont)
        fixed_font.setStyleHint(QFont.Monospace);
        self.setCurrentFont(fixed_font)
        self.setTabChangesFocus(True)
        self.default = self.get_value()

    def set_value(self, value):
        if value == self.get_value():
            return
        self.setText(str(value))
        self.default = self.get_value()

    def get_value(self):
        return self.toPlainText()


class FireflyInteger(QSpinBox):
    def __init__(self, parent, **kwargs):
        super(FireflyInteger,self).__init__(parent)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMinimum(kwargs.get("min", 0))
        self.setMaximum(kwargs.get("max", 99999))
        #TODO: set step to 1. disallow floats
        self.default = self.get_value()

    def wheelEvent(self, event):
        if self.hasFocus():
            super(FireflyInteger, self).wheelEvent(event)
        else:
            event.ignore()

    def set_value(self, value):
        if value == self.get_value():
            return
        self.setValue(int(value))
        self.default = self.get_value()

    def get_value(self):
        return int(self.value())


class FireflyNumeric(QSpinBox):
    def __init__(self, parent, **kwargs):
        super(FireflyNumeric,self).__init__(parent)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMinimum(kwargs.get("min", -99999))
        self.setMaximum(kwargs.get("max", 99999))
        #TODO: custom step (default 1, allow floats)
        self.default = self.get_value()

    def wheelEvent(self, event):
        if self.hasFocus():
            super(FireflyNumeric, self).wheelEvent(event)
        else:
            event.ignore()

    def set_value(self, value):
        if value == self.get_value():
            return
        self.setValue(int(value))
        self.default = self.get_value()

    def get_value(self):
        return self.value()


class FireflyDatetime(QLineEdit):
    def __init__(self, parent, **kwargs):
        super(FireflyDatetime,self).__init__(parent)
        mode = kwargs.get("mode", "datetime")

        if mode == "date":
            self.mask   = "9999-99-99"
            self.format = "%Y-%m-%d"

        elif mode == "datetime":
            self.mask   = "9999-99-99 99:99"
            self.format = "%Y-%m-%d %H:%M"

            if kwargs.get("show_seconds", False):
                self.mask += ":99"
                self.format += ":%S"

        self.setInputMask(self.mask)
        self.default = self.get_value()

    def set_value(self, timestamp):
        self.setInputMask("")
        if timestamp:
            tt = time.localtime(timestamp)
            self.setText(time.strftime(self.format, tt))
        else:
            self.setText(self.format.replace("9","-"))
        self.setInputMask(self.mask)
        self.default = self.get_value()

    def get_value(self):
        if not self.text().replace("-", "").replace(":","").strip():
            return float(0)
        t = time.strptime(self.text(), self.format)
        return float(time.mktime(t))


class FireflyTimecode(QLineEdit):
    def __init__(self, parent, **kwargs):
        super(FireflyTimecode,self).__init__(parent)
        self.fps = kwargs.get("fps", 25.0)
        self.setInputMask("99:99:99:99")
        self.setText("00:00:00:00")
        self.default = self.get_value()

        fm = self.fontMetrics()
        w = fm.boundingRect(self.text()).width() + 16
        self.setMinimumWidth(w)
        self.setMaximumWidth(w)

    def set_value(self, value):
        self.setText(s2tc(value, self.fps))
        self.setCursorPosition(0)
        self.default = self.get_value()

    def get_value(self):
        hh, mm, ss, ff = [int(i) for i in self.text().split(":")]
        return (hh*3600) + (mm*60) + ss + (ff/self.fps)




class FireflySelect(QComboBox):
    def __init__(self, parent, **kwargs):
        super(FireflySelect, self).__init__(parent)
        self.setFocusPolicy(Qt.StrongFocus)
        self.cdata = []
        if kwargs.get("data", []):
            self.set_data(kwargs["data"])
        self.default = self.get_value()

    def wheelEvent(self, event):
        if self.hasFocus():
            super(FireflySelect, self).wheelEvent(event)
        else:
            event.ignore()

    def setReadOnly(self, val):
        self.setEnabled(not val)

    def auto_data(self, key):
        data = format_select(key, -1, full=True)
        self.set_data(data)

    def set_data(self, data):
        self.clear()
        self.cdata = []
        i = 0
        for row in data:
            if row["role"] == "hidden":
                continue

            alias = row.get("alias", row["value"])
            self.addItem(alias)
            self.cdata.append(row["value"])

            self.setItemData(i, "<p>{}</p>".format(row["description"]) if row.get("description") else None, Qt.ToolTipRole)
            if row["role"] == "header":
                self.setItemData(i, fonts["bold"], Qt.FontRole)

            if row["role"] == "label":
                item = self.model().item(i)
                item.setEnabled(False)
            if row.get("selected"):
                self.setCurrentIndex(i)
            i+=1

    def set_value(self, value):
        if value == self.get_value():
            return
        if not value and self.cdata and self.cdata[0] == "0":
            self.setCurrentIndex(0)
            return
        if not value:
            return
        for i, val in enumerate(self.cdata):
            if val == value:
                self.setCurrentIndex(i)
                break
        else:
            self.setCurrentIndex(-1)
        self.default = self.get_value()

    def get_value(self):
        if self.currentIndex() == -1:
            return ""
        return self.cdata[self.currentIndex()]


class FireflyRadio(QWidget):
    def __init__(self, parent, **kwargs):
        super(FireflyRadio, self).__init__(parent)
        self.cdata = []
        self.current_index = -1
        self.buttons = []
        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(0,0,0,0)
        self.setLayout(self.layout)
        if kwargs.get("data", []):
            self.set_data(kwargs["data"])
        self.default = self.get_value()


    def clear(self):
        for i, button in enumerate(self.buttons):
            button.deleteLater()
            self.layout.removeWidget(button)
        self.current_index = -1
        self.buttons = []

    def auto_data(self, key):
        data = format_select(key, -1, full=True)
        self.set_data(data)

    def set_data(self, data):
        self.clear()
        self.current_index = -1
        i = 0
        for row in data:
            if not row.get("value"):
                continue
            if row["role"] == "hidden":
                continue
            self.cdata.append(row["value"])

            self.buttons.append(QPushButton(row.get("alias", row["value"]) ))
            self.buttons[-1].setToolTip("<p>{}</p>".format(row["description"]) if row.get("description") else "")
            self.buttons[-1].setCheckable(row["role"] in ["option", "header"])
            self.buttons[-1].setAutoExclusive(True)
            self.buttons[-1].clicked.connect(functools.partial(self.switch, i))
            self.layout.addWidget(self.buttons[-1])
            i+= 1


    def switch(self, index):
        self.current_index = index

    def set_value(self, value):
        value = str(value)

        if not value and self.cdata and self.cdata[0] == "0":
            value = "0"

        for i, val in enumerate(self.cdata):
            if val == value:
                self.buttons[i].setChecked(True)
                self.current_index = i
                break
        else:
            self.current_index = -1
            for button in self.buttons:
                button.setAutoExclusive(False);
                button.setChecked(False);
                button.setAutoExclusive(True);
        self.default = self.get_value()

    def get_value(self):
        if self.current_index == -1:
            return ""
        return str(self.cdata[self.current_index])

    def setReadOnly(self, val):
        for w in self.buttons:
            w.setEnabled(not val)


class FireflyBoolean(QCheckBox):
    def __init__(self, parent, **kwargs):
        super(FireflyBoolean, self).__init__(parent)
        self.default = self.get_value()

    def setReadOnly(self, val):
        self.setEnabled(not val)

    def set_value(self, value):
        self.setChecked(bool(value))

    def get_value(self):
        return self.isChecked()


class FireflyList(CheckComboBox):
    def __init__(self, parent, **kwargs):
        super(FireflyList, self).__init__(parent, placeholderText="")
        self.cdata = []
        if kwargs.get("data", []):
            self.set_data(kwargs["data"])
        self.default = self.get_value()

    def setReadOnly(self, val):
        self.setEnabled(not val)

    def auto_data(self, key):
        data = format_select(key, -1, full=True)
        self.set_data(data)

    def set_data(self, data):
        self.clear()
        self.cdata = []
        i = 0
        for row in data:
            if row["role"] == "hidden":
                continue

            alias = row.get("alias", row["value"])
            self.addItem(alias)
            self.cdata.append(row["value"])

            self.setItemData(i, "<p>{}</p>".format(row["description"]) if row.get("description") else None, Qt.ToolTipRole)

            if row["role"] == "label":
                item = self.model().item(i)
                self.setItemData(i, fonts["bolditalic"], Qt.FontRole)
                item.setEnabled(False)
            else:
                self.model().item(i).setCheckable(True)
                if row["role"] == "header":
                    self.setItemData(i, fonts["bold"], Qt.FontRole)
                self.setItemCheckState(i, row.get("selected"))
            i+=1
        self.update()

    def set_value(self, value):
        if type(value) == str:
            value = [value]
        value = [str(v) for v in value]
        for i, val in enumerate(self.cdata):
            self.setItemCheckState(i, val in value)
        self.default = self.get_value()

    def get_value(self):
        result = []
        for i, val in enumerate(self.cdata):
            if self.itemCheckState(i):
                result.append(val)
        return result


class FireflyColorPicker(QPushButton):
    def __init__(self, parent, **kwargs):
        super(FireflyColorPicker, self).__init__(parent)
        self.color = 0
        self.clicked.connect(self.execute)

    def execute(self):
        color = int(QColorDialog.getColor(QColor(self.color)).rgb())
        self.set_value(color)

    def get_value(self):
        return self.color

    def set_value(self, value):
        self.color = value
        self.setStyleSheet("background-color: #{:06x}".format(self.color))

    def setReadOnly(self, stat):
        self.setEnabled(not stat)

#TODO

class FireflyRegions(FireflyNotImplementedEditor):
    pass

class FireflyFraction(FireflyNotImplementedEditor):
    pass


meta_editors = {
    STRING    : FireflyString,
    TEXT      : FireflyText,
    INTEGER   : FireflyInteger,
    NUMERIC   : FireflyNumeric,
    BOOLEAN   : FireflyBoolean,
    DATETIME  : FireflyDatetime,
    TIMECODE  : FireflyTimecode,
    REGIONS   : FireflyRegions,
    FRACTION  : FireflyFraction,
    SELECT    : FireflySelect,
    LIST      : FireflyList,
    COLOR     : FireflyColorPicker,
    "radio"   : FireflyRadio
}


class MetaEditor(QWidget):
    def __init__(self, parent, keys):
        super(MetaEditor, self).__init__(parent)
        self.inputs = {}
        self.defaults = {}

        layout = QFormLayout()

        i = 0
        for key, conf in keys:
            key_label = meta_types[key].alias(config.get("language","en"))
            key_description = meta_types[key].description(config.get("language", "en"))
            key_class = meta_types[key]["class"]
            key_settings = copy.copy(meta_types[key].settings)
            key_settings.update(conf)

            widget = key_settings.get("widget", key_class)

            self.inputs[key] = meta_editors.get(
                    widget,
                    FireflyNotImplementedEditor
                )(self, **key_settings)

            self.inputs[key].meta_key = key

            layout.addRow(key_label, self.inputs[key])
            layout.labelForField(self.inputs[key]).setToolTip("<p>{}</p>".format(key_description) if key_description else None)
            i+=1
        self.setLayout(layout)

    def keys(self):
        return self.inputs.keys()

    @property
    def meta(self):
        return {key : self[key] for key in self.keys()}

    def __getitem__(self, key):
        return self.inputs[key].get_value()

    def __setitem__(self, key, value):
        self.inputs[key].set_value(value)

    def setEnabled(self, stat):
        for w in self.inputs:
            self.inputs[w].setReadOnly(not stat)

    @property
    def changed(self):
        keys = []
        for key in self.keys():
            if self[key] != self.defaults.get(key, None):
                keys.append(key)
        return keys

    def set_defaults(self):
        self.defaults = {}
        for key in self.keys():
            self.defaults[key] = self[key]
