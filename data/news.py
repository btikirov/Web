import datetime
import sqlalchemy
from sqlalchemy import orm
from .db_session import SqlAlchemyBase


association_table = sqlalchemy.Table(
    'news_to_categories',
    SqlAlchemyBase.metadata,
    sqlalchemy.Column('news', sqlalchemy.Integer,
                      sqlalchemy.ForeignKey('news.id')),
    sqlalchemy.Column('categories', sqlalchemy.Integer,
                      sqlalchemy.ForeignKey('categories.id'))
)


class News(SqlAlchemyBase):
    __tablename__ = 'news'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    title = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    content = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    created_date = sqlalchemy.Column(sqlalchemy.DateTime,
                                     default=datetime.datetime.now)
    is_private = sqlalchemy.Column(sqlalchemy.Boolean, default=True)

    user_id = sqlalchemy.Column(sqlalchemy.Integer,
                                sqlalchemy.ForeignKey("users.id"))
    user = orm.relation('User')

    categories = orm.relation("Category",
                              secondary="news_to_categories",
                              backref="news",
                              lazy='subquery')