import sys
from my_argparse import ArgumentsParser
from messenger import JimServer

arg = ArgumentsParser(sys.argv[1:])
my_server = JimServer(arg.ip_address, arg.port)
my_server.listen()

# Expected output:
#
# Server created and will be listen to port 7777
# User guest is now have status Busy!
