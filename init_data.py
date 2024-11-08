from app import app, db
from models import Staff, Category, Item, ModelNumber

def init_test_data():
    with app.app_context():
        # スタッフデータ
        staff_data = [
            "山田太郎",
            "佐藤花子",
            "鈴木一郎"
        ]
        for name in staff_data:
            if not Staff.query.filter_by(name=name).first():
                staff = Staff(name=name)
                db.session.add(staff)

        # 分類データ
        category_data = [
            {"name": "事務用品", "description": "一般的な事務用品"},
            {"name": "電子機器", "description": "PC関連機器など"},
            {"name": "消耗品", "description": "定期的に必要となる物品"}
        ]
        for cat in category_data:
            if not Category.query.filter_by(name=cat["name"]).first():
                category = Category(**cat)
                db.session.add(category)
        
        db.session.commit()

        # 事務用品の例
        office_category = Category.query.filter_by(name="事務用品").first()
        if office_category:
            items_data = [
                {"name": "ボールペン", "models": ["BIC-001", "PILOT-X1"]},
                {"name": "ノート", "models": ["A4-100", "B5-80"]},
                {"name": "付箋", "models": ["POST-S", "POST-L"]}
            ]
            for item_data in items_data:
                if not Item.query.filter_by(name=item_data["name"], category_id=office_category.id).first():
                    item = Item(name=item_data["name"], category_id=office_category.id)
                    db.session.add(item)
                    db.session.commit()
                    
                    for model in item_data["models"]:
                        if not ModelNumber.query.filter_by(number=model, item_id=item.id).first():
                            model_number = ModelNumber(number=model, item_id=item.id)
                            db.session.add(model_number)

        db.session.commit()
        print("テストデータの投入が完了しました。")

if __name__ == "__main__":
    init_test_data()
