# profile/routes.py（新規作成）

import os
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from ..extensions import db

profile_bp = Blueprint("profile", __name__, url_prefix="/profile")

UPLOAD_FOLDER = 'app/static/uploads/icons'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@profile_bp.route('/edit', methods=['GET', 'POST'])
@login_required
def edit():
    if request.method == 'POST':
        display_name = request.form.get('display_name', '').strip()
        file = request.files.get('icon')

        # 表示名の更新
        current_user.display_name = display_name or None

        # アイコン画像のアップロード
        if file and file.filename and allowed_file(file.filename):
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            ext = file.filename.rsplit('.', 1)[1].lower()
            filename = f"user_{current_user.id}.{ext}"
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)
            current_user.icon = f"uploads/icons/{filename}"

        db.session.commit()
        flash("プロフィールを更新しました", "success")
        return redirect(url_for('profile.edit'))

    return render_template('profile_setting.html')