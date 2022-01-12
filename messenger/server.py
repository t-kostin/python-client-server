import argparse
import threading
from modules.arg_types import ip_address, port
from loggers.server_log_config import SERVER_LOG
from modules.messenger import JimServer
from modules.server_db import ServerDB


def server_run(server):
    server.listen()


def main():
    SERVER_LOG.debug('Application is started')
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-a',
        type=ip_address,
        default='localhost',
        dest='ip_addr',
        help='valid server IP address: ddd.ddd.ddd.ddd or localhost',
    )
    parser.add_argument(
        '-p',
        type=port,
        default=7777,
        dest='port',
        help='server port: integer from 1024 to 65535',
    )
    args = parser.parse_args()
    server_db = ServerDB()
    my_server = JimServer(args.ip_addr, args.port, server_db, SERVER_LOG)
    server_thread = threading.Thread(
        target=server_run,
        args=(my_server,),
        daemon=True,
    )
    server_thread.start()
    while True:
        command = input('-users to print all registered users\n'
                        '-active to print connected users\n'
                        '-history <user> to print log history\n'
                        '-exit to shutdown server and quit\n: ').split()
        if command[0] == '-users':
            request = sorted(server_db.user_list(), key=lambda x: x[0])
            for name, login in request:
                print('User %12s, last login %s' % (name, login))
        elif command[0] == '-active':
            request = sorted(server_db.active_user_list(), key=lambda x: x[0])
            for name, ip, prt, login in request:
                print('User %12s (%s:%s), logged in %s' % (name, ip, prt, login))
        elif command[0] == '-history':
            user = command[1] if len(command) > 1 else None
            request = sorted(server_db.login_history(user), key=lambda x: x[3],
                             reverse=True)
            for name, ip, prt, login in request:
                print('User %12s (%s:%s), logged in %s' % (name, ip, prt, login))
        elif command[0] == '-exit':
            print('Shutting down server...')
            my_server.shutdown()
            break
        else:
            print('Unknown command')

    server_thread.join()

if __name__ == '__main__':
    main()
