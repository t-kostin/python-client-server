# 2. Написать функцию host_range_ping() для перебора ip-адресов из заданного
# диапазона. Меняться должен только последний октет каждого адреса.
# По результатам проверки должно выводиться соответствующее сообщение.

from ipaddress import ip_address, AddressValueError
from lesson_pqt_1_task_1 import host_ping


def get_ip_range(first: str, quantity: int):
    try:
        first = ip_address(first)
        last = first + (quantity - 1)
    except (ValueError, AddressValueError):
        print('Invalid ip address or range')
        return None
    if int(first) ^ int(last) > 0xFF:
        print('Only last octet of ip address should change in range')
        return None
    return [first + index for index in range(quantity)]


def host_range_ping(first: str, quantity: int) -> None:
    ip_range = get_ip_range(first, quantity)
    if ip_range is not None:
        host_ping(ip_range)


def main():
    first = input('Input first ip address in range: ')
    quantity = int(input('Input range of ip addresses to ping: '))
    host_range_ping(first, quantity)


if __name__ == '__main__':
    main()
