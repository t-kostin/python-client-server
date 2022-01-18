# 3. Написать функцию host_range_ping_tab(), возможности которой основаны на
# функции из примера 2. Но в данном случае результат должен быть итоговым
# по всем ip-адресам, представленным в табличном формате (использовать
# модуль tabulate). Таблица должна состоять из двух колонок и выглядеть
# примерно так:

# Reachable  Unreachable
# --------   -----------
# 10.0.0.1   10.0.0.3
# 10.0.0.2   10.0.0.4
# --------   ----------

from tabulate import tabulate
from lesson_pqt_1_task_1 import ping
from lesson_pqt_1_task_2 import get_ip_range


def host_range_ping_tab(start: str, quantity: int) -> None:
    reach = 'Reachable'
    unreach = 'Unreachable'
    result = {
        reach: [],
        unreach: [],
    }
    ip_range = get_ip_range(start, quantity)
    if ip_range is not None:
        for addr in ip_range:
            key = unreach if ping(addr) else reach
            result[key].append(str(addr))
        print(tabulate(result, headers='keys'))


def main():
    first = input('Input first ip address in range: ')
    quantity = int(input('Input range of ip addresses to ping: '))
    host_range_ping_tab(first, quantity)


if __name__ == '__main__':
    main()
