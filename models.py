"""
資料庫模型定義
專案：CSV 數據分析與管理系統
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, UniqueConstraint, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

Base = declarative_base()

class TestRecord(Base):
    """
    測試記錄主表
    設計原則：每個 SN + 測試時間 + 測試項目 組合的唯一性
    """
    __tablename__ = 'test_records'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    sn = Column(String(50), nullable=False, index=True, comment='設備序號')
    test_date = Column(String(8), nullable=False, comment='測試日期 YYYYMMDD')
    test_time = Column(String(6), nullable=False, comment='測試時間 HHMMSS')
    test_type = Column(String(10), nullable=False, comment='測試項目：left/right/rec1/rec2')
    
    # 測試數據欄位 - 對應 [630, 800, 1000, 1250, 1600, 2000] 等頻率
    freq_630 = Column(Float, comment='630Hz 測試值')
    freq_800 = Column(Float, comment='800Hz 測試值')
    freq_1000 = Column(Float, comment='1000Hz 測試值')
    freq_1250 = Column(Float, comment='1250Hz 測試值')
    freq_1600 = Column(Float, comment='1600Hz 測試值')
    freq_2000 = Column(Float, comment='2000Hz 測試值')
    
    # 擴展欄位，支援更多頻率
    freq_100 = Column(Float, comment='100Hz 測試值')
    freq_125 = Column(Float, comment='125Hz 測試值')
    freq_160 = Column(Float, comment='160Hz 測試值')
    freq_200 = Column(Float, comment='200Hz 測試值')
    freq_250 = Column(Float, comment='250Hz 測試值')
    freq_315 = Column(Float, comment='315Hz 測試值')
    freq_400 = Column(Float, comment='400Hz 測試值')
    freq_500 = Column(Float, comment='500Hz 測試值')
    
    # 元數據
    filename = Column(String(255), comment='原始檔案名稱')
    import_time = Column(DateTime, default=datetime.utcnow, comment='資料匯入時間')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 建立複合唯一約束：SN + 測試日期 + 測試時間 + 測試項目
    __table_args__ = (
        UniqueConstraint('sn', 'test_date', 'test_time', 'test_type', 
                        name='uq_sn_datetime_type'),
        Index('idx_sn_date', 'sn', 'test_date'),
        Index('idx_test_type', 'test_type'),
        Index('idx_import_time', 'import_time'),
    )
    
    def __repr__(self):
        return f"<TestRecord(sn='{self.sn}', date='{self.test_date}', time='{self.test_time}', type='{self.test_type}')>"
    
    def to_dict(self):
        """轉換為字典格式，便於 JSON 序列化"""
        return {
            'id': self.id,
            'sn': self.sn,
            'test_date': self.test_date,
            'test_time': self.test_time,
            'test_type': self.test_type,
            'freq_630': self.freq_630,
            'freq_800': self.freq_800,
            'freq_1000': self.freq_1000,
            'freq_1250': self.freq_1250,
            'freq_1600': self.freq_1600,
            'freq_2000': self.freq_2000,
            'filename': self.filename,
            'import_time': self.import_time.isoformat() if self.import_time else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class ImportLog(Base):
    """
    匯入記錄表 - 追蹤每次 CSV 匯入的詳細資訊
    """
    __tablename__ = 'import_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String(255), nullable=False, comment='匯入的檔案名稱')
    file_size = Column(Integer, comment='檔案大小（bytes）')
    total_rows = Column(Integer, comment='CSV 總行數')
    successful_imports = Column(Integer, default=0, comment='成功匯入筆數')
    failed_imports = Column(Integer, default=0, comment='失敗筆數')
    duplicate_skips = Column(Integer, default=0, comment='重複跳過筆數')
    import_status = Column(String(20), default='processing', comment='匯入狀態：processing/completed/failed')
    error_message = Column(String(1000), comment='錯誤訊息')
    import_time = Column(DateTime, default=datetime.utcnow, comment='匯入開始時間')
    completed_time = Column(DateTime, comment='匯入完成時間')
    
    def __repr__(self):
        return f"<ImportLog(filename='{self.filename}', status='{self.import_status}')>"

class DatabaseManager:
    """
    資料庫管理器 - 負責資料庫連接、初始化等操作
    採用單例模式確保資料庫連接的一致性
    """
    
    _instance = None
    _engine = None
    _SessionLocal = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.initialized = True
            self.database_url = self._get_database_url()
            self._setup_database()
    
    def _get_database_url(self):
        """獲取資料庫連接 URL"""
        # 支援環境變數配置，便於部署時切換資料庫
        db_url = os.getenv('DATABASE_URL')
        if db_url:
            return db_url
        
        # 預設使用 SQLite，數據檔案存放在 data 目錄
        os.makedirs('data', exist_ok=True)
        return 'sqlite:///data/test_records.db'
    
    def _setup_database(self):
        """設定資料庫連接和會話"""
        self._engine = create_engine(
            self.database_url,
            echo=False,  # 生產環境設為 False
            pool_pre_ping=True,  # 自動檢測連接有效性
            connect_args={'check_same_thread': False} if 'sqlite' in self.database_url else {}
        )
        
        self._SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self._engine
        )
        
        # 創建資料表
        Base.metadata.create_all(bind=self._engine)
    
    def get_session(self):
        """獲取資料庫會話"""
        if self._SessionLocal is None:
            raise Exception("資料庫未初始化")
        return self._SessionLocal()
    
    def get_engine(self):
        """獲取資料庫引擎"""
        return self._engine
    
    def close(self):
        """關閉資料庫連接"""
        if self._engine:
            self._engine.dispose()

# 全域資料庫管理器實例
db_manager = DatabaseManager()

def get_db_session():
    """
    獲取資料庫會話的便利函數
    使用 with 語句確保會話正確關閉
    """
    session = db_manager.get_session()
    try:
        yield session
    finally:
        session.close()

def init_database():
    """初始化資料庫（創建表格）"""
    try:
        Base.metadata.create_all(bind=db_manager.get_engine())
        print("資料庫初始化完成")
        return True
    except Exception as e:
        print(f"資料庫初始化失敗: {str(e)}")
        return False

if __name__ == "__main__":
    # 測試資料庫連接
    init_database()
    
    # 測試資料庫操作
    session = db_manager.get_session()
    try:
        # 測試創建記錄
        test_record = TestRecord(
            sn="TEST123456789",
            test_date="20250602",
            test_time="120000",
            test_type="left",
            freq_1000=-75.5,
            filename="test_file.csv"
        )
        
        session.add(test_record)
        session.commit()
        print("測試記錄創建成功")
        
        # 測試查詢
        records = session.query(TestRecord).filter_by(sn="TEST123456789").all()
        print(f"查詢到 {len(records)} 筆記錄")
        
    except Exception as e:
        print(f"資料庫操作錯誤: {str(e)}")
        session.rollback()
    finally:
        session.close()