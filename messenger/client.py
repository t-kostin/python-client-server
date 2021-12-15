import sys
import argparse
import time
import threading

from modules.arg_types import ip_address, port
from modules.messenger import JimClient
from loggers.client_log_config import CLIENT_LOG
from modules.constants import *


def sending(client):
    while True:
        recipient = input('Input recipient or\n-all send to all or\n'
                          '-exit disconnect and quit\n: ')
        if recipient == '-exit':
            break
        elif recipient == '':
            print('Recipient should not be empty.')
            continue
        text = input('Message: ')
        if text == '':
            print('Message should not be empty.')
            continue
        if recipient == '-all':
            client.send_to_all(text)
        else:
            client.send_message(recipient, text)


def listening(client):
    while client.active_session:
        client.listen()


def main():
    CLIENT_LOG.debug('Application Started')
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'user',
        type=str,
        help='User name. For testing valid names are user-1, user-2, user-3 and user-4',
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

    my_client = JimClient(args.ip_addr, args.port, CLIENT_LOG)
    my_client.connect()
    if my_client.send_presence(args.user, 'Online') != OK200:
        print(f'User {args.user} could not connect to the server')
        sys.exit()

    print(f'Client logged as {args.user}.')

    listening_thread = threading.Thread(
        target=listening,
        args=(my_client,),
        daemon=True,
    )
    sending_thread = threading.Thread(
        target=sending,
        args=(my_client,),
        daemon=True
    )
    listening_thread.start()
    sending_thread.start()

    while True:
        time.sleep(1)
        if not (listening_thread.is_alive() and sending_thread.is_alive()):
            break

    my_client.disconnect()


if __name__ == '__main__':
    main()
