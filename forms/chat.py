from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField
from wtforms import BooleanField, SubmitField
from wtforms.validators import DataRequired


class ChatForm(FlaskForm):
    name = StringField('Название', validators=[DataRequired()])
    users = TextAreaField("Имя пользователей через пробел")
    submit = SubmitField('Создать')