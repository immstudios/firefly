from firefly import *

class LoginDialog(QDialog):
    def __init__(self):
        QDialog.__init__(self)
        self.setWindowTitle("Please log in")
        self.setStyleSheet(app_skin)
        self.login = QLineEdit(self)
        self.password = QLineEdit(self)
        self.password.setEchoMode(QLineEdit.Password)
        self.btn_login = QPushButton('Login', self)
        self.btn_login.clicked.connect(self.handleLogin)

        #for debug
        self.login.setText("demo")
        self.password.setText("demo")

        layout = QFormLayout(self)
        layout.addRow("Login", self.login)
        layout.addRow("Password", self.password)
        layout.addRow("", self.btn_login)

        self.result = False

    def handleLogin(self):
        result = api.login(
                login=self.login.text(),
                password=self.password.text()
            )
        if result.is_success and result.data:
            self.result = User(meta=result.data)
            self.close()
        else:
            QMessageBox.critical(self, "Error", result.message)
