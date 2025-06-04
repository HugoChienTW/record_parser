"""
應用配置檔案
專案：CSV 數據分析與管理系統
負責：環境配置、參數設定、安全配置
"""

import os
from datetime import timedelta
from pathlib import Path

# 基礎路徑
BASE_DIR = Path(__file__).parent.absolute()

class Config:
    """基礎配置類 - 包含所有環境通用的配置"""
    
    # 基本應用配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'csv-analysis-secret-key-change-in-production-2025'
    
    # 應用資訊
    APP_NAME = "CSV 數據分析與管理系統"
    APP_VERSION = "1.0.0"
    APP_AUTHOR = "系統開發團隊"
    
    # 資料庫配置
    DATABASE_URL = os.environ.get('DATABASE_URL') or f'sqlite:///{BASE_DIR}/data/test_records.db'
    
    # 檔案上傳配置
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or str(BASE_DIR / 'uploads')
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB
    ALLOWED_EXTENSIONS = {'csv', 'txt'}
    
    # 分頁與查詢配置
    RECORDS_PER_PAGE = int(os.environ.get('RECORDS_PER_PAGE', 20))
    MAX_RECORDS_PER_PAGE = int(os.environ.get('MAX_RECORDS_PER_PAGE', 100))
    
    # 日誌配置
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE') or str(BASE_DIR / 'logs' / 'app.log')
    
    # 業務配置
    VALID_TEST_TYPES = ['left', 'right', 'rec1', 'rec2']
    
    SUPPORTED_FREQUENCIES = {
        '100': 'freq_100', '125': 'freq_125', '160': 'freq_160',
        '200': 'freq_200', '250': 'freq_250', '315': 'freq_315',
        '400': 'freq_400', '500': 'freq_500', '630': 'freq_630',
        '800': 'freq_800', '1000': 'freq_1000', '1250': 'freq_1250',
        '1600': 'freq_1600', '2000': 'freq_2000'
    }
    
    @staticmethod
    def init_app(app):
        """初始化應用時的配置"""
        directories = [
            Config.UPLOAD_FOLDER,
            os.path.dirname(Config.LOG_FILE),
            str(BASE_DIR / 'data'),
            str(BASE_DIR / 'static' / 'css'),
            str(BASE_DIR / 'static' / 'js'),
            str(BASE_DIR / 'static' / 'images')
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)

class DevelopmentConfig(Config):
    """開發環境配置"""
    DEBUG = True
    TESTING = False
    ALLOW_DATABASE_RESET = True

class ProductionConfig(Config):
    """生產環境配置"""
    DEBUG = False
    TESTING = False
    ALLOW_DATABASE_RESET = False

class TestingConfig(Config):
    """測試環境配置"""
    TESTING = True
    DEBUG = True
    DATABASE_URL = 'sqlite:///:memory:'

# 配置字典
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config(config_name=None):
    """獲取配置類"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')
    
    return config.get(config_name, config['default'])
