from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from models import db, Staff, Category, Item, ModelNumber, Order
from datetime import datetime, timedelta
from sqlalchemy import func, desc, or_
import os
import time
from werkzeug.utils import secure_filename
from flask import current_app

# 管理者用Blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# 管理者ルート
@admin_bp.route('/')
def index():
    """管理者トップページ"""
    return render_template('admin/index.html')

@admin_bp.route('/staff', methods=['GET', 'POST'])
def staff():
    """スタッフ管理ページ"""
    if request.method == 'POST':
        staff_id = request.form.get('staff_id')
        name = request.form.get('name')

        if staff_id:
            staff = Staff.query.get_or_404(staff_id)
            try:
                staff.name = name
                db.session.commit()
                flash('スタッフ情報を更新しました。', 'success')
            except Exception as e:
                db.session.rollback()
                flash('スタッフ情報の更新に失敗しました。', 'error')
        else:
            try:
                new_staff = Staff(name=name)
                db.session.add(new_staff)
                db.session.commit()
                flash('スタッフを追加しました。', 'success')
            except Exception as e:
                db.session.rollback()
                flash('スタッフの追加に失敗しました。', 'error')
        return redirect(url_for('admin.staff'))

    staff_list = Staff.query.order_by(Staff.name).all()
    return render_template('admin/staff.html', staff_list=staff_list)

@admin_bp.route('/staff/<int:staff_id>/delete', methods=['POST'])
def delete_staff(staff_id):
    """スタッフの削除"""
    staff = Staff.query.get_or_404(staff_id)
    try:
        # 発注データがあるか確認
        has_orders = Order.query.filter(
            db.or_(
                Order.requester_id == staff_id,
                Order.receiver_id == staff_id
            )
        ).first() is not None

        if has_orders:
            return jsonify({
                'success': False,
                'error': '発注データが存在するため削除できません。\n代わりに無効化してください。'
            }), 400
        else:
            db.session.delete(staff)
            db.session.commit()
            return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400

@admin_bp.route('/staff/<int:staff_id>/status', methods=['POST'])
def toggle_staff_status(staff_id):
    """スタッフの有効/無効切り替え"""
    staff = Staff.query.get_or_404(staff_id)
    try:
        # FormDataからデータを取得
        active_value = request.form.get('active')
        # 文字列の'true'または'false'をブール値に変換
        is_active = active_value.lower() == 'true' if active_value is not None else not staff.is_active
        
        staff.is_active = is_active
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400

@admin_bp.route('/categories', methods=['GET', 'POST'])
def categories():
    """分類管理ページ"""
    if request.method == 'POST':
        category_id = request.form.get('category_id')
        name = request.form.get('name')
        description = request.form.get('description')

        if category_id:
            # 編集の場合
            category = Category.query.get_or_404(category_id)
            try:
                category.name = name
                category.description = description
                db.session.commit()
                flash('分類情報を更新しました。', 'success')
            except Exception as e:
                db.session.rollback()
                flash('分類情報の更新に失敗しました。', 'error')
        else:
            # 新規追加の場合
            try:
                new_category = Category(name=name, description=description)
                db.session.add(new_category)
                db.session.commit()
                flash('分類を追加しました。', 'success')
            except Exception as e:
                db.session.rollback()
                flash('分類の追加に失敗しました。', 'error')
        return redirect(url_for('admin.categories'))

    categories = Category.query.order_by(Category.name).all()
    return render_template('admin/categories.html', categories=categories)

@admin_bp.route('/categories/<int:category_id>/delete', methods=['POST'])
def delete_category(category_id):
    """分類の削除"""
    category = Category.query.get_or_404(category_id)
    try:
        # 関連する物品があるか確認
        if Item.query.filter_by(category_id=category_id).first():
            return jsonify({
                'success': False,
                'error': 'この分類に関連する物品が存在するため削除できません。'
            }), 400

        db.session.delete(category)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400

@admin_bp.route('/categories/<int:category_id>/edit', methods=['POST'])
def edit_category(category_id):
    """分類の編集"""
    category = Category.query.get_or_404(category_id)
    try:
        category.name = request.form.get('name')
        category.description = request.form.get('description')
        db.session.commit()
        flash('分類情報を更新しました。', 'success')
    except Exception as e:
        db.session.rollback()
        flash('分類情報の更新に失敗しました。', 'error')
    return redirect(url_for('admin.categories'))

@admin_bp.route('/items', methods=['GET', 'POST'])
def items():
    """物品管理ページ"""
    if request.method == 'POST':
        item_id = request.form.get('item_id')
        category_id = request.form.get('category_id')
        name = request.form.get('name')

        if item_id:
            item = Item.query.get_or_404(item_id)
            try:
                item.name = name
                item.category_id = category_id
                db.session.commit()
                flash('物品情報を更新しました。', 'success')
            except Exception as e:
                db.session.rollback()
                flash('物品情報の更新に失敗しました。', 'error')
        else:
            try:
                new_item = Item(name=name, category_id=category_id)
                db.session.add(new_item)
                db.session.commit()
                flash('物品を追加しました。', 'success')

                # 型番追加への遷移のために新しい物品のIDを返す
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({
                        'success': True,
                        'item_id': new_item.id,
                        'name': new_item.name
                    })

            except Exception as e:
                db.session.rollback()
                flash('物品の追加に失敗しました。', 'error')
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({'success': False, 'error': str(e)}), 400

        return redirect(url_for('admin.items'))

    # カテゴリーと関連する物品を一括で取得
    categories = Category.query.options(
        db.joinedload(Category.items).joinedload(Item.model_numbers)
    ).order_by(Category.name).all()

    for category in categories:
        # 物品を名前順にソート
        category.items = sorted(category.items, key=lambda x: x.name)

    # 選択されたカテゴリIDまたは新しい分類名を取得
    selected_category_id = request.args.get('category_id', type=int)
    new_category = request.args.get('new_category')

    # 新しい分類名が指定されている場合、その分類のIDを取得
    if new_category and not selected_category_id:
        category = Category.query.filter_by(name=new_category).first()
        if category:
            selected_category_id = category.id

    return render_template('admin/items.html',
                         categories=categories,
                         selected_category_id=selected_category_id,
                         new_category=new_category)

@admin_bp.route('/items/<int:item_id>/status', methods=['POST'])
def toggle_item_status(item_id):
    """物品の有効/無効切り替え"""
    item = Item.query.get_or_404(item_id)
    try:
        data = request.get_json()
        item.is_active = data.get('active', not item.is_active)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400

@admin_bp.route('/items/<int:item_id>/delete', methods=['POST'])
def delete_item(item_id):
    """物品の削除"""
    item = Item.query.get_or_404(item_id)
    try:
        # 型番の存在確認
        has_model_numbers = ModelNumber.query.filter_by(item_id=item_id).first() is not None
        # 発注データの存在確認
        has_orders = Order.query.filter_by(item_id=item_id).first() is not None

        if has_orders:
            return jsonify({
                'success': False,
                'error': 'この物品に関連する発注データが存在するため削除できません。'
            }), 400
        elif has_model_numbers:
            return jsonify({
                'success': False,
                'error': 'この物品に型番が登録されています。\n本当に削除しますか？',
                'confirmRequired': True
            }), 200

        # 物品を削除
        db.session.delete(item)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400

@admin_bp.route('/model_numbers', methods=['POST'])
def add_model_number():
    """型番の追加"""
    item_id = request.form.get('item_id')
    number = request.form.get('number')
    notes = request.form.get('notes')
    
    # 画像ファイルの処理
    image_path = None
    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename and file.filename != '':
            # 安全なファイル名に変換
            filename = secure_filename(f"{item_id}_{number}_{int(time.time())}.{file.filename.rsplit('.', 1)[1].lower()}")
            upload_folder = os.path.join(current_app.static_folder, 'images', 'model_images')
            
            # アップロードディレクトリがなければ作成
            os.makedirs(upload_folder, exist_ok=True)
            
            file_path = os.path.join(upload_folder, filename)
            file.save(file_path)
            image_path = f"images/model_images/{filename}"

    try:
        new_model = ModelNumber(item_id=item_id, number=number, notes=notes, image_path=image_path)
        db.session.add(new_model)
        db.session.commit()
        flash('型番を追加しました。', 'success')
    except Exception as e:
        db.session.rollback()
        flash('型番の追加に失敗しました。', 'error')

    return redirect(url_for('admin.items'))

@admin_bp.route('/model_numbers/<int:model_id>/edit', methods=['POST'])
def edit_model_number(model_id):
    """型番と物品名の編集"""
    model = ModelNumber.query.get_or_404(model_id)
    try:
        # 型番の更新
        model.number = request.form.get('number')
        model.notes = request.form.get('notes')
        
        # 画像ファイルの処理
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename and file.filename != '':
                # 古い画像ファイルの削除
                if model.image_path:
                    old_file_path = os.path.join(current_app.static_folder, model.image_path)
                    if os.path.exists(old_file_path):
                        os.remove(old_file_path)
                
                # 新しい画像ファイルの保存
                filename = secure_filename(f"{model.item_id}_{model.number}_{int(time.time())}.{file.filename.rsplit('.', 1)[1].lower()}")
                upload_folder = os.path.join(current_app.static_folder, 'images', 'model_images')
                
                # アップロードディレクトリがなければ作成
                os.makedirs(upload_folder, exist_ok=True)
                
                file_path = os.path.join(upload_folder, filename)
                file.save(file_path)
                model.image_path = f"images/model_images/{filename}"

        # 物品名の更新
        item = Item.query.get(model.item_id)
        if item:
            item.name = request.form.get('item_name')

        db.session.commit()
        flash('情報を更新しました。', 'success')
    except Exception as e:
        db.session.rollback()
        flash('更新に失敗しました。', 'error')

    return redirect(url_for('admin.items'))

@admin_bp.route('/model_numbers/<int:model_id>/delete', methods=['POST'])
def delete_model_number(model_id):
    """型番の削除"""
    model = ModelNumber.query.get_or_404(model_id)
    try:
        # 発注データがあるか確認
        if Order.query.filter_by(model_number_id=model_id).first():
            return jsonify({
                'success': False,
                'error': 'この型番に関連する発注データが存在するため削除できません。'
            }), 400

        db.session.delete(model)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400

@admin_bp.route('/model_numbers/<int:model_id>/status', methods=['POST'])
def toggle_model_number_status(model_id):
    """型番の有効/無効切り替え"""
    model = ModelNumber.query.get_or_404(model_id)
    try:
        data = request.get_json()
        model.is_active = data.get('active', not model.is_active)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400

@admin_bp.route('/report')
def report():
    """レポートページ"""
    # 期間の取得（デフォルトは過去30日）
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    if request.args.get('start_date'):
        start_date = datetime.strptime(request.args.get('start_date'), '%Y-%m-%d')
    if request.args.get('end_date'):
        end_date = datetime.strptime(request.args.get('end_date'), '%Y-%m-%d')

    # 基本統計情報
    stats = {
        'total_orders': Order.query.filter(
            Order.order_date.between(start_date, end_date)
        ).count(),
        'delivered_orders': Order.query.filter(
            Order.order_date.between(start_date, end_date),
            Order.delivery_status == '納品済み'
        ).count(),
        'pending_orders': Order.query.filter(
            Order.order_date.between(start_date, end_date),
            Order.delivery_status == '未納品'
        ).count()
    }

    # 分類別統計
    category_stats = db.session.query(
        Category.name,
        func.count(Order.id).label('count')
    ).select_from(Category).join(
        Order, Category.id == Order.category_id
    ).filter(
        Order.order_date.between(start_date, end_date)
    ).group_by(Category.name).all()

   # 発注者別統計
    requester_stats = db.session.query(
        Staff.name,
        func.count(Order.id).label('count')
    ).select_from(Staff).join(
        Order, Staff.id == Order.requester_id
    ).filter(
        Order.order_date.between(start_date, end_date)
    ).group_by(Staff.name).all()

    # 発注TOP10
    top_items = db.session.query(
        Item.name,
        Category.name.label('category'),
        func.count(Order.id).label('order_count'),
        func.sum(Order.quantity).label('total_quantity'),
        Order.unit
    ).select_from(Item).join(
        Order, Item.id == Order.item_id
    ).join(
        Category, Item.category_id == Category.id
    ).filter(
        Order.order_date.between(start_date, end_date)
    ).group_by(
        Item.name, Category.name, Order.unit
    ).order_by(func.count(Order.id).desc()).limit(10).all()

    return render_template('admin/report.html',
        start_date=start_date.strftime('%Y-%m-%d'),
        end_date=end_date.strftime('%Y-%m-%d'),
        stats=stats,
        category_stats={
            'labels': [c[0] for c in category_stats],
            'data': [c[1] for c in category_stats]
        },
        requester_stats={
            'labels': [r[0] for r in requester_stats],
            'data': [r[1] for r in requester_stats]
        },
        top_items=[{
            'name': item[0],
            'category': item[1],
            'order_count': item[2],
            'total_quantity': item[3],
            'unit': item[4]
        } for item in top_items]
    )

# メインアプリケーションのルート
def register_main_routes(app):
    """メインアプリケーションのルートを登録する"""
    
    @app.route('/')
    def index():
        """トップページ"""
        return render_template('index.html')
    
    @app.route('/new_order', methods=['GET', 'POST'])
    def new_order():
        """新規発注ページ"""
        if request.method == 'POST':
            try:
                order = Order(
                    order_date=datetime.strptime(request.form['order_date'], '%Y-%m-%d'),
                    requester_id=request.form['requester'],
                    category_id=request.form['category'],
                    item_id=request.form['item'],
                    model_number_id=request.form['model_number'],
                    quantity=request.form['quantity'],
                    unit=request.form['unit'],
                    reason=request.form.get('reason', '')
                )
                db.session.add(order)
                db.session.commit()
                flash('発注が正常に登録されました。', 'success')
                return redirect(url_for('pending_orders'))
            except Exception as e:
                db.session.rollback()
                flash('発注の登録に失敗しました。', 'error')
                return redirect(url_for('new_order'))

        staff = Staff.query.filter_by(is_active=True).order_by(Staff.name).all()
        categories = Category.query.order_by(Category.name).all()
        return render_template('new_order.html',
                             staff=staff,
                             categories=categories,
                             today=datetime.now().strftime('%Y-%m-%d'))

    @app.route('/pending_orders')
    def pending_orders():
        """発注済みリスト"""
        try:
            # 基本クエリ
            query = db.session.query(Order).filter(Order.delivery_status == '未納品')
            
            # 検索条件の適用
            # 期間検索
            start_date = request.args.get('start_date')
            if start_date:
                query = query.filter(Order.order_date >= start_date)
            
            end_date = request.args.get('end_date')
            if end_date:
                query = query.filter(Order.order_date <= end_date)
            
            # スタッフ検索
            requester_id = request.args.get('requester_id')
            if requester_id:
                query = query.filter(Order.requester_id == requester_id)
            
            # 分類検索
            category_id = request.args.get('category_id')
            if category_id:
                query = query.join(ModelNumber, Order.model_number_id == ModelNumber.id).join(Item, ModelNumber.item_id == Item.id).filter(Item.category_id == category_id)
            
            # フリーワード検索
            keyword = request.args.get('keyword')
            if keyword:
                search_term = f"%{keyword}%"
                query = query.join(ModelNumber, Order.model_number_id == ModelNumber.id).join(Item, ModelNumber.item_id == Item.id).join(Staff, Order.requester_id == Staff.id).outerjoin(Category, Item.category_id == Category.id).filter(
                    or_(
                        Item.name.ilike(search_term),
                        ModelNumber.number.ilike(search_term),
                        Order.reason.ilike(search_term),
                        Staff.name.ilike(search_term),
                        Category.name.ilike(search_term)
                    )
                )
            
            # 並び順（新しい順）
            query = query.order_by(desc(Order.order_date))
            
            # クエリ実行
            orders = query.all()
            
            # 関連データの取得
            staff = db.session.query(Staff).filter(Staff.is_active == True).order_by(Staff.name).all()
            categories = db.session.query(Category).order_by(Category.name).all()
            
            # テンプレートのレンダリング
            return render_template('pending_orders.html',
                                orders=orders,
                                staffs=staff,
                                categories=categories,
                                today=datetime.now().strftime('%Y-%m-%d'))
        except Exception as e:
            # エラーをログに記録
            app.logger.error(f"Error in pending_orders: {str(e)}")
            # 最小限のテンプレートを返す
            return f"発注済みリストの読み込み中にエラーが発生しました: {str(e)}", 500

    @app.route('/delivered_orders')
    def delivered_orders():
        """納品済みリスト"""
        try:
            # 基本クエリ
            query = db.session.query(Order).filter(Order.delivery_status == '納品済み')
            
            # 検索条件の適用
            # 期間検索
            start_date = request.args.get('start_date')
            if start_date:
                query = query.filter(Order.delivery_date >= start_date)
            
            end_date = request.args.get('end_date')
            if end_date:
                query = query.filter(Order.delivery_date <= end_date)
            
            # スタッフ検索
            requester_id = request.args.get('requester_id')
            if requester_id:
                query = query.filter(Order.requester_id == requester_id)
            
            # 分類検索
            category_id = request.args.get('category_id')
            if category_id:
                query = query.join(ModelNumber, Order.model_number_id == ModelNumber.id).join(Item, ModelNumber.item_id == Item.id).filter(Item.category_id == category_id)
            
            # フリーワード検索
            keyword = request.args.get('keyword')
            if keyword:
                search_term = f"%{keyword}%"
                query = query.join(ModelNumber, Order.model_number_id == ModelNumber.id).join(Item, ModelNumber.item_id == Item.id).join(Staff, Order.requester_id == Staff.id).outerjoin(Category, Item.category_id == Category.id).filter(
                    or_(
                        Item.name.ilike(search_term),
                        ModelNumber.number.ilike(search_term),
                        Order.reason.ilike(search_term),
                        Staff.name.ilike(search_term),
                        Category.name.ilike(search_term)
                    )
                )
            
            # クエリ実行
            orders = query.all()
            
            # 関連データの取得
            staff = db.session.query(Staff).filter(Staff.is_active == True).order_by(Staff.name).all()
            categories = db.session.query(Category).order_by(Category.name).all()
            
            # テンプレートのレンダリング
            return render_template('delivered_orders.html',
                                orders=orders,
                                staffs=staff,
                                categories=categories)
        except Exception as e:
            # エラーをログに記録
            app.logger.error(f"Error in delivered_orders: {str(e)}")
            # 最小限のテンプレートを返す
            return f"納品済みリストの読み込み中にエラーが発生しました: {str(e)}", 500

    @app.route('/get_items/<int:category_id>')
    def get_items(category_id):
        """物品リスト取得API"""
        items = Item.query.filter_by(category_id=category_id, is_active=True).all()
        return jsonify([{'id': item.id, 'name': item.name} for item in items])

    @app.route('/get_model_numbers/<int:item_id>')
    def get_model_numbers(item_id):
        """型番リスト取得API"""
        model_numbers = ModelNumber.query.filter_by(item_id=item_id, is_active=True).all()
        return jsonify([{'id': mn.id, 'number': mn.number, 'notes': mn.notes, 'image_path': mn.image_path} for mn in model_numbers])

    @app.route('/mark_as_delivered/<int:order_id>', methods=['POST'])
    def mark_as_delivered(order_id):
        """納品処理"""
        order = Order.query.get_or_404(order_id)

        try:
            delivery_date_str = request.form.get('delivery_date')
            receiver_id = request.form.get('receiver_id')

            # 必須項目チェック
            if not receiver_id:
                flash('受取者を選択してください。', 'error')
                return redirect(url_for('pending_orders'))

            # 納品日の設定
            if delivery_date_str:
                try:
                    delivery_date = datetime.strptime(delivery_date_str, '%Y-%m-%d')
                except ValueError:
                    delivery_date = datetime.utcnow()
            else:
                delivery_date = datetime.utcnow()

            # データ更新
            order.delivery_status = '納品済み'
            order.delivery_date = delivery_date
            order.receiver_id = receiver_id

            db.session.commit()
            flash('納品処理が完了しました。', 'success')

        except Exception as e:
            db.session.rollback()
            flash('納品処理に失敗しました。', 'error')
            app.logger.error(f"Error in mark_as_delivered: {str(e)}")

        return redirect(url_for('pending_orders'))

    @app.route('/cancel_order/<int:order_id>', methods=['POST'])
    def cancel_order(order_id):
        """発注取り消し処理"""
        try:
            order = Order.query.get_or_404(order_id)
            
            # 発注取り消し処理
            db.session.delete(order)
            db.session.commit()
            flash('発注を取り消しました。', 'success')
        except Exception as e:
            db.session.rollback()
            flash('発注の取り消しに失敗しました。', 'error')
            app.logger.error(f"Error in cancel_order: {str(e)}")
        
        # エラーが発生しても、リダイレクトは行う
        return redirect(url_for('pending_orders'))

    def apply_search_filters(query):
        """検索フィルタを適用する共通関数"""
        try:
            # 期間検索
            if request.args.get('start_date'):
                query = query.filter(Order.order_date >= datetime.strptime(request.args.get('start_date'), '%Y-%m-%d'))
            if request.args.get('end_date'):
                query = query.filter(Order.order_date <= datetime.strptime(request.args.get('end_date'), '%Y-%m-%d'))

            # スタッフ検索
            if request.args.get('requester_id'):
                query = query.filter(Order.requester_id == request.args.get('requester_id'))

            # 分類検索
            if request.args.get('category_id'):
                query = query.filter(Order.category_id == request.args.get('category_id'))

            # キーワード検索
            if request.args.get('keyword'):
                keyword = f"%{request.args.get('keyword')}%"
                # 結合クエリを単純化
                query = query.join(Item, Order.item_id == Item.id)
                query = query.outerjoin(ModelNumber, Item.id == ModelNumber.item_id)
                query = query.filter(
                    db.or_(
                        Item.name.ilike(keyword),
                        db.or_(ModelNumber.number.ilike(keyword), ModelNumber.number == None),
                        Order.reason.ilike(keyword)
                    )
                )
            
            return query
        except Exception as e:
            app.logger.error(f"Error in apply_search_filters: {str(e)}")
            # エラーが発生した場合は元のクエリをそのまま返す
            return query
