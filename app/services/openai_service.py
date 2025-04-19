import openai
import os
import re
from dotenv import load_dotenv

load_dotenv()

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
ASSISTANT_ID = os.getenv("ASSISTANT_ID")
VECTOR_STORE_ID = os.getenv("VECTOR_STORE_ID")

def get_existing_assistant():
    assistants = client.beta.assistants.list()
    for assistant in assistants.data:
        if assistant.id == ASSISTANT_ID:
            print(f"Using existing Assistant ID: {ASSISTANT_ID}")
            return ASSISTANT_ID
    return None

def get_existing_vector_store():
    vector_stores = client.beta.vector_stores.list()
    for store in vector_stores.data:
        if store.id == VECTOR_STORE_ID:
            print(f"Using existing Vector Store ID: {VECTOR_STORE_ID}")
            return VECTOR_STORE_ID
    return None

def run_assistant(user_input, thread_id):
    client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=user_input
    )

    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread_id, assistant_id=ASSISTANT_ID
    )

    messages = client.beta.threads.messages.list(thread_id=thread_id)

    response_text = ""
    for block in messages.data[0].content:
        if block.type == "text":
            response_text += block.text.value

    pattern = r'【\d+†source】'
    response_text = re.sub(pattern, '', response_text)

    return response_text

def run_assistant_for_store(assistant_id, user_input):
    thread = client.beta.threads.create()
    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=user_input
    )
    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread.id,
        assistant_id=assistant_id
    )
    messages = client.beta.threads.messages.list(thread_id=thread.id)

    response_text = ""
    for block in messages.data[0].content:
        if block.type == "text":
            response_text += block.text.value

    pattern = r'【\d+†source】'
    response_text = re.sub(pattern, '', response_text)
    return response_text