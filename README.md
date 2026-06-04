# SRT 台灣口語化精確翻譯軟體 v1.0 (SRT Taiwanese Translator)

這是一個輕量且精確的開源字幕翻譯工具，透過 Google Gemini API 將一般的繁體/簡體中文 `.srt` 字幕檔案，自動翻譯成自然、流暢的**台灣口語化中文**。

## ✨ 特色 (Features)
- **精確對齊**：完美保留原始 SRT 檔案的時間軸與排序，不破壞字幕結構。
- **純淨翻譯**：嚴格限制 AI 不加入額外的數字、標點符號或無意義的註解。
- **自動中斷點記憶 (Checkpoint)**：每 200 句為一個批次儲存暫存檔。遇到 API 限制或網路中斷時，重新啟動會自動從上次的進度接續，不浪費 API 額度。
- **多模型支援**：支援切換 `gemini-1.5-pro`, `gemini-3.1-pro-preview`, `gemini-2.5-flash` 等不同模型，讓您自由在「最高翻譯品質」與「最快翻譯速度」間取得平衡。
- **圖形化介面**：簡單直觀的 GUI 介面，免下指令即可輕鬆使用。

## 🚀 快速開始 (Quick Start)

### 1. 取得 Gemini API Key
前往 [Google AI Studio](https://aistudio.google.com/) 申請一組免費的 API Key。

### 2. 環境安裝
請確保您的電腦已安裝 [Python 3](https://www.python.org/)。接著在終端機輸入：
```bash
# 下載專案後，安裝相依套件
pip install -r requirements.txt
```

### 3. 執行程式
```bash
python srt_translator.py
```
*(或者您也可以使用 PyInstaller 自行打包成 exe 執行檔)*

### 4. 使用方式
1. 開啟程式後，貼上您的 Gemini API Key。
2. 點擊「瀏覽...」選擇您的 `.srt` 字幕檔。
3. 選擇您想使用的 AI 模型。
4. 點擊「開始翻譯」，完成後會在同目錄下自動產生 `[原檔名]_zh-TW.srt`。

## ⚠️ 注意事項
- 請妥善保管您的 API Key，**絕對不要**將包含 API Key 的 `.env` 檔案上傳到 GitHub！本專案的 `.gitignore` 已預設防護。
- 如果使用 Pro 系列模型遇到 `API 請求上限 (429)`，請將模型切換為 `Flash` 系列，或是在 Google Cloud 中綁定信用卡啟用隨付隨付計費。

## 👨‍💻 作者 (Author)
- **Gary Ouyang** (2026)

## 📄 授權 (License)
MIT License
