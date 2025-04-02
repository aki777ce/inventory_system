from app import app
from models import db
import os

with app.app_context():
    # データベースファイルのパス
    db_path = os.path.join(os.getcwd(), 'inventory.db')
    instance_db_path = os.path.join(os.getcwd(), 'instance', 'inventory.db')
    
    # データベース接続を閉じる
    db.session.close()
    
    # データベースファイルが存在する場合は削除
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"{db_path} を削除しました。")
    
    if os.path.exists(instance_db_path):
        os.remove(instance_db_path)
        print(f"{instance_db_path} を削除しました。")
    
    # データベースを再作成
    db.create_all()
    print("データベースを再作成しました。")
    
    # 初期データの読み込み
    try:
        from init_data import init_db
        init_db()
        print("初期データを読み込みました。")
    except Exception as e:
        print(f"初期データの読み込みに失敗しました: {e}")
