from flask import Blueprint, request, redirect, url_for, render_template, jsonify
from flask_login import login_required, current_user
from app.models.models import Store
from app.extensions import db
from app.services.assistant_utils import create_dynamic_assistant
import time

admin_bp = Blueprint("admin", __name__)

@admin_bp.route('/admin_panel', methods=["GET", "POST"])
@login_required
def admin_panel():
    store = Store.query.filter_by(user_id=current_user.user_id).first()
    message = None

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

    if not store.inventory_file_id:
        if request.method == "POST" and 'txtFile' in request.files:
            txt_file = request.files.get("txtFile")
            if txt_file:
                try:
                    if store.assistant_id:
                        from app.services.openai_service import client
                        uploaded_file = client.files.create(
                            file=(txt_file.filename, txt_file.stream, "text/plain"),
                            purpose="assistants"
                        )
                        new_file_id = uploaded_file.id

                        vector_store = client.beta.vector_stores.create(
                            name=f"Dynamic Vector Store {int(time.time())}",
                            file_ids=[new_file_id]
                        )
                        new_vector_store_id = vector_store.id

                        client.beta.assistants.update(
                            store.assistant_id,
                            tool_resources={"file_search": {"vector_store_ids": [new_vector_store_id]}}
                        )
                        new_assistant_id = store.assistant_id
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

    return render_template("admin_panel.html", message=message, store=store)

@admin_bp.route('/update_inventory', methods=["GET", "POST"])
@login_required
def update_inventory():
    from app.services.openai_service import client
    store = Store.query.filter_by(user_id=current_user.user_id).first()
    if not store:
        return redirect(url_for('admin.admin_panel'))

    message = None
    if request.method == "POST" and 'txtFile' in request.files:
        txt_file = request.files.get("txtFile")
        if txt_file:
            try:
                if store.inventory_file_id:
                    try:
                        client.files.delete(store.inventory_file_id)
                    except Exception as e:
                        print(f"Error deleting old file: {e}")

                uploaded_file = client.files.create(
                    file=(txt_file.filename, txt_file.stream, "text/plain"),
                    purpose="assistants"
                )
                new_file_id = uploaded_file.id

                vector_store = client.beta.vector_stores.create(
                    name=f"Dynamic Vector Store {int(time.time())}",
                    file_ids=[new_file_id]
                )
                new_vector_store_id = vector_store.id

                if store.assistant_id:
                    try:
                        client.beta.assistants.update(
                            store.assistant_id,
                            tool_resources={"file_search": {"vector_store_ids": [new_vector_store_id]}}
                        )
                        new_assistant_id = store.assistant_id
                    except Exception as e:
                        print(f"Error updating assistant: {e}")
                        new_assistant_id = store.assistant_id
                else:
                    assistant = client.beta.assistants.create(
                        name=f"Dynamic Assistant {int(time.time())}",
                        instructions="You are a helpful assistant that uses file search to answer questions based on the uploaded document.",
                        model="gpt-4o-mini",
                        tools=[{"type": "file_search"}],
                        tool_resources={"file_search": {"vector_store_ids": [new_vector_store_id]}}
                    )
                    new_assistant_id = assistant.id

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

@admin_bp.route("/stores")
@login_required
def list_stores():
    all_stores = Store.query.all()
    results = [
        {
            "store_id": s.store_id,
            "name": s.name,
            "address": s.address,
            "assistant_id": s.assistant_id
        } for s in all_stores
    ]
    return jsonify(results)

@admin_bp.route('/delete_uploaded_file', methods=["POST"])
def delete_uploaded_file():
    from app.services.openai_service import client
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