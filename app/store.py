from flask import Blueprint, jsonify
from flask_login import login_required
from .models import Store

store_bp = Blueprint('store', __name__)

@store_bp.route('/list', methods=["GET"])
@login_required
def list_stores():
    all_stores = Store.query.all()
    results = []
    for s in all_stores:
        results.append({
            "store_id": s.store_id,
            "name": s.name,
            "address": s.address,
            "assistant_id": s.assistant_id
        })
    return jsonify(results)
