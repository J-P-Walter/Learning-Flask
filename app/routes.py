from app import app, db
from flask import render_template, flash, redirect, url_for, request, g
from app.models import User, Post
from app.forms import LoginForm, RegistrationForm, EditProfileForm, EmptyForm, PostForm, ResetPasswordRequestForm, ResetPasswordForm
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse
from datetime import datetime
from app.email import send_password_reset_email
from flask_babel import get_locale
from langdetect import detect, LangDetectException

#Different pages
#Added methods for post form
@app.route('/', methods=['GET', 'POST'])
@app.route("/index", methods=['GET', 'POST'])
@login_required #intercepts and redirects to 'login'
def index():
    #Can do pythonic stuff here and then pass to html page
    form = PostForm()
    if form.validate_on_submit():
        #Attempts to detect language from post
        try:
            language = detect(form.post.data)
        except LangDetectException:
            language = ""
        #Create post and push to database
        post = Post(body=form.post.data, author=current_user, language=language)
        db.session.add(post)
        db.session.commit()
        flash("Post now live")
        #Standard practice to respond to post request with redirect
        #Post/Redirect/Get pattern
        return redirect(url_for('index'))
    #request args accesses arguments given in query string
    page = request.args.get('page', 1, type=int)
    #gets Pagination object, contains list of items of requested page
    #Can use attributes of Pag. object for navigation
    posts = current_user.followed_posts().paginate(page=page, per_page=app.config['POSTS_PER_PAGE'], error_out=False)
    #url_for auto applies keyword arguments to URL
    next_url = url_for('index', page=posts.next_num) if posts.has_next else None
    prev_url = url_for('index', page=posts.prev_num) if posts.has_prev else None
    return render_template('index.html', title='Home Page', posts=posts.items, form=form, next_url=next_url, prev_url=prev_url)

#before_request executed right before view function
#checks if user is logged in, sets last_seen and updates database
@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
    g.locale = str(get_locale());

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
    page = request.args.get('page', 1, type=int)
    posts = user.posts.order_by(Post.timestamp.desc()).paginate(page=page, per_page=app.config['POSTS_PER_PAGE'], error_out=False)
    next_url = url_for('user', username=user.username, page=posts.next_num) if posts.has_next else None
    prev_url = url_for('user', username=user.username, page=posts.prev_num) if posts.has_prev else None
    #EmptyForm acts as unfollow button
    form = EmptyForm()
    return render_template('user.html', user=user, posts=posts.items, next_url=next_url, prev_url=prev_url, form=form)

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

#Page to find other users
@app.route('/explore')
@login_required
def explore():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(page=page, per_page=app.config['POSTS_PER_PAGE'], error_out=False)
    next_url = url_for('explore', page=posts.next_num) if posts.has_next else None
    prev_url = url_for('explore', page=posts.prev_num) if posts.has_prev else None
    return render_template("index.html", title='Explore', posts=posts.items,
                          next_url=next_url, prev_url=prev_url)

@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash('Check your email for the instructions to reset your password')
        return redirect(url_for('login'))
    return render_template('reset_password_request.html',
                           title='Reset Password', form=form) 

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.')
        return redirect(url_for('login'))
    return render_template('reset_password.html', form=form)