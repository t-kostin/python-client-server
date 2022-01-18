import sys
from socket import socket, AF_INET, SOCK_STREAM
import time
import json
from select import select
from .constants import *
from .decorators import log
from .meta.descriptors import PortDescriptor, IpAddressDescriptor
from .server_db import ServerDB


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

    port = PortDescriptor('port', 7777)
    address = IpAddressDescriptor('address', 'localhost')

    def __init__(self, logger):
        self._logger = logger

    @staticmethod
    def send(sock, data):
        binary_data = json.dumps(data).encode('utf-8')
        sock.send(binary_data)

    # @log
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

    # @log
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

    def attend(self):
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

    # @log
    def disconnect(self):
        message = {
            ACTION: CLOSE_SESSION,
            TIME: self.timestamp,
            USER_NAME: self.account_name,
        }
        self.send(self.client_sock, message)
        time.sleep(1)
        self.client_sock.close()
        self.active_session = False

    # @log
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
        return self.attend()

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

    # @log
    def process_response(self, data: dict) -> None:
        handlers = {
            OK200: self.ok_handler,
            ERR400: self.error_handler,
            ERR401: self.error_handler,
            ERR403: self.user_already_online,
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

    def user_already_online(self, data):
        self._logger.critical(data[ALERT])
        self.active_session = False
        self.client_sock.close()
        sys.exit(1)

    # @log
    def ok_handler(self, data: dict):
        try:
            code = data[CODE]
            alert = 'no additional message provided' \
                if len(data['alert']) == 0 else 'message: ' + data[ALERT]
            self._logger.info(f'Ok ({code}): {alert}')
            return code
        except (KeyError, ValueError):
            self._logger.critical(INVALID_JSON)
            self.client_sock.close()
            self.active_session = False
            sys.exit(1)

    # @log
    def error_handler(self, data: dict):
        try:
            code = data[CODE]
            error = data[ALERT]
            self._logger.error(f'Error ({code}): {error}')
            return code
        except (KeyError, ValueError):
            self._logger.critical(INVALID_JSON)
            self.client_sock.close()
            self.active_session = False
            sys.exit(1)

    # @log
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

    def __init__(self, address: str, port: int, dbase: ServerDB, logger=EmptyLogger()) -> None:
        super().__init__(logger)
        self.clients = []
        self.users = {}
        self.server_sock = socket(AF_INET, SOCK_STREAM)
        self.address = address
        self.port = port
        self.dbase = dbase
        self.server_running = True

    def send_to_client(self, client_sock, data):
        try:
            self.send(client_sock, data)
        except OSError:
            self.close_session(client_sock)

    # @log
    def listen(self) -> None:
        self.server_sock.bind((self.address, self.port))
        self.server_sock.listen(self.REQUEST_QUEUE)
        self.server_sock.settimeout(self.TIMEOUT)
        self._logger.info(f'Server created and will be listen to port {self.port}')
        try:
            while self.server_running:
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
            self.process_requests(requests, clients_write)

    def process_requests(self, requests, clients_write):
        for client, data in requests.items():
            self.process_request(client, data, clients_write)

    @log
    def process_request(self, client, data, clients_write):
        handlers = {
            SEND_PRESENCE: self.presence,
            SEND_TO_ALL: self.to_all,
            SEND_MESSAGE: self.message,
            CLOSE_SESSION: self.close_session,
        }
        try:
            action = data[ACTION]
        except KeyError:
            self.response_and_close(client, ERR400, INVALID_JSON)
        try:
            handlers[action](client, data, clients_write)
        except KeyError:
            self.response_and_close(client, ERR400, INVALID_ACTION)

    @log
    def presence(self, client_sock, data, clients_write):
        if client_sock in clients_write:
            try:
                acc_name = data[USER][USER_NAME]
                if acc_name in self.users:
                    self.response_and_close(client_sock, ERR403, USER_ONLINE)
                elif len(data[USER][STATUS]) == 0:
                    self.response_and_close(client_sock, ERR400, NO_STATUS)
                elif data[TIME] > self.timestamp:
                    self.response_and_close(client_sock, ERR400, BAD_TIMESTAMP)
                else:
                    self.users.update({acc_name: client_sock})
                    acc_ip, acc_port = client_sock.getpeername()
                    self.dbase.login(acc_name, acc_ip, acc_port)
                    self._logger.info(USER_LOGGED_IN % acc_name)
                    self.response(client_sock, OK200)
            except (KeyError, TypeError):
                self.response_and_close(client_sock, ERR400, INVALID_JSON)

    def to_all(self, client, data, clients_write):
        for current_client in clients_write:
            if current_client != client:
                self.send_to_client(current_client, data)

    def message(self, client, data, *args):
        try:
            if data[USER_NAME] not in self.users:
                self.response_and_close(client, ERR401, WRONG_USER)
            elif data[TIME] > self.timestamp:
                self.response_and_close(client, ERR400, BAD_TIMESTAMP)
            elif data[DESTINATION] in self.users:
                self.send_to_client(self.users[data[DESTINATION]], data)
            else:
                self.response(client, ERR404, USER_OFFLINE)
        except (KeyError, TypeError):
            self.response_and_close(client, ERR400, INVALID_JSON)

    def close_session(self, client, *args):
        self.clients.remove(client)
        for user_name, user_sock in self.users.items():
            if client == user_sock:
                self.users.pop(user_name)
                self.dbase.logout(user_name)
                break
        client.close()

    @log
    def response_and_close(self, client, code: int, message: str):
        response_data = {
            CODE: code,
            TIME: self.timestamp,
            ALERT: message,
        }
        try:
            self.send(client, response_data)
        except OSError:
            pass
        finally:
            self.close_session(client)

    @log
    def response(self, client, code: int, message=''):
        response_data = {
            CODE: code,
            TIME: self.timestamp,
            ALERT: message,
        }
        self.send_to_client(client, response_data)

    def shutdown(self):
        self.server_running = False
