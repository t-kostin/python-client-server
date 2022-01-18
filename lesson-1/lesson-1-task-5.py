# 5. Выполнить пинг веб-ресурсов yandex.ru, youtube.com и
# преобразовать результаты из байтовового в строковый тип на кириллице.

from subprocess import Popen, PIPE
from chardet import detect
from sys import platform

ECHOES = '3'

if platform == 'win32':
    COUNT_OPTION = '-n'
else:
    COUNT_OPTION = '-c'

commands = [
    ['ping', COUNT_OPTION, ECHOES, 'yandex.ru'],
    ['ping', COUNT_OPTION, ECHOES, 'youtube.com'],
]

for command in commands:
    command_pipe = Popen(command, stdout=PIPE)
    for line in command_pipe.stdout:
        detected = detect(line)
        print(line.decode(detected['encoding']), end='')
