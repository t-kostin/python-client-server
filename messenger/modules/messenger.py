import sys
from socket import socket, AF_INET, SOCK_STREAM
import time
import json
import logging
from .constants import *


class Jim:
    def __init__(self, logger: logging.Logger):
        self._logger = logger

    def send_message(self, sock, data):
        binary_data = json.dumps(data).encode('utf-8')
        self._logger.debug('JSON successfully encoded')
        sock.send(binary_data)

    def receive_message(self, sock) -> dict:
        try:
            binary_data = sock.recv(BUFFER_SIZE)
            message = json.loads(binary_data.decode('utf-8', errors='replace'))
            self._logger.debug('JSON successfully decoded')
            return message
        except json.JSONDecodeError:
            self._logger.error('JSON decode error')
            return {}

    @property
    def current_timestamp(self) -> float:
        self._logger.debug('Timestamp requested')
        return time.time()


class JimClient(Jim):

    def __init__(self, address: str, port: int, logger: logging.Logger) -> None:
        super().__init__(logger)
        self.address = address
        self.port = port

    def send_presence(self, account_name: str, status: str) -> None:
        client_sock = socket(AF_INET, SOCK_STREAM)
        try:
            client_sock.connect((self.address, self.port))
            self._logger.debug(f'Connected to server {self.address}:{self.port}')
        except ConnectionRefusedError:
            self._logger.critical(f'Server {self.address}:{self.port}'
                                  f' refusing to connect')
            sys.exit()
        message = {
            'action': PRESENCE,
            'time': self.current_timestamp,
            'type': 'status',
            'user': {
                'account_name': account_name,
                'status': status,
            },
        }
        self.send_message(client_sock, message)
        self._logger.debug('Presence message sent')
        answer = self.receive_message(client_sock)
        self._logger.debug('Answer received')
        self.process_response(answer)
        self._logger.debug('Answer processed')
        client_sock.close()

    def process_response(self, data: dict) -> None:
        handlers = {
            OK200: self.ok_handler,
            ERR400: self.error_handler,
            ERR402: self.error_handler,
        }
        try:
            handlers[data['code']](data)
        except KeyError or ValueError:
            self._logger.critical(INVALID_JSON)

    def ok_handler(self, data: dict) -> None:
        try:
            code = data['code']
            alert = 'no additional message provided' \
                if len(data['alert']) == 0 else 'message: ' + data['alert']
            self._logger.info(f'Ok ({code}): {alert}')
        except KeyError or ValueError:
            self._logger.critical(INVALID_JSON)

    def error_handler(self, data: dict) -> None:
        try:
            code = data['code']
            error = data['error']
            self._logger.error(f'Error ({code}): {error}')
        except KeyError or ValueError:
            self._logger.critical(INVALID_JSON)


class JimServer(Jim):
    REQUEST_QUEUE = 5

    def __init__(self, address: str, port: int, logger: logging.Logger) -> None:
        super().__init__(logger)
        self.server_sock = socket(AF_INET, SOCK_STREAM)
        self.server_sock.bind((address, port))
        self.server_sock.listen(self.REQUEST_QUEUE)
        self._logger.info(f'Server created and will be listen to port {port}')

    def listen(self) -> None:
        try:
            while True:
                client_sock, address = self.server_sock.accept()
                data = self.receive_message(client_sock)
                self._logger.debug('Message from client received')
                response = self.process_request(data)
                self._logger.debug('Message from client processed with '
                                   'code %(code)d', response)
                self.send_message(client_sock, response)
                self._logger.debug('Response to client sent')
                client_sock.close()
                self._logger.debug('Client sock closed')
        finally:
            self.server_sock.close()

    def process_request(self, data) -> dict:
        handlers = {
            PRESENCE: self.presence,
        }
        try:
            action = data['action']
        except KeyError:
            self._logger.error(f'{ERR400}: {INVALID_JSON}')
            return self.error_response(ERR400, INVALID_JSON)
        try:
            return handlers[action](data)
        except KeyError:
            self._logger.error(f'{ERR400}: {INVALID_JSON}')
            return self.error_response(ERR400, INVALID_ACTION)

    def presence(self, data) -> dict:
        try:
            account_name = data['user']['account_name']
            if account_name != 'guest':
                self._logger.error(f'{ERR402}: {WRONG_USER}')
                return self.error_response(ERR402, WRONG_USER)
            status = data['user']['status']
            if len(status) == 0:
                self._logger.error(f'{ERR400}: {NO_STATUS}')
                return self.error_response(ERR400, NO_STATUS)
            timestamp = data['time']
            if timestamp > self.current_timestamp:
                self._logger.error(f'{ERR400}: {BAD_TIMESTAMP}')
                return self.error_response(ERR400, BAD_TIMESTAMP)
            self._logger.info(f'200: User {account_name} is now have'
                              f' status {status}')
            return self.ok_response(OK200)
        except (KeyError, TypeError):
            self._logger.error(f'{ERR400}: {INVALID_JSON}')
            return self.error_response(ERR400, INVALID_JSON)

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
