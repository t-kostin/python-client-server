# 3. Определить, какие из слов «attribute», «класс», «функция»,
# «type» невозможно записать в байтовом типе.

words = ['attribute', 'класс', 'функция', 'type']


def check_word(arg: str) -> None:
    try:
        eval('b\'%s\'' % arg)
    except SyntaxError:
        print(f'Cannot use string {arg} to define bytes.')
    else:
        print(f'String {arg} can be used to define bytes.')


for word in words:
    check_word(word)
