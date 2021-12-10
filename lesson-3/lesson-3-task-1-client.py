import sys
from re import fullmatch
from messenger import JimClient

parameters = sys.argv[1:]
port = 7777
if len(parameters) > 2:
    print('Too many parameters')
    sys.exit()
else:
    pattern = r'(?a)(localhost|((\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])\.){3}' \
              r'(\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5]))'
    try:
        match = fullmatch(pattern, parameters[0])
    except IndexError:
        print('Mandatory parameter <ip address> is missing.')
        sys.exit()
    if match:
        ip_address = match.group(1)
    else:
        print('Invalid parameter')
        sys.exit()
    try:
        port = int(parameters[1])
        if port < 1024 or port > 65535:
            raise ValueError
    except ValueError:
        print('Port value should be an integer between 1024 and 65535')
        sys.exit()
    except IndexError:
        pass

my_client = JimClient(ip_address, port)
my_client.send_presence('user', 'Online')

my_client = JimClient(ip_address, port)
my_client.send_presence('guest', '')

my_client = JimClient(ip_address, port)
my_client.send_presence('guest', 'Busy!')

# Expected output:
#
# Error (402) received with message: Wrong account name.
# Error (400) received with message: No status provided.
# Ok (200) received with no additional message provided.
