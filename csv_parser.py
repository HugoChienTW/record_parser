"""
CSV 解析模組
專案：CSV 數據分析與管理系統
負責：檔案解析、數據驗證、格式轉換
"""

import pandas as pd
import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ParsedFilename:
    """解析後的檔案名稱結構"""
    sn: str
    test_date: str  # YYYYMMDD
    test_time: str  # HHMMSS
    test_type: str  # left/right/rec1/rec2
    original_filename: str
    is_valid: bool
    error_message: Optional[str] = None

@dataclass
class ParsedRecord:
    """解析後的測試記錄"""
    parsed_filename: ParsedFilename
    frequency_data: Dict[str, float]  # 頻率 -> 測試值
    original_row_index: int
    is_valid: bool
    error_message: Optional[str] = None

class FilenameParser:
    """
    檔案名稱解析器
    專門處理格式：SN_YYYYMMDD_HHMMSS_(left/right/rec1/rec2)
    """
    
    # 定義正規表達式模式
    FILENAME_PATTERN = re.compile(
        r'^([A-Za-z0-9]+)_(\d{8})_(\d{6})_(left|right|rec1|rec2)$'
    )
    
    VALID_TEST_TYPES = {'left', 'right', 'rec1', 'rec2'}
    
    @classmethod
    def parse(cls, filename: str) -> ParsedFilename:
        """
        解析檔案名稱
        
        Args:
            filename: 檔案名稱（可包含副檔名）
            
        Returns:
            ParsedFilename: 解析結果
        """
        # 移除副檔名
        base_name = filename.split('.')[0] if '.' in filename else filename
        
        try:
            match = cls.FILENAME_PATTERN.match(base_name)
            
            if not match:
                return ParsedFilename(
                    sn="", test_date="", test_time="", test_type="",
                    original_filename=filename, is_valid=False,
                    error_message="檔案名稱格式不符合規範，應為：SN_YYYYMMDD_HHMMSS_(left/right/rec1/rec2)"
                )
            
            sn, date, time, test_type = match.groups()
            
            # 驗證日期格式
            if not cls._validate_date(date):
                return ParsedFilename(
                    sn=sn, test_date=date, test_time=time, test_type=test_type,
                    original_filename=filename, is_valid=False,
                    error_message=f"日期格式錯誤：{date}，應為有效的 YYYYMMDD 格式"
                )
            
            # 驗證時間格式
            if not cls._validate_time(time):
                return ParsedFilename(
                    sn=sn, test_date=date, test_time=time, test_type=test_type,
                    original_filename=filename, is_valid=False,
                    error_message=f"時間格式錯誤：{time}，應為有效的 HHMMSS 格式"
                )
            
            return ParsedFilename(
                sn=sn, test_date=date, test_time=time, test_type=test_type,
                original_filename=filename, is_valid=True
            )
            
        except Exception as e:
            return ParsedFilename(
                sn="", test_date="", test_time="", test_type="",
                original_filename=filename, is_valid=False,
                error_message=f"解析錯誤：{str(e)}"
            )
    
    @staticmethod
    def _validate_date(date_str: str) -> bool:
        """驗證日期字符串"""
        try:
            datetime.strptime(date_str, '%Y%m%d')
            return True
        except ValueError:
            return False
    
    @staticmethod
    def _validate_time(time_str: str) -> bool:
        """驗證時間字符串"""
        try:
            datetime.strptime(time_str, '%H%M%S')
            return True
        except ValueError:
            return False

class CSVDataParser:
    """
    CSV 數據解析器
    負責解析 CSV 檔案內容，提取測試數據
    """
    
    # 標準頻率欄位映射 - 支援多種可能的欄位名稱
    FREQUENCY_MAPPINGS = {
        '100': ['100', 'freq_100', 'F100'],
        '125': ['125', 'freq_125', 'F125'],
        '160': ['160', 'freq_160', 'F160'],
        '200': ['200', 'freq_200', 'F200'],
        '250': ['250', 'freq_250', 'F250'],
        '315': ['315', 'freq_315', 'F315'],
        '400': ['400', 'freq_400', 'F400'],
        '500': ['500', 'freq_500', 'F500'],
        '630': ['630', 'freq_630', 'F630'],
        '800': ['800', 'freq_800', 'F800'],
        '1000': ['1000', 'freq_1000', 'F1000'],
        '1250': ['1250', 'freq_1250', 'F1250'],
        '1600': ['1600', 'freq_1600', 'F1600'],
        '2000': ['2000', 'freq_2000', 'F2000'],
    }
    
    def __init__(self):
        self.reset_statistics()
    
    def reset_statistics(self):
        """重置解析統計"""
        self.stats = {
            'total_rows': 0,
            'valid_records': 0,
            'invalid_filenames': 0,
            'invalid_data': 0,
            'duplicate_records': 0
        }
    
    def parse_csv_file(self, file_path: str, encoding: str = 'utf-8') -> Tuple[List[ParsedRecord], Dict]:
        """
        解析 CSV 檔案
        
        Args:
            file_path: CSV 檔案路徑
            encoding: 檔案編碼
            
        Returns:
            Tuple[List[ParsedRecord], Dict]: (解析記錄列表, 統計資訊)
        """
        self.reset_statistics()
        parsed_records = []
        
        try:
            # 讀取 CSV 檔案
            df = pd.read_csv(file_path, encoding=encoding)
            self.stats['total_rows'] = len(df)
            
            # 確認第一欄是檔案名稱
            if len(df.columns) == 0:
                raise ValueError("CSV 檔案為空或格式錯誤")
            
            filename_col = df.columns[0]
            
            # 建立頻率欄位映射
            frequency_columns = self._map_frequency_columns(df.columns)
            
            logger.info(f"開始解析 CSV 檔案：{file_path}")
            logger.info(f"總行數：{len(df)}")
            logger.info(f"找到頻率欄位：{list(frequency_columns.keys())}")
            
            # 逐行解析
            for index, row in df.iterrows():
                try:
                    parsed_record = self._parse_row(row, filename_col, frequency_columns, index)
                    parsed_records.append(parsed_record)
                    
                    if parsed_record.is_valid:
                        self.stats['valid_records'] += 1
                    else:
                        if not parsed_record.parsed_filename.is_valid:
                            self.stats['invalid_filenames'] += 1
                        else:
                            self.stats['invalid_data'] += 1
                            
                except Exception as e:
                    logger.error(f"解析第 {index + 1} 行時發生錯誤：{str(e)}")
                    # 創建錯誤記錄
                    error_record = ParsedRecord(
                        parsed_filename=ParsedFilename(
                            sn="", test_date="", test_time="", test_type="",
                            original_filename="", is_valid=False,
                            error_message=f"行解析錯誤：{str(e)}"
                        ),
                        frequency_data={},
                        original_row_index=index,
                        is_valid=False,
                        error_message=f"行解析錯誤：{str(e)}"
                    )
                    parsed_records.append(error_record)
                    self.stats['invalid_data'] += 1
            
        except Exception as e:
            logger.error(f"讀取 CSV 檔案失敗：{str(e)}")
            self.stats['file_read_error'] = str(e)
        
        return parsed_records, self.stats
    
    def _parse_row(self, row: pd.Series, filename_col: str, frequency_columns: Dict[str, str], 
                   row_index: int) -> ParsedRecord:
        """解析單行數據"""
        
        # 解析檔案名稱
        filename = str(row[filename_col]) if pd.notna(row[filename_col]) else ""
        parsed_filename = FilenameParser.parse(filename)
        
        # 提取頻率數據
        frequency_data = {}
        for freq, col_name in frequency_columns.items():
            try:
                value = row[col_name]
                if pd.notna(value):
                    # 嘗試轉換為浮點數
                    numeric_value = float(value)
                    frequency_data[freq] = numeric_value
            except (ValueError, TypeError) as e:
                # 記錄無法轉換的數據，但不阻止整體解析
                logger.warning(f"行 {row_index + 1}，頻率 {freq} 數據轉換失敗：{value}")
        
        # 驗證記錄完整性
        is_valid = parsed_filename.is_valid and len(frequency_data) > 0
        error_message = None
        
        if not parsed_filename.is_valid:
            error_message = parsed_filename.error_message
        elif len(frequency_data) == 0:
            error_message = "未找到有效的頻率測試數據"
        
        return ParsedRecord(
            parsed_filename=parsed_filename,
            frequency_data=frequency_data,
            original_row_index=row_index,
            is_valid=is_valid,
            error_message=error_message
        )
    
    def _map_frequency_columns(self, columns: List[str]) -> Dict[str, str]:
        """
        映射 CSV 欄位到標準頻率
        
        Args:
            columns: CSV 欄位列表
            
        Returns:
            Dict[str, str]: {頻率: 欄位名稱}
        """
        frequency_columns = {}
        
        for freq, possible_names in self.FREQUENCY_MAPPINGS.items():
            for col_name in columns:
                # 精確匹配或包含匹配
                if col_name in possible_names or any(name in col_name for name in possible_names):
                    frequency_columns[freq] = col_name
                    break
        
        # 嘗試數字欄位匹配
        for col_name in columns:
            try:
                # 檢查是否為純數字欄位
                if col_name.isdigit():
                    freq = col_name
                    if freq in self.FREQUENCY_MAPPINGS and freq not in frequency_columns:
                        frequency_columns[freq] = col_name
            except:
                continue
        
        return frequency_columns

class DataValidator:
    """
    數據驗證器
    負責驗證解析後的數據是否符合業務規則
    """
    
    @staticmethod
    def validate_frequency_range(value: float, frequency: str) -> bool:
        """驗證頻率數據範圍是否合理"""
        # 基於您的數據特徵，設定合理範圍
        if -200 <= value <= 50:  # dB 值通常在此範圍
            return True
        return False
    
    @staticmethod
    def validate_sn_format(sn: str) -> bool:
        """驗證 SN 格式"""
        if len(sn) < 5 or len(sn) > 50:
            return False
        # SN 應包含字母和數字
        return bool(re.match(r'^[A-Za-z0-9]+$', sn))
    
    @classmethod
    def validate_parsed_record(cls, record: ParsedRecord) -> Tuple[bool, Optional[str]]:
        """
        驗證解析記錄
        
        Returns:
            Tuple[bool, Optional[str]]: (是否有效, 錯誤訊息)
        """
        if not record.is_valid:
            return False, record.error_message
        
        # 驗證 SN
        if not cls.validate_sn_format(record.parsed_filename.sn):
            return False, f"SN 格式不正確：{record.parsed_filename.sn}"
        
        # 驗證頻率數據
        for freq, value in record.frequency_data.items():
            if not cls.validate_frequency_range(value, freq):
                return False, f"頻率 {freq} 的數據 {value} 超出合理範圍"
        
        return True, None

# 便利函數
def parse_csv_file(file_path: str, encoding: str = 'utf-8') -> Tuple[List[ParsedRecord], Dict]:
    """解析 CSV 檔案的便利函數"""
    parser = CSVDataParser()
    return parser.parse_csv_file(file_path, encoding)

if __name__ == "__main__":
    # 測試解析功能
    test_filename = "32120121ED0755130005_20250522_084534_left"
    parsed = FilenameParser.parse(test_filename)
    print(f"解析結果：{parsed}")
    
    # 測試 CSV 解析（需要實際檔案）
    # records, stats = parse_csv_file("test.csv")
    # print(f"解析統計：{stats}")