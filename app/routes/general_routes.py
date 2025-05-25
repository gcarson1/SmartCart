from flask import Blueprint, request, redirect, url_for, render_template, jsonify
from flask_login import login_required, current_user
from app.models.models import Store
from app.extensions import db
from app.services.assistant_utils import create_dynamic_assistant
import time


general_bp = Blueprint('general', __name__)

@general_bp.route('/')
def landing():
    return render_template('landing.html')

@general_bp.route('/index')
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

@general_bp.route('/account_settings')
def account_settings():
    return render_template('account_settings.html')

@general_bp.route('/delete_account', methods=['POST'])
@login_required
def delete_account():
    from app.models.models import User, Store, ChatSession, ChatMessage
    from flask_login import logout_user

    try:
        user = current_user

        # Delete chat messages
        ChatMessage.query.filter_by(user_id=user.user_id).delete()

        # Delete chat sessions
        ChatSession.query.filter_by(user_id=user.user_id).delete()

        # Delete store (if any)
        Store.query.filter_by(user_id=user.user_id).delete()

        # Now delete the user
        db.session.delete(user)

        db.session.commit()
        logout_user()
        return redirect('/')
    except Exception as e:
        db.session.rollback()
        return render_template("account_settings.html", message=f"Error deleting account: {str(e)}", username=user.username, email=user.email)
