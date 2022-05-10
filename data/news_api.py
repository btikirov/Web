from flask_restful import reqparse, abort, Api, Resource
from flask import jsonify
from . import db_session
from .news import News
from .users import User


def abort_if_news_not_found(news_id):
    session = db_session.create_session()
    news = session.query(News).get(news_id)
    if not news:
        abort(404, message=f"News {news_id} not found")


class NewsResource(Resource):
    def get(self, news_id):
        abort_if_news_not_found(news_id)
        session = db_session.create_session()
        news = session.query(News).get(news_id)
        return jsonify({'news': news.to_dict(
            only=('title', 'content', 'user_id', 'is_private'))})


parser = reqparse.RequestParser()
parser.add_argument('title', required=True)
parser.add_argument('content', required=True)
parser.add_argument('is_private', required=True, type=bool)
parser.add_argument('user_id', required=True, type=int)
parser.add_argument('user_password', required=True, type=str)


class NewsListResource(Resource):
    def get(self):
        session = db_session.create_session()
        news = session.query(News).all()
        return jsonify({'news': [item.to_dict(
            only=('title', 'content', 'user.name')) for item in news]})

    def post(self):
        args = parser.parse_args()
        session = db_session.create_session()
        if session.query(User).filter(User.id == args['user_id']).first().check_password(args['user_password']):
            news = News(
                title=args['title'],
                content=args['content'],
                user_id=args['user_id'],
                is_private=args['is_private']
            )
            session.add(news)
            session.commit()
            return jsonify({'success': 'OK'})
        else:
            abort(401, message=f"Wrong password")