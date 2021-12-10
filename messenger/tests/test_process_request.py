import unittest
from ..modules.messenger import JimServer


class TestProcessRequest(unittest.TestCase):

    def setUp(self) -> None:
        """
        Создаем класс на основе сервера и перегуржаем init
        для тестирования и создаем тестовый сервер

        """
        class JimServerTest(JimServer):

            def __init__(self):
                pass

        self.server = JimServerTest()

    def test_ok_response(self) -> None:
        data = {
            'action': 'presence',
            'time': self.server.timestamp,
            'type': 'status',
            'user': {
                'account_name': 'guest',
                'status': 'I\'m online!',
            },
        }
        respond = {
            'code': 200,
            'alert': '',
            'time': self.server.timestamp
        }
        self.assertEqual(self.server.process_request(data), respond)

    def test_invalid_json(self) -> None:
        data = {}
        respond = {
            'code': 400,
            'error': 'Invalid JSON format',
            'time': self.server.timestamp
        }
        self.assertEqual(self.server.process_request(data), respond)

    def test_invalid_action(self) -> None:
        data = {
            'action': 'absence',
            'time': self.server.timestamp,
            'type': 'status',
            'user': {
                'account_name': 'guest',
                'status': 'I\'m online!',
            },
        }
        respond = {
            'code': 400,
            'error': 'Invalid action',
            'time': self.server.timestamp
        }
        self.assertEqual(self.server.process_request(data), respond)

    def test_no_account_provided(self) -> None:
        data = {
            'action': 'presence',
            'time': self.server.timestamp,
            'type': 'status',
        }
        respond = {
            'code': 400,
            'error': 'Invalid JSON format',
            'time': self.server.timestamp
        }
        self.assertEqual(self.server.process_request(data), respond)

    def test_wrong_account_name(self) -> None:
        data = {
            'action': 'presence',
            'time': self.server.timestamp,
            'type': 'status',
            'user': {
                'account_name': 'guest_001',
                'status': 'I\'m online!',
            },
        }
        respond = {
            'code': 402,
            'error': 'Wrong account name',
            'time': self.server.timestamp
        }
        self.assertEqual(self.server.process_request(data), respond)

    def test_no_status_provided(self) -> None:
        data = {
            'action': 'presence',
            'time': self.server.timestamp,
            'type': 'status',
            'user': {
                'account_name': 'guest',
                'status': '',
            },
        }
        respond = {
            'code': 400,
            'error': 'No status provided',
            'time': self.server.timestamp
        }
        self.assertEqual(self.server.process_request(data), respond)

    def test_status_as_a_number(self):
        data = {
            'action': 'presence',
            'time': self.server.timestamp,
            'type': 'status',
            'user': {
                'account_name': 'guest',
                'status': 5678,
            },
        }
        respond = {
            'code': 400,
            'error': 'Invalid JSON format',
            'time': self.server.timestamp
        }
        self.assertEqual(self.server.process_request(data), respond)

    def test_bad_timestamp(self):
        data = {
            'action': 'presence',
            'time': self.server.timestamp + 1,
            'type': 'status',
            'user': {
                'account_name': 'guest',
                'status': 'I\'m online!',
            },
        }
        respond = {
            'code': 400,
            'error': 'Bad timestamp',
            'time': self.server.timestamp
        }
        self.assertEqual(self.server.process_request(data), respond)

    def test_str_as_timestamp(self):
        data = {
            'action': 'presence',
            'time': str(self.server.timestamp),
            'type': 'status',
            'user': {
                'account_name': 'guest',
                'status': 'I\'m online!',
            },
        }
        respond = {
            'code': 400,
            'error': 'Invalid JSON format',
            'time': self.server.timestamp
        }
        self.assertEqual(self.server.process_request(data), respond)

    def test_no_timestamp(self):
        data = {
            'action': 'presence',
            'type': 'status',
            'user': {
                'account_name': 'guest',
                'status': 'I\'m online!',
            },
        }
        respond = {
            'code': 400,
            'error': 'Invalid JSON format',
            'time': self.server.timestamp
        }
        self.assertEqual(self.server.process_request(data), respond)

    def test_dict_keys_ok(self):
        data = {
            'action': 'presence',
            'time': self.server.timestamp,
            'type': 'status',
            'user': {
                'account_name': 'guest',
                'status': 'I\'m online!',
            },
        }
        keys_list = ['alert', 'code', 'time']
        keys_list.sort()
        result = list(self.server.process_request(data).keys())
        result.sort()
        self.assertEqual(result, keys_list)

    def test_dict_keys_err(self):
        data = {}
        keys_list = ['error', 'code', 'time']
        keys_list.sort()
        result = list(self.server.process_request(data).keys())
        result.sort()
        self.assertEqual(result, keys_list)


if __name__ == '__main__':
    unittest.main()
