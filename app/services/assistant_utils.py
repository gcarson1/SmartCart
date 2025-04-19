import time
from app.services.openai_service import client

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
            instructions="You are a helpful retail store assistant and your name is SmartCart. You use file search to answer questions based on the  inventory data. Be brief, accurate, and friendly. If you can't find the answer in the document you may answer from outside sources only if the question was about something that is in the document for example if the document has doritos and the user asks if wheat is in doritos you are allowed to look at other sources to answer it. Dont be scared to use an emoji in your responses for characater.",
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
