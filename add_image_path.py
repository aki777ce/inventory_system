import sqlite3
import os

def add_image_path_column():
    # メインのデータベースファイル
    main_db_path = 'inventory.db'
    # インスタンスディレクトリのデータベースファイル
    instance_db_path = os.path.join('instance', 'inventory.db')
    
    db_paths = []
    if os.path.exists(main_db_path):
        db_paths.append(main_db_path)
    if os.path.exists(instance_db_path):
        db_paths.append(instance_db_path)
    
    for db_path in db_paths:
        try:
            # データベースに接続
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # model_numbersテーブルに画像パスカラムを追加
            cursor.execute("PRAGMA table_info(model_numbers)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'image_path' not in columns:
                cursor.execute("ALTER TABLE model_numbers ADD COLUMN image_path TEXT")
                print(f"{db_path}: model_numbersテーブルにimage_pathカラムを追加しました。")
            else:
                print(f"{db_path}: image_pathカラムはすでに存在します。")
            
            # 変更をコミット
            conn.commit()
            conn.close()
            print(f"{db_path}: マイグレーション完了")
        except Exception as e:
            print(f"{db_path}: エラー発生 - {e}")

if __name__ == "__main__":
    add_image_path_column()
    print("マイグレーション処理が完了しました。")
