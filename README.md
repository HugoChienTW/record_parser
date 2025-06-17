# record_parser


## 專案結構

```
csv_analysis_system/
├── README.md                    # 專案說明文件
├── requirements.txt             # Python 依賴套件
├── app.py                      # Flask 主應用程式
├── models.py                   # 資料庫模型定義
├── csv_parser.py               # CSV 解析模組
├── data_service.py             # 數據服務層
├── config.py                   # 配置檔案
├── run.py                      # 應用啟動腳本
├── data/                       # 資料庫檔案目錄
│   └── test_records.db         # SQLite 資料庫檔案
├── uploads/                    # 檔案上傳暫存目錄
├── templates/                  # HTML 模板
│   ├── base.html              # 基礎模板
│   ├── index.html             # 首頁
│   ├── import.html            # 匯入頁面
│   ├── search.html            # 搜尋頁面
│   ├── analysis.html          # 分析頁面
│   └── error.html             # 錯誤頁面
├── static/                     # 靜態檔案
│   ├── css/
│   ├── js/
│   └── images/
├── tests/                      # 測試檔案
│   ├── test_models.py
│   ├── test_parser.py
│   ├── test_service.py
│   └── test_api.py
└── logs/                       # 記錄檔目錄
```