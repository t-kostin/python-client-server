import sys
from re import fullmatch
from modules.messenger import JimClient
from loggers.client_log_config import CLIENT_LOG


def main():
    CLIENT_LOG.debug('Application Started')
    parameters = sys.argv[1:]
    port = 7777
    if len(parameters) > 2:
        CLIENT_LOG.critical('Too many parameters')
        sys.exit()
    else:
        pattern = r'(?a)(localhost|((\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])\.){3}' \
                  r'(\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5]))'
        try:
            match = fullmatch(pattern, parameters[0])
        except IndexError:
            CLIENT_LOG.critical('Mandatory parameter <ip address> is missing.')
            sys.exit()
        if match:
            ip_address = match.group(1)
        else:
            CLIENT_LOG.critical('Invalid format of ip address')
            sys.exit()
        try:
            port = int(parameters[1])
            if port < 1024 or port > 65535:
                raise ValueError
        except ValueError:
            CLIENT_LOG.critical('Port value should be an integer between 1024 and 65535')
            sys.exit()
        except IndexError:
            pass
    my_client = JimClient(ip_address, port, CLIENT_LOG)
    my_client.send_presence('user', 'Online')

    my_client = JimClient(ip_address, port, CLIENT_LOG)
    my_client.send_presence('guest', '')
    
    my_client = JimClient(ip_address, port, CLIENT_LOG)
    my_client.send_presence('guest', 'Busy!')


if __name__ == '__main__':
    main()
