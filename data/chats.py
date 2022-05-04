import datetime
import sqlalchemy
from sqlalchemy import orm
from .db_session import SqlAlchemyBase


class Chat(SqlAlchemyBase):
    __tablename__ = 'chats'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    unique_chat_href = sqlalchemy.Column(sqlalchemy.String)

    name = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    created_date = sqlalchemy.Column(sqlalchemy.DateTime,
                                     default=datetime.datetime.now)

    messages = orm.relation("Message", back_populates='chat', lazy='subquery')

    admin_id = sqlalchemy.Column(sqlalchemy.Integer,
                                sqlalchemy.ForeignKey("users.id"))

    admin = orm.relation('User')