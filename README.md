# SmartCart

[![Python Version](https://img.shields.io/badge/python-3.10+-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)](#)

SmartCart is a **GenAI-powered grocery assistant** that helps users navigate stores, check inventory in real-time, and build shopping lists through natural language interaction. It’s built with Flask and OpenAI APIs and now fully deployed to Azure using modern IaC principles with OpenTofu.

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
- [☁️ Deployment (Azure w/ IaC)](#️-deployment-azure-w-iac)
- [🤝 Contributing](#️-contributing)
- [📜 License](#️-license)
- [🙋‍♂️ Authors](#️-authors)

---

## 🚀 Key Features

| Feature                         | Description                                                         |
|---------------------------------|---------------------------------------------------------------------|
| 🔐 **User Authentication**      | Supports login via username/password                                |
| 🛠️ **Admin Panel**              | Upload inventory via CSV, manage store profile, update agent        |
| 🤖 **OpenAI Assistants**        | Custom assistant per store, vector search via embedded inventory    |
| 💬 **Chatbot Interface**        | Persistent sessions, history stored in PostgreSQL                   |
| 📦 **Inventory Insights**       | Ask about item availability, pricing, location, and list management |
| 📱 **Responsive UI**            | Bootstrap + custom CSS                                              |

---

## 🏗️ Architecture

```
SmartCart/
├─ app/
│  ├─ extensions.py       # Flask extension setup
│  ├─ models/             # SQLAlchemy models
│  ├─ services/           # OpenAI + assistant utils
│  ├─ routes/             # Flask Blueprints
│  ├─ static/css/         # Styles
│  └─ templates/          # Jinja2 views
├─ config.py              # App config loader
├─ app.py                 # Dev entrypoint
├─ wsgi.py                # Gunicorn production entry
├─ IaC/                   # OpenTofu infrastructure setup for Azure
├─ requirements.txt
├─ Dockerfile
└─ README.md
```

---

## 🛠️ Getting Started

### Prerequisites

- Python ≥ 3.10
- PostgreSQL (Azure Flexible Server recommended)
- OpenAI API key
- Google OAuth credentials (optional)

### Installation

```bash
git clone https://github.com/gcarson1/SmartCart.git
cd SmartCart

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
```

### Configuration

Create a `.env` file with the following:

```ini
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://USER:PASSWORD@HOST:PORT/DATABASE
OPENAI_API_KEY=sk-...
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
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
python app.py       # Development mode
# or
gunicorn -b 0.0.0.0:8080 wsgi:app   # Production
```

Visit `http://localhost:8080` to interact with SmartCart.

Recommended: Run in a Docker container with the Dockerfile.

---

## ☁️ Deployment (Azure w/ IaC)

This project now uses **OpenTofu** to manage Azure resources declaratively.

### Infrastructure Stack

- Azure App Service (Python 3.10)
- Azure PostgreSQL Flexible Server
- Azure Key Vault for secret management
- Azure Storage (optional)
- Managed Identity access

### Steps

1. Clone and navigate into the `IaC` directory:
   ```bash
   cd IaC
   ```

2. Initialize and apply the infrastructure:
   ```bash
   tofu init
   tofu apply
   ```

3. Set environment variables in Azure via `appsettings` or Key Vault bindings:
   - `SECRET_KEY`
   - `DATABASE_URL`
   - `OPENAI_API_KEY`
   - etc.

4. Push your code to Azure via GitHub Actions, ZipDeploy, or `az webapp deployment source`.

---

## 📜 License

Licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

## 🙋‍♂️ Authors

- **Gabriel Carson** – Cloud Engineer Intern & CS Student – [GitHub](https://github.com/gcarson1)
