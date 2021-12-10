import unittest
from messenger import Jim, BUFFER_SIZE


class TestSendReceiveMessage(unittest.TestCase):

    def setUp(self) -> None:
        """
        Создаем класс Socket с методами send и recv
        для тестирования

        """

        class Socket:

            def __init__(self):
                self.buffer = b''

            def send(self, data: bytes) -> None:
                self.buffer = data

            def recv(self, buffer_size: int) -> bytes:
                return self.buffer[:buffer_size]

        self.socket = Socket()
        self.server = Jim()

    def test_send_receive(self):
        message = {
            'action': 'presence',
            'time': self.server.current_timestamp,
            'type': 'status',
            'user': {
                'account_name': 'guest',
                'status': 'I am busy!',
            },
        }
        self.server.send_message(self.socket, message)
        self.assertEqual(self.server.receive_message(self.socket), message)

    def test_very_long_message(self):
        message = {
            'action': 'presence',
            'time': self.server.current_timestamp,
            'type': 'status',
            'user': {
                'account_name': 'usr' * BUFFER_SIZE,
                'status': 'I am busy!',
            },
        }
        self.server.send_message(self.socket, message)
        self.assertEqual(self.server.receive_message(self.socket), {})

    def test_tuple(self):
        message = (1, 2, 3)
        self.server.send_message(self.socket, message)
        self.assertNotEqual(self.server.receive_message(self.socket), message)


if __name__ == '__main__':
    unittest.main()
