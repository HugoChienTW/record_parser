"""
Flask Web 應用主程式
專案：CSV 數據分析與管理系統
負責：Web 路由、API 接口、前端介面
修正：相容 Flask 2.2+ 版本，新增治具功能
"""

from flask import Flask, render_template, request, jsonify, flash, redirect, url_for
from werkzeug.utils import secure_filename
import os
import tempfile
from datetime import datetime
import logging

# 導入自定義模組
try:
    from models import init_database
    from data_service import database_service, import_service, query_service
    from config import get_config
except ImportError as e:
    print(f"❌ 模組匯入失敗：{e}")
    print("請確認所有檔案都在正確位置")
    exit(1)

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 創建 Flask 應用
app = Flask(__name__)

# 載入配置
config_class = get_config()
app.secret_key = config_class.SECRET_KEY

# 配置
UPLOAD_FOLDER = getattr(config_class, 'UPLOAD_FOLDER', 'uploads')
ALLOWED_EXTENSIONS = getattr(config_class, 'ALLOWED_EXTENSIONS', {'csv'})
MAX_CONTENT_LENGTH = getattr(config_class, 'MAX_CONTENT_LENGTH', 16 * 1024 * 1024)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# 確保上傳目錄存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """檢查檔案類型是否允許"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 應用啟動時初始化（替代 before_first_request）
def initialize_app():
    """應用初始化"""
    try:
        logger.info("初始化應用...")
        
        # 創建必要目錄
        directories = [UPLOAD_FOLDER, 'data', 'logs']
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
        
        # 初始化資料庫
        if init_database():
            logger.info("資料庫初始化成功")
        else:
            logger.error("資料庫初始化失敗")
        
        logger.info("應用初始化完成")
        
    except Exception as e:
        logger.error(f"應用初始化失敗：{str(e)}")

# 在第一次請求時執行初始化
@app.before_request
def before_first_request():
    if not hasattr(app, '_initialized'):
        initialize_app()
        app._initialized = True

# ==================== 主要路由 ====================

@app.route('/')
def index():
    """首頁 - 顯示系統概覽"""
    try:
        stats = database_service.get_sn_statistics()
        return render_template('index.html', stats=stats)
    except Exception as e:
        logger.error(f"載入首頁失敗：{str(e)}")
        flash(f'載入資料失敗：{str(e)}', 'error')
        return render_template('index.html', stats={})

@app.route('/import')
def import_page():
    """匯入頁面"""
    return render_template('import.html')

@app.route('/search')
def search_page():
    """搜尋頁面"""
    return render_template('search.html')

@app.route('/analysis')
def analysis_page():
    """分析頁面"""
    return render_template('analysis.html')

# ==================== API 路由 ====================

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """CSV 檔案上傳 API"""
    try:
        # 檢查檔案是否存在
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': '未選擇檔案'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'message': '未選擇檔案'}), 400
        
        # 檢查檔案類型
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'message': '只支援 CSV 檔案'}), 400
        
        # 儲存檔案
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)
        
        file.save(filepath)
        
        # 獲取參數
        encoding = request.form.get('encoding', 'utf-8')
        fixture = request.form.get('fixture', '治具1')  # 新增治具參數
        
        # 驗證治具參數
        if fixture not in ['治具1', '治具2']:
            fixture = '治具1'  # 預設值
        
        # 匯入資料
        logger.info(f"開始匯入檔案：{filename}，治具：{fixture}")
        success, result = import_service.import_csv_file(filepath, filename, fixture, encoding)
        
        # 清理臨時檔案
        try:
            os.remove(filepath)
        except:
            pass
        
        if success:
            return jsonify({
                'success': True,
                'message': result['message'],
                'statistics': result['statistics']
            })
        else:
            return jsonify({
                'success': False,
                'message': result['message'],
                'errors': result.get('errors', [])[:10]  # 只返回前10個錯誤
            }), 400
            
    except Exception as e:
        logger.error(f"