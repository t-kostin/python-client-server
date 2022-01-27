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


# def sending(client):
#     while True:
#         recipient = input('Input recipient or\n-all send to all or\n'
#                           '-users to get all users list or\n'
#                           '-contacts to get contact list or\n'
#                           '-add/-del to add/remove contact or\n'
#                           '-history to get message history or\n'
#                           '-exit to disconnect and quit\n: ')
#         if recipient == '-contacts':
#             for contact in client.get_contacts():
#                 print(contact)
#             continue
#         elif recipient == '-users':
#             for user in client.get_users():
#                 print(user)
#             continue
#         elif recipient == '-add':
#             contact = input('Contact name: ')
#             client.add_contact(contact)
#             continue
#         elif recipient == '-del':
#             contact = input('Contact name: ')
#             client.remove_contact(contact)
#             continue
#         elif recipient == '-history':
#             history = client.get_history()
#             for row in history:
#                 print(f'{row[3]} {row[0]:8} {row[1]:8} {row[2]}')
#             continue
#         elif recipient == '-exit':
#             client.disconnect()
#             break
#         elif recipient == '':
#             print('Recipient should not be empty.')
#             continue
#         text = input('Message: ')
#         if text == '':
#             print('Message should not be empty.')
#             continue
#         if recipient == '-all':
#             client.send_to_all(text)
#         else:
#             client.send_message(recipient, text)


def listening(client):
    while client.active_session:
        client.attend_with_lock()


def main():
    CLIENT_LOG.debug('Application Started')
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'user',
        type=str,
        nargs='?',
        help='User name',
    )
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
    user_name = args.user

    if user_name is None:
        user_login = UserNameInput()
        client_app.exec_()
        if user_login.ok_pressed:
            user_name = user_login.user_name.text()
            del user_login
        else:
            sys.exit()

    client_db = ClientDB(user_name)
    my_client = JimClient(args.ip_addr, args.port, client_db, CLIENT_LOG)
    my_client.connect()
    if my_client.send_presence(user_name, 'Online') != OK200:
        print(f'User {user_name} could not connect to the server')
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

    # while True:
    #     time.sleep(1)
    #     if not (listening_thread.is_alive() and sending_thread.is_alive()):
    #         break


if __name__ == '__main__':
    main()
