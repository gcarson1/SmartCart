from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models.models import db, ChatSession, ChatMessage, Store
from services.openai_service import run_assistant, run_assistant_for_store
from services.openai_service import client
from sqlalchemy import desc


chat_bp = Blueprint('chat', __name__)

@chat_bp.route("/new_chat", methods=["POST"])
@login_required
def new_chat():
    data = request.get_json() or {}
    store_id = data.get("store_id")
    if store_id:
        count = ChatSession.query.filter_by(user_id=current_user.user_id, store_id=store_id).count()
        store = Store.query.get(store_id)
        store_name = store.name if store else "Store"
        title = f"{store_name} Chat {count + 1}"
    else:
        title = "New Chat"
    thread = client.beta.threads.create()
    new_session = ChatSession(
        user_id=current_user.user_id,
        title=title,
        store_id=store_id,
        thread_id=thread.id  # <-- Save it
    )    
    db.session.add(new_session)
    db.session.commit()
    return jsonify({"session_id": new_session.session_id, "title": new_session.title})

from sqlalchemy import desc

@chat_bp.route("/chat_sessions", methods=["GET"])
@login_required
def chat_sessions():
    sessions = ChatSession.query.filter_by(user_id=current_user.user_id)\
        .order_by(ChatSession.created_at.desc()).all()

    session_list = []
    for s in sessions:
        # Fetch most recent chat message for this session
        last_msg = ChatMessage.query.filter_by(session_id=s.session_id)\
            .order_by(ChatMessage.sent_at.desc()).first()

        # Use the message text or fallback string
        snippet = last_msg.message if last_msg else "(No messages yet)"

        # Truncate the snippet to 50 characters
        if len(snippet) > 35:
            snippet = snippet[:35] + "..."

        session_list.append({
            "session_id": s.session_id,
            "title": s.title,
            "store_id": s.store_id,
            "created_at": s.created_at.isoformat(),
            "snippet": snippet
        })

    return jsonify(session_list)

@chat_bp.route("/chat_history", methods=["GET"])
@login_required
def chat_history():
    session_id = request.args.get("session_id")
    if not session_id:
        return jsonify({"error": "No session id provided."}), 400
    messages = ChatMessage.query.filter_by(user_id=current_user.user_id, session_id=session_id).order_by(ChatMessage.sent_at).all()
    history = [{'sender': msg.sender, 'message': msg.message} for msg in messages]
    return jsonify(history)

@chat_bp.route("/get", methods=["POST"])
def get_bot_response():
    data = request.get_json() or {}
    user_input = data.get('msg')
    session_id = data.get('session_id')

    if not session_id:
        return jsonify({'error': 'No session id provided.'}), 400
    if not user_input:
        return jsonify({'error': 'No message provided.'}), 400

    session_obj = ChatSession.query.filter_by(session_id=session_id, user_id=current_user.user_id).first()
    store_id = session_obj.store_id if session_obj else None

    user_message = ChatMessage(session_id=session_id, user_id=current_user.user_id, sender='user', message=user_input)
    db.session.add(user_message)
    db.session.commit()

    if store_id:
        store = Store.query.get(store_id)
        bot_response = run_assistant_for_store(store.assistant_id, user_input) if store and store.assistant_id else run_assistant(user_input)
    else:
        bot_response = run_assistant(user_input)

    bot_message = ChatMessage(session_id=session_id, user_id=current_user.user_id, sender='bot', message=bot_response)
    db.session.add(bot_message)
    db.session.commit()

    return jsonify({'response': bot_response})

@chat_bp.route("/delete_chat_history", methods=["POST"])
@login_required
def delete_chat_history():
    data = request.get_json() or {}
    session_id = data.get("session_id")
    if not session_id:
        return jsonify({"error": "No session id provided."}), 400
    try:
        session_id = int(session_id)
    except ValueError:
        return jsonify({"error": "Invalid session id provided."}), 400

    session_to_delete = ChatSession.query.filter_by(session_id=session_id, user_id=current_user.user_id).first()
    if not session_to_delete:
        return jsonify({"message": "Chat session not found."}), 200

    ChatMessage.query.filter_by(session_id=session_id, user_id=current_user.user_id).delete()
    db.session.delete(session_to_delete)
    db.session.commit()

    return jsonify({"message": "Chat session deleted successfully."})
