from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, ValidationError, Email, EqualTo, Length
from app.models import User

#Form to login
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign in')

#Form to register
class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()]) #second validator ensures matches structure
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    #Queries database to check if username and email are already in use
    #"validate_<fieldname>" is taken as custom validator for validate_on_submit()
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError("Username taken")
    
    def validate_email(self, email):
        email = User.query.filter_by(username=email.data).first()
        if email is not None:
            raise ValidationError("Email already in use")

class PostForm(FlaskForm):
    post = TextAreaField("What are you thinking about?", validators=[DataRequired(), Length(min=1, max=140)])
    submit = SubmitField('Submit')

#Form to edit user profile: username and about me section
#Saves previous username as original_username to you can leave username untouched
#and there is no reason to check for duplicates
class EditProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    about_me = TextAreaField('About me', validators=[Length(min=0, max=140)])
    submit = SubmitField('Submit')

    def __init__(self, original_username, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username
    
    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=self.username.data).first()
            if user is not None:
                raise ValidationError('Please use a different username')

#Used for follow feature
#Implemented as POST request, safer
#GET requests should only be on actions that do not introduce state changes
class EmptyForm(FlaskForm):
    submit = SubmitField('Submit')