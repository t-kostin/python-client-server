from datetime import datetime
from sqlalchemy import Table, Column
from sqlalchemy import Integer, String, Text, DateTime
from sqlalchemy import create_engine, MetaData, ForeignKey
from sqlalchemy.orm import mapper, sessionmaker
from .constants import CLIENT_DB


class ClientDB:

    class Users:
        def __init__(self, user_name):
            self.id = None
            self.name = user_name

    class Contacts:
        def __init__(self, user_name):
            self.id = None
            self.name = user_name

    class MessageHistory:
        def __init__(self, from_user, to_user, message_text):
            self.id = None
            self.from_user = from_user
            self.to_user = to_user
            self.message = message_text
            self.date = datetime.now()

    def __init__(self, user_name):
        self.db_engine = create_engine(
            CLIENT_DB % user_name,
            echo=False,
            pool_recycle=7200,
            connect_args={'check_same_thread': False},
        )
        self.metadata = MetaData()

        users_table = Table(
            'users',
            self.metadata,
            Column('id', Integer, primary_key=True),
            Column('name', String(64)),
        )
        contacts = Table(
            'contacts',
            self.metadata,
            Column('id', Integer, primary_key=True),
            Column('name', String(64), unique=True)
        )
        message_history = Table(
            'message_history',
            self.metadata,
            Column('id', Integer, primary_key=True),
            Column('from_user', String(64)),
            Column('to_user', String(64)),
            Column('message', Text),
            Column('date', DateTime)
        )

        self.metadata.create_all(self.db_engine)

        mapper(self.Users, users_table)
        mapper(self.Contacts, contacts)
        mapper(self.MessageHistory, message_history)

        Session = sessionmaker(bind=self.db_engine)
        self.session = Session()
        self.session.query(self.Contacts).delete()
        self.session.commit()

    def add_contact(self, contact):
        if not self.session.query(self.Contacts).filter_by(name=contact).count():
            contact_row = self.Contacts(contact)
            self.session.add(contact_row)
            self.session.commit()

    def remove_contact(self, contact):
        self.session.query(self.Contacts).filter_by(name=contact).delete()
        self.session.commit()

    def add_users(self, users_list):
        self.session.query(self.Users).delete()
        for user in users_list:
            user_row = self.Users(user)
            self.session.add(user_row)
        self.session.commit()

    def save_message(self, from_user, to_user, message):
        message_row = self.MessageHistory(from_user, to_user, message)
        self.session.add(message_row)
        self.session.commit()

    def get_contacts(self):
        contact_rows = self.session.query(self.Contacts.name).all()
        return [contact_row[0] for contact_row in contact_rows]

    def get_users(self):
        user_rows = self.session.query(self.Users.name).all()
        return [user_row[0] for user_row in user_rows]

    def is_registered_user(self, user):
        return bool(self.session.query(self.Users).
                    filter_by(name=user).count())

    def is_contact(self, contact):
        return bool(self.session.query(self.Contacts).
                    filter_by(name=contact).count())

    def get_message_history(self, from_user=None, to_user=None):
        query = self.session.query(self.MessageHistory)
        if from_user:
            query = query.filter_by(from_user=from_user)
        if to_user:
            query = query.filter_by(to_user=to_user)
        return [(history_row.from_user,
                 history_row.to_user,
                 history_row.message,
                 history_row.date) for history_row in query.all()]
