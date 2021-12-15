import sys
from socket import socket, AF_INET, SOCK_STREAM
import time
import json
from select import select
from .constants import *
from .decorators import log


class EmptyLogger:

    def critical(self, arg: str):
        pass

    def error(self, arg: str):
        pass

    def warning(self, arg: str):
        pass

    def info(self, arg: str):
        pass

    def debug(self, arg: str):
        pass


class Jim:
    def __init__(self, logger):
        self._logger = logger

    @log
    def send(self, sock, data):
        binary_data = json.dumps(data).encode('utf-8')
        sock.send(binary_data)

    @log
    def send_data(self, responses: dict, clients_all: list):
        for client, data in responses.items():
            try:
                self.send(client, data)
            except OSError:
                clients_all.remove(client)
                client.close()

    @log
    def receive(self, sock):
        try:
            binary_data = sock.recv(BUFFER_SIZE)
            if binary_data == b'':
                return None
            message = json.loads(binary_data.decode('utf-8', errors='replace'))
            return message
        except json.JSONDecodeError:
            self._logger.error('JSON decode error')
            return {}

    @log
    def receive_data(self, clients_to_read: list, clients_all: list) -> dict:
        data = {}
        for client in clients_to_read:
            try:
                client_data = self.receive(client)
                if client_data is None:
                    raise OSError
            except OSError:
                client.close()
                clients_all.remove(client)
            else:
                data[client] = client_data
        return data

    @property
    def timestamp(self) -> float:
        return time.time()


class JimClient(Jim):

    def __init__(self, address: str, port: int, logger=EmptyLogger()) -> None:
        super().__init__(logger)
        self.address = address
        self.port = port
        self.client_sock = socket(AF_INET, SOCK_STREAM)
        self.account_name = ''
        self.active_session = False

    def connect(self):
        try:
            self.client_sock.connect((self.address, self.port))
            self.active_session = True
            self._logger.debug(f'Connected to server {self.address}:{self.port}')
        except ConnectionRefusedError:
            self._logger.critical(f'Server {self.address}:{self.port}'
                                  f' refusing to connect')
            sys.exit()

    def listen(self):
        try:
            answer = self.receive(self.client_sock)
            if answer is None:
                raise ConnectionAbortedError
        except (ConnectionError, ConnectionResetError, ConnectionAbortedError):
            if not self.active_session:
                print('Connection to server is lost')
                sys.exit(1)
        except OSError:
            pass
        else:
            return self.process_response(answer)

    @log
    def disconnect(self):
        message = {
            ACTION: CLOSE_SESSION,
            TIME: self.timestamp,
            USER_NAME: self.account_name,
        }
        self.send(self.client_sock, message)
        self.client_sock.close()

    @log
    def send_presence(self, account_name: str, status: str):
        message = {
            ACTION: SEND_PRESENCE,
            TIME: self.timestamp,
            TYPE: STATUS,
            USER: {
                USER_NAME: account_name,
                STATUS: status,
            },
        }
        self.send(self.client_sock, message)
        self.account_name = account_name
        return self.listen()

    def send_message(self, recipient: str, text: str):
        message = {
            ACTION: SEND_MESSAGE,
            TIME: self.timestamp,
            USER_NAME: self.account_name,
            DESTINATION: recipient,
            MESSAGE: text,
        }
        self.send(self.client_sock, message)

    def send_to_all(self, text: str):
        message = {
            ACTION: SEND_TO_ALL,
            TIME: self.timestamp,
            USER_NAME: self.account_name,
            MESSAGE: text,
        }
        self.send(self.client_sock, message)

    @log
    def process_response(self, data: dict) -> None:
        handlers = {
            OK200: self.ok_handler,
            ERR400: self.error_handler,
            ERR402: self.error_handler,
            ERR404: self.user_not_found,
            SEND_TO_ALL: self.message_handler,
            SEND_MESSAGE: self.message_handler,
        }
        try:
            return handlers[data[CODE]](data)
        except (KeyError, ValueError):
            try:
                return handlers[data[ACTION]](data)
            except (KeyError, ValueError):
                self._logger.critical(INVALID_JSON)
                self.client_sock.close()
                self.active_session = False
                sys.exit(1)

    def user_not_found(self, data):
        print('\nUser not found')
        return self.error_handler(data)

    @log
    def ok_handler(self, data: dict):
        try:
            code = data['code']
            alert = 'no additional message provided' \
                if len(data['alert']) == 0 else 'message: ' + data['alert']
            self._logger.info(f'Ok ({code}): {alert}')
            return code
        except (KeyError, ValueError):
            self._logger.critical(INVALID_JSON)
            self.client_sock.close()
            self.active_session = False
            sys.exit(1)

    @log
    def error_handler(self, data: dict):
        try:
            code = data['code']
            error = data['error']
            self._logger.error(f'Error ({code}): {error}')
            return code
        except (KeyError, ValueError):
            self._logger.critical(INVALID_JSON)
            self.client_sock.close()
            self.active_session = False
            sys.exit(1)

    @log
    def message_handler(self, data: dict):
        try:
            print(f'\n{data[USER_NAME]}: {data[MESSAGE]}')
        except KeyError:
            self._logger.critical(INVALID_JSON)
            self.client_sock.close()
            self.active_session = False
            sys.exit(1)


class JimServer(Jim):
    REQUEST_QUEUE = 5
    TIMEOUT = 1
    SELECT_WAIT = 0

    def __init__(self, address: str, port: int, logger=EmptyLogger()) -> None:
        super().__init__(logger)
        self.clients = []
        self.users = {}
        self.server_sock = socket(AF_INET, SOCK_STREAM)
        self.server_sock.bind((address, port))
        self.server_sock.listen(self.REQUEST_QUEUE)
        self.server_sock.settimeout(self.TIMEOUT)
        self._logger.info(f'Server created and will be listen to port {port}')

    @log
    def listen(self) -> None:
        try:
            while True:
                try:
                    client_sock, address = self.server_sock.accept()
                except OSError:
                    pass
                else:
                    self.clients.append(client_sock)
                finally:
                    if self.clients:
                        self.process_clients()
        finally:
            self.server_sock.close()

    def process_clients(self):
        clients_read = []
        clients_write = []
        try:
            clients_read, clients_write, errors = select(
                self.clients,
                self.clients,
                [],
                self.SELECT_WAIT,
            )
        except OSError:
            pass
        if clients_read:
            requests = self.receive_data(clients_read, self.clients)
            responses = self.process_requests(requests, clients_write)
            self.send_data(responses, self.clients)
            users_to_remove = []
            for user, client in self.users.items():
                if client not in self.clients:
                    users_to_remove.append(user)
            for user in users_to_remove:
                self._logger.info(USER_LOGGED_OUT % user)
                self.users.pop(user)

    def process_requests(self, requests, clients_write):
        responses = {}
        for client, data in requests.items():
            responses.update(self.process_request(client, data, clients_write))
        return responses

    @log
    def process_request(self, client, data, clients_write) -> dict:
        handlers = {
            SEND_PRESENCE: self.presence,
            SEND_TO_ALL: self.to_all,
            SEND_MESSAGE: self.message,
            CLOSE_SESSION: self.close_session,
        }
        try:
            action = data[ACTION]
        except KeyError:
            return self.error_response(client, ERR400, INVALID_JSON)
        try:
            return handlers[action](client, data, clients_write)
        except KeyError:
            return self.error_response(client, ERR400, INVALID_ACTION)

    @log
    def presence(self, client, data, clients_write) -> dict:
        if client in clients_write:
            try:
                account_name = data[USER][USER_NAME]
                if account_name not in USER_LIST:
                    return self.error_response(client, ERR402, WRONG_USER)
                status = data[USER][STATUS]
                if len(status) == 0:
                    return self.error_response(client, ERR400, NO_STATUS)
                timestamp = data[TIME]
                if timestamp > self.timestamp:
                    return self.error_response(client, ERR400, BAD_TIMESTAMP)
                self.users.update({account_name: client})
                self._logger.info(USER_LOGGED_IN % account_name)
                return self.ok_response(client, OK200)
            except (KeyError, TypeError):
                return self.error_response(client, ERR400, INVALID_JSON)

    def to_all(self, client, data, clients_write) -> dict:
        response = {}
        for current_client in clients_write:
            if current_client != client:
                response[current_client] = data
        return response

    def message(self, client, data, *args):
        try:
            account_name = data[USER_NAME]
            if account_name not in self.users:
                return self.error_response(client, ERR402, WRONG_USER)
            timestamp = data[TIME]
            if timestamp > self.timestamp:
                return self.error_response(client, ERR400, BAD_TIMESTAMP)
            recipient = data[DESTINATION]
            if recipient in self.users:
                return {self.users[recipient]: data}
            return self.error_response(client, ERR404, USER_OFFLINE)
        except (KeyError, TypeError):
            return self.error_response(client, ERR400, INVALID_JSON)

    def close_session(self, client, *args):
        self.clients.remove(client)
        client.close()
        return {}

    @log
    def error_response(self, client, code: int, message: str) -> dict:
        response_data = {
            client: {
                CODE: code,
                TIME: self.timestamp,
                ERROR: message,
            }
        }
        return response_data

    @log
    def ok_response(self, client, code: int, message='') -> dict:
        response_data = {
            client: {
                CODE: code,
                TIME: self.timestamp,
                ALERT: message,
            }
        }
        return response_data
