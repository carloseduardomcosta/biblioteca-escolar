from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length

class LoginForm(FlaskForm):
    username = StringField('Usuário', validators=[DataRequired(), Length(3,50)])
    senha    = PasswordField('Senha', validators=[DataRequired(), Length(6,128)])
    submit   = SubmitField('Entrar')
