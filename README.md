# 🛒 SmartCart

**SmartCart** is a GenAI-powered retail assistant chatbot designed to help customers efficiently navigate grocery stores, manage shopping lists, and get real-time information on inventory and product locations.

Built with **Flask**, integrated with **PostgreSQL**, and deployable on **Heroku**, SmartCart offers a scalable, intelligent, and responsive assistant experience for modern retail environments.

---

## 🚀 Features

- 🧠 Natural Language Chatbot for grocery assistance
- 📦 Product inventory search
- 🛍️ Shopping list management
- 🗺️ Aisle and product location guidance
- 🛠️ Admin panel for store management
- 🔐 Secure credential storage

---

## 🧰 Tech Stack

- **Backend**: Python, Flask, Gunicorn
- **Frontend**: HTML, CSS, JS
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy
- **Deployment**: Heroku
- **Storage**: PostgreSQL + OpenAI Vector Store

---

## 🧑‍💻 Local Setup

### MacOS / Linux

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

### Windows

```bash
python -m venv venv
.env\Scriptsctivate
pip install -r requirements.txt
python app.py
```

---

## 🌐 Deployment

The app is currently deployed on **Heroku** using:
- A `Procfile` for web dyno configuration
- Heroku Postgres as the database
- `gunicorn` as the WSGI server

To deploy:

```bash
git push heroku main
```

---

## 🗃️ Project Structure

```
SmartCart/
├── app.py                  # Entry point
├── config.py               # Configuration (including DB)
├── models/                 # SQLAlchemy models
├── static/                 # Static assets (images, CSS)
├── templates/              # HTML templates
├── requirements.txt        # Python dependencies
├── Procfile                # Heroku deployment config
├── postgres.sql            # Schema setup
├── .env                    # Local environment variables
└── README.md
```

---

## 🧪 Testing

To test your setup:

1. Navigate to `http://127.0.0.1:5000`
2. Try adding products, chatting with the bot, and checking admin pages.

---

## ⚙️ Environment Variables

Create a `.env` file:

```env
ASSISTANT_ID=asst_********************
DATABASE_URL=postgres://************************
OPENAI_API_KEY=******************
SECRET_KEY=***************
VECTOR_STORE_ID=******************
```

---

## 📜 License

This project is licensed under the MIT License.

---

## 🙋‍♂️ Maintainer

**Gabriel Carson**  
Cloud Engineer & CS Student  
🔗 [LinkedIn](https://www.linkedin.com/in/gabrielcarson)

**Ethan Head**  
AI Researcher & CS Student  
🔗 [LinkedIn](https://www.linkedin.com/in/gabrielcarson)
