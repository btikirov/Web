from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, TextAreaField, SubmitField, BooleanField
from wtforms.validators import DataRequired, InputRequired


class SendForm(FlaskForm):
    message = StringField('Сообщение', validators=[InputRequired()])
    submit = SubmitField('Отправить')