import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import pysrt
import threading
import json
import os
import time
from google import genai
from google.genai import types
from dotenv import load_dotenv

# 讀取 .env 檔案中的環境變數
load_dotenv()

class SRTTranslatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SRT 台灣口語化精確翻譯軟體 v1.1")
        self.root.geometry("600x450")
        
        self.srt_path = tk.StringVar()
        self.api_key = tk.StringVar(value=os.getenv("GEMINI_API_KEY", ""))
        self.model_var = tk.StringVar(value="gemini-3.1-pro-preview")
        self.style_var = tk.StringVar(value="中度口語化")
        self.status_var = tk.StringVar(value="請選擇 SRT 檔案並輸入 API Key")
        
        self.create_widgets()
        
    def create_widgets(self):
        # API 設定區域
        frame_api = ttk.LabelFrame(self.root, text="Gemini API 設定", padding=10)
        frame_api.pack(fill="x", padx=10, pady=5)
        ttk.Label(frame_api, text="API Key:").pack(side="left")
        ttk.Entry(frame_api, textvariable=self.api_key, width=65, show="*").pack(side="left", padx=5)
        
        # 翻譯選項區域
        frame_options = ttk.LabelFrame(self.root, text="翻譯選項", padding=10)
        frame_options.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(frame_options, text="模型:").pack(side="left")
        model_combo = ttk.Combobox(frame_options, textvariable=self.model_var, values=["gemini-3.1-pro-preview", "gemini-2.5-pro", "gemini-2.5-flash", "gemini-pro-latest"], width=25, state="readonly")
        model_combo.pack(side="left", padx=5)
        
        ttk.Label(frame_options, text="風格:").pack(side="left", padx=(20, 0))
        style_combo = ttk.Combobox(frame_options, textvariable=self.style_var, values=["輕度口語化", "中度口語化"], width=15, state="readonly")
        style_combo.pack(side="left", padx=5)
        
        # 檔案選擇區域
        frame_file = ttk.LabelFrame(self.root, text="檔案選擇", padding=10)
        frame_file.pack(fill="x", padx=10, pady=5)
        ttk.Label(frame_file, text="SRT 檔案:").pack(side="left")
        ttk.Entry(frame_file, textvariable=self.srt_path, width=40, state="readonly").pack(side="left", padx=5)
        ttk.Button(frame_file, text="瀏覽...", command=self.browse_file).pack(side="left")
        
        # 進度區域
        frame_progress = ttk.LabelFrame(self.root, text="進度與狀態", padding=10)
        frame_progress.pack(fill="both", expand=True, padx=10, pady=5)
        self.progress = ttk.Progressbar(frame_progress, orient="horizontal", length=100, mode="determinate")
        self.progress.pack(fill="x", pady=10)
        ttk.Label(frame_progress, textvariable=self.status_var, wraplength=550).pack(fill="both", expand=True)
        
        # 執行按鈕
        self.start_btn = ttk.Button(self.root, text="開始翻譯", command=self.start_translation)
        self.start_btn.pack(pady=10)
        
        # 右下角簽名
        signature_frame = ttk.Frame(self.root)
        signature_frame.pack(side="bottom", anchor="e", padx=10, pady=5)
        ttk.Label(signature_frame, text="Author: Gary Ouyang\nDate: June 2026", justify="right", foreground="gray").pack()
        
    def browse_file(self):
        filename = filedialog.askopenfilename(filetypes=[("SRT Files", "*.srt")])
        if filename:
            self.srt_path.set(filename)
            
    def update_status(self, msg, progress_val=None):
        self.status_var.set(msg)
        if progress_val is not None:
            self.progress["value"] = progress_val
        self.root.update_idletasks()
            
    def start_translation(self):
        if not self.api_key.get().strip():
            messagebox.showerror("錯誤", "請輸入 Gemini API Key")
            return
        if not self.srt_path.get().strip():
            messagebox.showerror("錯誤", "請選擇一個 SRT 檔案")
            return
            
        # 儲存 API Key 到 .env 方便下次使用
        with open(".env", "w", encoding="utf-8") as f:
            f.write(f"GEMINI_API_KEY={self.api_key.get().strip()}\n")
            
        self.start_btn.config(state="disabled")
        threading.Thread(target=self.process_translation, daemon=True).start()
        
    def process_translation(self):
        try:
            self.update_status("正在讀取 SRT 檔案...", 0)
            
            # 嘗試讀取 SRT 檔，若有編碼問題可自動 fallback
            try:
                srt_file = pysrt.open(self.srt_path.get(), encoding='utf-8')
            except UnicodeDecodeError:
                srt_file = pysrt.open(self.srt_path.get(), encoding='cp950') # 針對 Big5/ANSI
                
            total_subs = len(srt_file)
            if total_subs == 0:
                self.root.after(0, lambda: messagebox.showerror("錯誤", "SRT 檔案是空的或無法正確解析。"))
                self.update_status("解析失敗。")
                return

            chunk_size = 200
            
            # 建立暫存資料夾
            file_dir = os.path.dirname(self.srt_path.get())
            base_name = os.path.basename(self.srt_path.get())
            cache_dir = os.path.join(file_dir, f".{base_name}_cache")
            if not os.path.exists(cache_dir):
                os.makedirs(cache_dir)
                
            client = genai.Client(api_key=self.api_key.get().strip())
            
            style_prompt = "自然、流暢的『台灣口語化中文』，使其非常符合台灣在地用語習慣。"
            if self.style_var.get() == "輕度口語化":
                style_prompt = "『輕度台灣口語化中文』，保留原本的語意與語氣，稍微調整用詞使其符合台灣在地習慣即可，不要過度改寫。"
                
            system_instruction = (
                f"你是一個專業的台灣影視字幕翻譯員。請將輸入的 JSON 陣列中的每一句簡體或繁體字幕翻譯成{style_prompt}\n"
                "請嚴格遵守以下規則：\n"
                "1. 絕對不要加入任何不必要的數字、標點符號或註解，只回傳純文字翻譯。\n"
                "2. 保持句意精確。\n"
                "3. 確保你的回傳格式是一個 JSON 字串陣列 (例如: [\"翻譯結果一\", \"翻譯結果二\"])。\n"
                "4. 你回傳的 JSON 陣列長度，必須與輸入的 JSON 陣列長度完全一致，且順序完美對應。"
            )
            
            config = types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
            )
            
            translated_texts = []
            
            # 切分 chunks
            chunks = [srt_file[i:i + chunk_size] for i in range(0, total_subs, chunk_size)]
            
            for chunk_idx, chunk in enumerate(chunks):
                cache_file = os.path.join(cache_dir, f"chunk_{chunk_idx}.json")
                
                # 如果該批次暫存存在，直接讀取跳過呼叫 LLM
                if os.path.exists(cache_file):
                    self.update_status(f"讀取批次 {chunk_idx+1}/{len(chunks)} 暫存...", (chunk_idx / len(chunks)) * 100)
                    with open(cache_file, "r", encoding="utf-8") as f:
                        chunk_trans = json.load(f)
                    translated_texts.extend(chunk_trans)
                    continue
                    
                self.update_status(f"正在呼叫 LLM 翻譯批次 {chunk_idx+1}/{len(chunks)}...", (chunk_idx / len(chunks)) * 100)
                
                # 準備輸入
                input_texts = [sub.text for sub in chunk]
                input_json = json.dumps(input_texts, ensure_ascii=False)
                
                # 呼叫 Gemini (加入重試機制)
                max_retries = 3
                retry_count = 0
                while retry_count <= max_retries:
                    try:
                        selected_model = self.model_var.get()
                        response = client.models.generate_content(
                            model=selected_model,
                            contents=input_json,
                            config=config
                        )
                        
                        response_text = response.text
                        chunk_trans = json.loads(response_text)
                        
                        if not isinstance(chunk_trans, list) or len(chunk_trans) != len(input_texts):
                            raise ValueError(f"回傳長度 ({len(chunk_trans) if isinstance(chunk_trans, list) else '非陣列'}) 與輸入長度 ({len(input_texts)}) 不符")
                            
                        # 寫入暫存
                        with open(cache_file, "w", encoding="utf-8") as f:
                            json.dump(chunk_trans, f, ensure_ascii=False)
                            
                        translated_texts.extend(chunk_trans)
                        
                        # 成功後，為了避免達到免費版 API 的限制 (每分鐘請求數 RPM)，強制等待
                        if chunk_idx < len(chunks) - 1:
                            delay = 35 if "pro" in selected_model else 5 # Pro 模型免費版通常限制 2 RPM，Flash 限制 15 RPM
                            self.update_status(f"批次 {chunk_idx+1} 成功，等待 {delay} 秒以避免 API 限制...", (chunk_idx / len(chunks)) * 100)
                            time.sleep(delay)
                        
                        break # 成功跳出 while
                        
                    except Exception as e:
                        err_str = str(e)
                        if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                            retry_count += 1
                            if retry_count > max_retries:
                                raise Exception("已達到 API 請求次數上限，且重試失敗。請檢查您的免費額度，或稍後再試。")
                            self.update_status(f"遇到 API 限制 (429)，等待 60 秒後重試 ({retry_count}/{max_retries})...")
                            time.sleep(60)
                        else:
                            raise e # 其他錯誤直接拋出
                            
            # 全部翻譯完畢，回填並合併
            self.update_status("翻譯完成，正在合併產生新的 SRT 檔案...", 95)
            for i, sub in enumerate(srt_file):
                sub.text = translated_texts[i]
                
            output_path = os.path.join(file_dir, f"{os.path.splitext(base_name)[0]}_zh-TW.srt")
            srt_file.save(output_path, encoding='utf-8')
            
            self.update_status(f"完成！檔案已儲存至:\n{output_path}", 100)
            self.root.after(0, lambda: messagebox.showinfo("完成", f"SRT 檔案已成功翻譯並儲存至：\n{output_path}"))
            
        except Exception as e:
            self.root.after(0, lambda err=str(e): messagebox.showerror("錯誤", f"發生未預期的錯誤:\n{err}"))
            self.update_status("發生錯誤。")
        finally:
            self.root.after(0, lambda: self.start_btn.config(state="normal"))

if __name__ == "__main__":
    root = tk.Tk()
    app = SRTTranslatorApp(root)
    root.mainloop()
