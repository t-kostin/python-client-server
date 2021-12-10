from subprocess import Popen, CREATE_NEW_CONSOLE

CLIENTS = 5


def main():
    server = Popen('python server.py', creationflags=CREATE_NEW_CONSOLE)

    clients = []
    while True:
        answer = input(f'Start {CLIENTS} clients (s), Close clients (c), Close clients & exit (x): ')

        if answer == 's' and clients == []:
            for i in range(CLIENTS):
                mode = 'send' if i % 2 else 'listen'
                client = Popen(f'python client.py --mode {mode}', creationflags=CREATE_NEW_CONSOLE)
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
