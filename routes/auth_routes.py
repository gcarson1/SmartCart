from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_user, logout_user
from models.models import db, User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        email = request.form.get('email')
        if not username or not password or not confirm_password:
            error = "All fields are required."
        elif password != confirm_password:
            error = "Passwords do not match."
        else:
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                error = "Username already exists."
            else:
                new_user = User(username=username, email=email)
                new_user.set_password(password)
                db.session.add(new_user)
                db.session.commit()
                return redirect(url_for('auth.user_login'))
    return render_template('signup.html', error=error)

@auth_bp.route('/user_login', methods=['GET', 'POST'])
def user_login():
    error = None
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = User.query.filter_by(username=username).first()
        if not user or not user.check_password(password):
            error = "Invalid username or password. Please try again."
        else:
            login_user(user)
            return redirect(url_for("general.index"))
    return render_template("user_login.html", error=error)

@auth_bp.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        admin = User.query.filter_by(username=username, is_admin=True).first()
        if not admin or not admin.check_password(password):
            error = "Invalid credentials or not an admin user."
            return render_template('admin_login.html', error=error)
        login_user(admin)
        return redirect('/admin_panel')
    return render_template('admin_login.html', error=error)

@auth_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('general.landing'))

@auth_bp.route('/google_login')
def google_login():
    from app import oauth
    google = oauth.create_client('google')
    redirect_uri = url_for('auth.google_authorize', _external=True)
    return google.authorize_redirect(redirect_uri)

@auth_bp.route('/google_authorize')
def google_authorize():
    from app import oauth
    google = oauth.create_client('google')
    token = google.authorize_access_token()
    resp = google.get('userinfo')
    user_info = resp.json()
    email = user_info.get('email')

    user = User.query.filter_by(email=email).first()
    if not user:
        import os
        random_password = os.urandom(16).hex()
        user = User(username=email, email=email)
        user.set_password(random_password)
        db.session.add(user)
        db.session.commit()

    login_user(user)
    return redirect(url_for('general.index'))