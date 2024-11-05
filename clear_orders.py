from app import create_app
from app.sqlite_db import SQLiteDB
from config import Config

app = create_app()
db = SQLiteDB(Config.DATABASE_PATH)

def clear_orders():
    try:
        # データベース接続
        conn = db.get_connection()
        c = conn.cursor()
        
        # 発注データのみ削除
        c.execute('DELETE FROM orders')
        
        # 変更を保存
        conn.commit()
        conn.close()
        
        print("発注データを削除しました")
        print("※スタッフ、物品、型番のマスターデータは保持されています")
        
    except Exception as e:
        print(f"エラーが発生しました: {str(e)}")

if __name__ == '__main__':
    clear_orders()
