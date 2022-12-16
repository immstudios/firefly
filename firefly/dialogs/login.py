from firefly.qt import QDialog, QLineEdit, QPushButton, QFormLayout, QMessageBox
from firefly.core.common import config
from firefly.qt import app_skin
from firefly.api import api


class LoginDialog(QDialog):
    def __init__(self, parent):
        QDialog.__init__(self, parent)
        self.setWindowTitle("Please log in")
        self.setStyleSheet(app_skin)
        self.login = QLineEdit(self)
        self.password = QLineEdit(self)
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.btn_login = QPushButton("Login", self)
        self.btn_login.clicked.connect(self.handleLogin)

        # for debug
        self.login.setText("")
        self.password.setText("")

        layout = QFormLayout(self)
        layout.addRow("Login", self.login)
        layout.addRow("Password", self.password)
        layout.addRow("", self.btn_login)

        self.result = False

    def handleLogin(self):
        response = api.login(
            username=self.login.text(),
            password=self.password.text(),
        )
        if response and response.get("accessToken", False):
            config["session_id"] = response["accessToken"]
            self.result = config["session_id"]
            self.close()
        else:
            QMessageBox.critical(self, "Error", response.message)


def show_login_dialog(parent=None):
    dlg = LoginDialog(parent)
    dlg.exec()
    return dlg.result
