from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField
from wtforms import BooleanField, SubmitField
from wtforms.validators import DataRequired
from flask_wtf.file import FileField, FileAllowed


class ChatForm(FlaskForm):
    name = StringField('Название', validators=[DataRequired()])
    users = TextAreaField("Имя пользователей через пробел")
    content = TextAreaField("Описание чата")
    submit = SubmitField('Создать')
    icon = FileField('Иконка', validators=[
        FileAllowed(['png', 'jpg'], 'Только .png и .jpg файлы!')
    ])