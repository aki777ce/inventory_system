from app import app
from models import db

with app.app_context():
    # 既存のテーブルを保持したままスキーマを更新
    db.create_all()
    print("データベースが更新されました。")
