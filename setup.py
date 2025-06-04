#!/usr/bin/env python3
"""
CSV 數據分析系統 - 自動化建立腳本
執行此腳本來自動建立完整的專案結構
"""

import os
import sys
import subprocess
from pathlib import Path

def create_directories():
    """創建必要目錄"""
    directories = [
        'templates',
        'static/css',
        'static/js', 
        'static/images',
        'data',
        'uploads',
        'logs',
        'backups'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✓ 創建目錄: {directory}")

def create_config_py():
    """創建 config.py"""
    config_content = '''"""
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
'''
    
    with open('config.py', 'w', encoding='utf-8') as f:
        f.write(config_content)
    print("✓ 創建檔案: config.py")

def create_run_py():
    """創建 run.py"""
    run_content = '''#!/usr/bin/env python3
"""
應用啟動腳本
專案：CSV 數據分析與管理系統
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime

# 添加專案根目錄到 Python 路徑
PROJECT_ROOT = Path(__file__).parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

# 導入應用模組
try:
    from app import app
    from models import init_database
    from config import get_config
except ImportError as e:
    print(f"❌ 模組匯入失敗：{e}")
    sys.exit(1)

def setup_logging():
    """設定日誌系統"""
    config_class = get_config()
    log_dir = os.path.dirname(config_class.LOG_FILE)
    os.makedirs(log_dir, exist_ok=True)
    
    logging.basicConfig(
        level=getattr(logging, config_class.LOG_LEVEL),
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(config_class.LOG_FILE, encoding='utf-8')
        ]
    )

def create_directories():
    """創建必要目錄"""
    config_class = get_config()
    directories = [
        config_class.UPLOAD_FOLDER,
        os.path.dirname(config_class.LOG_FILE),
        str(PROJECT_ROOT / 'data'),
        str(PROJECT_ROOT / 'static' / 'css'),
        str(PROJECT_ROOT / 'static' / 'js'),
        str(PROJECT_ROOT / 'static' / 'images')
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

def main():
    """主函數"""
    print(f"🔄 啟動 CSV 數據分析與管理系統...")
    print(f"⏰ 啟動時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 設定日誌
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # 創建目錄
    create_directories()
    logger.info("必要目錄創建完成")
    
    # 初始化資料庫
    if init_database():
        logger.info("資料庫初始化成功")
    else:
        logger.error("資料庫初始化失敗")
        return False
    
    # 獲取配置
    config_class = get_config()
    host = os.environ.get('HOST', '127.0.0.1')
    port = int(os.environ.get('PORT', 5000))
    
    print("=" * 60)
    print(f"🚀 {config_class.APP_NAME}")
    print(f"🌐 位址：http://{host}:{port}")
    print(f"⚙️  Debug 模式：{'開啟' if config_class.DEBUG else '關閉'}")
    print("=" * 60)
    print("📚 使用說明：")
    print("   1. 打開瀏覽器訪問上述網址")
    print("   2. 點擊「數據匯入」上傳 CSV 檔案")
    print("   3. 使用「搜尋記錄」查找數據")
    print("   4. 透過「數據分析」進行分析")
    print("   5. 按 Ctrl+C 停止服務")
    print("=" * 60)
    
    # 啟動應用
    try:
        app.run(
            host=host,
            port=port,
            debug=config_class.DEBUG,
            threaded=True
        )
    except KeyboardInterrupt:
        logger.info("收到中斷信號，正在關閉...")
        return True
    except Exception as e:
        logger.error(f"應用啟動失敗：{e}")
        return False

# 命令行工具
if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "init":
            print("初始化資料庫...")
            if init_database():
                print("✓ 資料庫初始化成功")
            else:
                print("✗ 資料庫初始化失敗")
                
        elif command == "help":
            print("=== CSV 數據分析系統 - 命令行工具 ===")
            print("用法：python run.py [命令]")
            print("可用命令：")
            print("  (無參數)    啟動 Web 應用")
            print("  init        初始化資料庫")
            print("  help        顯示此幫助訊息")
        else:
            print(f"❌ 未知命令：{command}")
            print("使用 'python run.py help' 查看可用命令")
    else:
        main()
'''
    
    with open('run.py', 'w', encoding='utf-8') as f:
        f.write(run_content)
    print("✓ 創建檔案: run.py")

def create_templates():
    """創建模板檔案"""
    
    # base.html
    base_template = '''<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}CSV 數據分析系統{% endblock %}</title>
    
    <!-- Bootstrap CSS -->
    <link href="https://cdnjs.cloudflare.com/ajax/libs/bootstrap/5.3.0/css/bootstrap.min.css" rel="stylesheet">
    <!-- Bootstrap Icons -->
    <link href="https://cdnjs.cloudflare.com/ajax/libs/bootstrap-icons/1.10.5/font/bootstrap-icons.min.css" rel="stylesheet">
    <!-- Chart.js -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js"></script>
    
    <style>
        body { font-family: 'Microsoft JhengHei', sans-serif; background-color: #f8f9fa; }
        .navbar { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
        .navbar .nav-link { color: white !important; font-weight: 500; }
        .card { border: none; border-radius: 15px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); }
        .btn-primary { background: linear-gradient(135deg, #3498db, #5dade2); border: none; border-radius: 25px; }
    </style>
</head>
<body>
    <!-- 導航列 -->
    <nav class="navbar navbar-expand-lg">
        <div class="container">
            <a class="navbar-brand text-white" href="{{ url_for('index') }}">
                <i class="bi bi-graph-up-arrow"></i> CSV 數據分析系統
            </a>
            
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="{{ url_for('index') }}">
                    <i class="bi bi-house"></i> 首頁
                </a>
                <a class="nav-link" href="{{ url_for('import_page') }}">
                    <i class="bi bi-upload"></i> 匯入數據
                </a>
                <a class="nav-link" href="{{ url_for('search_page') }}">
                    <i class="bi bi-search"></i> 搜尋記錄
                </a>
                <a class="nav-link" href="{{ url_for('analysis_page') }}">
                    <i class="bi bi-graph-up"></i> 數據分析
                </a>
            </div>
        </div>
    </nav>

    <!-- 主要內容 -->
    <div class="container mt-4">
        {% block content %}{% endblock %}
    </div>

    <!-- Bootstrap JS -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/bootstrap/5.3.0/js/bootstrap.bundle.min.js"></script>
    {% block scripts %}{% endblock %}
</body>
</html>'''
    
    # import.html
    import_template = '''{% extends "base.html" %}

{% block title %}數據匯入 - CSV 數據分析系統{% endblock %}

{% block content %}
<div class="row">
    <div class="col-12">
        <h2 class="mb-4">
            <i class="bi bi-upload"></i> CSV 數據匯入
        </h2>
    </div>
</div>

<div class="row">
    <div class="col-md-8">
        <div class="card">
            <div class="card-header">
                <h5 class="mb-0">上傳 CSV 檔案</h5>
            </div>
            <div class="card-body">
                <form id="uploadForm" enctype="multipart/form-data">
                    <div class="mb-3">
                        <label for="file" class="form-label">選擇檔案</label>
                        <input type="file" class="form-control" id="file" name="file" accept=".csv" required>
                    </div>
                    
                    <div class="mb-3">
                        <label for="encoding" class="form-label">檔案編碼</label>
                        <select class="form-select" id="encoding" name="encoding">
                            <option value="utf-8">UTF-8</option>
                            <option value="big5">Big5</option>
                            <option value="gb2312">GB2312</option>
                        </select>
                    </div>
                    
                    <button type="submit" class="btn btn-primary">
                        <i class="bi bi-upload"></i> 開始匯入
                    </button>
                </form>
                
                <div id="result" class="mt-4" style="display: none;"></div>
            </div>
        </div>
    </div>
    
    <div class="col-md-4">
        <div class="card">
            <div class="card-header">
                <h6 class="mb-0">檔案格式說明</h6>
            </div>
            <div class="card-body">
                <h6>檔案名稱格式：</h6>
                <code>SN_YYYYMMDD_HHMMSS_(left/right/rec1/rec2)</code>
                
                <h6 class="mt-3">範例：</h6>
                <small>32120121ED0755130005_20250522_084534_left.csv</small>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block scripts %}
<script>
document.getElementById('uploadForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const formData = new FormData(this);
    const resultDiv = document.getElementById('result');
    
    try {
        resultDiv.style.display = 'block';
        resultDiv.innerHTML = '<div class="alert alert-info">上傳中...</div>';
        
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            resultDiv.innerHTML = `
                <div class="alert alert-success">
                    <i class="bi bi-check-circle"></i> ${result.message}
                </div>`;
        } else {
            resultDiv.innerHTML = `
                <div class="alert alert-danger">
                    <i class="bi bi-exclamation-triangle"></i> ${result.message}
                </div>`;
        }
    } catch (error) {
        resultDiv.innerHTML = `
            <div class="alert alert-danger">
                <i class="bi bi-exclamation-triangle"></i> 上傳失敗：${error.message}
            </div>`;
    }
});
</script>
{% endblock %}'''

    # search.html
    search_template = '''{% extends "base.html" %}

{% block title %}搜尋記錄 - CSV 數據分析系統{% endblock %}

{% block content %}
<div class="row">
    <div class="col-12">
        <h2 class="mb-4">
            <i class="bi bi-search"></i> 搜尋測試記錄
        </h2>
    </div>
</div>

<div class="row">
    <div class="col-md-3">
        <div class="card">
            <div class="card-header">
                <h6 class="mb-0">搜尋條件</h6>
            </div>
            <div class="card-body">
                <form id="searchForm">
                    <div class="mb-3">
                        <label for="sn" class="form-label">設備序號 (SN)</label>
                        <input type="text" class="form-control" id="sn" placeholder="輸入 SN">
                    </div>
                    
                    <div class="mb-3">
                        <label for="testType" class="form-label">測試類型</label>
                        <select class="form-select" id="testType">
                            <option value="">全部</option>
                            <option value="left">left</option>
                            <option value="right">right</option>
                            <option value="rec1">rec1</option>
                            <option value="rec2">rec2</option>
                        </select>
                    </div>
                    
                    <button type="submit" class="btn btn-primary w-100">
                        <i class="bi bi-search"></i> 搜尋
                    </button>
                </form>
            </div>
        </div>
    </div>
    
    <div class="col-md-9">
        <div class="card">
            <div class="card-header">
                <h6 class="mb-0">搜尋結果</h6>
            </div>
            <div class="card-body">
                <div id="results">
                    <div class="text-center text-muted">
                        請輸入搜尋條件
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block scripts %}
<script>
document.getElementById('searchForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const params = new URLSearchParams();
    const sn = document.getElementById('sn').value.trim();
    const testType = document.getElementById('testType').value;
    
    if (sn) params.append('sn', sn);
    if (testType) params.append('test_type', testType);
    
    const resultsDiv = document.getElementById('results');
    resultsDiv.innerHTML = '<div class="text-center">搜尋中...</div>';
    
    try {
        const response = await fetch(`/api/search?${params}`);
        const result = await response.json();
        
        if (result.success && result.data.length > 0) {
            const html = result.data.map(record => `
                <div class="border rounded p-3 mb-2">
                    <strong>SN:</strong> ${record.sn}<br>
                    <strong>日期:</strong> ${record.test_date}<br>
                    <strong>時間:</strong> ${record.test_time}<br>
                    <strong>類型:</strong> ${record.test_type}
                </div>
            `).join('');
            resultsDiv.innerHTML = html;
        } else {
            resultsDiv.innerHTML = '<div class="text-center text-muted">未找到相關記錄</div>';
        }
    } catch (error) {
        resultsDiv.innerHTML = '<div class="alert alert-danger">搜尋失敗</div>';
    }
});
</script>
{% endblock %}'''

    # analysis.html 
    analysis_template = '''{% extends "base.html" %}

{% block title %}數據分析 - CSV 數據分析系統{% endblock %}

{% block content %}
<div class="row">
    <div class="col-12">
        <h2 class="mb-4">
            <i class="bi bi-graph-up"></i> 數據分析
        </h2>
    </div>
</div>

<div class="card">
    <div class="card-body text-center py-5">
        <i class="bi bi-graph-up display-4 text-muted"></i>
        <h4 class="mt-3">數據分析功能</h4>
        <p class="text-muted">此功能正在開發中，敬請期待...</p>
    </div>
</div>
{% endblock %}'''

    # error.html
    error_template = '''{% extends "base.html" %}

{% block title %}錯誤 - CSV 數據分析系統{% endblock %}

{% block content %}
<div class="row justify-content-center">
    <div class="col-md-6 text-center">
        <div class="display-1 text-muted">⚠️</div>
        <h2 class="mb-3">發生錯誤</h2>
        <p class="text-muted mb-4">抱歉，系統發生了一些問題。</p>
        <a href="{{ url_for('index') }}" class="btn btn-primary">
            <i class="bi bi-house"></i> 回到首頁
        </a>
    </div>
</div>
{% endblock %}'''

    # 寫入模板檔案
    templates = {
        'templates/base.html': base_template,
        'templates/import.html': import_template,
        'templates/search.html': search_template,
        'templates/analysis.html': analysis_template,
        'templates/error.html': error_template
    }
    
    for filename, content in templates.items():
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✓ 創建檔案: {filename}")

def check_python_version():
    """檢查 Python 版本"""
    if sys.version_info < (3, 8):
        print("❌ 錯誤：需要 Python 3.8 或更高版本")
        print(f"當前版本：{sys.version}")
        return False
    return True

def install_dependencies():
    """安裝依賴套件"""
    print("📦 安裝依賴套件...")
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        print("✓ 依賴套件安裝完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 安裝失敗：{e}")
        return False

def setup_virtual_environment():
    """設定虛擬環境"""
    if os.path.exists('venv'):
        print("✓ 虛擬環境已存在")
        return True
    
    print("📦 創建虛擬環境...")
    try:
        subprocess.check_call([sys.executable, '-m', 'venv', 'venv'])
        print("✓ 虛擬環境創建完成")
        
        # 提示啟動虛擬環境
        if os.name == 'nt':  # Windows
            print("💡 請執行以下命令啟動虛擬環境：")
            print("   venv\\Scripts\\activate")
        else:  # Linux/Mac
            print("💡 請執行以下命令啟動虛擬環境：")
            print("   source venv/bin/activate")
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 創建虛擬環境失敗：{e}")
        return False

def main():
    """主函數"""
    print("🚀 CSV 數據分析系統 - 自動化建立")
    print("=" * 50)
    
    # 檢查 Python 版本
    if not check_python_version():
        return
    
    # 創建目錄
    print("📁 創建專案目錄...")
    create_directories()
    
    # 創建配置檔案
    print("⚙️ 創建配置檔案...")
    create_config_py()
    create_run_py()
    
    # 創建模板檔案
    print("📄 創建模板檔案...")
    create_templates()
    
    # 處理 index.html
    if os.path.exists('index_template.html'):
        os.rename('index_template.html', 'templates/index.html')
        print("✓ 移動檔案: index_template.html -> templates/index.html")
    
    # 清理不需要的檔案
    cleanup_files = ['additional_templates.py', 'web_templates.html']
    for file in cleanup_files:
        if os.path.exists(file):
            os.remove(file)
            print(f"✓ 清理檔案: {file}")
    
    # 設定虛擬環境
    print("🐍 設定 Python 虛擬環境...")
    setup_virtual_environment()
    
    print("\n" + "=" * 50)
    print("✅ 專案建立完成！")
    print("\n📋 後續步驟：")
    
    if os.name == 'nt':  # Windows
        print("1. 啟動虛擬環境：")
        print("   venv\\Scripts\\activate")
    else:  # Linux/Mac
        print("1. 啟動虛擬環境：")
        print("   source venv/bin/activate")
    
    print("\n2. 安裝依賴套件：")
    print("   pip install -r requirements.txt")
    
    print("\n3. 初始化資料庫：")
    print("   python run.py init")
    
    print("\n4. 啟動應用：")
    print("   python run.py")
    
    print("\n5. 瀏覽器訪問：")
    print("   http://localhost:5000")
    
    print("\n💡 提示：如果您已在虛擬環境中，可以直接執行步驟 2-4")

if __name__ == "__main__":
    main()