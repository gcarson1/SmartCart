from flask import Flask, render_template, request, redirect
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

# Initialize OpenAI client
client = openai.OpenAI(api_key=OPENAI_API_KEY)

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

    # Remove file citation brackets like se_text = re.sub(r"【.*?】", "", response_text)
    pattern = r'【\d+†source】'
    # Remove mathematical brackets like \[ 2.00 + 3.50 + ... \]
    response_text = re.sub(pattern, '', response_text)

    return response_text  # Return clean text

# Flask Routes
app = Flask(__name__)

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

if __name__ == "__main__":
    # Ensure existing Assistant & Vector Store are used
    if not get_existing_assistant():
        print("⚠️ Assistant ID not found in OpenAI. Make sure it exists or update your .env file.")
    
    if not get_existing_vector_store():
        print("⚠️ Vector Store ID not found in OpenAI. Make sure it exists or update your .env file.")

    app.run(debug=True)
