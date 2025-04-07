import re
import time
from . import client

def get_existing_assistant(ASSISTANT_ID):
    assistants = client.beta.assistants.list()
    for assistant in assistants.data:
        if assistant.id == ASSISTANT_ID:
            print(f"Using existing Assistant ID: {ASSISTANT_ID}")
            return ASSISTANT_ID
    return None

def get_existing_vector_store(VECTOR_STORE_ID):
    vector_stores = client.beta.vector_stores.list()
    for store in vector_stores.data:
        if store.id == VECTOR_STORE_ID:
            print(f"Using existing Vector Store ID: {VECTOR_STORE_ID}")
            return VECTOR_STORE_ID
    return None

def run_assistant(user_input, ASSISTANT_ID):
    thread = client.beta.threads.create()
    print(f"Thread Created: {thread.id}")

    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=user_input
    )

    client.beta.threads.runs.create_and_poll(
        thread_id=thread.id, assistant_id=ASSISTANT_ID
    )

    messages = client.beta.threads.messages.list(thread_id=thread.id)
    
    response_text = ""
    for block in messages.data[0].content:
        if block.type == "text":
            response_text += block.text.value

    pattern = r'【\d+†source】'
    return re.sub(pattern, '', response_text)

def run_assistant_for_store(assistant_id, user_input):
    thread = client.beta.threads.create()
    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=user_input
    )
    client.beta.threads.runs.create_and_poll(
        thread_id=thread.id,
        assistant_id=assistant_id
    )
    messages = client.beta.threads.messages.list(thread_id=thread.id)

    response_text = ""
    for block in messages.data[0].content:
        if block.type == "text":
            response_text += block.text.value

    pattern = r'【\d+†source】'
    return re.sub(pattern, '', response_text)

def create_dynamic_assistant(txt_file):
    txt_file.seek(0)
    try:
        uploaded_file = client.files.create(
            file=(txt_file.filename, txt_file.stream, "text/plain"),
            purpose="assistants"
        )
        print(f"Uploaded file, id: {uploaded_file.id}")
    except Exception as e:
        raise Exception(f"Failed to upload file: {e}")

    try:
        vector_store = client.beta.vector_stores.create(
            name=f"Dynamic Vector Store {int(time.time())}",
            file_ids=[uploaded_file.id]
        )
        new_vector_store_id = vector_store.id
        print(f"Created new vector store with ID: {new_vector_store_id}")
    except Exception as e:
        raise Exception(f"Failed to create vector store: {e}")

    try:
        assistant = client.beta.assistants.create(
            name=f"Dynamic Assistant {int(time.time())}",
            instructions="You are a helpful assistant that uses file search to answer questions based on the uploaded document.",
            model="gpt-4o-mini",
            tools=[{"type": "file_search"}],
            tool_resources={
                "file_search": {"vector_store_ids": [new_vector_store_id]}
            }
        )
        new_assistant_id = assistant.id
        print(f"Created new assistant with ID: {new_assistant_id}")
    except Exception as e:
        raise Exception(f"Failed to create dynamic assistant: {e}")

    return new_assistant_id, new_vector_store_id, uploaded_file.id
