from subprocess import Popen, CREATE_NEW_CONSOLE
from modules.constants import USER_LIST


def main():
    server = Popen('python server.py', creationflags=CREATE_NEW_CONSOLE)

    clients = []
    while True:
        answer = input(f'Start {len(USER_LIST)} clients (s), Close clients (c),'
                       f' Close clients & exit (x): ')

        if answer == 's' and clients == []:
            for user in USER_LIST:
                client = Popen(f'python client.py {user}',
                               creationflags=CREATE_NEW_CONSOLE)
                clients.append(client)
        elif answer == 'c' or answer == 'x':
            for client in clients:
                client.kill()
                clients = []

        if answer == 'x':
            break

    server.kill()


if __name__ == '__main__':
    main()
