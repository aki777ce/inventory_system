import sqlite3
from datetime import datetime

class SQLiteDB:
    def __init__(self, db_path):
        self.db_path = db_path
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def init_db(self):
        conn = self.get_connection()
        c = conn.cursor()

        # テーブル作成
        c.execute('''
        CREATE TABLE IF NOT EXISTS staff (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL
        )
        ''')

        c.execute('''
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL
        )
        ''')

        c.execute('''
        CREATE TABLE IF NOT EXISTS model_numbers (
            id INTEGER PRIMARY KEY,
            item_id INTEGER,
            number TEXT NOT NULL,
            FOREIGN KEY (item_id) REFERENCES items (id)
        )
        ''')

        c.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY,
            order_date TEXT NOT NULL,
            orderer TEXT NOT NULL,
            item_name TEXT NOT NULL,
            model_number TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            unit TEXT NOT NULL,
            reason TEXT,
            delivery_status TEXT DEFAULT '未納品',
            delivery_date TEXT,
            receiver TEXT
        )
        ''')

        conn.commit()
        conn.close()

    def get_all_staff(self):
        conn = self.get_connection()
        c = conn.cursor()
        c.execute('SELECT * FROM staff')
        results = [{'id': row[0], 'name': row[1]} for row in c.fetchall()]
        conn.close()
        return results

    def add_staff(self, name):
        conn = self.get_connection()
        c = conn.cursor()
        c.execute('INSERT INTO staff (name) VALUES (?)', (name,))
        staff_id = c.lastrowid
        conn.commit()
        conn.close()
        return staff_id

    def get_all_items(self):
        conn = self.get_connection()
        c = conn.cursor()
        # アイテムの基本情報を取得
        c.execute('SELECT id, name FROM items')
        items = []
        for row in c.fetchall():
            item_id, item_name = row
            # 各アイテムの型番を取得
            c.execute('SELECT number FROM model_numbers WHERE item_id = ?', (item_id,))
            model_numbers = [model[0] for model in c.fetchall()]
            items.append({
                'id': item_id,
                'name': item_name,
                'model_numbers': model_numbers
            })
        conn.close()
        return items

    def add_item(self, name):
        conn = self.get_connection()
        c = conn.cursor()
        c.execute('INSERT INTO items (name) VALUES (?)', (name,))
        item_id = c.lastrowid
        conn.commit()
        conn.close()
        return item_id

    def add_model_number(self, item_id, number):
        conn = self.get_connection()
        c = conn.cursor()
        c.execute('INSERT INTO model_numbers (item_id, number) VALUES (?, ?)', 
                 (item_id, number))
        model_id = c.lastrowid
        conn.commit()
        conn.close()
        return model_id

    def get_model_numbers(self, item_id):
        conn = self.get_connection()
        c = conn.cursor()
        c.execute('SELECT id, number FROM model_numbers WHERE item_id = ?', (item_id,))
        models = [{'id': row[0], 'number': row[1]} for row in c.fetchall()]
        conn.close()
        return models

    def add_order(self, order_data):
        conn = self.get_connection()
        c = conn.cursor()
        c.execute('''
            INSERT INTO orders 
            (order_date, orderer, item_name, model_number, quantity, unit, reason)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            order_data['order_date'],
            order_data['orderer'],
            order_data['item_name'],
            order_data['model_number'],
            order_data['quantity'],
            order_data['unit'],
            order_data.get('reason', '')
        ))
        order_id = c.lastrowid
        conn.commit()
        conn.close()
        return order_id

    def get_pending_orders(self):
        conn = self.get_connection()
        c = conn.cursor()
        c.execute('SELECT * FROM orders WHERE delivery_status = "未納品"')
        columns = [description[0] for description in c.description]
        results = [dict(zip(columns, row)) for row in c.fetchall()]
        conn.close()
        return results

    def get_delivered_orders(self):
        conn = self.get_connection()
        c = conn.cursor()
        c.execute('SELECT * FROM orders WHERE delivery_status = "納品済み"')
        columns = [description[0] for description in c.description]
        results = [dict(zip(columns, row)) for row in c.fetchall()]
        conn.close()
        return results

    def update_delivery_status(self, order_id, receiver):
        conn = self.get_connection()
        c = conn.cursor()
        c.execute('''
            UPDATE orders 
            SET delivery_status = "納品済み",
                delivery_date = ?,
                receiver = ?
            WHERE id = ?
        ''', (
            datetime.now().strftime('%Y-%m-%d'),
            receiver,
            order_id
        ))
        conn.commit()
        conn.close()
