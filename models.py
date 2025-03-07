from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Staff(db.Model):
    """スタッフモデル"""
    __tablename__ = 'staff'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    # リレーションシップ定義
    orders_requested = db.relationship('Order', foreign_keys='Order.requester_id', backref='requester')
    orders_received = db.relationship('Order', foreign_keys='Order.receiver_id', backref='receiver')

    def __repr__(self):
        return f'<Staff {self.name}>'

class Category(db.Model):
    """物品カテゴリモデル"""
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # リレーションシップ定義
    items = db.relationship('Item', backref='category', lazy='select')
    orders = db.relationship('Order', backref='category', lazy=True)

    def __repr__(self):
        return f'<Category {self.name}>'

class Item(db.Model):
    """物品モデル"""
    __tablename__ = 'items'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    # リレーションシップ定義
    model_numbers = db.relationship('ModelNumber', backref='item', lazy='select')
    orders = db.relationship('Order', backref='item', lazy=True)

    __table_args__ = (
        db.UniqueConstraint('name', 'category_id', name='unique_item_per_category'),
    )

    def __repr__(self):
        return f'<Item {self.name}>'

class ModelNumber(db.Model):
    """型番モデル"""
    __tablename__ = 'model_numbers'

    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.String(100), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    # リレーションシップ定義
    orders = db.relationship('Order', backref='model_number', lazy=True)

    __table_args__ = (
        db.UniqueConstraint('number', 'item_id', name='unique_model_number_per_item'),
    )

    def __repr__(self):
        return f'<ModelNumber {self.number}>'

class Order(db.Model):
    """発注モデル"""
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    order_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    requester_id = db.Column(db.Integer, db.ForeignKey('staff.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
    model_number_id = db.Column(db.Integer, db.ForeignKey('model_numbers.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit = db.Column(db.String(20), nullable=False)
    reason = db.Column(db.Text)
    delivery_status = db.Column(db.String(20), default='未納品')
    delivery_date = db.Column(db.DateTime)
    receiver_id = db.Column(db.Integer, db.ForeignKey('staff.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def days_since_order(self):
        """発注からの経過日数を計算"""
        if self.order_date:
            delta = datetime.utcnow() - self.order_date
            return delta.days
        return 0

    @property
    def formatted_order_date(self):
        """発注日のフォーマット"""
        return self.order_date.strftime('%Y/%m/%d') if self.order_date else '-'

    @property
    def formatted_delivery_date(self):
        """納品日のフォーマット"""
        return self.delivery_date.strftime('%Y/%m/%d') if self.delivery_date else '-'

    @property
    def days_required(self):
        """納品までの所要日数を計算"""
        if self.delivery_date and self.order_date:
            delta = self.delivery_date - self.order_date
            return delta.days
        return None

    def __repr__(self):
        return f'<Order {self.id}>'