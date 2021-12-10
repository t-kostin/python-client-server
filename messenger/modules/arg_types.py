from re import fullmatch


def ip_address(address_string: str) -> str:
    pattern = r'(?a)(localhost)|' \
              r'(((\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])\.){3}' \
              r'(\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5]))'
    if fullmatch(pattern, address_string):
        return address_string
    else:
        raise ValueError


def port(port_string: str) -> int:
    result = int(port_string)
    if result < 1024 or result > 65535:
        raise ValueError
    return result
