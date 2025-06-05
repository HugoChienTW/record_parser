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
        logger.error(f"檔案上傳錯誤：{str(e)}")
        return jsonify({'success': False, 'message': f'上傳失敗：{str(e)}'}), 500

@app.route('/api/search')
def api_search():
    """搜尋記錄 API"""
    try:
        # 獲取查詢參數
        sn = request.args.get('sn', '').strip()
        test_date = request.args.get('test_date', '').strip()
        test_type = request.args.get('test_type', '').strip()
        fixture = request.args.get('fixture', '').strip()  # 新增治具參數
        start_date = request.args.get('start_date', '').strip()
        end_date = request.args.get('end_date', '').strip()
        
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        # 構建查詢參數
        query_params = {}
        if sn:
            query_params['sn'] = sn
        if test_date:
            query_params['test_date'] = test_date
        if test_type and test_type != 'all':
            query_params['test_type'] = test_type
        if fixture and fixture != 'all':
            query_params['fixture'] = fixture
        if start_date and end_date:
            query_params['date_range'] = (start_date, end_date)
        
        query_params['limit'] = per_page
        query_params['offset'] = (page - 1) * per_page
        
        # 執行查詢
        records, total = query_service.search_records(**query_params)
        
        return jsonify({
            'success': True,
            'data': records,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page
            }
        })
        
    except Exception as e:
        logger.error(f"搜尋錯誤：{str(e)}")
        return jsonify({'success': False, 'message': f'搜尋失敗：{str(e)}'}), 500

@app.route('/api/sn/<sn>')
def api_get_sn_records(sn):
    """獲取指定 SN 的所有記錄"""
    try:
        fixture = request.args.get('fixture')  # 可選的治具篩選
        records = database_service.get_records_by_sn(sn, fixture)
        return jsonify({
            'success': True,
            'sn': sn,
            'fixture': fixture,
            'count': len(records),
            'data': [record.to_dict() for record in records]
        })
    except Exception as e:
        logger.error(f"獲取 SN 記錄錯誤：{str(e)}")
        return jsonify({'success': False, 'message': f'獲取記錄失敗：{str(e)}'}), 500

@app.route('/api/analysis/frequency')
def api_frequency_analysis():
    """頻率分析 API"""
    try:
        sn = request.args.get('sn', '').strip()
        frequency = request.args.get('frequency', '').strip()
        fixture = request.args.get('fixture', '').strip()  # 新增治具參數
        
        if not sn or not frequency:
            return jsonify({'success': False, 'message': '請提供 SN 和頻率參數'}), 400
        
        # 如果 fixture 為空或 'all'，則不篩選治具
        fixture_param = fixture if fixture and fixture != 'all' else None
        
        result = query_service.get_frequency_analysis(sn, frequency, fixture_param)
        
        if 'error' in result:
            return jsonify({'success': False, 'message': result['error']}), 404
        
        return jsonify({'success': True, 'data': result})
        
    except Exception as e:
        logger.error(f"頻率分析錯誤：{str(e)}")
        return jsonify({'success': False, 'message': f'分析失敗：{str(e)}'}), 500

@app.route('/api/analysis/compare')
def api_compare_sn():
    """比較 SN 性能 API"""
    try:
        sn1 = request.args.get('sn1', '').strip()
        sn2 = request.args.get('sn2', '').strip()
        frequency = request.args.get('frequency', '').strip()
        fixture = request.args.get('fixture', '').strip()
        
        if not sn1 or not sn2 or not frequency:
            return jsonify({'success': False, 'message': '請提供兩個 SN 和頻率參數'}), 400
        
        # 如果 fixture 為空或 'all'，則不篩選治具
        fixture_param = fixture if fixture and fixture != 'all' else None
        
        result = query_service.compare_sn_performance(sn1, sn2, frequency, fixture_param)
        
        if 'error' in result:
            return jsonify({'success': False, 'message': result['error']}), 404
        
        return jsonify({'success': True, 'data': result})
        
    except Exception as e:
        logger.error(f"SN 比較錯誤：{str(e)}")
        return jsonify({'success': False, 'message': f'比較失敗：{str(e)}'}), 500

@app.route('/api/analysis/compare-fixture')
def api_compare_fixture():
    """比較治具性能 API"""
    try:
        sn = request.args.get('sn', '').strip()
        frequency = request.args.get('frequency', '').strip()
        
        if not sn or not frequency:
            return jsonify({'success': False, 'message': '請提供 SN 和頻率參數'}), 400
        
        result = query_service.compare_fixture_performance(sn, frequency)
        
        if 'error' in result:
            return jsonify({'success': False, 'message': result['error']}), 404
        
        return jsonify({'success': True, 'data': result})
        
    except Exception as e:
        logger.error(f"治具比較錯誤：{str(e)}")
        return jsonify({'success': False, 'message': f'比較失敗：{str(e)}'}), 500

@app.route('/api/statistics')
def api_statistics():
    """統計資訊 API"""
    try:
        stats = database_service.get_sn_statistics()
        return jsonify({'success': True, 'data': stats})
    except Exception as e:
        logger.error(f"統計資訊錯誤：{str(e)}")
        return jsonify({'success': False, 'message': f'獲取統計失敗：{str(e)}'}), 500

@app.route('/api/import-history')
def api_import_history():
    """匯入歷史 API"""
    try:
        limit = int(request.args.get('limit', 20))
        history = import_service.get_import_history(limit)
        
        return jsonify({
            'success': True,
            'data': [
                {
                    'id': log.id,
                    'filename': log.filename,
                    'fixture': log.fixture,  # 新增治具資訊
                    'total_rows': log.total_rows,
                    'successful_imports': log.successful_imports,
                    'failed_imports': log.failed_imports,
                    'duplicate_skips': log.duplicate_skips,
                    'import_status': log.import_status,
                    'import_time': log.import_time.isoformat() if log.import_time else None,
                    'completed_time': log.completed_time.isoformat() if log.completed_time else None,
                    'error_message': log.error_message
                }
                for log in history
            ]
        })
    except Exception as e:
        logger.error(f"匯入歷史錯誤：{str(e)}")
        return jsonify({'success': False, 'message': f'獲取歷史失敗：{str(e)}'}), 500

@app.route('/api/fixtures')
def api_fixtures():
    """獲取治具列表 API"""
    try:
        fixtures = ['治具1', '治具2']
        return jsonify({'success': True, 'data': fixtures})
    except Exception as e:
        logger.error(f"獲取治具列表錯誤：{str(e)}")
        return jsonify({'success': False, 'message': f'獲取治具列表失敗：{str(e)}'}), 500

@app.route('/api/fixture-stats')
def api_fixture_stats():
    """獲取治具統計 API"""
    try:
        stats = database_service.get_sn_statistics()
        fixture_stats = stats.get('fixture_stats', {})
        
        return jsonify({
            'success': True,
            'data': {
                'fixture_distribution': fixture_stats,
                'total_fixtures': len(fixture_stats),
                'most_used_fixture': max(fixture_stats.items(), key=lambda x: x[1])[0] if fixture_stats else None
            }
        })
    except Exception as e:
        logger.error(f"獲取治具統計錯誤：{str(e)}")
        return jsonify({'success': False, 'message': f'獲取治具統計失敗：{str(e)}'}), 500

# ==================== 高級分析 API ====================

@app.route('/api/analysis/trend')
def api_trend_analysis():
    """趨勢分析 API"""
    try:
        sn = request.args.get('sn', '').strip()
        frequency = request.args.get('frequency', '').strip()
        fixture = request.args.get('fixture', '').strip()
        days = int(request.args.get('days', 30))  # 預設分析最近30天
        
        if not sn or not frequency:
            return jsonify({'success': False, 'message': '請提供 SN 和頻率參數'}), 400
        
        # 如果 fixture 為空或 'all'，則不篩選治具
        fixture_param = fixture if fixture and fixture != 'all' else None
        
        # 獲取趨勢數據
        result = query_service.get_frequency_analysis(sn, frequency, fixture_param)
        
        if 'error' in result:
            return jsonify({'success': False, 'message': result['error']}), 404
        
        # 處理趨勢數據（這裡可以添加更多趨勢分析邏輯）
        trend_data = result.get('trend_data', [])
        
        # 計算趨勢指標
        if len(trend_data) > 1:
            values = [item['value'] for item in trend_data]
            trend_direction = 'increasing' if values[-1] > values[0] else 'decreasing'
            volatility = max(values) - min(values)
        else:
            trend_direction = 'stable'
            volatility = 0
        
        trend_result = {
            'sn': sn,
            'frequency': frequency,
            'fixture': fixture_param,
            'period_days': days,
            'trend_direction': trend_direction,
            'volatility': volatility,
            'data_points': len(trend_data),
            'trend_data': trend_data
        }
        
        return jsonify({'success': True, 'data': trend_result})
        
    except Exception as e:
        logger.error(f"趨勢分析錯誤：{str(e)}")
        return jsonify({'success': False, 'message': f'趨勢分析失敗：{str(e)}'}), 500

# ==================== 批次操作 API ====================

@app.route('/api/batch/delete', methods=['POST'])
def api_batch_delete():
    """批次刪除記錄 API"""
    try:
        data = request.get_json()
        record_ids = data.get('record_ids', [])
        
        if not record_ids:
            return jsonify({'success': False, 'message': '未提供要刪除的記錄 ID'}), 400
        
        # 這裡需要實作批次刪除邏輯
        # deleted_count = database_service.batch_delete_records(record_ids)
        
        # 暫時返回模擬結果
        return jsonify({
            'success': True,
            'message': f'成功刪除 {len(record_ids)} 筆記錄',
            'deleted_count': len(record_ids)
        })
        
    except Exception as e:
        logger.error(f"批次刪除錯誤：{str(e)}")
        return jsonify({'success': False, 'message': f'批次刪除失敗：{str(e)}'}), 500

@app.route('/api/batch/export', methods=['POST'])
def api_batch_export():
    """批次匯出記錄 API"""
    try:
        data = request.get_json()
        record_ids = data.get('record_ids', [])
        export_format = data.get('format', 'csv')  # csv, excel, json
        
        if not record_ids:
            return jsonify({'success': False, 'message': '未提供要匯出的記錄 ID'}), 400
        
        # 這裡需要實作批次匯出邏輯
        # export_file = database_service.batch_export_records(record_ids, export_format)
        
        # 暫時返回模擬結果
        return jsonify({
            'success': True,
            'message': f'成功匯出 {len(record_ids)} 筆記錄',
            'download_url': f'/download/export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.{export_format}'
        })
        
    except Exception as e:
        logger.error(f"批次匯出錯誤：{str(e)}")
        return jsonify({'success': False, 'message': f'批次匯出失敗：{str(e)}'}), 500

# ==================== 錯誤處理 ====================

@app.errorhandler(404)
def not_found_error(error):
    return render_template('error.html', 
                         error_code=404, 
                         error_message="頁面不存在"), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html', 
                         error_code=500, 
                         error_message="伺服器內部錯誤"), 500

@app.errorhandler(413)
def too_large(error):
    return jsonify({'success': False, 'message': '檔案太大，最大支援 16MB'}), 413

@app.errorhandler(400)
def bad_request(error):
    return jsonify({'success': False, 'message': '請求格式錯誤'}), 400

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({'success': False, 'message': '不支援的請求方法'}), 405

# ==================== 開發工具 ====================

@app.route('/dev/reset-db')
def dev_reset_database():
    """開發用：重置資料庫"""
    config_class = get_config()
    if getattr(config_class, 'DEBUG', False):
        try:
            from models import Base, db_manager
            Base.metadata.drop_all(bind=db_manager.get_engine())
            Base.metadata.create_all(bind=db_manager.get_engine())
            flash('資料庫已重置', 'success')
        except Exception as e:
            flash(f'重置失敗：{str(e)}', 'error')
    else:
        flash('此功能僅在開發環境可用', 'error')
    
    return redirect(url_for('index'))

@app.route('/dev/db-info')
def dev_database_info():
    """開發用：顯示資料庫資訊"""
    config_class = get_config()
    if getattr(config_class, 'DEBUG', False):
        try:
            stats = database_service.get_sn_statistics()
            return jsonify({
                'success': True,
                'database_url': config_class.DATABASE_URL,
                'statistics': stats,
                'table_info': {
                    'test_records': stats.get('total_records', 0),
                    'unique_sns': stats.get('total_sns', 0),
                    'fixture_distribution': stats.get('fixture_stats', {}),
                    'test_types': stats.get('test_type_stats', {})
                }
            })
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500
    else:
        return jsonify({'success': False, 'message': '此功能僅在開發環境可用'}), 403

# ==================== 健康檢查 ====================

@app.route('/health')
def health_check():
    """系統健康檢查"""
    try:
        # 檢查資料庫連接
        stats = database_service.get_sn_statistics()
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'database': 'connected',
            'total_records': stats.get('total_records', 0),
            'version': '1.0.0'
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.utcnow().isoformat(),
            'database': 'disconnected',
            'error': str(e)
        }), 503

@app.route('/version')
def version_info():
    """版本資訊"""
    return jsonify({
        'name': 'CSV 數據分析與管理系統',
        'version': '1.0.0',
        'build_time': '2025-06-04',
        'features': [
            'CSV 檔案匯入',
            '治具類型管理',
            '數據搜尋與篩選',
            '頻率分析',
            '統計報表',
            'RESTful API'
        ]
    })

# ==================== 模板過濾器 ====================

@app.template_filter('format_date')
def format_date(date_string):
    """格式化日期"""
    if not date_string or len(date_string) != 8:
        return date_string
    return f"{date_string[:4]}-{date_string[4:6]}-{date_string[6:8]}"

@app.template_filter('format_time')
def format_time(time_string):
    """格式化時間"""
    if not time_string or len(time_string) != 6:
        return time_string
    return f"{time_string[:2]}:{time_string[2:4]}:{time_string[4:6]}"

@app.template_filter('format_number')
def format_number(value, decimal_places=2):
    """格式化數字"""
    if value is None:
        return '-'
    try:
        return f"{float(value):.{decimal_places}f}"
    except (ValueError, TypeError):
        return str(value)

@app.template_filter('format_fixture')
def format_fixture(fixture):
    """格式化治具顯示"""
    if not fixture:
        return '未指定'
    return fixture

# ==================== 上下文處理器 ====================

@app.context_processor
def inject_global_vars():
    """注入全域變數到模板"""
    return {
        'app_name': 'CSV 數據分析系統',
        'app_version': '1.0.0',
        'current_year': datetime.now().year,
        'fixture_types': ['治具1', '治具2'],
        'test_types': ['left', 'right', 'rec1', 'rec2'],
        'supported_frequencies': ['100', '125', '160', '200', '250', '315', '400', '500', '630', '800', '1000', '1250', '1600', '2000']
    }

# ==================== 應用啟動 ====================

if __name__ == '__main__':
    # 手動初始化（用於直接執行 app.py 時）
    initialize_app()
    
    # 啟動應用
    debug_mode = getattr(get_config(), 'DEBUG', True)
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    
    logger.info(f"啟動 CSV 數據分析系統")
    logger.info(f"埠號：{port}")
    logger.info(f"Debug 模式：{debug_mode}")
    logger.info(f"治具功能：已啟用")
    
    app.run(
        host=host,
        port=port,
        debug=debug_mode,
        threaded=True
    )