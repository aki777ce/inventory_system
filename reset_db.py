from app import app, db
from models import Category, Item, ModelNumber, Order

def reset_database():
    """データベースを初期化する"""
    try:
        with app.app_context():
            # 全てのテーブルを削除
            print("テーブルを削除中...")
            db.session.commit()  # 既存のトランザクションをコミット
            Order.__table__.drop(db.engine)
            ModelNumber.__table__.drop(db.engine)
            Item.__table__.drop(db.engine)
            Category.__table__.drop(db.engine)


            # テーブルを再作成
            print("テーブルを再作成中...")
            db.create_all()

            print("データベースの初期化が完了しました。")
    except Exception as e:
        print(f"エラーが発生しました: {str(e)}")
        db.session.rollback()

if __name__ == "__main__":
    # 確認プロンプト
    answer = input("全てのデータが削除されます。本当に実行しますか？ (yes/no): ")
    if answer.lower() == 'yes':
        reset_database()
    else:
        print("キャンセルしました。")
