🛒 SmartCart

SmartCart is a GenAI-powered retail assistant chatbot that helps users find products, check inventory, and navigate grocery stores with natural language queries. It leverages OpenAI Assistants and vector search to deliver personalized, context-aware responses based on each store’s inventory data.

🚀 Key Features

User Authentication: Sign up and log in with username/password or Google OAuth 2.0 (Authlib).

Admin Panel: Store owners can create and manage store profiles, upload inventory files (CSV), and provision custom OpenAI Assistants and vector stores.

Dynamic Assistant Generation: Automatically uploads inventory data to OpenAI Files API, creates a vector store, and spins up a dedicated Assistant for store-specific queries.

Chat Interface: Persistent chat sessions with history stored in PostgreSQL (SQLAlchemy); users can start new chats or resume past conversations.

Inventory Search & Guidance: Query product availability, price, aisle location, and add items to a shopping list.

Responsive UI: Front-end built with Bootstrap and custom CSS; templates organized under app/templates and static assets under app/static/css.

Secure Configuration: Environment variables manage secrets and API keys; database credentials, OpenAI keys, and OAuth secrets never hard-coded.

Deployment-Ready: Includes Procfile and wsgi.py for Gunicorn; tested on Heroku and Azure App Service.

🏗️ Architecture Overview

SmartCart/
├── app/
│   ├── extensions.py       # Initializes Flask extensions (SQLAlchemy)
│   ├── models/             # SQLAlchemy models for Users, Stores, ChatSessions, Messages
│   ├── services/           # OpenAI integration and assistant utilities
│   ├── routes/             # Flask Blueprints: auth, admin, chat, general
│   ├── static/css/         # Custom stylesheets
│   └── templates/          # Jinja2 templates for all pages
├── config.py               # Flask configuration (env vars)
├── requirements.txt        # Python dependencies
├── app.py                  # Application entry point (development server)
├── wsgi.py                 # WSGI entry point for production
├── Procfile                # Heroku/Gunicorn process definition
└── README.md               # Project documentation (this file)

🛠️ Getting Started

Prerequisites

Python 3.10 or higher

PostgreSQL server (or fallback to SQLite for testing)

OpenAI account with API key

Google Cloud credentials for OAuth (optional)

Heroku CLI or Azure CLI for deployment (optional)

Installation

Clone the repository

git clone https://github.com/yourusername/SmartCart.git
cd SmartCart

Create a virtual environment

python3 -m venv venv
source venv/bin/activate  # Windows: venv\\Scripts\\activate

Install dependencies

pip install -r requirements.txt

Configure environment variables
Create a .env file in the project root:

SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://USER:PASSWORD@HOST:PORT/DB_NAME
OPENAI_API_KEY=sk-...
ASSISTANT_ID=             # Optional: preexisting Assistant ID
VECTOR_STORE_ID=          # Optional: preexisting Vector Store ID
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

Database Setup

Within the virtual environment, initialize the database:

python - << 'EOF'
from app import create_app
from app.extensions import db
app = create_app()
with app.app_context():
    db.create_all()
EOF

Running Locally

# Development server
python app.py
# Production (Gunicorn)
gunicorn --bind 0.0.0.0:8080 wsgi:app

Navigate to http://localhost:8080 and follow the landing page to sign up or log in.

☁️ Deployment

Heroku

heroku create smartcart-app
heroku config:set SECRET_KEY=...
heroku buildpacks:set heroku/python
git push heroku main

Azure App Service

az webapp up --name smartcart-app --sku F1 --runtime "PYTHON|3.10"
az webapp config appsettings set --name smartcart-app --settings \
    SECRET_KEY=... DATABASE_URL=... OPENAI_API_KEY=... \
    GOOGLE_CLIENT_ID=... GOOGLE_CLIENT_SECRET=...

📜 License

This project is licensed under the MIT License. See LICENSE for details.

🙋‍♂️ Authors & Contributors

Gabriel Carson – Cloud Engineer Intern & CS Student – GitHub

Ethan Head – AI Researcher & CS Student – GitHub

Feel free to open issues or submit pull requests for improvements.

