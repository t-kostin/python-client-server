from datetime import datetime
from sqlalchemy import Table, Column
from sqlalchemy import Integer, String, DateTime
from sqlalchemy import create_engine, MetaData, ForeignKey
from sqlalchemy.orm import mapper, sessionmaker


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

    class UsersHistory:

        def __init__(self, user_id, sent=0, received=0):
            self.id = None
            self.user_id = user_id
            self.sent = sent
            self.received = received

    class Contacts:

        def __init__(self, user_id, contact_id):
            self.id = None
            self.user_id = user_id
            self.contact_id = contact_id

    def __init__(self, file_name):
        self.db_engine = create_engine(
            'sqlite:///' + file_name,
            echo=False,
            pool_recycle=7200,
            connect_args={'check_same_thread': False},
        )
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
        users_history = Table(
            'users_history',
            self.metadata,
            Column('id', Integer, primary_key=True),
            Column('user_id', ForeignKey('users.id')),
            Column('sent', Integer),
            Column('received', Integer),
        )
        contacts = Table(
            'contacts',
            self.metadata,
            Column('id', Integer, primary_key=True),
            Column('user_id', ForeignKey('users.id')),
            Column('contact_id', ForeignKey('users.id')),
        )

        self.metadata.create_all(self.db_engine)

        mapper(self.Users, users_table)
        mapper(self.ActiveUsers, active_users_table)
        mapper(self.LoginHistory, login_history)
        mapper(self.UsersHistory, users_history)
        mapper(self.Contacts, contacts)

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
            new_history_record = self.UsersHistory(user.id)
            self.session.add(new_history_record)

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

    def count_message(self, sender, recipient):
        sender_id = self.session.query(self.Users). \
            filter_by(name=sender).first().id
        recipient_id = self.session.query(self.Users). \
            filter_by(name=recipient).first().id

        sender_row = self.session.query(self.UsersHistory). \
            filter_by(user_id=sender_id).first()
        recipient_row = self.session.query(self.UsersHistory). \
            filter_by(user_id=recipient_id).first()

        sender_row.sent += 1
        recipient_row.received += 1

        self.session.commit()

    def count_send_to_all(self, sender, dict_of_active_users):
        sender_id = self.session.query(self.Users). \
            filter_by(name=sender).first().id
        sender_row = self.session.query(self.UsersHistory). \
            filter_by(user_id=sender_id).first()
        sender_row.sent += 1

        print(dict_of_active_users.keys())
        for recipient in dict_of_active_users:
            if sender != recipient:
                print(f'{recipient=}')
                recipient_id = self.session.query(self.Users). \
                    filter_by(name=recipient).first().id
                recipient_row = self.session.query(self.UsersHistory). \
                    filter_by(user_id=recipient_id).first()
                recipient_row.received += 1

        self.session.commit()

    def add_contact(self, user, contact):
        user_row = self.session.query(self.Users). \
            filter_by(name=user).first()
        contact_row = self.session.query(self.Users). \
            filter_by(name=contact).first()
        contact_not_exists = not self.session.query(self.Contacts). \
            filter_by(user_id=user_row.id, contact_id=contact_row.id).count()

        if contact_row and contact_not_exists:
            new_contact_row = self.Contacts(user_row.id, contact_row.id)
            self.session.add(new_contact_row)
            self.session.commit()

    def remove_contact(self, user, contact):
        contact_row = self.session.query(self.Users). \
            filter_by(name=contact).first()

        if contact_row:
            user_row = self.session.query(self.Users). \
                filter_by(name=user).first()
            self.session.query(self.Contacts). \
                filter_by(user_id=user_row.id, contact_id=contact_row.id). \
                delete()
            self.session.commit()

    def get_contacts(self, user):
        user_row = self.session.query(self.Users).filter_by(name=user).first()
        contact_rows = not self.session.query(self.Contacts, self.Users.name). \
            filter_by(user_id=user_row.id). \
            join(self.Users, self.Contacts.contact_id == self.Users.id). \
            all()
        list_of_contact_names = [contact[1] for contact in contact_rows]
        return list_of_contact_names

    def messages_history(self):
        return self.session.query(
            self.Users.name,
            self.Users.last_login,
            self.UsersHistory.sent,
            self.UsersHistory.received,
        ).join(self.Users).all()
