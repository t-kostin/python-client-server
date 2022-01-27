from PyQt5.QtWidgets import QDialog, QPushButton, QLineEdit, QLabel
from PyQt5.QtWidgets import QMainWindow, qApp, QMessageBox
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QBrush, QColor
from PyQt5.QtCore import pyqtSlot, Qt
from .constants import *
from .ui_window import Ui_MainClientWindow
from .add_contact import AddContactDialog
from .del_contact import DelContactDialog
from .client_db import ClientDB
from .messenger import JimClient


class UserNameInput(QDialog):
    def __init__(self):
        super().__init__()

        self.ok_pressed = False

        self.setWindowTitle('Login')
        self.setFixedSize(175, 93)

        self.label = QLabel('Input user name:', self)
        self.label.move(10, 10)
        self.label.setFixedSize(150, 10)

        self.user_name = QLineEdit(self)
        self.user_name.setFixedSize(154, 20)
        self.user_name.move(10, 30)

        self.btn_ok = QPushButton('Start', self)
        self.btn_ok.move(10, 60)
        self.btn_ok.clicked.connect(self.click)

        self.btn_cancel = QPushButton('Exit', self)
        self.btn_cancel.move(90, 60)
        self.btn_cancel.clicked.connect(qApp.exit)

        self.show()

    def click(self):
        if self.user_name.text():
            self.ok_pressed = True
            qApp.exit()


class ClientMainWindow(QMainWindow):
    def __init__(self, database: ClientDB, transport: JimClient):
        super().__init__()
        self.database = database
        self.transport = transport
        self.ui = Ui_MainClientWindow()
        self.ui.setupUi(self)
        self.ui.menu_exit.triggered.connect(self.logout_user)
        self.ui.btn_send.clicked.connect(self.send_message)
        self.ui.btn_add_contact.clicked.connect(self.add_contact_window)
        self.ui.menu_add_contact.triggered.connect(self.add_contact_window)
        self.ui.btn_remove_contact.clicked.connect(self.delete_contact_window)
        self.ui.menu_del_contact.triggered.connect(self.delete_contact_window)
        self.contacts_model = None
        self.history_model = None
        self.messages = QMessageBox()
        self.current_chat = None
        self.ui.list_messages.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.ui.list_messages.setWordWrap(True)
        self.ui.list_contacts.doubleClicked.connect(self.select_active_user)

        self.clients_list_update()
        self.set_disabled_input()
        self.show()

    def logout_user(self):
        self.transport.disconnect()
        qApp.exit()

    # Деактивировать поля ввода
    def set_disabled_input(self):
        self.ui.label_new_message.setText('To select recipient, double-click on it in contact list')
        self.ui.text_message.clear()
        if self.history_model:
            self.history_model.clear()

        self.ui.btn_clear.setDisabled(True)
        self.ui.btn_send.setDisabled(True)
        self.ui.text_message.setDisabled(True)

    # Заполняем историю сообщений.
    def history_list_update(self):
        messages_list = sorted(self.database.get_message_history(self.current_chat), key=lambda el: el[3])
        if not self.history_model:
            self.history_model = QStandardItemModel()
            self.ui.list_messages.setModel(self.history_model)
        self.history_model.clear()
        length = len(messages_list)
        start_index = 0
        if length > 20:
            start_index = length - 20
        for i in range(start_index, length):
            item = messages_list[i]
            if item[0] == self.current_chat:
                mess = QStandardItem(f'Received {item[3].replace(microsecond=0)}:\n {item[2]}')
                mess.setEditable(False)
                mess.setBackground(QBrush(QColor(255, 213, 213)))
                mess.setTextAlignment(Qt.AlignLeft)
                self.history_model.appendRow(mess)
            else:
                mess = QStandardItem(f'Sent {item[3].replace(microsecond=0)}:\n {item[2]}')
                mess.setEditable(False)
                mess.setTextAlignment(Qt.AlignRight)
                mess.setBackground(QBrush(QColor(204, 255, 204)))
                self.history_model.appendRow(mess)
        self.ui.list_messages.scrollToBottom()

    # Функция обработчик даблклика по контакту
    def select_active_user(self):
        self.current_chat = self.ui.list_contacts.currentIndex().data()
        self.set_active_user()

    # Функция устанавливающяя активного собеседника
    def set_active_user(self):
        self.ui.label_new_message.setText(f'Input message for {self.current_chat}:')
        self.ui.btn_clear.setDisabled(False)
        self.ui.btn_send.setDisabled(False)
        self.ui.text_message.setDisabled(False)
        self.history_list_update()

    # Функция обновляющяя контакт лист
    def clients_list_update(self):
        contacts_list = self.database.get_contacts()
        self.contacts_model = QStandardItemModel()
        for i in sorted(contacts_list):
            item = QStandardItem(i)
            item.setEditable(False)
            self.contacts_model.appendRow(item)
        self.ui.list_contacts.setModel(self.contacts_model)

    # Функция добавления контакта
    def add_contact_window(self):
        global select_dialog
        select_dialog = AddContactDialog(self.transport, self.database)
        select_dialog.btn_ok.clicked.connect(lambda: self.add_contact_action(select_dialog))
        select_dialog.show()

    # Функция - обработчик добавления, сообщает серверу, обновляет таблицу и список контактов
    def add_contact_action(self, item):
        new_contact = item.selector.currentText()
        self.add_contact(new_contact)
        item.close()

    # Функция добавляющяя контакт в базы
    def add_contact(self, new_contact):
        try:
            self.transport.add_contact(new_contact)
        except OSError as err:
            if err.errno:
                self.messages.critical(self, 'Error', 'Connection to server lost')
                self.close()
            self.messages.critical(self, 'Error', 'Timeout error')
        else:
            self.database.add_contact(new_contact)
            new_contact = QStandardItem(new_contact)
            new_contact.setEditable(False)
            self.contacts_model.appendRow(new_contact)
            self.messages.information(self, 'Success', 'Contact successfully added')

    # Функция удаления контакта
    def delete_contact_window(self):
        global remove_dialog
        remove_dialog = DelContactDialog(self.database)
        remove_dialog.btn_ok.clicked.connect(lambda: self.delete_contact(remove_dialog))
        remove_dialog.show()

    # Функция обработчик удаления контакта, сообщает на сервер, обновляет таблицу контактов
    def delete_contact(self, item):
        selected = item.selector.currentText()
        try:
            self.transport.remove_contact(selected)
        except OSError as err:
            if err.errno:
                self.messages.critical(self, 'Error', 'Connection to server lost')
                self.close()
            self.messages.critical(self, 'Error', 'Timeout error')
        else:
            self.database.remove_contact(selected)
            self.clients_list_update()
            self.messages.information(self, 'Success', 'Contact deleted')
            item.close()
            if selected == self.current_chat:
                self.current_chat = None
                self.set_disabled_input()

    # Функция отправки собщения пользователю.
    def send_message(self):
        message_text = self.ui.text_message.toPlainText()
        self.ui.text_message.clear()
        if not message_text:
            return
        try:
            code = self.transport.send_message(self.current_chat, message_text)
        except OSError as err:
            if err.errno:
                self.messages.critical(self, 'Error', 'Connection to server lost')
                self.close()
            self.messages.critical(self, 'Error', 'Timeout error')
        except (ConnectionResetError, ConnectionAbortedError):
            self.messages.critical(self, 'Error', 'Connection to server lost')
            self.close()
        else:
            if code == ERR404:
                self.messages.warning(self, 'Warning', '%s offline, message does not sent' % self.current_chat)
            else:
                self.history_list_update()

    # Слот приёма нового сообщений
    @pyqtSlot(str)
    def message(self, sender):
        if sender == self.current_chat:
            self.history_list_update()
        else:
            if self.database.is_contact(sender):
                if self.messages.question(
                        self,
                        'New message',
                        f'Received new message from '
                        f'{sender}, switch to chat with him?',
                        QMessageBox.Yes,
                        QMessageBox.No) == QMessageBox.Yes:
                    self.current_chat = sender
                    self.set_active_user()
            else:
                if self.messages.question(
                        self,
                        'New message',
                        f'Received new message from {sender}.\n '
                        f'This user not in your contact list.\n'
                        f'Add user to contacts and switch to chat with it?',
                        QMessageBox.Yes,
                        QMessageBox.No) == QMessageBox.Yes:
                    self.add_contact(sender)
                    self.current_chat = sender
                    self.set_active_user()

    # Слот потери соединения
    @pyqtSlot()
    def connection_lost(self):
        self.messages.warning(self, 'Connection failure', 'Connection to server lost')
        self.close()

    def connect_to_signals(self, trans_obj):
        trans_obj.message_signal.connect(self.message)
        # trans_obj.connection_lost.connect(self.connection_lost)
