from flask import Flask, render_template, request, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import openai
import os
import re
import time
from dotenv import load_dotenv

# Load environment variables (API key & existing assistant/vector store IDs)
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ASSISTANT_ID = os.getenv("ASSISTANT_ID")
VECTOR_STORE_ID = os.getenv("VECTOR_STORE_ID")

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")  # Use a strong secret key

db = SQLAlchemy(app)

# Initialize OpenAI client
client = openai.OpenAI(api_key=OPENAI_API_KEY)

# Create a single LoginManager instance
login_manager = LoginManager(app)
login_manager.login_view = 'user_login'  # The route where users log in

# Update your User model to inherit from UserMixin, which provides default implementations
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.Text, nullable=False)  # storing hashed passwords
    email = db.Column(db.String(255), unique=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    def get_id(self):
        # Flask-Login expects the ID as a string
        return str(self.user_id)

    def set_password(self, password):
        self.password = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password, password)

# Tell Flask-Login how to load a user from the session
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Function to check if an assistant already exists
def get_existing_assistant():
    assistants = client.beta.assistants.list()
    for assistant in assistants.data:
        if assistant.id == ASSISTANT_ID:
            print(f"Using existing Assistant ID: {ASSISTANT_ID}")
            return ASSISTANT_ID
    return None

# Function to check if a vector store already exists
def get_existing_vector_store():
    vector_stores = client.beta.vector_stores.list()
    for store in vector_stores.data:
        if store.id == VECTOR_STORE_ID:
            print(f"Using existing Vector Store ID: {VECTOR_STORE_ID}")
            return VECTOR_STORE_ID
    return None

# Function to run assistant using stored IDs
def run_assistant(user_input):
    thread = client.beta.threads.create()
    print(f"Thread Created: {thread.id}")

    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=user_input
    )

    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread.id, assistant_id=ASSISTANT_ID
    )

    messages = client.beta.threads.messages.list(thread_id=thread.id)
    
    # Extract and clean the text from the response
    response_text = ""
    for block in messages.data[0].content:
        if block.type == "text":
            response_text += block.text.value  # Extract text without annotations

    pattern = r'【\d+†source】'
    response_text = re.sub(pattern, '', response_text)

    return response_text  # Return clean text

# Flask Routes
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/get")
def get_bot_response():
    userText = request.args.get('msg')
    return str(run_assistant(userText))

@app.route('/refresh')
def refresh():
    time.sleep(600)  # Wait for 10 minutes
    return redirect('/refresh')

# New Route: Admin Login
@app.route('/admin_login', methods=["GET", "POST"])
def admin_login():
    error = None
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        # Check against default credentials
        if username == "user1234" and password == "pass1234":
            return redirect("/admin_panel")
        else:
            error = "Invalid credentials. Please try again."
    return render_template("admin_login.html", error=error)

# New Route: Admin Panel with CSV upload
@app.route('/admin_panel', methods=["GET", "POST"])
def admin_panel():
    message = None
    if request.method == "POST":
        csv_file = request.files.get("csvFile")
        if csv_file:
            message = "CSV file uploaded successfully (dummy action)."
        else:
            message = "No file selected."
    return render_template("admin_panel.html", message=message)

@app.route('/user_login', methods=["GET", "POST"])
def user_login():
    error = None
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        # Query the database for the user by username
        user = User.query.filter_by(username=username).first()
        
        if not user or not user.check_password(password):
            error = "Invalid username or password. Please try again."
        else:
            # Log the user in
            login_user(user)
            return redirect(url_for('index'))
    
    return render_template("user_login.html", error=error)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


# New Route: User Panel (User Dashboard)
@app.route('/user_panel')
def user_panel():
    return render_template("user_login.html")

# New Route: Sign Up
@app.route('/signup', methods=["GET", "POST"])
def signup():
    error = None
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")
        email = request.form.get("email")
        
        if not username or not password or not confirm_password:
            error = "All fields are required."
        elif password != confirm_password:
            error = "Passwords do not match."
        else:
            # Check if username already exists
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                error = "Username already exists."
            else:
                # Create new user, hash the password, add to session, and commit
                new_user = User(username=username, email=email)
                new_user.set_password(password)
                db.session.add(new_user)
                db.session.commit()
                return redirect(url_for('user_login'))
    return render_template("signup.html", error=error)


if __name__ == "__main__":
    # Ensure existing Assistant & Vector Store are used
    if not get_existing_assistant():
        print("⚠️ Assistant ID not found in OpenAI. Make sure it exists or update your .env file.")
    
    if not get_existing_vector_store():
        print("⚠️ Vector Store ID not found in OpenAI. Make sure it exists or update your .env file.")

    app.run(debug=True)
