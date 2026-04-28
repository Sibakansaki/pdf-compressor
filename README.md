# PDF 壓縮器

用 Ghostscript 壓縮 PDF 的 Mac 桌面應用程式。

---

## 環境需求

- Python 3
- Ghostscript（`/opt/homebrew/bin/gs`）

如果還沒裝 Ghostscript：
```bash
brew install ghostscript
```

---

## 第一次使用

```bash
# 1. clone 下來
git clone https://github.com/Sibakansaki/pdf-compressor.git
cd pdf-compressor

# 2. 打包成 .app
chmod +x build_app.sh
./build_app.sh

# 3. 把 app 拖到 Applications
mv dist/PDF壓縮器.app /Applications/
```

---

## 修改程式碼後重新打包

```bash
# 1. 打包
./build_app.sh

# 2. 更新 Applications 裡的 app
rm -rf /Applications/PDF壓縮器.app
mv dist/PDF壓縮器.app /Applications/
```

---

## 推上 GitHub

```bash
git add .
git commit -m "說明改了什麼"
git push
```

---

## 檔案說明

| 檔案 | 說明 |
|------|------|
| `pdf_compressor.py` | 主程式，改這個 |
| `build_app.sh` | 打包腳本 |
| `dist/` | 打包後的 .app（自動產生，不會上傳） |
| `.venv/` | Python 虛擬環境（自動產生，不會上傳） |
| `build/` | 打包暫存檔（自動產生，不會上傳） |
