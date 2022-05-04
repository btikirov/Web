import datetime

from flask import Flask, render_template, redirect, request, abort
from data.users import User
from data.news import News
from data.chats import Chat
from data.messages import Message
from data import db_session, news_api
from forms.user import RegisterForm, LoginForm, FindUserForm
from forms.new import NewsForm
from forms.chat import ChatForm
from forms.message import SendForm
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_restful import reqparse

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'

login_manager = LoginManager()
login_manager.init_app(app)


# all for news


@app.route("/")
@app.route("/news")
def news():
    db_sess = db_session.create_session()
    news = db_sess.query(News).filter(News.is_private != True)

    return render_template("index.html", news=news)


@app.route('/add_news', methods=['GET', 'POST'])
@login_required
def add_news():
    if not current_user.is_authenticated:
        return redirect("/login")

    form = NewsForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        news = News()
        news.title = form.title.data
        news.content = form.content.data
        news.is_private = form.is_private.data
        current_user.news.append(news)
        db_sess.merge(current_user)
        db_sess.commit()

        return redirect('/')
    return render_template('news.html', title='Добавление новости',
                           form=form)


@app.route('/edit_news/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_news(id):
    if not current_user.is_authenticated:
        return redirect("/login")

    form = NewsForm()
    if request.method == "GET":
        db_sess = db_session.create_session()
        news = db_sess.query(News).filter(News.id == id,
                                          News.user == current_user
                                          ).first()

        if news:
            form.title.data = news.title
            form.content.data = news.content
            form.is_private.data = news.is_private
        else:
            abort(404)
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        news = db_sess.query(News).filter(News.id == id,
                                          News.user == current_user
                                          ).first()

        if news:
            news.title = form.title.data
            news.content = form.content.data
            news.is_private = form.is_private.data
            db_sess.commit()
            return redirect('/')
        else:
            abort(404)
    return render_template('news.html',
                           title='Редактирование новости',
                           form=form
                           )


@app.route('/news_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def news_delete(id):
    if not current_user.is_authenticated:
        return redirect("/login")

    db_sess = db_session.create_session()
    news = db_sess.query(News).filter(News.id == id,
                                      News.user == current_user
                                      ).first()
    if news:
        db_sess.delete(news)
        db_sess.commit()
    else:

        abort(404)

    return redirect('/')


# all for user


@app.route("/users", methods=['GET', 'POST'])
def users():
    form = FindUserForm()
    if form.validate_on_submit():
        return redirect(f'/users/{form.search.data}')
        # form = FindUserForm()
    db_sess = db_session.create_session()
    users_list = db_sess.query(User).all()

    return render_template("users.html", users=users_list, form=form)


@app.route("/users/<string:data>", methods=['GET', 'POST'])
def search_for_users(data):
    db_sess = db_session.create_session()
    search = '%' + data + '%'
    name = search.split()[0]
    surname = search.split()[-1]
    users_list = db_sess.query(User).filter(
        (User.email.like(search)) | (User.username.like(search)) | (User.name.like(name)) | User.surname.like(
            surname))

    form = FindUserForm()
    if form.validate_on_submit():
        return redirect(f'/users/{form.search.data}')
        # form = FindUserForm()
    return render_template("users.html", users=users_list, form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(
            (User.email == form.email_or_username.data) | (User.username == form.email_or_username.data)).first()

        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter((User.email == form.email.data) | (User.username == form.username.data)).first():

            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        for ch in ['@', '#', '$', ' ']:
            if ch in form.username.data:

                return render_template('register.html', title='Регистрация',
                                       form=form,
                                       message="Имя пользователя не должно содержать символы @, #, $ и пробелы")
        user = User(
            username=form.username.data,
            name=form.name.data,
            surname=form.surname.data,
            email=form.email.data,
            about=form.about.data
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()

        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    user = db_sess.query(User).get(user_id)

    return user


# all for chats


@app.route("/chats")
def chats():
    if not current_user.is_authenticated:
        return redirect("/login")
    db_sess = db_session.create_session()
    db_sess.query(User).all()
    chats = current_user.chats
    return render_template("chats.html", chats=chats)


def create_chat(name, users, creator_username, unique_id=None):
    db_sess = db_session.create_session()
    chat = Chat()
    chat.name = name
    chat.unique_chat_href = unique_id
    db_sess.merge(chat)
    db_sess.commit()
    if chat.unique_chat_href is None:
        chat.unique_chat_href = str(chat.id)
        chat = db_sess.merge(chat)
        db_sess.commit()

    creator = db_sess.query(User).filter(User.username == creator_username).first()
    chat.admin = creator
    db_sess.add(chat)
    db_sess.commit()
    db_sess.close()
    db_sess = db_session.create_session()
    for chat_user in users:
        chat_user.chats.append(chat)
        db_sess.merge(chat_user)
        db_sess.commit()
    db_sess.merge(chat)
    db_sess.commit()



@app.route("/chats/<string:chat_id>", methods=['GET', 'POST'])
def open_chat(chat_id):
    if not current_user.is_authenticated:
        return redirect("/login")

    form = SendForm()
    find_chat = None
    id = chat_id
    if not chat_id.isdigit():
        names = sorted(list(chat_id.split('_')))
        id = '_'.join(names)
    user_chats = current_user.chats
    for chat in user_chats:
        if chat.unique_chat_href == id:
            find_chat = chat
            break

    if find_chat is None and not id.isdigit():
        db_sess = db_session.create_session()
        users = db_sess.query(User).filter(User.username.in_(list(id.split('_')))).all()

        if users:
            name = ' и '.join(id.split('_'))
            if id == current_user.username:
                name = "Заметки"
            create_chat(name, users, 'admin', unique_id=id)
            user_chats = current_user.chats
            for chat in user_chats:
                if chat.unique_chat_href == id:
                    find_chat = chat
                    break
        else:
            abort(404)
    elif find_chat is None:
        abort(404)

    if form.validate_on_submit():
        db_sess = db_session.create_session()
        message = Message()
        message.content = form.message.data
        message.sender = current_user
        message.chat = find_chat
        message = db_sess.merge(message)
        db_sess.add(message)
        db_sess.commit()

        return redirect(f"/chats/{id}")
    return render_template("chat_dialog.html", chat=find_chat, form=form)


@app.route("/add_chat", methods=["GET", "POST"])
def add_chat():
    if not current_user.is_authenticated:
        return redirect("/login")

    form = ChatForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        users = db_sess.query(User).filter(User.username.in_(list(form.users.data.split()) + [current_user.username])).all()

        create_chat(form.name.data, users, current_user.username)
        return redirect('/chats')
    return render_template('add_chat.html', title='Добавление чата',
                           form=form)


if __name__ == '__main__':
    db_session.global_init("db/blogs.db")
    app.register_blueprint(news_api.blueprint)
    db_sess = db_session.create_session()
    if not db_sess.query(User).filter(User.username == 'admin').first():
        user = User(
            username='admin',
            name='main',
            surname='admin',
            email='devyatyarov.06@mail.ru',
            about='Главный админ'
        )
        user.set_password('admin')
        db_sess.add(user)
        db_sess.commit()

    app.run()
