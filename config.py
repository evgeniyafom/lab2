import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-change-in-production'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER = 'static/uploads'
    GRAPH_FOLDER = 'static/graphs'
    
    # Настройки капчи
    CAPTCHA_LENGTH = 6
    CAPTCHA_WIDTH = 280
    CAPTCHA_HEIGHT = 90
    
    # Настройки нейросети
    MODEL_PATH = 'models/classifier.pkl'
    SCALER_PATH = 'models/scaler.pkl'
    
    @staticmethod
    def init_app(app):
        # Создаем необходимые папки
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        os.makedirs(app.config['GRAPH_FOLDER'], exist_ok=True)
        os.makedirs('models', exist_ok=True)

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
