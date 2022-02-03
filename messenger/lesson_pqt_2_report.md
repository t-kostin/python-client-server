###Базы данных и PyQT. Урок 2. Отчет по метаклассам и использованию пакета dis

Поскольку классы *JimServer* и *JimClient* были созданы на основе одного класса - *Jim*, то было принято решение написать один общий метакласс и "обернуть" им *Jim*. Однако после этого начались проблемы. Вот так выглядело содержание операций, которые получал через *dis* (на примере *JimServer*):
```python
{'LOAD_ATTR': ['messenger',
               '_logger',
               '__name__',
               'clients',
               'SELECT_WAIT',
               'users',
               'timestamp'],
 'LOAD_GLOBAL': ['super',
                 'socket',
                 'AF_INET',
                 'SOCK_STREAM',
                 're',
                 'format_list',
                 'extract_stack',
                 'len',
                 'select',
                 'OSError',
                 'USER_LOGGED_OUT',
                 'USER_NAME',
                 'ERR402',
                 'WRONG_USER',
                 'TIME',
                 'ERR400',
                 'BAD_TIMESTAMP',
                 'DESTINATION',
                 'ERR404',
                 'USER_OFFLINE',
                 'KeyError',
                 'TypeError',
                 'INVALID_JSON'],
 'LOAD_METHOD': ['__init__',
                 'compile',
                 'search',
                 'debug',
                 'group',
                 'error',
                 'info',
                 'receive_data',
                 'process_requests',
                 'send_data',
                 'items',
                 'append',
                 'pop',
                 'update',
                 'process_request',
                 'error_response',
                 'remove',
                 'close']}
```

Пара интересных вещей с которыми пришлось разобраться:

####1. *AF_INET* и *SOCK_STREAM* находятся в *LOAD_GLOBAL*, а не, как предполагалось, в *LOAD_ATTR*.

После активного гугления, выяснилось, что для того, чтобы *AF_INET* и *SOCK_STREAM* попали в *LOAD_ATTR*, необходимо, чтобы строка импорта имела вид:
    
```python
import socket
```
Я же использую код
```python
from socket import socket, AF_INET, SOCK_STREAM
```
Изменил код проверки чтобы наличие *AF_INET* и *SOCK_STREAM* проверялось и в *LOAD_GLOBAL*, и в *LOAD_ATTR*.

####2. В сервере действительно нет метода *connect*, но в нем также нет методов *bind* и *listen*, хотя по факту они есть!

Нужно добавить, что метод *connect* в клиенте присутствовал, но не в *LOAD_GLOBAL*, а в *LOAD_METHOD*! Что совсем не проясняло ситуацию. После сравнения, какие методы и вызовы попали в список, а какие нет, выяснилось, что все, что "обернуто" декоратором *@log* экранируется от пакета *dis*, так как вызывается *@log*, уже в нем вызывается метод класса. Поэтому в *LOAD_METHOD* попадают все методы класса *JimServer* обернутые в *@log*. Помог найти решение метод *compile* неведомо откуда взявшийся в *LOAD_METHOD*, который я использовал только в декораторе.

Итак комментируем все логирования при помощи декоратора и получаем для *JimServer:*
```python
{'LOAD_ATTR': ['messenger',
               'server_sock',
               'address',
               'port',
               'REQUEST_QUEUE',
               'TIMEOUT',
               '_logger',
               'clients',
               'SELECT_WAIT',
               'users',
               'presence',
               'to_all',
               'message',
               'close_session',
               'timestamp'],
 'LOAD_GLOBAL': ['super',
                 'socket',
                 'AF_INET',
                 'SOCK_STREAM',
                 'OSError',
                 'select',
                 'USER_LOGGED_OUT',
                 'SEND_PRESENCE',
                 'SEND_TO_ALL',
                 'SEND_MESSAGE',
                 'CLOSE_SESSION',
                 'ACTION',
                 'KeyError',
                 'ERR400',
                 'INVALID_JSON',
                 'INVALID_ACTION',
                 'USER',
                 'USER_NAME',
                 'USER_LIST',
                 'ERR402',
                 'WRONG_USER',
                 'STATUS',
                 'len',
                 'NO_STATUS',
                 'TIME',
                 'BAD_TIMESTAMP',
                 'USER_LOGGED_IN',
                 'OK200',
                 'TypeError',
                 'DESTINATION',
                 'ERR404',
                 'USER_OFFLINE',
                 'CODE',
                 'ERROR',
                 'ALERT'],
 'LOAD_METHOD': ['__init__',
                 'bind',
                 'listen',
                 'settimeout',
                 'info',
                 'accept',
                 'append',
                 'process_clients',
                 'close',
                 'receive_data',
                 'process_requests',
                 'send_data',
                 'items',
                 'pop',
                 'update',
                 'process_request',
                 'error_response',
                 'ok_response',
                 'remove']}

``` 
Вот они, *bind* и *listen* под под кодом операции *LOAD_METHOD*. В списке остались методы класса, такие как *process_request*, *error_response*, которые вызываются другими методами этого же класса.

####3. В списке методов вызываемых из *JimClient* присутствует *listen*, который запрещен:
```python
{'LOAD_ATTR': ['messenger',
               'client_sock',
               'address',
               'port',
               '_logger',
               'active_session',
               'timestamp',
               'account_name',
               'ok_handler',
               'error_handler',
               'user_not_found',
               'message_handler'],
 'LOAD_GLOBAL': ['super',
                 'socket',
                 'AF_INET',
                 'SOCK_STREAM',
                 'ConnectionRefusedError',
                 'sys',
                 'ConnectionAbortedError',
                 'ConnectionError',
                 'ConnectionResetError',
                 'print',
                 'OSError',
                 'ACTION',
                 'CLOSE_SESSION',
                 'TIME',
                 'USER_NAME',
                 'SEND_PRESENCE',
                 'TYPE',
                 'STATUS',
                 'USER',
                 'SEND_MESSAGE',
                 'DESTINATION',
                 'MESSAGE',
                 'SEND_TO_ALL',
                 'OK200',
                 'ERR400',
                 'ERR402',
                 'ERR404',
                 'CODE',
                 'KeyError',
                 'ValueError',
                 'INVALID_JSON',
                 'len'],
 'LOAD_METHOD': ['__init__',
                 'connect',
                 'debug',
                 'critical',
                 'exit',
                 'receive',
                 'process_response',
                 'send',
                 'close',
                 'listen',
                 'error_handler',
                 'info',
                 'error']}
```
На самом деле никакой ошибки нет: в классе есть мой собственный метод *listen*, который вызывается внутри класса. Клиент ведь тоже слушает, что пришло от сервера. Отрефакторил его в *attend*. Теперь все Ok.

###Выводы

1. Процесс дизассемблирования, как и прочий реверс-инжиниринг, остался таким же сложным как и в годы моей юности. :-) Он требует творческого подхода и даже простейшие изменения в коде, который подвергаются дизассемблированию приводят к неудовлетворительным результатам.

2. Второй вывод делается из первого: очень просто проверить код другого программиста в автоматическом режиме с использованием метаклассов и *dis* не получится.
