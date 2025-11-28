# 🏋️ My Gym Tracker

一個功能完整的健身追蹤應用程式，使用 Streamlit 構建，幫助您記錄訓練、追蹤進度並分析數據。

## 功能特色

### 📝 記錄訓練 (Log Workout)
- 快速記錄多組訓練數據
- 自動填入上一次訓練記錄（Auto-fill）
- RPE（自覺強度）評分
- 支援多種單位（kg、lb、notch）
- 休息計時器

### 📈 進度儀表板 (Progress Dashboard)
- 動作趨勢圖表（重量、容量、1RM）
- 個人紀錄牆（PR Wall）
- 肌肉群訓練分布熱力圖
- 時間範圍篩選

### 📚 動作庫管理 (Library Manager)
- 新增自定義動作
- 管理動作分類和類型
- 支援多種動作類型（Barbell、Dumbbell、Machine、Cable）

### 🔧 進階功能
- 1RM 計算器（Epley 公式）
- 單位自動轉換
- 訓練容量計算

## 安裝說明

### 1. 安裝依賴套件

```bash
pip install -r requirements.txt
```

### 2. 執行應用程式

**預設連接埠（8501）：**
```bash
streamlit run app.py
```

**指定其他連接埠（避免與其他專案衝突）：**
```bash
streamlit run app.py --server.port 8502
```

或使用其他可用連接埠：
```bash
streamlit run app.py --server.port 8503
streamlit run app.py --server.port 8504
```

應用程式將在瀏覽器中自動開啟（例如 `http://localhost:8502`）

## 使用指南

### 首次使用

1. 應用程式會自動建立 SQLite 資料庫（`data/gym_tracker.db`）
2. 建議先在「動作庫管理」頁面新增常用動作
3. 開始在「記錄訓練」頁面記錄您的訓練

### 記錄訓練

1. 選擇訓練日期（預設為今天）
2. 選擇肌肉群，然後選擇動作
3. 在動態表格中輸入多組數據（重量、次數）
4. 調整 RPE 和添加備註（可選）
5. 點擊「儲存訓練」按鈕

### 查看進度

1. 前往「進度儀表板」頁面
2. 選擇要分析的動作
3. 查看趨勢圖表、個人紀錄和訓練分布

## 資料儲存

所有資料儲存在 SQLite 資料庫中（`data/gym_tracker.db`），包含：
- 訓練記錄
- 動作庫
- 歷史數據

## 技術架構

- **前端框架**: Streamlit
- **資料庫**: SQLite
- **資料視覺化**: Plotly
- **資料處理**: Pandas

## 注意事項

- 單位轉換：系統會自動將所有重量統一轉換為 kg 進行分析，但保留原始單位顯示
- 1RM 計算：使用 Epley 公式 `Weight × (1 + Reps/30)`
- 資料備份：建議定期備份 `data/gym_tracker.db` 檔案

## 授權

本專案為個人使用，可自由修改和擴展。

