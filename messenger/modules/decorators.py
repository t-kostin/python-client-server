# from functools import wraps
import re
from traceback import extract_stack, format_list


def log(func):
    def wrapper(self, *args, **kwargs):
        pattern = re.compile(r'(?a)File "[^"]+", (line \d+), in (\S+)\s')

        match = pattern.search(format_list(extract_stack(limit=2))[0])
        if match:
            self._logger.debug(f'Function <{func.__name__}> called from '
                               f'function <{match.group(2)}> '
                               f'({match.group(1)}) with '
                               f'arguments {args}')
        else:
            self._logger.debug(f'Function <{func.__name__}> called '
                               f'with arguments {args}')
        result = func(self, *args, **kwargs)
        return result
    return wrapper
