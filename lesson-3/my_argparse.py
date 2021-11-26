from re import fullmatch
import sys


class ArgumentsParser():

    DEFAULT_IP = ''
    DEFAULT_PORT = 7777

    def __init__(self, args: list) -> None:
        parse = {
            '-a': {'handler': self.parse_ip_address, 'is_parsed': False},
            '-p': {'handler': self.parse_port, 'is_parsed': False},
        }
        self._ip_address = self.DEFAULT_IP
        self._port = self.DEFAULT_PORT
        for i in range(0, len(args), 2):
            try:
                if parse[args[i]]['is_parsed']:
                    print('Too many %s options' % args[i])
                    sys.exit()
                else:
                    parse[args[i]]['handler'](args[i + 1])
                    parse[args[i]]['is_parsed'] = True
            except KeyError:
                print('Invalid option', args[i])
                sys.exit()
            except IndexError:
                print('Value for option %s are missing' % args[i])
                sys.exit()

    def parse_ip_address(self, address_string: str) -> None:
        pattern = r'(?a)(localhost)|' \
                  r'(((\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])\.){3}' \
                  r'(\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5]))'
        match = fullmatch(pattern, address_string)
        if match:
            self._ip_address = address_string
        else:
            print('Invalid IP address')
            sys.exit()

    def parse_port(self, port_string: str) -> None:
        try:
            self._port = int(port_string)
            if self._port < 1024 or self._port > 65535:
                raise ValueError
        except ValueError:
            print('Port value should be an integer between 1024 and 65535')
            sys.exit()

    @property
    def ip_address(self) -> str:
        return self._ip_address

    @property
    def port(self) -> int:
        return self._port
