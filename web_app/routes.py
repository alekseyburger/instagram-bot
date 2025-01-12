from flask import render_template, flash, redirect, url_for, request
from web_app import app, db
from web_app.forms import LoginForm, FollowingForm
from web_app.models import Following, AdminPassword
from flask_login import current_user, login_user, logout_user, login_required
# from werkzeug.urls import url_parse

@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    add_form = FollowingForm()
    following = Following.query.all()
    if add_form.validate_on_submit():
        new = Following(name=add_form.username.data)
        db.session.add(new)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('index.html', names = following, form=add_form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    admin_password = AdminPassword.query.all()
    #flash(f'got passwords {len(admin_password)}') # {admin_password.password_hash}')
    if 0 == len(admin_password):
        print("Create default_password")
        default_password = AdminPassword(name='admin')
        default_password.set_password('admin')
        db.session.add(default_password)
        db.session.commit()  
    form = LoginForm()
    if form.validate_on_submit():
        admin_password = AdminPassword.query.get(1)
        if admin_password is None or not admin_password.check_password(form.password.data):
            return redirect(url_for('login'))
        login_user(admin_password, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page: #  or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

# @app.route('/register', methods=['GET', 'POST'])
# def register():
#     if current_user.is_authenticated:
#         return redirect(url_for('index'))
#     form = RegistrationForm()
#     if form.validate_on_submit():
#         user = User(username=form.username.data, email=form.email.data)
#         user.set_password(form.password.data)
#         db.session.add(user)
#         db.session.commit()
#         flash('Congratulations, you are now a registered user!')
#         return redirect(url_for('login'))
#     return render_template('register.html', title='Register', form=form)
