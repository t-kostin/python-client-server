# 1. Написать функцию host_ping(), в которой с помощью утилиты ping будет
# проверяться доступность сетевых узлов. Аргументом функции является список,
# в котором каждый сетевой узел должен быть представлен именем хоста или
# ip-адресом. В функции необходимо перебирать ip-адреса и проверять их
# доступность с выводом соответствующего сообщения («Узел доступен»,
# «Узел недоступен»). При этом ip-адрес сетевого узла должен создаваться
# с помощью функции ip_address().

from ipaddress import ip_address, IPv4Address
from subprocess import call
import os


def ping(host):
    call_args = ['ping', '-c' if os.name == 'posix' else '-n', '3', '']
    with open(os.devnull, 'w') as null:
        if isinstance(host, IPv4Address):
            call_args[3] = str(host)
        elif isinstance(host, str):
            call_args[3] = host
        else:
            return 1
        return call(call_args, stdout=null, stderr=null)


def host_ping(host_list: list) -> None:
    for host_name in host_list:
        availability = 'un' if ping(host_name) else ''
        print('Host %s %sreachable' % (host_name, availability))


def main():
    test_args = ['yandex.ru', ip_address('127.0.0.1'), ip_address('255.167.0.44')]
    host_ping(test_args)


if __name__ == '__main__':
    main()
