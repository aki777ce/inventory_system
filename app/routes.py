from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from datetime import datetime
from .sqlite_db import SQLiteDB
from config import Config
import pandas as pd
import os

main = Blueprint('main', __name__)
db = SQLiteDB(Config.DATABASE_PATH)

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/new_order', methods=['GET', 'POST'])
def new_order():
    if request.method == 'POST':
        order_data = {
            'order_date': request.form['order_date'],
            'orderer': request.form['orderer'],
            'item_name': request.form['item_name'],
            'model_number': request.form['model_number'],
            'quantity': request.form['quantity'],
            'unit': request.form['unit'],
            'reason': request.form.get('reason', '')
        }
        try:
            db.add_order(order_data)
            flash('発注が登録されました', 'success')
        except Exception as e:
            flash(f'エラーが発生しました: {str(e)}', 'error')
        return redirect(url_for('main.order_list'))
    
    staff = db.get_all_staff()
    items = db.get_all_items()
    today_date = datetime.now().strftime('%Y-%m-%d')
    return render_template('new_order.html', 
                         staff=staff,
                         items=items,
                         today_date=today_date)

@main.route('/order_list')
def order_list():
    orders = db.get_pending_orders()
    staff = db.get_all_staff()
    return render_template('order_list.html', 
                         orders=orders,
                         staff=staff)

@main.route('/delivered_list')
def delivered_list():
    orders = db.get_delivered_orders()
    # 納品日で降順にソート（新しい順）
    orders.sort(key=lambda x: x['delivery_date'], reverse=True)
    return render_template('delivered_list.html', orders=orders)

@main.route('/mark_delivered/<int:order_id>', methods=['POST'])
def mark_delivered(order_id):
    try:
        receiver = request.form['receiver']
        db.update_delivery_status(order_id, receiver)
        flash('納品処理が完了しました', 'success')
    except Exception as e:
        flash(f'納品処理中にエラーが発生しました: {str(e)}', 'error')
    return redirect(url_for('main.order_list'))

@main.route('/admin')
def admin():
    staffs = db.get_all_staff()
    items = db.get_all_items()
    return render_template('admin.html', staffs=staffs, items=items)

@main.route('/admin/add_staff', methods=['POST'])
def add_staff():
    name = request.form.get('name')
    if name:
        try:
            db.add_staff(name)
            flash('スタッフを追加しました', 'success')
        except Exception as e:
            flash(f'スタッフの追加に失敗しました: {str(e)}', 'error')
    return redirect(url_for('main.admin'))

@main.route('/admin/delete_staff/<int:staff_id>')
def delete_staff(staff_id):
    try:
        conn = db.get_connection()
        c = conn.cursor()
        c.execute('DELETE FROM staff WHERE id = ?', (staff_id,))
        conn.commit()
        conn.close()
        flash('スタッフを削除しました', 'success')
    except Exception as e:
        flash(f'削除に失敗しました: {str(e)}', 'error')
    return redirect(url_for('main.admin'))

@main.route('/admin/add_item', methods=['POST'])
def add_item():
    name = request.form.get('name')
    model_numbers = request.form.get('model_numbers', '').split(',')
    
    if name:
        try:
            item_id = db.add_item(name)
            for number in model_numbers:
                number = number.strip()
                if number:
                    db.add_model_number(item_id, number)
            flash('物品を追加しました', 'success')
        except Exception as e:
            flash(f'物品の追加に失敗しました: {str(e)}', 'error')
    return redirect(url_for('main.admin'))

@main.route('/admin/delete_item/<int:item_id>')
def delete_item(item_id):
    try:
        conn = db.get_connection()
        c = conn.cursor()
        # 関連する型番も削除
        c.execute('DELETE FROM model_numbers WHERE item_id = ?', (item_id,))
        c.execute('DELETE FROM items WHERE id = ?', (item_id,))
        conn.commit()
        conn.close()
        flash('物品を削除しました', 'success')
    except Exception as e:
        flash(f'削除に失敗しました: {str(e)}', 'error')
    return redirect(url_for('main.admin'))

@main.route('/admin/add_model', methods=['POST'])
def add_model():
    try:
        item_id = request.form.get('item_id', type=int)
        number = request.form.get('number')
        
        if item_id and number:
            db.add_model_number(item_id, number)
            flash('型番を追加しました', 'success')
        else:
            flash('必要な情報が不足しています', 'error')
    except Exception as e:
        flash(f'型番の追加に失敗しました: {str(e)}', 'error')
    
    return redirect(url_for('main.admin'))

@main.route('/get_model_numbers/<item_name>')
def get_model_numbers(item_name):
    items = db.get_all_items()
    item = next((item for item in items if item['name'] == item_name), None)
    if item:
        models = db.get_model_numbers(item['id'])
        return jsonify([{'id': m['id'], 'number': m['number']} for m in models])
    return jsonify([])

@main.route('/export_list')
def export_list():
    try:
        # 全ての注文データを取得
        orders = db.get_delivered_orders()
        
        # DataFrameに変換
        df = pd.DataFrame(orders)
        
        # エクスポートファイルのパス
        export_dir = os.path.dirname(Config.DATABASE_PATH)
        excel_file = os.path.join(export_dir, 'orders_export.xlsx')
        
        # Excelファイルとして保存
        df.to_excel(excel_file, index=False, encoding='utf-8')
        
        try:
            return send_file(
                excel_file,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name='発注データ一覧.xlsx'
            )
        finally:
            # ファイル送信後、一時ファイルを削除
            if os.path.exists(excel_file):
                os.remove(excel_file)
                
    except Exception as e:
        flash(f'エクスポート中にエラーが発生しました: {str(e)}', 'error')
        return redirect(url_for('main.delivered_list'))
