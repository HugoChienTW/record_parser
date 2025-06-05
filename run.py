#!/usr/bin/env python3
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
    port = int(os.environ.get('PORT', 5500))
    
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
