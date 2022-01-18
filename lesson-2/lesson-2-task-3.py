"""
Задание на закрепление знаний по модулю yaml. Написать скрипт,
автоматизирующий сохранение данных в файле YAML-формата.
Для этого:

a) Подготовить данные для записи в виде словаря, в котором
первому ключу соответствует список, второму — целое число,
третьему — вложенный словарь, где значение каждого ключа —
это целое число с юникод-символом, отсутствующим
в кодировке ASCII (например, €);

b) Реализовать сохранение данных в файл формата YAML — например,
в файл file.yaml. При этом обеспечить стилизацию файла
с помощью параметра default_flow_style, а также установить
возможность работы с юникодом: allow_unicode = True;

c) Реализовать считывание данных из созданного файла и проверить,
совпадают ли они с исходными.
"""

import yaml

UTF_SYMBOLS = 'ἄ⇄◍∑∰'

DATA = {
    'first': [f'some string {i ** 2}' for i in range(6)],
    'second': 814,
    'third': {f'key_{i}': value for i, value in enumerate(UTF_SYMBOLS)}
}

with open('data/file.yaml', 'w', encoding='utf-8') as target:
    yaml.dump(DATA, target, allow_unicode=True, default_flow_style=False)

with open('data/file.yaml', 'r', encoding='utf-8') as source:
    data_loaded = yaml.load(source, Loader=yaml.FullLoader)

print('Dictionaries is%s equal.' % ('' if DATA == data_loaded else ' not'))
