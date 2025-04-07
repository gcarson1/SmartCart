import time
from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from flask_login import login_required, current_user
from .models import Store
from . import db, client
from .utils import create_dynamic_assistant

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin_panel', methods=["GET", "POST"])
@login_required
def admin_panel():
    store = Store.query.filter_by(user_id=current_user.user_id).first()
    message = None
    
    # Step 1: If no store exists, show the Store Info Form.
    if not store:
        if request.method == "POST" and 'name' in request.form:
            name = request.form.get("name")
            address = request.form.get("address")
            city = request.form.get("city")
            state = request.form.get("state")
            zip_code = request.form.get("zip_code")
            if not (name and address and city and state and zip_code):
                message = "All fields are required."
            else:
                new_store = Store(
                    user_id=current_user.user_id,
                    name=name,
                    address=address,
                    city=city,
                    state=state,
                    zip_code=zip_code
                )
                db.session.add(new_store)
                db.session.commit()
                message = "Store information saved. Please upload your inventory file."
                store = new_store
        return render_template("admin_panel.html", message=message, store=store)
    
    # Step 2: If store exists but no inventory file is present, handle file upload.
    if not store.inventory_file_id:
        if request.method == "POST" and 'txtFile' in request.files:
            txt_file = request.files.get("txtFile")
            if txt_file:
                try:
                    txt_file.seek(0)
                    if store.assistant_id:
                        uploaded_file = client.files.create(
                            file=(txt_file.filename, txt_file.stream, "text/plain"),
                            purpose="assistants"
                        )
                        new_file_id = uploaded_file.id
                        print(f"Uploaded new file, id: {new_file_id}")
                        
                        vector_store = client.beta.vector_stores.create(
                            name=f"Dynamic Vector Store {int(time.time())}",
                            file_ids=[new_file_id]
                        )
                        new_vector_store_id = vector_store.id
                        print(f"Created new vector store with ID: {new_vector_store_id}")
                        
                        client.beta.assistants.update(
                            store.assistant_id,
                            tool_resources={"file_search": {"vector_store_ids": [new_vector_store_id]}}
                        )
                        new_assistant_id = store.assistant_id
                        print(f"Updated existing assistant {new_assistant_id} with new vector store.")
                    else:
                        new_assistant_id, new_vector_store_id, new_file_id = create_dynamic_assistant(txt_file)
                    
                    store.inventory_file_id = new_file_id
                    store.vector_store_id = new_vector_store_id
                    store.assistant_id = new_assistant_id
                    db.session.commit()
                    message = f"Inventory updated. New File ID: {new_file_id}"
                except Exception as e:
                    message = f"Error updating inventory: {str(e)}"
            else:
                message = "No file selected."
        return render_template("admin_panel.html", message=message, store=store)
    
    # Step 3: If store has an inventory file, show the dashboard view.
    return render_template("admin_panel.html", message=message, store=store)

@admin_bp.route('/update_inventory', methods=["GET", "POST"])
@login_required
def update_inventory():
    store = Store.query.filter_by(user_id=current_user.user_id).first()
    if not store:
        return redirect(url_for('admin.admin_panel'))
    
    message = None
    if request.method == "POST":
        if 'txtFile' not in request.files:
            message = "No file selected."
        else:
            txt_file = request.files.get("txtFile")
            if txt_file:
                try:
                    if store.inventory_file_id:
                        try:
                            client.files.delete(store.inventory_file_id)
                        except Exception as e:
                            print(f"Error deleting old file: {e}")
                    
                    txt_file.seek(0)
                    try:
                        uploaded_file = client.files.create(
                            file=(txt_file.filename, txt_file.stream, "text/plain"),
                            purpose="assistants"
                        )
                        new_file_id = uploaded_file.id
                        print(f"Uploaded new file, id: {new_file_id}")
                    except Exception as e:
                        raise Exception(f"Failed to upload file: {e}")
                    
                    try:
                        vector_store = client.beta.vector_stores.create(
                            name=f"Dynamic Vector Store {int(time.time())}",
                            file_ids=[new_file_id]
                        )
                        new_vector_store_id = vector_store.id
                        print(f"Created new vector store with ID: {new_vector_store_id}")
                    except Exception as e:
                        raise Exception(f"Failed to create vector store: {e}")
                    
                    if store.assistant_id:
                        try:
                            client.beta.assistants.update(
                                store.assistant_id,
                                tool_resources={"file_search": {"vector_store_ids": [new_vector_store_id]}}
                            )
                            new_assistant_id = store.assistant_id
                            print(f"Updated existing assistant {new_assistant_id} with new vector store.")
                        except Exception as e:
                            print(f"Error updating assistant: {e}")
                            new_assistant_id = store.assistant_id
                    else:
                        try:
                            assistant = client.beta.assistants.create(
                                name=f"Dynamic Assistant {int(time.time())}",
                                instructions="You are a helpful assistant that uses file search to answer questions based on the uploaded document.",
                                model="gpt-4o-mini",
                                tools=[{"type": "file_search"}],
                                tool_resources={"file_search": {"vector_store_ids": [new_vector_store_id]}}
                            )
                            new_assistant_id = assistant.id
                            print(f"Created new assistant with ID: {new_assistant_id}")
                        except Exception as e:
                            raise Exception(f"Failed to create dynamic assistant: {e}")
                    
                    store.inventory_file_id = new_file_id
                    store.vector_store_id = new_vector_store_id
                    store.assistant_id = new_assistant_id  
                    db.session.commit()
                    
                    message = f"Inventory updated. New File ID: {new_file_id}"
                except Exception as e:
                    message = f"Error updating inventory: {str(e)}"
            else:
                message = "No file selected."
    return render_template("update_inventory.html", message=message, store=store)

@admin_bp.route('/delete_uploaded_file', methods=["POST"])
def delete_uploaded_file():
    data = request.get_json() or {}
    file_id = data.get("file_id")
    if not file_id:
        return jsonify({"error": "No file id provided."}), 400
    try:
        deletion_result = client.files.delete(file_id)
    except Exception as e:
        error_message = str(e)
        if "No such File object" in error_message:
            deletion_result = {"message": "File not found; treating as deleted."}
        else:
            print("Error deleting file:", e)
            return jsonify({"success": False, "error": error_message})
    
    store = Store.query.filter_by(inventory_file_id=file_id).first()
    if store:
        if store.vector_store_id:
            try:
                client.beta.vector_stores.delete(store.vector_store_id)
            except Exception as e:
                print("Error deleting vector store:", e)
        store.inventory_file_id = None
        store.vector_store_id = None
        db.session.commit()
    
    return jsonify({
        "success": True,
        "message": "File and associated vector store deleted, store record updated.",
        "result": deletion_result
    })
