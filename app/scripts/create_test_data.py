import random
from app import create_app # __init__.pyからcreate_appをインポート
from app.extensions import db  # extensions.pyからdbをインポート
from app.models import User, Entry, Room  # モデルをインポート

def run_seed(room_id):
    # アプリを作成し、DB操作ができる状態（コンテキスト）にする
    app = create_app()
    
    with app.app_context():
        room = Room.query.get(room_id)
        if not room:
            print(f"ID:{room_id} のルームが見つかりません。")
            return

        print(f"ルーム「{room.name}」に100人のダミーデータを生成中...")

        for i in range(1, 101):
            # 1. ユーザー作成
            username = f"test_u_{i:03d}_{random.randint(1000, 9999)}" # 重複防止
            user = User(
                username=username,
                password="1234pass"
                # name=f"テスト参加者{i:03d}"
            )
            # パスワードが必要なモデルならここで設定
            if hasattr(user, 'set_password'):
                user.set_password('password123')
                
            db.session.add(user)
            db.session.flush()  # IDを確定させる

            # 2. エントリー作成
            # 20%の確率でドライバーにする（約20台）
            is_driver = random.random() < 0.20
            
            entry = Entry(
                room_id=room_id,
                user_id=user.id,
                has_car=is_driver,
                capacity=random.randint(2, 4) if is_driver else 0, # 2〜4人乗り
                # 必要に応じて他のカラム（has_rehersal等）を追加
            )
            db.session.add(entry)

        try:
            db.session.commit()
            print(f"成功！100人のエントリーを登録しました。")
        except Exception as e:
            db.session.rollback()
            print(f"エラーが発生しました: {e}")

if __name__ == "__main__":
    # ブラウザで作成したルームのIDを指定してください
    # 例: http://localhost:5000/rooms/5 だったら 5
    target_id = int(input("データを流し込むRoom IDを入力してください: "))
    run_seed(target_id)