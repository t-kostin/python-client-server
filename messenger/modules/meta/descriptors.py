from re import fullmatch


class PortDescriptor:

    def __init__(self, name, default=None):
        self.name = '_' + name
        self.type = int
        self.default = default if default else self.type

    def __get__(self, instance, cls):
        return getattr(instance, self.name, self.default)

    def __set__(self, instance, value):
        if not isinstance(value, self.type) or (value < 1024 or value > 65535):
            raise TypeError('Port should be integer from 1024 to 65535')
        setattr(instance, self.name, value)

    def __delete__(self, instance):
        raise AttributeError(f'Attribute {self.name} can not be deleted')


class IpAddressDescriptor:

    def __init__(self, name, default=None):
        self.name = '_' + name
        self.type = str
        self.default = default if default else self.type

    def __get__(self, instance, cls):
        return getattr(instance, self.name, self.default)

    def __set__(self, instance, address):
        pattern = r'(?a)(localhost)|' \
                  r'(((\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])\.){3}' \
                  r'(\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5]))'
        if not isinstance(address, self.type) or not fullmatch(pattern, address):
            raise TypeError('Not valid ip address')
        setattr(instance, self.name, address)

    def __delete__(self, instance):
        raise AttributeError(f'Attribute {self.name} can not be deleted')


def main_test():
    class TestClass:

        port = PortDescriptor('port', default=7777)
        address = IpAddressDescriptor('address', default='localhost')

        def __init__(self, port):
            self.port = port

    test = TestClass(2000)

    print(f'{test.port=}')
    print(f'{test.address=}')

    test.port = 7778
    test.address = '192.168.22.22'
    print(f'{test.port=}')
    print(f'{test.address=}')


if __name__ == '__main__':
    main_test()
