import os

class Config:
    # 本番環境用の設定
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///app.db')
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev')

    @staticmethod
    def init_app():
        db_dir = os.path.dirname(Config.SQLALCHEMY_DATABASE_URI.replace('sqlite:///', ''))
        if not os.path.exists(db_dir):
            os.makedirs(db_dir)
