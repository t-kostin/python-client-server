import sys
import argparse
import threading
from PyQt5.QtWidgets import QApplication

from modules.arg_types import ip_address, port
from modules.messenger import JimClient
from loggers.client_log_config import CLIENT_LOG
from modules.constants import *
from modules.client_db import ClientDB
from modules.gui_client import UserNameInput, ClientMainWindow


def listening(client):
    while client.active_session:
        client.attend_with_lock()


def main():
    CLIENT_LOG.debug('Application Started')
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'ip_addr',
        type=ip_address,
        nargs='?',
        default='localhost',
        help='valid server IP address: ddd.ddd.ddd.ddd or localhost',
    )
    parser.add_argument(
        'port',
        type=port,
        nargs='?',
        default=7777,
        help='server port: integer from 1024 to 65535',
    )
    args = parser.parse_args()

    client_app = QApplication(sys.argv)

    user_login = UserNameInput()
    client_app.exec_()
    if user_login.ok_pressed:
        user_name = user_login.user_name.text()
        user_pwd = user_login.password.text()
        del user_login
    else:
        sys.exit()

    client_db = ClientDB(user_name)
    my_client = JimClient(args.ip_addr, args.port, client_db, CLIENT_LOG)
    my_client.connect()
    if my_client.send_presence(user_name, user_pwd, 'Online') != OK200:
        print(f'User {user_name}: wrong user name or password')
        sys.exit()
    my_client.request_users()
    my_client.request_contacts()

    print(f'Client logged as {user_name}.')

    listening_thread = threading.Thread(
        target=listening,
        args=(my_client,),
        daemon=True,
    )
    listening_thread.start()

    main_window = ClientMainWindow(client_db, my_client)
    main_window.connect_to_signals(my_client)
    main_window.setWindowTitle('Text Messenger - %s' % user_name)
    client_app.exec_()

if __name__ == '__main__':
    main()
