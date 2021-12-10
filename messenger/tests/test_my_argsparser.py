from ..modules.arg_types import ArgumentsParser
import unittest


class TestArgumentParser(unittest.TestCase):

    def setUp(self) -> None:
        self.args = ArgumentsParser([])

    def test_ip_parse(self):
        self.assertRaises(SystemExit, self.args.parse_ip_address, '192.257.129.1')

    def test_ip_parse_wrong_delimeter(self):
        self.assertRaises(SystemExit, self.args.parse_ip_address, '192-168-129-1')

    def test_ip_parse_comma(self):
        self.assertRaises(SystemExit, self.args.parse_ip_address, '192,168.129.1')

    def test_ip_parse_three_octets(self):
        self.assertRaises(SystemExit, self.args.parse_ip_address, '192.168.129')

    def test_ip_parse_four_dots(self):
        self.assertRaises(SystemExit, self.args.parse_ip_address, '192.168.129.1.')

    def test_ip_parse_three_dots(self):
        self.assertRaises(SystemExit, self.args.parse_ip_address, '192...1')

    def test_ip_parse_two_zero(self):
        self.assertRaises(SystemExit, self.args.parse_ip_address, '00.168.129.1')

    def test_ip_parse_alfa(self):
        self.assertRaises(SystemExit, self.args.parse_ip_address, '192d.168.129.1')

    def test_ip_parse_wrong_numbers(self):
        self.assertRaises(SystemExit, self.args.parse_ip_address, 'a0.b0.c0.d0')

    def test_ip_parse_random_string(self):
        self.assertRaises(SystemExit, self.args.parse_ip_address, 'some string')

    def test_ip_parse_no_parameter(self):
        self.assertRaises(SystemExit, self.args.parse_ip_address, '')

    def test_port_parser_too_low(self):
        self.assertRaises(SystemExit, self.args.parse_port, '80')

    def test_port_parser_too_high(self):
        self.assertRaises(SystemExit, self.args.parse_port, '65578')

    def test_port_parser_way_too_hight(self):
        self.assertRaises(SystemExit, self.args.parse_port, '10003304')

    def test_port_parser_not_int(self):
        self.assertRaises(SystemExit, self.args.parse_port, '1304.0')

    def test_port_parser_negative(self):
        self.assertRaises(SystemExit, self.args.parse_port, '-1304')

    def test_port_parser_not_number(self):
        self.assertRaises(SystemExit, self.args.parse_port, 'PORT')

    def test_port_parser_no_parameter(self):
        self.assertRaises(SystemExit, self.args.parse_port, '')


if __name__ == '__main__':
    unittest.main()

# test = ArgumentsParser(['-a', '192.168.0.1'])
# print(test.ip_address)
