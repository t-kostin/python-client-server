import argparse
import sys

from modules.arg_types import ip_address, port
from modules.messenger import JimClient
from loggers.client_log_config import CLIENT_LOG
from modules.constants import *


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
    parser.add_argument(
        '--mode',
        type=str,
        choices=('send', 'listen'),
        default='send',
        help='Mode of the client: send or listen',
    )
    args = parser.parse_args()

    my_client = JimClient(args.ip_addr, args.port, CLIENT_LOG)
    my_client.connect()
    my_client.send_presence('guest', 'Online')
    print(f'Client now {args.mode}')
    while True:
        if args.mode == 'send':
            text_to_send = input('Input text to send, to exit press enter without input: ')
            if text_to_send == '':
                break
            my_client.send_to_all('guest', text_to_send)

        if args.mode == 'listen':
            my_client.listen()

    my_client.disconnect()


if __name__ == '__main__':
    main()
