from socket import socket, AF_INET, SOCK_STREAM
# from socket import SOL_SOCKET, SO_REUSEADDR
import time
import json

BUFFER_SIZE = 4096


class Jim:

    @staticmethod
    def send_message(sock, data):
        binary_data = json.dumps(data).encode('utf-8')
        sock.send(binary_data)

    @staticmethod
    def receive_message(sock) -> dict:
        try:
            binary_data = sock.recv(BUFFER_SIZE)
            message = json.loads(binary_data.decode('utf-8', errors='replace'))
            return message
        except json.JSONDecodeError:
            return {}

    @property
    def current_timestamp(self) -> int:
        return int(time.time())


class JimClient(Jim):

    def __init__(self, address: str, port: int) -> None:
        self.address = address
        self.port = port

    def send_presence(self, account_name: str, status: str) -> None:
        client_sock = socket(AF_INET, SOCK_STREAM)
        client_sock.connect((self.address, self.port))
        message = {
            'action': 'presence',
            'time': self.current_timestamp,
            'type': 'status',
            'user': {
                'account_name': account_name,
                'status': status,
            },
        }
        self.send_message(client_sock, message)
        answer = self.receive_message(client_sock)
        self.process_response(answer)
        client_sock.close()

    def process_response(self, answer: dict) -> None:
        handlers = {
            200: self.ok_handler,
            400: self.error_handler,
            402: self.error_handler,
        }
        try:
            handlers[answer['code']](answer)
        except KeyError or ValueError:
            print('Invalid JSON format')

    @staticmethod
    def ok_handler(data: dict) -> None:
        try:
            code = data['code']
            alert = 'no additional message provided' \
                if len(data['alert']) == 0 else 'message: ' + data['alert']
            print(f'Ok ({code}) received with {alert}.')
        except KeyError or ValueError:
            print('Invalid JSON format')

    @staticmethod
    def error_handler(data: dict) -> None:
        try:
            code = data['code']
            error = data['error']
            print(f'Error ({code}) received with message: {error}.')
        except KeyError or ValueError:
            print('Invalid JSON format')


class JimServer(Jim):
    REQUEST_QUEUE = 5

    def __init__(self, address: str, port: int) -> None:
        self.server_sock = socket(AF_INET, SOCK_STREAM)
        self.server_sock.bind((address, port))
        # для переиспользования сокета
        # self.server_sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.server_sock.listen(self.REQUEST_QUEUE)
        print('Server created and will be listen to port 7777')

    def listen(self) -> None:
        try:
            while True:
                client_sock, address = self.server_sock.accept()
                data = json.loads(client_sock.recv(BUFFER_SIZE).
                                  decode('utf-8'))
                response = self.process_request(data)
                self.send_message(client_sock, response)
                client_sock.close()
        finally:
            self.server_sock.close()

    def process_request(self, data) -> dict:
        handlers = {
            'presence': self.presence,
        }
        try:
            action = data['action']
        except KeyError:
            return self.error_response(400, 'Invalid JSON format')
        try:
            return handlers[action](data)
        except KeyError:
            return self.error_response(400, 'Invalid action')

    def presence(self, data) -> dict:
        try:
            account_name = data['user']['account_name']
            if account_name != 'guest':
                return self.error_response(402, 'Wrong account name')
            status = data['user']['status']
            if len(status) == 0:
                return self.error_response(400, 'No status provided')
            timestamp = data['time']
            if timestamp > self.current_timestamp:
                return self.error_response(400, 'Bad timestamp')
            print(f'User {account_name} is now have status {status}')
            return self.ok_response(200)
        except (KeyError, TypeError):
            return self.error_response(400, 'Invalid JSON format')

    def error_response(self, code: int, message: str) -> dict:
        response_data = {
            'code': code,
            'time': self.current_timestamp,
            'error': message,
        }
        return response_data

    def ok_response(self, code: int, message='') -> dict:
        response_data = {
            'code': code,
            'time': self.current_timestamp,
            'alert': message,
        }
        return response_data
