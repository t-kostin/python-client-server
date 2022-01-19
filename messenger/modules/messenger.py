import sys
from socket import socket, AF_INET, SOCK_STREAM, timeout
import time
import json
from select import select
from .constants import *
from .decorators import log
from .meta.descriptors import PortDescriptor, IpAddressDescriptor
from .server_db import ServerDB
from .client_db import ClientDB
from threading import Lock


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

    def __init__(self, address: str, port: int, dbase: ClientDB, logger=EmptyLogger()) -> None:
        super().__init__(logger)
        self.address = address
        self.port = port
        self.client_sock = socket(AF_INET, SOCK_STREAM)
        self.client_sock.settimeout(1.1)
        self.account_name = ''
        self.active_session = False
        self.sock_locker = Lock()
        self.dbase_locker = Lock()
        self.dbase = dbase

    def connect(self):
        try:
            self.client_sock.connect((self.address, self.port))
            self.active_session = True
            self._logger.debug(f'Connected to server {self.address}:{self.port}')
        except (ConnectionRefusedError, timeout):
            self._logger.critical(f'Server {self.address}:{self.port}'
                                  f' refusing to connect')
            sys.exit()

    def attend_with_lock(self):
        time.sleep(1)
        with self.sock_locker:
            self.attend()

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
            return ERR504
        else:
            return self.process_response(answer)

    # @log
    def disconnect(self):
        message = {
            ACTION: CLOSE_SESSION,
            TIME: self.timestamp,
            USER_NAME: self.account_name,
        }
        try:
            self.send(self.client_sock, message)
        except (ConnectionError, ConnectionResetError, ConnectionAbortedError):
            pass
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

    def request_users(self, account_name: str):
        message = {
            ACTION: GET_USERS,
            TIME: self.timestamp,
            USER_NAME: account_name,
        }
        self.send(self.client_sock, message)
        self.account_name = account_name
        user_list = self.attend()
        if isinstance(user_list, list):
            self.dbase.add_users(user_list)
        else:
            print('Server responded with error %s' % user_list)

    def request_contacts(self, account_name: str):
        message = {
            ACTION: GET_CONTACTS,
            TIME: self.timestamp,
            USER_NAME: account_name,
        }
        self.send(self.client_sock, message)
        self.account_name = account_name
        contact_list = self.attend()
        if isinstance(contact_list, list):
            for contact in contact_list:
                self.dbase.add_contact(contact)
        else:
            print('Server responded with error %s' % contact_list)

    def get_contacts(self):
        with self.dbase_locker:
            return self.dbase.get_contacts()

    def get_users(self):
        with self.dbase_locker:
            return self.dbase.get_users()

    def add_contact(self, contact):
        message = {
            ACTION: ADD_CONTACT,
            TIME: self.timestamp,
            USER_NAME: self.account_name,
            CONTACT_NAME: contact,
        }
        with self.dbase_locker:
            if self.dbase.is_registered_user(contact):
                self.dbase.add_contact(contact)
                with self.sock_locker:
                    self.send(self.client_sock, message)
                    answer = self.attend()
                    if answer != OK200:
                        print('Server can\'t add contact %s' % contact)
            else:
                print('Cannot add: %s is not registered user' % contact)

    def remove_contact(self, contact):
        message = {
            ACTION: REMOVE_CONTACT,
            TIME: self.timestamp,
            USER_NAME: self.account_name,
            CONTACT_NAME: contact,
        }
        with self.dbase_locker:
            if self.dbase.is_contact(contact):
                self.dbase.remove_contact(contact)
                with self.sock_locker:
                    self.send(self.client_sock, message)
                    answer = self.attend()
                    if answer != OK200:
                        print('Server can\'t remove contact %s' % contact)
            else:
                print('Cannot remove: %s not in contact list' % contact)

    def get_history(self, from_user=None, to_user=None):
        with self.dbase_locker:
            return self.dbase.get_message_history(from_user, to_user)

    def send_message(self, recipient: str, text: str):
        message = {
            ACTION: SEND_MESSAGE,
            TIME: self.timestamp,
            USER_NAME: self.account_name,
            DESTINATION: recipient,
            MESSAGE: text,
        }
        if self.dbase.is_registered_user(recipient):
            with self.sock_locker:
                self.send(self.client_sock, message)
            with self.dbase_locker:
                self.dbase.save_message(message[USER_NAME],
                                        message[DESTINATION],
                                        message[MESSAGE])
        else:
            print('User %s not found' % recipient)

    def send_to_all(self, text: str):
        message = {
            ACTION: SEND_TO_ALL,
            TIME: self.timestamp,
            USER_NAME: self.account_name,
            MESSAGE: text,
        }
        with self.sock_locker:
            self.send(self.client_sock, message)
        with self.dbase_locker:
            self.dbase.save_message(message[USER_NAME],
                                    '///TO_ALL',
                                    message[MESSAGE])

    # @log
    def process_response(self, data: dict) -> None:
        handlers = {
            OK200: self.ok_handler,
            OK202: self.user_list,
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
            with self.dbase_locker:
                self.dbase.save_message(data[USER_NAME],
                                        self.account_name,
                                        data[MESSAGE])
        except KeyError:
            self._logger.critical(INVALID_JSON)
            self.client_sock.close()
            self.active_session = False
            sys.exit(1)

    def user_list(self, data: dict):
        try:
            user_list = data[ALERT]
            if not isinstance(user_list, list):
                raise ValueError
            return user_list
        except (KeyError, ValueError):
            self._logger.critical(INVALID_JSON)
            self.client_sock.close()
            self.active_session = False
            sys.exit(1)


class JimServer(Jim):
    REQUEST_QUEUE = 5
    TIMEOUT = 0.5
    SELECT_WAIT = 0

    def __init__(self, address: str, port: int, dbase: ServerDB, logger=EmptyLogger()) -> None:
        super().__init__(logger)
        self.clients = []
        self.users = {}
        self.server_sock = socket(AF_INET, SOCK_STREAM)
        self.address = address
        self.port = port
        self.dbase = dbase
        self.thread_locker = Lock()
        self.shutdown_locker = Lock()
        self.clients_number_changed = False
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
            GET_CONTACTS: self.contacts,
            GET_USERS: self.registered_users,
            ADD_CONTACT: self.add_contact,
            REMOVE_CONTACT: self.remove_contact,
            CLOSE_SESSION: self.close_session,
        }
        try:
            action = data[ACTION]
            if data[TIME] > self.timestamp:
                self.response_and_close(client, ERR400, BAD_TIMESTAMP)
                return
        except KeyError:
            self.response_and_close(client, ERR400, INVALID_JSON)
            return
        try:
            handlers[action](client, data)
        except KeyError:
            self.response_and_close(client, ERR400, INVALID_ACTION)

    @log
    def presence(self, client_sock, data):
        try:
            acc_name = data[USER][USER_NAME]
            if acc_name in self.users:
                self.response_and_close(client_sock, ERR403, USER_ONLINE)
            elif len(data[USER][STATUS]) == 0:
                self.response_and_close(client_sock, ERR400, NO_STATUS)
            else:
                self.users.update({acc_name: client_sock})
                acc_ip, acc_port = client_sock.getpeername()
                self.dbase.login(acc_name, acc_ip, acc_port)
                self._logger.info(USER_LOGGED_IN % acc_name)
                self.response(client_sock, OK200)
                with self.thread_locker:
                    self.clients_number_changed = True
        except (KeyError, TypeError):
            self.response_and_close(client_sock, ERR400, INVALID_JSON)

    def to_all(self, client, data):
        for current_user, current_sock in self.users.items():
            if current_sock != client:
                self.send_to_client(current_sock, data)
        self.dbase.count_send_to_all(data[USER_NAME], self.users)

    def message(self, client, data):
        try:
            if data[USER_NAME] not in self.users:
                self.response_and_close(client, ERR401, WRONG_USER)
            elif data[DESTINATION] in self.users:
                self.send_to_client(self.users[data[DESTINATION]], data)
                self.dbase.count_message(data[USER_NAME], data[DESTINATION])
            else:
                self.response(client, ERR404, USER_OFFLINE)
        except (KeyError, TypeError):
            self.response_and_close(client, ERR400, INVALID_JSON)

    def registered_users(self, client, data):
        try:
            response_data = [user[0] for user in self.dbase.user_list()]
            self.response(client, OK202, response_data)
        except (KeyError, TypeError):
            self.response_and_close(client, ERR400, INVALID_JSON)

    def contacts(self, client, data):
        try:
            response_data = self.dbase.get_contacts(data[USER_NAME])
            self.response(client, OK202, response_data)
        except (KeyError, TypeError):
            self.response_and_close(client, ERR400, INVALID_JSON)

    def add_contact(self, client, data):
        try:
            self.dbase.add_contact(data[USER_NAME], data[CONTACT_NAME])
            self.response(client, OK200)
        except KeyError:
            self.response_and_close(client, ERR400, INVALID_JSON)

    def remove_contact(self, client, data):
        try:
            self.dbase.remove_contact(data[USER_NAME], data[CONTACT_NAME])
            self.response(client, OK200)
        except KeyError:
            self.response_and_close(client, ERR400, INVALID_JSON)

    def close_session(self, client, *args):
        self.clients.remove(client)
        for user_name, user_sock in self.users.items():
            if client == user_sock:
                self.users.pop(user_name)
                self.dbase.logout(user_name)
                break
        client.close()
        with self.thread_locker:
            self.clients_number_changed = True

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
        with self.shutdown_locker:
            self.server_running = False

    def clients_refreshed(self):
        with self.thread_locker:
            self.clients_number_changed = False
