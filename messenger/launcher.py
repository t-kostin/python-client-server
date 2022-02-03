from subprocess import Popen, CREATE_NEW_CONSOLE


def main():
    server = Popen('python server.py', creationflags=CREATE_NEW_CONSOLE)

    clients = []
    while True:
        answer = input(f'Start 3 clients (s), Close clients (c),'
                       f' Close clients & exit (x): ')

        if answer == 's' and clients == []:
            for user in range(3):
                client = Popen(f'python client.py',
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
