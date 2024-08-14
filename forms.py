from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, EmailField, TextAreaField, PasswordField
from wtforms.validators import DataRequired, URL, Email, Length

class CafeForm(FlaskForm):
    name = StringField('İsim', validators=[DataRequired()])
    map_url = StringField('Harita URL', validators=[DataRequired(), URL()])
    img_url = StringField('Fotoğraf URL', validators=[DataRequired(), URL()])
    location = StringField('Nerede', validators=[DataRequired()])
    has_sockets = BooleanField('Priz var mı?')
    has_toilet = BooleanField('Tuvalet var mı?')
    has_wifi = BooleanField('WiFi var mı?')
    can_take_calls = BooleanField('Çağrı alıyor mu?')
    seats = StringField('Koltuklar', validators=[DataRequired()])
    coffee_price = StringField('Kahve fiyatı', validators=[DataRequired()])
    details = TextAreaField('Detay')

class ContactForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired(), Email()])
    subject = StringField('Konu', validators=[DataRequired()])
    message = TextAreaField('Mesaj', validators=[DataRequired()])

class UserForm(FlaskForm):
    name = StringField('İsim', validators=[DataRequired(), Length(max=100)])
    email = EmailField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField('Şifre', validators=[DataRequired(), Length(min=8, max=128)])