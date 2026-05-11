# PDF 壓縮器

全選圖片右鍵 → 快速動作 → 製作 PDF，直接產生壓縮好的 PDF。

---

## 需要安裝的東西

### 1. Homebrew
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### 2. Python 虛擬環境 & Pillow
```bash
cd ~/Documents/Coding
python3 -m venv .venv
source .venv/bin/activate
pip install PyQt6 Pillow
```

---

## 安裝快速動作

### 步驟一：下載腳本
```bash
curl -o ~/img_to_pdf.py https://raw.githubusercontent.com/Sibakansaki/pdf-compressor/main/img_to_pdf.py
```

### 步驟二：建立 Automator 快速動作
1. 打開 **Automator** → 新增文件 → **快速動作**
2. 工作流程接收：**檔案或資料夾**，在：**Finder**
3. 左邊搜尋「**執行 Shell 工序指令**」拖進來
4. Shell 選 `/bin/zsh`，傳遞輸入選「**做為引數**」
5. 貼上以下腳本：

```bash
/Users/你的帳號/Documents/Coding/.venv/bin/python3 /Users/你的帳號/img_to_pdf.py "$@"
```

> 把「你的帳號」換成你的 Mac 使用者名稱

6. 存檔，取名「**製作 PDF**」

---

## 使用方式

1. 在 Finder 全選要轉換的圖片（支援 JPG、JPEG、PNG）
2. 右鍵 → 快速動作 → **製作 PDF**
3. 出現進度視窗，完成後 PDF 會出現在**圖片所在的資料夾**

---

## 檔案說明

| 檔案 | 說明 |
|------|------|
| `img_to_pdf.py` | 主程式，放在 `~/` 家目錄 |

---

## 注意事項

- 圖片會依照檔名數字排序後合併成 PDF
- 壓縮率約 70%，縮小至原始的 0.7 倍尺寸
- 失敗時桌面會產生 `img_to_pdf_error.txt` 顯示錯誤原因
