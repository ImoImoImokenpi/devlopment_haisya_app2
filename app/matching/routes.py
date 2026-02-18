from flask import Blueprint, render_template
from flask_login import login_required
from ..models import Room

matching_bp = Blueprint("matching", __name__, url_prefix="/matching")

@matching_bp.route("/preview/<int:room_id>")
@login_required
def preview(room_id):
    room = Room.query.get_or_404(room_id)
    return render_template("preview.html", room=room)
