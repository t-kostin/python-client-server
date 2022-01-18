# 2. Каждое из слов «class», «function», «method» записать
# в байтовом типе без преобразования в последовательность
# кодов (не используя методы encode и decode) и определить тип,
# содержимое и длину соответствующих переменных.

words = ['class', 'function', 'method']


def encode_with_eval(arg: str) -> None:
    converted = eval('b\'%s\'' % arg)
    print(
        f'Type of argument is {type(converted)}. Length is {len(converted)}.'
        f'\nValue is: {converted}\n'
    )


for word in words:
    encode_with_eval(word)
