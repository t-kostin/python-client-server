import sys
from loggers.server_log_config import SERVER_LOG
from modules.my_argparse import ArgumentsParser
from modules.messenger import JimServer


def main():
    SERVER_LOG.debug('Application is started')
    arg = ArgumentsParser(sys.argv[1:])
    my_server = JimServer(arg.ip_address, arg.port, SERVER_LOG)
    my_server.listen()


if __name__ == '__main__':
    main()
