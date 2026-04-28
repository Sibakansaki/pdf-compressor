#!/bin/bash
set -e

echo ""
echo "🔧 PDF 壓縮器 v2 - 打包腳本"
echo "──────────────────────────────"

if ! command -v python3 &>/dev/null; then
  echo "❌ 找不到 Python3"; exit 1
fi
echo "✅ Python3: $(python3 --version)"

if ! command -v gs &>/dev/null; then
  echo "❌ 找不到 Ghostscript，請先執行：brew install ghostscript"; exit 1
fi
echo "✅ Ghostscript: $(gs --version)"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV="$SCRIPT_DIR/.venv"

echo ""
echo "🐍 建立虛擬環境..."
python3 -m venv "$VENV"
source "$VENV/bin/activate"

echo "📦 安裝 PyQt6 & PyInstaller..."
pip install PyQt6 pyinstaller --quiet

echo "🏗  打包中（約需 1-2 分鐘）..."
pyinstaller \
  --onefile \
  --windowed \
  --name "PDF壓縮器" \
  --hidden-import PyQt6.QtCore \
  --hidden-import PyQt6.QtGui \
  --hidden-import PyQt6.QtWidgets \
  --collect-all PyQt6 \
  "$SCRIPT_DIR/pdf_compressor.py" \
  --distpath "$SCRIPT_DIR/dist" \
  --workpath "$SCRIPT_DIR/build" \
  --specpath "$SCRIPT_DIR" \
  --noconfirm \
  --log-level WARN

echo "🔓 解除 Gatekeeper 限制..."
xattr -cr "$SCRIPT_DIR/dist/PDF壓縮器.app"

deactivate

echo ""
echo "✅ 完成！直接雙擊開啟："
echo "   $SCRIPT_DIR/dist/PDF壓縮器.app"
echo ""
