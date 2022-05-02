from flask import Flask, render_template, redirect, request, abort
from data.users import User
from data.news import News
from data.chats import Chat
from data import db_session, news_api
from forms.user import RegisterForm, LoginForm, FindUserForm
from forms.new import NewsForm
from forms.chat import ChatForm
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_restful import reqparse

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'

login_manager = LoginManager()
login_manager.init_app(app)


@app.route("/")
@app.route("/news")
def news():
    db_sess = db_session.create_session()
    news = db_sess.query(News).filter(News.is_private != True)
    return render_template("index.html", news=news)


@app.route("/users", methods=['GET', 'POST'])
def users():
    form = FindUserForm()
    db_sess = db_session.create_session()
    if form.validate_on_submit():
        return redirect(f'/users/{form.search.data}')
        #form = FindUserForm()
    users_list = db_sess.query(User)
    return render_template("users.html", users=users_list, form=form)


@app.route("/users/<string:data>", methods=['GET', 'POST'])
def search_for_users(data):
    print(1)
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


@app.route("/chats")
def chats():
    if current_user.is_authenticated:
        chats = current_user.chats
        for i in chats:
            print(i.admin.name)
        return render_template("chats.html", chats=chats)
    else:
        return redirect("/login")


@app.route("/chats/<int:id>")
def open_chat(id):
    pass


@app.route("/add_chat", methods=["GET", "POST"])
def add_chat():
    form = ChatForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        chat = Chat()
        chat.name = form.name.data
        current_user.chats_where_admin.append(chat)
        db_sess.commit()
        chat = db_sess.merge(chat)
        db_sess.commit()
        chat_users = db_sess.query(User).filter(User.username.in_(form.users.data.split(' ') + [current_user.username])).all()
        for chat_user in chat_users:
            chat_user.chats.append(chat)
            db_sess.merge(chat_user)
            db_sess.commit()
        return redirect('/')
    return render_template('add_chat.html', title='Добавление чата',
                           form=form)


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
        if '@' in form.username.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Имя пользователя не должно содержать @")
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


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route('/add_news', methods=['GET', 'POST'])
@login_required
def add_news():
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


if __name__ == '__main__':
    db_session.global_init("db/blogs.db")
    app.register_blueprint(news_api.blueprint)
    app.run()
