"""
數據服務層
專案：CSV 數據分析與管理系統
負責：數據庫操作、業務邏輯處理、數據匯入/查詢
"""

from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from datetime import datetime, timedelta
import logging
from contextlib import contextmanager

from models import TestRecord, ImportLog, db_manager
from csv_parser import ParsedRecord, parse_csv_file, DataValidator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseService:
    """
    資料庫服務類
    提供高層次的資料庫操作接口
    """
    
    def __init__(self):
        self.db_manager = db_manager
    
    @contextmanager
    def get_session(self):
        """獲取資料庫會話的上下文管理器"""
        session = self.db_manager.get_session()
        try:
            yield session
        except Exception as e:
            session.rollback()
            logger.error(f"資料庫操作錯誤：{str(e)}")
            raise
        finally:
            session.close()
    
    def create_test_record(self, parsed_record: ParsedRecord, filename: str, 
                          session: Optional[Session] = None) -> Tuple[bool, str]:
        """
        創建測試記錄
        
        Args:
            parsed_record: 解析後的記錄
            filename: 原始檔案名稱
            session: 資料庫會話（可選）
            
        Returns:
            Tuple[bool, str]: (是否成功, 訊息)
        """
        def _create_record(db_session):
            # 驗證數據
            is_valid, error_msg = DataValidator.validate_parsed_record(parsed_record)
            if not is_valid:
                return False, f"數據驗證失敗：{error_msg}"
            
            pf = parsed_record.parsed_filename
            
            # 檢查是否已存在（避免重複匯入）
            existing = db_session.query(TestRecord).filter(
                and_(
                    TestRecord.sn == pf.sn,
                    TestRecord.test_date == pf.test_date,
                    TestRecord.test_time == pf.test_time,
                    TestRecord.test_type == pf.test_type
                )
            ).first()
            
            if existing:
                return False, f"記錄已存在：SN={pf.sn}, 時間={pf.test_date}_{pf.test_time}, 類型={pf.test_type}"
            
            # 創建新記錄
            test_record = TestRecord(
                sn=pf.sn,
                test_date=pf.test_date,
                test_time=pf.test_time,
                test_type=pf.test_type,
                filename=filename
            )
            
            # 設定頻率數據
            frequency_mapping = {
                '100': 'freq_100', '125': 'freq_125', '160': 'freq_160',
                '200': 'freq_200', '250': 'freq_250', '315': 'freq_315',
                '400': 'freq_400', '500': 'freq_500', '630': 'freq_630',
                '800': 'freq_800', '1000': 'freq_1000', '1250': 'freq_1250',
                '1600': 'freq_1600', '2000': 'freq_2000'
            }
            
            for freq, value in parsed_record.frequency_data.items():
                if freq in frequency_mapping:
                    setattr(test_record, frequency_mapping[freq], value)
            
            db_session.add(test_record)
            db_session.commit()
            
            return True, f"記錄創建成功：ID={test_record.id}"
        
        if session:
            return _create_record(session)
        else:
            with self.get_session() as db_session:
                return _create_record(db_session)
    
    def query_records(self, sn: Optional[str] = None, test_date: Optional[str] = None,
                     test_type: Optional[str] = None, date_range: Optional[Tuple[str, str]] = None,
                     limit: int = 100, offset: int = 0) -> Tuple[List[TestRecord], int]:
        """
        查詢測試記錄
        
        Args:
            sn: 設備序號（可選）
            test_date: 測試日期（可選）
            test_type: 測試類型（可選）
            date_range: 日期範圍 (start_date, end_date)（可選）
            limit: 限制返回筆數
            offset: 偏移量
            
        Returns:
            Tuple[List[TestRecord], int]: (記錄列表, 總筆數)
        """
        with self.get_session() as session:
            query = session.query(TestRecord)
            
            # 建立過濾條件
            filters = []
            
            if sn:
                filters.append(TestRecord.sn.like(f'%{sn}%'))
            
            if test_date:
                filters.append(TestRecord.test_date == test_date)
            
            if test_type:
                filters.append(TestRecord.test_type == test_type)
            
            if date_range:
                start_date, end_date = date_range
                filters.append(TestRecord.test_date >= start_date)
                filters.append(TestRecord.test_date <= end_date)
            
            if filters:
                query = query.filter(and_(*filters))
            
            # 獲取總筆數
            total_count = query.count()
            
            # 應用分頁和排序
            records = query.order_by(desc(TestRecord.import_time))\
                          .offset(offset)\
                          .limit(limit)\
                          .all()
            
            return records, total_count
    
    def get_sn_statistics(self) -> Dict[str, any]:
        """獲取 SN 統計資訊"""
        with self.get_session() as session:
            # SN 總數
            total_sns = session.query(func.count(func.distinct(TestRecord.sn))).scalar()
            
            # 記錄總數
            total_records = session.query(func.count(TestRecord.id)).scalar()
            
            # 最新記錄日期
            latest_date = session.query(func.max(TestRecord.test_date)).scalar()
            
            # 各測試類型統計
            test_type_stats = session.query(
                TestRecord.test_type,
                func.count(TestRecord.id)
            ).group_by(TestRecord.test_type).all()
            
            # SN 出現次數統計（前20名）
            sn_counts = session.query(
                TestRecord.sn,
                func.count(TestRecord.id).label('count')
            ).group_by(TestRecord.sn)\
             .order_by(desc('count'))\
             .limit(20).all()
            
            return {
                'total_sns': total_sns,
                'total_records': total_records,
                'latest_date': latest_date,
                'test_type_stats': dict(test_type_stats),
                'top_sns': [{'sn': sn, 'count': count} for sn, count in sn_counts]
            }
    
    def get_records_by_sn(self, sn: str) -> List[TestRecord]:
        """根據 SN 獲取所有相關記錄"""
        with self.get_session() as session:
            return session.query(TestRecord)\
                         .filter(TestRecord.sn == sn)\
                         .order_by(TestRecord.test_date, TestRecord.test_time)\
                         .all()

class ImportService:
    """
    匯入服務類
    負責 CSV 檔案的匯入處理
    """
    
    def __init__(self):
        self.db_service = DatabaseService()
    
    def import_csv_file(self, file_path: str, filename: str, 
                       encoding: str = 'utf-8') -> Tuple[bool, Dict]:
        """
        匯入 CSV 檔案
        
        Args:
            file_path: 檔案路徑
            filename: 檔案名稱
            encoding: 檔案編碼
            
        Returns:
            Tuple[bool, Dict]: (是否成功, 詳細結果)
        """
        import_start_time = datetime.utcnow()
        
        # 創建匯入記錄
        import_log = ImportLog(
            filename=filename,
            import_status='processing',
            import_time=import_start_time
        )
        
        result = {
            'success': False,
            'message': '',
            'statistics': {
                'total_rows': 0,
                'successful_imports': 0,
                'failed_imports': 0,
                'duplicate_skips': 0
            },
            'errors': []
        }
        
        try:
            with self.db_service.get_session() as session:
                session.add(import_log)
                session.commit()
                
                # 解析 CSV 檔案
                logger.info(f"開始解析檔案：{filename}")
                parsed_records, parse_stats = parse_csv_file(file_path, encoding)
                
                import_log.total_rows = parse_stats['total_rows']
                result['statistics']['total_rows'] = parse_stats['total_rows']
                
                # 批次匯入記錄
                for parsed_record in parsed_records:
                    try:
                        if parsed_record.is_valid:
                            success, message = self.db_service.create_test_record(
                                parsed_record, filename, session
                            )
                            
                            if success:
                                import_log.successful_imports += 1
                                result['statistics']['successful_imports'] += 1
                            else:
                                if "已存在" in message:
                                    import_log.duplicate_skips += 1
                                    result['statistics']['duplicate_skips'] += 1
                                else:
                                    import_log.failed_imports += 1
                                    result['statistics']['failed_imports'] += 1
                                    result['errors'].append({
                                        'row': parsed_record.original_row_index + 1,
                                        'error': message
                                    })
                        else:
                            import_log.failed_imports += 1
                            result['statistics']['failed_imports'] += 1
                            result['errors'].append({
                                'row': parsed_record.original_row_index + 1,
                                'error': parsed_record.error_message
                            })
                            
                    except Exception as e:
                        import_log.failed_imports += 1
                        result['statistics']['failed_imports'] += 1
                        result['errors'].append({
                            'row': parsed_record.original_row_index + 1,
                            'error': f"匯入錯誤：{str(e)}"
                        })
                        logger.error(f"匯入記錄失敗：{str(e)}")
                
                # 更新匯入記錄狀態
                import_log.import_status = 'completed'
                import_log.completed_time = datetime.utcnow()
                session.commit()
                
                result['success'] = True
                result['message'] = f"匯入完成：成功 {result['statistics']['successful_imports']} 筆，" \
                                  f"失敗 {result['statistics']['failed_imports']} 筆，" \
                                  f"重複跳過 {result['statistics']['duplicate_skips']} 筆"
                
                logger.info(result['message'])
                
        except Exception as e:
            # 更新匯入記錄為失敗狀態
            try:
                with self.db_service.get_session() as session:
                    import_log.import_status = 'failed'
                    import_log.error_message = str(e)
                    import_log.completed_time = datetime.utcnow()
                    session.merge(import_log)
                    session.commit()
            except:
                pass
            
            result['message'] = f"匯入失敗：{str(e)}"
            logger.error(result['message'])
        
        return result['success'], result
    
    def get_import_history(self, limit: int = 50) -> List[ImportLog]:
        """獲取匯入歷史記錄"""
        with self.db_service.get_session() as session:
            return session.query(ImportLog)\
                         .order_by(desc(ImportLog.import_time))\
                         .limit(limit)\
                         .all()

class QueryService:
    """
    查詢服務類
    提供複雜的數據查詢和分析功能
    """
    
    def __init__(self):
        self.db_service = DatabaseService()
    
    def search_records(self, **kwargs) -> Tuple[List[Dict], int]:
        """
        搜尋記錄（返回字典格式，便於 JSON 序列化）
        """
        records, total = self.db_service.query_records(**kwargs)
        return [record.to_dict() for record in records], total
    
    def get_frequency_analysis(self, sn: str, frequency: str) -> Dict:
        """
        獲取指定 SN 和頻率的數據分析
        
        Args:
            sn: 設備序號
            frequency: 頻率（如 '1000'）
            
        Returns:
            Dict: 分析結果
        """
        with self.db_service.get_session() as session:
            freq_column = getattr(TestRecord, f'freq_{frequency}', None)
            if not freq_column:
                return {'error': f'不支援的頻率：{frequency}'}
            
            records = session.query(TestRecord)\
                            .filter(TestRecord.sn == sn)\
                            .filter(freq_column.isnot(None))\
                            .order_by(TestRecord.test_date, TestRecord.test_time)\
                            .all()
            
            if not records:
                return {'error': f'未找到 SN {sn} 在頻率 {frequency} 的數據'}
            
            values = [getattr(record, f'freq_{frequency}') for record in records]
            
            return {
                'sn': sn,
                'frequency': frequency,
                'count': len(values),
                'min_value': min(values),
                'max_value': max(values),
                'avg_value': sum(values) / len(values),
                'latest_value': values[-1] if values else None,
                'trend_data': [
                    {
                        'date': record.test_date,
                        'time': record.test_time,
                        'type': record.test_type,
                        'value': getattr(record, f'freq_{frequency}')
                    }
                    for record in records
                ]
            }
    
    def compare_sn_performance(self, sn1: str, sn2: str, frequency: str) -> Dict:
        """比較兩個 SN 在指定頻率下的表現"""
        analysis1 = self.get_frequency_analysis(sn1, frequency)
        analysis2 = self.get_frequency_analysis(sn2, frequency)
        
        if 'error' in analysis1 or 'error' in analysis2:
            return {
                'error': '其中一個或兩個 SN 都沒有數據',
                'sn1_error': analysis1.get('error'),
                'sn2_error': analysis2.get('error')
            }
        
        return {
            'frequency': frequency,
            'sn1': {
                'sn': sn1,
                'avg': analysis1['avg_value'],
                'min': analysis1['min_value'],
                'max': analysis1['max_value'],
                'count': analysis1['count']
            },
            'sn2': {
                'sn': sn2,
                'avg': analysis2['avg_value'],
                'min': analysis2['min_value'],
                'max': analysis2['max_value'],
                'count': analysis2['count']
            },
            'comparison': {
                'avg_diff': analysis1['avg_value'] - analysis2['avg_value'],
                'performance_better': sn1 if analysis1['avg_value'] > analysis2['avg_value'] else sn2
            }
        }

# 服務實例（單例）
database_service = DatabaseService()
import_service = ImportService()
query_service = QueryService()

if __name__ == "__main__":
    # 測試服務功能
    stats = database_service.get_sn_statistics()
    print(f"資料庫統計：{stats}")
    
    # 測試查詢
    records, total = query_service.search_records(limit=5)
    print(f"查詢到 {total} 筆記錄，顯示前 {len(records)} 筆")