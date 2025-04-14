from flask import Blueprint, render_template, redirect

general_bp = Blueprint('general', __name__)

@general_bp.route('/')
def index():
    return render_template("index.html")

@general_bp.route('/user_panel')
def user_panel():
    return render_template("user_login.html")

@general_bp.route('/refresh')
def refresh():
    import time
    time.sleep(600)
    return redirect('/refresh')

@general_bp.route('/admin_signup', methods=['GET'])
def show_admin_signup_form():
    return render_template('admin_signup.html')