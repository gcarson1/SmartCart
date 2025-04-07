from flask import Blueprint, render_template, redirect
import time

main_bp = Blueprint('main', __name__)

@main_bp.route("/")
def index():
    return render_template("index.html")

@main_bp.route('/refresh')
def refresh():
    time.sleep(600)
    return redirect('/refresh')
