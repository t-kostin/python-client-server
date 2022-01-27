import dis
from pprint import pprint


class JimMeta(type):
    def __init__(cls, cls_name, names, cls_dict):
        if cls_name in ('JimServer', 'JimClient'):
            objects = {
                'LOAD_GLOBAL': [],
                'LOAD_ATTR': [],
                'LOAD_METHOD': [],
            }
            for func in cls_dict:
                try:
                    cls_object_iterator = dis.get_instructions(cls_dict[func])
                except TypeError:
                    pass
                else:
                    for i in cls_object_iterator:
                        if i.opname in objects and i.argval not in objects[i.opname]:
                            objects[i.opname].append(i.argval)
            # print(cls_name)
            # pprint(objects)
            # print('\n')
            if cls_name == 'JimClient':
                forbidden = ('accept', 'listen')
            else:
                forbidden = ('connect')
            for attr in ('SOCK_STREAM', 'AF_INET'):
                if attr not in objects['LOAD_GLOBAL'] and attr not in objects['LOAD_ATTR']:
                    raise TypeError('Invalid socket initialization')
            for method in forbidden:
                if method in objects['LOAD_METHOD']:
                     raise TypeError(f'Forbidden method <{method}> found in {cls_name}.')
        super().__init__(cls_name, names, cls_dict)
