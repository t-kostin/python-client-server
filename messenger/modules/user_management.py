from PyQt5.QtWidgets import QDialog, QPushButton, QLineEdit, QComboBox, QLabel, QMessageBox
from PyQt5.QtCore import Qt
import hashlib
import binascii
from .constants import *


class AddUser(QDialog):

    def __init__(self, database, server):
        super().__init__()

        self.database = database
        self.server = server

        self.setWindowTitle('New user')
        self.setFixedSize(175, 183)
        self.setModal(True)
        self.setAttribute(Qt.WA_DeleteOnClose)

        self.label_username = QLabel('User name:', self)
        self.label_username.move(10, 10)
        self.label_username.setFixedSize(150, 15)

        self.client_name = QLineEdit(self)
        self.client_name.setFixedSize(154, 20)
        self.client_name.move(10, 30)

        self.label_passwd = QLabel('Password:', self)
        self.label_passwd.move(10, 55)
        self.label_passwd.setFixedSize(150, 15)

        self.client_passwd = QLineEdit(self)
        self.client_passwd.setFixedSize(154, 20)
        self.client_passwd.move(10, 75)
        self.client_passwd.setEchoMode(QLineEdit.Password)
        self.label_conf = QLabel('Confirm password:', self)
        self.label_conf.move(10, 100)
        self.label_conf.setFixedSize(150, 15)

        self.client_conf = QLineEdit(self)
        self.client_conf.setFixedSize(154, 20)
        self.client_conf.move(10, 120)
        self.client_conf.setEchoMode(QLineEdit.Password)

        self.btn_ok = QPushButton('Save', self)
        self.btn_ok.move(10, 150)
        self.btn_ok.clicked.connect(self.save_data)

        self.btn_cancel = QPushButton('Cancel', self)
        self.btn_cancel.move(90, 150)
        self.btn_cancel.clicked.connect(self.close)

        self.messages = QMessageBox()

        self.show()

    def save_data(self):
        """
        Метод проверки правильности ввода и сохранения в базу нового пользователя.
        """
        if not self.client_name.text():
            self.messages.critical(
                self, 'Error', 'User name is empty')
            return
        elif self.client_passwd.text() != self.client_conf.text():
            self.messages.critical(
                self, 'Error', 'Passwords does not match')
            return
        elif self.database.is_user_registered(self.client_name.text()):
            self.messages.critical(
                self, 'Error', 'User already exists')
            return
        else:
            passwd_bytes = self.client_passwd.text().encode('utf-8')
            salt = self.client_name.text().lower().encode('utf-8')
            passwd_hash = hashlib.pbkdf2_hmac(
                'sha512', passwd_bytes, salt, 10000)
            self.database.add_user(
                self.client_name.text(),
                binascii.hexlify(passwd_hash))
            self.messages.information(
                self, 'Message', 'User successfully added')
            # Рассылаем клиентам сообщение о необходимости обновить справочники
            self.server.users_updated(ADD_USR, self.client_name.text())
            self.close()


class DeleteUser(QDialog):

    def __init__(self, database, server):
        super().__init__()
        self.database = database
        self.server = server

        self.setFixedSize(350, 120)
        self.setWindowTitle('User delete')
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setModal(True)

        self.selector_label = QLabel(
            'Choose user:', self)
        self.selector_label.setFixedSize(200, 20)
        self.selector_label.move(10, 0)

        self.selector = QComboBox(self)
        self.selector.setFixedSize(200, 20)
        self.selector.move(10, 30)

        self.btn_ok = QPushButton('Delete', self)
        self.btn_ok.setFixedSize(100, 30)
        self.btn_ok.move(230, 20)
        self.btn_ok.clicked.connect(self.remove_user)

        self.btn_cancel = QPushButton('Cancel', self)
        self.btn_cancel.setFixedSize(100, 30)
        self.btn_cancel.move(230, 60)
        self.btn_cancel.clicked.connect(self.close)

        self.all_users_fill()
        self.show()

    def all_users_fill(self):

        self.selector.addItems([item[0]
                                for item in self.database.user_list()])

    def remove_user(self):

        self.database.remove_user(self.selector.currentText())
        if self.selector.currentText() in self.server.users:
            sock = self.server.users[self.selector.currentText()]
            self.server.remove_client(sock)
            del self.server.users[self.selector.currentText()]
        self.server.users_updated(DEL_USR, self.selector.currentText())
        self.close()
