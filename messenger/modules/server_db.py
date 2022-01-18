from datetime import datetime
from sqlalchemy import Table, Column
from sqlalchemy import Integer, String, DateTime
from sqlalchemy import create_engine, MetaData, ForeignKey
from sqlalchemy.orm import mapper, sessionmaker
from .constants import SERVER_DB


class ServerDB:

    class Users:

        def __init__(self, user_name, last_login):
            self.id = None
            self.name = user_name
            self.last_login = last_login

    class ActiveUsers:

        def __init__(self, user_id, ip_address, port, login_time):
            self.id = None
            self.user_id = user_id
            self.ip_address = ip_address
            self.port = port
            self.login_time = login_time

    class LoginHistory:

        def __init__(self, user_id, ip_address, port, login_time):
            self.id = None
            self.user_id = user_id
            self.ip_address = ip_address
            self.port = port
            self.login_time = login_time

    def __init__(self):
        self.db_engine = create_engine(SERVER_DB, echo=False, pool_recycle=7200)
        self.metadata = MetaData()

        users_table = Table(
            'users',
            self.metadata,
            Column('id', Integer, primary_key=True),
            Column('name', String(64), unique=True),
            Column('last_login', DateTime),
        )
        active_users_table = Table(
            'active_users',
            self.metadata,
            Column('id', Integer, primary_key=True),
            Column('user_id', ForeignKey('users.id'), unique=True),
            Column('ip_address', String(15)),
            Column('port', Integer),
            Column('login_time', DateTime),
        )
        login_history = Table(
            'login_history',
            self.metadata,
            Column('id', Integer, primary_key=True),
            Column('user_id', ForeignKey('users.id')),
            Column('ip_address', String(15)),
            Column('port', Integer),
            Column('login_time', DateTime),
        )

        self.metadata.create_all(self.db_engine)

        mapper(self.Users, users_table)
        mapper(self.ActiveUsers, active_users_table)
        mapper(self.LoginHistory, login_history)

        Session = sessionmaker(bind=self.db_engine)
        self.session = Session()
        self.session.query(self.ActiveUsers).delete()
        self.session.commit()

    def login(self, user_name, ip_address, port):
        request = self.session.query(self.Users).filter_by(name=user_name)
        current_time = datetime.now()

        if request.count():
            user = request.first()
            user.last_login = current_time
        else:
            user = self.Users(user_name, current_time)
            self.session.add(user)
            self.session.commit()

        active_user = self.ActiveUsers(user.id, ip_address, port, current_time)
        user_history = self.LoginHistory(user.id, ip_address, port, current_time)
        self.session.add(active_user)
        self.session.add(user_history)
        self.session.commit()

    def logout(self, user_name):
        user = self.session.query(self.Users).filter_by(name=user_name).first()
        self.session.query(self.ActiveUsers).filter_by(user_id=user.id).delete()
        self.session.commit()

    def user_list(self):
        return self.session.query(self.Users.name, self.Users.last_login).all()

    def active_user_list(self):
        return self.session.query(
            self.Users.name,
            self.ActiveUsers.ip_address,
            self.ActiveUsers.port,
            self.ActiveUsers.login_time,
        ).join(self.Users).all()

    def login_history(self, user_name=None):
        request = self.session.query(
            self.Users.name,
            self.LoginHistory.ip_address,
            self.LoginHistory.port,
            self.LoginHistory.login_time,
        ).join(self.Users)

        if user_name:
            request = request.filter(self.Users.name == user_name)

        return request.all()


if __name__ == '__main__':
    test_db = ServerDB()
    # Выполняем "подключение" пользователя
    test_db.login('client_1', '192.168.1.4', 8080)
    test_db.login('client_2', '192.168.1.5', 7777)

    # Выводим список кортежей - активных пользователей
    print(' ---- test_db.active_users_list() ----')
    print(test_db.active_user_list())

    # Выполняем "отключение" пользователя
    test_db.logout('client_1')
    # И выводим список активных пользователей
    print(' ---- test_db.active_users_list() after logout client_1 ----')
    print(test_db.active_user_list())

    # Запрашиваем историю входов по пользователю
    print(' ---- test_db.login_history(client_1) ----')
    print(test_db.login_history('client_1'))

    # и выводим список известных пользователей
    print(' ---- test_db.users_list() ----')
    print(test_db.user_list())
