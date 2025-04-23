# 🛒 SmartCart

[![Python Version](https://img.shields.io/badge/python-3.10+-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)](#)

A **GenAI-powered** retail assistant chatbot that guides shoppers through grocery stores, answers inventory questions, and builds shopping lists—all via natural language.

---

## 📋 Table of Contents

- [🚀 Key Features](#-key-features)
- [🏗️ Architecture](#️-architecture)
- [🛠️ Getting Started](#️-getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Configuration](#configuration)
  - [Database Setup](#database-setup)
  - [Running Locally](#running-locally)
- [☁️ Deployment](#️-deployment)
- [🤝 Contributing](#️-contributing)
- [📜 License](#️-license)
- [🙋‍♂️ Authors](#️-authors)

---

## 🚀 Key Features

| Feature                         | Description                                                         |
|---------------------------------|----------------------------------------------------------------------|
| 🔒 **Auth**                     | Username/password & Google OAuth login                              |
| 🛠️ **Admin Panel**              | Upload CSV inventory, manage store profile, regenerate assistants   |
| 🤖 **Dynamic Assistants**       | Custom OpenAI Assistants per store with vector-search on inventory  |
| 💬 **Chat Interface**           | Persistent sessions, history stored in PostgreSQL                   |
| 📦 **Inventory Management**     | Query product availability, price, aisle location, add to list      |
| 🎨 **Responsive UI**            | Bootstrap + custom CSS templates                                    |

---

## 🏗️ Architecture

```text
SmartCart/
├─ app/
│  ├─ extensions.py       # Init Flask extensions
│  ├─ models/             # SQLAlchemy models
│  ├─ services/           # OpenAI integration & assistant utils
│  ├─ routes/             # Flask Blueprints
│  ├─ static/css/         # Stylesheets
│  └─ templates/          # Jinja2 templates
├─ config.py              # Env-based config
├─ requirements.txt       # Dependencies
├─ app.py                 # Dev server entrypoint
├─ wsgi.py                # Production entrypoint
├─ Procfile               # Gunicorn process for Heroku
└─ README.md              # Project docs
```

---

## 🛠️ Getting Started

### Prerequisites

- **Python** ≥ 3.10
- **PostgreSQL** (or fallback to SQLite)
- **OpenAI** API key
- **Google OAuth** credentials (optional)

### Installation

```bash
# Clone & enter
git clone https://github.com/yourusername/SmartCart.git
cd SmartCart

# Setup venv
env=$(python3 -m venv venv && echo venv)  # or python3 -m venv venv
source $env/bin/activate

# Install deps
pip install -r requirements.txt
```

### Configuration

Create a `.env` file in the root:

```ini
SECRET_KEY=<your-secret>
DATABASE_URL=postgresql://USER:PASS@HOST:PORT/DB
OPENAI_API_KEY=<sk-...>
ASSISTANT_ID=             # optional
VECTOR_STORE_ID=          # optional
GOOGLE_CLIENT_ID=<id>     # optional
GOOGLE_CLIENT_SECRET=<secret>
```

### Database Setup

```bash
python - << 'EOF'
from app import create_app
from app.extensions import db
app = create_app()
with app.app_context():
    db.create_all()
EOF
```

### Running Locally

```bash
# Dev mode
env/bin/python app.py
# Prod mode
gunicorn --bind 0.0.0.0:8080 wsgi:app
```
Visit <http://localhost:8080> to use SmartCart.

---

## ☁️ Deployment

**Heroku**
```bash
heroku create smartcart-app
heroku config:set SECRET_KEY=... DATABASE_URL=... OPENAI_API_KEY=...
git push heroku main
```

**Azure App Service**
```bash
az webapp up -n smartcart-app --sku F1 --runtime "PYTHON|3.10"
az webapp config appsettings set -n smartcart-app --settings \
  SECRET_KEY=... DATABASE_URL=... OPENAI_API_KEY=...
```

---

## 🤝 Contributing

1. Fork the repo
2. Create feature branch (`git checkout -b feature/XYZ`)
3. Commit changes (`git commit -m "Add XYZ feature"`)
4. Push & open PR

Please follow the existing code style and add tests where appropriate.

---

## 📜 License

Distributed under the **MIT License**. See [LICENSE](LICENSE) for details.

---

## 🙋‍♂️ Authors

- **Gabriel Carson** – Cloud Engineer Intern & CS Student – [GitHub](https://github.com/gcarson1)
- **Ethan Head** – AI Researcher & CS Student – [GitHub](https://github.com/ethanhead)

