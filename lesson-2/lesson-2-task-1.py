"""
Задание на закрепление знаний по модулю CSV. Написать скрипт,
осуществляющий выборку определенных данных из файлов info_1.txt,
info_2.txt, info_3.txt и формирующий новый «отчетный» файл
в формате CSV. Для этого:

Создать функцию get_data(), в которой в цикле осуществляется перебор
файлов с данными, их открытие и считывание данных. В этой функции
из считанных данных необходимо с помощью регулярных выражений
извлечь значения параметров «Изготовитель системы»,  «Название ОС»,
«Код продукта», «Тип системы». Значения каждого параметра поместить
в соответствующий список. Должно получиться четыре списка — например,
os_prod_list, os_name_list, os_code_list, os_type_list. В этой же
функции создать главный список для хранения данных отчета — например,
main_data — и поместить в него названия столбцов отчета в виде списка:
«Изготовитель системы», «Название ОС», «Код продукта», «Тип системы».
Значения для этих столбцов также оформить в виде списка и поместить в
файл main_data (также для каждого файла);

Создать функцию write_to_csv(), в которую передавать ссылку на CSV-файл.
В этой функции реализовать получение данных через вызов функции
get_data(), а также сохранение подготовленных данных в соответствующий
CSV-файл;

Проверить работу программы через вызов функции write_to_csv().
"""

import re
import csv


def get_data() -> list:
    os_prod_list = []
    os_name_list = []
    os_code_list = []
    os_type_list = []
    main_data = [['Изготовитель системы', 'Название ОС', 'Код продукта',
                  'Тип системы']]
    for file_num in range(1, 4):
        file_name = f'data/info_{file_num}.txt'
        with open(file_name, 'r', encoding='cp1251') as source:
            data = source.read()
        result = re.search(r'Изготовитель системы:[ \t]*(\S+[ *\S+]*)\s*', data)
        os_prod_list.append('N/A' if result is None else result.group(1))
        result = re.search(r'Название ОС:[ \t]*(\S+[ *\S+]*)\s*\n*', data)
        os_name_list.append('N/A' if result is None else result.group(1))
        result = re.search(r'Код продукта:[ \t]*(\d{5}-OEM-\d{7}-\d{5})\s*', data)
        os_code_list.append('N/A' if result is None else result.group(1))
        result = re.search(r'Тип системы:[ \t]*(\S+[ *\S+]*)\s*', data)
        os_type_list.append('N/A' if result is None else result.group(1))
    # Не уверен что правильно понял формулировку "Значения для этих столбцов
    # также оформить в виде списка и поместить в файл main_data
    # (также для каждого файла)". Под файлами здесь понимаются списки?
    for i in range(0, 3):
        row = [os_prod_list[i], os_name_list[i], os_code_list[i],
               os_type_list[i]]
        main_data.append(row)
    return main_data


def write_to_csv(csv_file_io) -> None:
    data = get_data()
    csv_write = csv.writer(csv_file_io)
    for row in data:
        csv_write.writerow(row)


with open('data/report.csv', 'w', encoding='utf-8', newline='') as target:
    write_to_csv(target)
