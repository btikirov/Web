from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, TextAreaField, SubmitField, BooleanField, EmailField
from wtforms.validators import DataRequired
from flask_wtf.file import FileField, FileAllowed



class RegisterForm(FlaskForm):
    email = EmailField('Почта', validators=[DataRequired()])
    username = StringField('Имя пользователя', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    password_again = PasswordField('Повторите пароль', validators=[DataRequired()])
    name = StringField('Имя', validators=[DataRequired()])
    icon = FileField('Иконка', validators=[
        FileAllowed(['png', 'jpg'], 'Только .png и .jpg файлы!')
    ])
    surname = StringField('Фамилия', validators=[DataRequired()])
    about = TextAreaField("Немного о себе")
    submit = SubmitField('Создать')


class LoginForm(FlaskForm):
    email_or_username = StringField('Почта или Имя пользователя', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


class FindUserForm(FlaskForm):
    search = StringField('Поиск пользователя')
    submit = SubmitField('Найти')
