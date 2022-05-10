import os
from flask_restful import Api
from flask import Flask, render_template, redirect, request, abort
from data.users import User
from data.tasks import Task
from data.news import News
from data.chats import Chat
from data.messages import Message
from data.categories import Category
from data import db_session, news_api, users_api
from forms.user import RegisterForm, LoginForm, FindUserForm
from forms.task import TaskForm
from forms.new import NewsForm
from forms.chat import ChatForm
from forms.message import SendForm
from forms.category import CategoryForm
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = os.getcwd() + '/static/img'
ALLOWED_EXTENSIONS = {'png', 'jpg'}

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

api = Api(app)

login_manager = LoginManager()
login_manager.init_app(app)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# all for news


@app.route("/", methods=['GET', 'POST'])
@app.route("/news", methods=['GET', 'POST'])
def news():
    db_sess = db_session.create_session()
    news = db_sess.query(News).filter(News.is_private != True).all()
    categories = db_sess.query(Category).all()
    form = CategoryForm()
    if form.validate_on_submit():
        category = Category()
        category.name = form.add.data
        db_sess.add(category)
        db_sess.commit()
        return redirect('/news')

    return render_template("news.html", news=news, categories=categories, form=form)


@app.route("/news/category/<int:category_id>", methods=['GET', 'POST'])
def category_news(category_id):
    db_sess = db_session.create_session()
    req_categories = db_sess.query(Category).filter(Category.id == category_id).all()
    news_old = db_sess.query(News).filter(News.is_private != True).all()
    news = []
    for item in news_old:
        for category in item.categories:
            if category.id == category_id:
                news.append(item)
                break
    categories = db_sess.query(Category).all()
    form = CategoryForm()
    if form.validate_on_submit():
        category = Category()
        category.name = form.add.data
        db_sess.add(category)
        db_sess.commit()
        return redirect('/news')

    return render_template("news.html", news=news, categories=categories, form=form)


@app.route('/news/add_news', methods=['GET', 'POST'])
@login_required
def add_news():
    if not current_user.is_authenticated:
        return redirect("/login")

    form = NewsForm()
    db_sess = db_session.create_session()
    categories_old = db_sess.query(Category).all()
    categories = []
    for item in categories_old:
        categories.append((int(item.id), item.name))

    form.categories.choices = categories

    if form.validate_on_submit():
        news = News()
        selected_categories = db_sess.query(Category).filter(Category.id.in_(form.categories.data)).all()
        news.title = form.title.data
        news.content = form.content.data
        news.is_private = form.is_private.data
        news.user = current_user
        news = db_sess.merge(news)
        news.categories = selected_categories
        db_sess.add(news)
        db_sess.commit()
        return redirect('/')
    return render_template('edit_news.html', title='Добавление новости',
                           form=form)


@app.route('/news/edit_news/<int:id>', methods=['GET', 'POST'])
def edit_news(id):
    if not current_user.is_authenticated:
        return redirect("/login")

    form = NewsForm()
    db_sess = db_session.create_session()
    categories_old = db_sess.query(Category).all()
    categories = []
    for item in categories_old:
        categories.append((item.id, item.name))

    form.categories.choices = categories

    if request.method == "GET":
        news = db_sess.query(News).filter(News.id == id,
                                          News.user == current_user
                                          ).first()

        if news:
            form.title.data = news.title
            form.content.data = news.content
            form.is_private.data = news.is_private
            news_categories = [item.id for item in news.categories]

            form.categories.data = news_categories
        else:
            abort(404)
    if form.validate_on_submit():
        news = db_sess.query(News).filter(News.id == id,
                                          News.user == current_user
                                          ).first()

        if news:
            news.title = form.title.data
            news.content = form.content.data
            news.is_private = form.is_private.data
            news.categories = db_sess.query(Category).filter(Category.id.in_(form.categories.data)).all()
            db_sess.commit()
            return redirect('/')
        else:
            abort(404)
    return render_template('edit_news.html',
                           title='Редактирование новости',
                           form=form
                           )


@app.route('/news/news_delete/<int:id>', methods=['GET', 'POST'])
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
        return redirect(f'/users/search/{form.search.data}')
        # form = FindUserForm()
    db_sess = db_session.create_session()
    users_list = db_sess.query(User).all()

    return render_template("users.html", users=users_list, form=form)


@app.route("/users/<int:user_id>")
def user(user_id):
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == user_id).first()
    return render_template("user.html", user=user)


@app.route("/users/search/<string:data>", methods=['GET', 'POST'])
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
        return redirect(f'/users/search/{form.search.data}')
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
        user_icon_href = '$void.png'
        if form.icon.data:
            icon = form.icon.data
            filename = secure_filename(form.username.data + '.' + form.icon.data.filename.split('.')[-1])
            icon.save(os.path.join(
                app.config["UPLOAD_FOLDER"], 'users', filename
            ))
            user_icon_href = filename
        user = User(
            username=form.username.data,
            icon_href=user_icon_href,
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


@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    if not current_user.is_authenticated:
        return redirect("/login")

    form = RegisterForm()

    if request.method == "GET":
        user = current_user

        if user:
            form.email.data = user.email
            form.username.data = user.username
            form.name.data = user.name
            form.surname.data = user.surname
            form.about.data = user.about
        else:
            abort(404)
    else:
        form.username.data = "pass"
        form.password.data = "pass"
        form.password_again.data = "pass"
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.id == current_user.id).first()

        user_icon_href = '$void.png'
        if form.icon.data:
            icon = form.icon.data
            filename = secure_filename(user.username + '.' + form.icon.data.filename.split('.')[-1])
            icon.save(os.path.join(
                app.config["UPLOAD_FOLDER"], filename
            ))
            user_icon_href = filename

        if user:
            user.email = form.email.data
            user.name = form.name.data
            user.surname = form.surname.data
            user.about = form.about.data
            if form.icon.data:
                user.icon_href = user_icon_href
            db_sess.commit()
            return redirect('/users')
        else:
            abort(404)
    return render_template('register.html',
                           title='Редактирование профиля',
                           form=form
                           )

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


def create_chat(name, users, creator_username, icon_data, description, unique_id=None):
    db_sess = db_session.create_session()
    chat = Chat()
    chat.name = name
    chat.content = description
    chat.icon_href = "$void.jpg"
    chat.unique_chat_href = unique_id
    db_sess.add(chat)
    db_sess.commit()
    if chat.unique_chat_href is None:
        chat.unique_chat_href = str(chat.id)
        chat = db_sess.merge(chat)
        db_sess.commit()
    if icon_data is not None and icon_data:
        icon = icon_data
        filename = secure_filename(str(chat.id) + '.' + icon_data.filename.split('.')[-1])
        icon.save(os.path.join(
            app.config["UPLOAD_FOLDER"], 'chats', filename
        ))
        chat.icon_href = filename
        chat = db_sess.merge(chat)
        db_sess.commit()
    creator = db_sess.query(User).filter(User.username == creator_username).first()
    chat.admin = creator
    db_sess.merge(chat)
    db_sess.commit()
    db_sess = db_session.create_session()
    for chat_user in users:
        chat_user.chats.append(chat)
        db_sess.merge(chat_user)
        db_sess.commit()
    db_sess.merge(chat)
    db_sess.commit()



@app.route("/chats/<string:chat_id>/", methods=['GET', 'POST'])
def open_chat(chat_id):
    if not current_user.is_authenticated:
        return redirect("/login")

    form = SendForm()
    find_chat = None
    id_check = chat_id
    if not chat_id.isdigit():
        names = sorted(list(chat_id.split('_')))
        id_check = '_'.join(names)
    user_chats = current_user.chats
    for chat in user_chats:
        if chat.unique_chat_href == id_check:
            find_chat = chat
            break

    if find_chat is None and not id_check.isdigit():
        db_sess = db_session.create_session()
        users = db_sess.query(User).filter(User.username.in_(list(id_check.split('_')))).all()
        db_sess.close()
        if users:
            db_sess = db_session.create_session()
            name = ' и '.join(id_check.split('_'))
            desc = f"Личные сообщения пользователей {id_check.split('_')[0]} и {id_check.split('_')[-1]}"
            if id_check == current_user.username:
                name = "Заметки"
                desc = "Заметки"
            create_chat(name, users, 'admin', None, desc, unique_id=id_check)
            find_chat = db_sess.query(Chat).filter(Chat.unique_chat_href==id_check).first()
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
        return redirect(f"/chats/{id_check}")

    chat_messages = sorted(list(find_chat.messages), key=lambda item: item.created_date)
    return render_template("chat_dialog.html", chat=find_chat, form=form, messages = chat_messages)


@app.route("/chats/<string:chat_id>/delete_message/<int:message_id>")
def delete_message(chat_id, message_id):
    if not current_user.is_authenticated:
        return redirect("/login")

    db_sess = db_session.create_session()
    messages = db_sess.query(Message).filter(Message.id == message_id,
                                      Message.sender == current_user
                                      ).first()
    if messages:
        db_sess.delete(messages)
        db_sess.commit()
    else:
        abort(404)

    return redirect(f'/chats/{chat_id}')


@app.route("/chats/add_chat", methods=["GET", "POST"])
def add_chat():
    if not current_user.is_authenticated:
        return redirect("/login")

    form = ChatForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        users = db_sess.query(User).filter(User.username.in_(list(form.users.data.split()) + [current_user.username])).all()
        create_chat(form.name.data, users, current_user.username, form.icon.data, form.content.data)

        return redirect('/chats')
    return render_template('add_chat.html', title='Добавление чата',
                           form=form)


# all for tasks


@app.route("/tasks", methods=['GET', 'POST'])
def tasks():
    db_sess = db_session.create_session()
    tasks = db_sess.query(Task).filter(Task.is_private != True).all()
    categories = db_sess.query(Category).all()
    form = CategoryForm()
    if form.validate_on_submit():
        category = Category()
        category.name = form.add.data
        db_sess.add(category)
        db_sess.commit()
        return redirect('/tasks')

    return render_template("tasks.html", tasks=tasks, categories=categories, form=form)


@app.route("/tasks/category/<int:category_id>", methods=['GET', 'POST'])
def category_task(category_id):
    db_sess = db_session.create_session()
    req_categories = db_sess.query(Category).filter(Category.id == category_id).all()
    news_old = db_sess.query(Task).filter(Task.is_private != True).all()
    tasks = []
    for item in news_old:
        for category in item.categories:
            if category.id == category_id:
                tasks.append(item)
                break
    categories = db_sess.query(Category).all()
    form = CategoryForm()
    if form.validate_on_submit():
        category = Category()
        category.name = form.add.data
        db_sess.add(category)
        db_sess.commit()
        return redirect('/tasks')

    return render_template("tasks.html", tasks=tasks, categories=categories, form=form)


@app.route('/tasks/add_task', methods=['GET', 'POST'])
@login_required
def add_task():
    if not current_user.is_authenticated:
        return redirect("/login")

    form = TaskForm()
    db_sess = db_session.create_session()
    categories_old = db_sess.query(Category).all()
    categories = []
    for item in categories_old:
        categories.append((int(item.id), item.name))

    form.categories.choices = categories

    if form.validate_on_submit():
        task = Task()
        selected_categories = db_sess.query(Category).filter(Category.id.in_(form.categories.data)).all()
        task.title = form.title.data
        task.content = form.content.data
        task.is_private = form.is_private.data
        task.user = current_user
        task = db_sess.merge(task)
        news.categories = selected_categories
        db_sess.add(task)
        db_sess.commit()
        return redirect('/tasks')
    return render_template('edit_task.html', title='Добавление задания',
                           form=form)


@app.route('/tasks/edit_task/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_task(id):
    if not current_user.is_authenticated:
        return redirect("/login")

    form = NewsForm()
    db_sess = db_session.create_session()
    categories_old = db_sess.query(Category).all()
    categories = []
    for item in categories_old:
        categories.append((item.id, item.name))

    form.categories.choices = categories

    if request.method == "GET":
        task = db_sess.query(Task).filter(Task.id == id,
                                          Task.user == current_user
                                          ).first()

        if task:
            form.title.data = task.title
            form.content.data = task.content
            form.is_private.data = task.is_private
            news_categories = [item.id for item in task.categories]

            form.categories.data = news_categories
        else:
            abort(404)
    if form.validate_on_submit():
        task = db_sess.query(Task).filter(Task.id == id,
                                          Task.user == current_user
                                          ).first()

        if task:
            task.title = form.title.data
            task.content = form.content.data
            task.is_private = form.is_private.data
            task.categories = db_sess.query(Category).filter(Category.id.in_(form.categories.data)).all()
            db_sess.commit()
            return redirect('/tasks')
        else:
            abort(404)
    return render_template('edit_task.html',
                           title='Редактирование задания',
                           form=form
                           )


@app.route('/tasks/task_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def task_delete(id):
    if not current_user.is_authenticated:
        return redirect("/login")

    db_sess = db_session.create_session()
    task = db_sess.query(Task).filter(Task.id == id,
                                      Task.user == current_user
                                      ).first()
    if task:
        db_sess.delete(task)
        db_sess.commit()
    else:

        abort(404)

    return redirect('/tasks')


if __name__ == '__main__':
    db_session.global_init("db/blogs.db")
    db_sess = db_session.create_session()
    if not db_sess.query(User).filter(User.username == 'admin').first():
        user = User(
            username='admin',
            icon_href="$void.png",
            name='main',
            surname='admin',
            email='devyatyarov.06@mail.ru',
            about='Главный админ'
        )
        user.set_password('admin')
        db_sess.add(user)
        db_sess.commit()

    api.add_resource(news_api.NewsListResource, '/api/news')
    api.add_resource(news_api.NewsResource, '/api/news/<int:news_id>')
    api.add_resource(users_api.UserResource, '/api/users/<int:user_id>')
    api.add_resource(users_api.UsersListResource, '/api/users')
    app.run()
