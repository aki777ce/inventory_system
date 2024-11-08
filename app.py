from flask import Flask
from config import Config
from models import db
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # データベースの初期化
    db.init_app(app)

    with app.app_context():
        # Blueprintの登録
        from routes import admin_bp
        app.register_blueprint(admin_bp)

        # メインルートの登録
        from routes import register_main_routes
        register_main_routes(app)

        # データベースのテーブル作成
        db.create_all()

    return app

# アプリケーションインスタンスの作成
app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
