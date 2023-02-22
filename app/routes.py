from app import app, db
from flask import render_template, flash, redirect, url_for, request
from app.models import User
from app.forms import LoginForm, RegistrationForm, EditProfileForm, EmptyForm
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse
from datetime import datetime

#Different pages
@app.route('/')
@app.route("/index")
@login_required #intercepts and redirects to 'login'
def index():
    #Can do pythonic stuff here and then pass to html page
    user = {'username': 'John'}
    posts = [
        {
            'author': {'username': 'John'},
            'body': 'Beautiful day in Portland!'
        },
        {
            'author': {'username': 'Susan'},
            'body': 'The Avengers movie was so cool!'
        }
    ]
    return render_template('index.html', title='Home Page', posts=posts)

#before_request executed right before view function
#checks if user is logged in, sets last_seen and updates database
@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()

@app.route('/login', methods=['GET', 'POST'])
def login():
    #Redirects to home if already logged in
    #current_user from Flask-login
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        #Queries the database for correct username
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        #login_user from Flask-Login
        login_user(user, remember=form.remember_me.data)

        #handles redirect from @login_required decorator:
        #returns user to page they were trying to access before logging in
        #or home if there is not "next_page"
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign in', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    #Redirects if already logged in
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        #adds new user to database and redirects to home
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash("Registration success!")
        return redirect(url_for('index'))
    return render_template('register.html', title='Register', form=form)

#<> denote dynamic component, used as function parameter
#view user page
@app.route('/user/<username>')
@login_required
def user(username):
    #Queries database for username
    user = User.query.filter_by(username=username).first_or_404()
    posts = [
        {'author': user, 'body': 'Test post 1'},
        {'author': user, 'body': 'Test post 2'}
    ]
    #EmptyForm acts as unfollow button
    form = EmptyForm()
    return render_template('user.html', user=user, posts=posts, form=form)

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    #If form.validate... is true, update user and commit to the database
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Changes saved')
        return redirect(url_for('edit_profile'))
    #If form.validate is false, request.method checks if browser sent "GET" to get form which
    #renders form and initial data
    #otherwise, does nothing because it would be a validation error, already taken care of
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title="Edit Profile", form=form)

#Using empty form and POST because its safer than GET
@app.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        #Find the user to follow
        user = User.query.filter_by(username=username).first()
        #if user not found
        if user is None:
            flash('User {} not found'.format(username))
            return redirect(url_for('index'))
        #If user is self
        if user == current_user:
            flash('You cannot follow yourself')
            return redirect(url_for('user', username=username))
        #Follow user
        current_user.follow(user)
        db.session.commit()
        flash('Now following {}'.format(username))
        return redirect(url_for('user', username=username))
    else:
        return redirect(url_for('index'))

#Same as above, just opposite
@app.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash('User {} not found.'.format(username))
            return redirect(url_for('index'))
        if user == current_user:
            flash('You cannot unfollow yourself!')
            return redirect(url_for('user', username=username))
        current_user.unfollow(user)
        db.session.commit()
        flash('You are not following {}.'.format(username))
        return redirect(url_for('user', username=username))
    else:
        return redirect(url_for('index'))