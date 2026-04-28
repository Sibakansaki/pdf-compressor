import sys
import os
import subprocess
import threading
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QFrame,
    QFileDialog, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QObject
from PyQt6.QtGui import QFont

GS_PATH = "/opt/homebrew/bin/gs"

PRESETS = [
    ("screen",   "🖥  螢幕顯示",  "最小檔案 · 72 dpi",   "#f25f5c"),
    ("ebook",    "📱  電子書",    "平衡品質 · 150 dpi",  "#f59e4a"),
    ("printer",  "🖨  一般列印",  "高品質 · 300 dpi",    "#2dd4a0"),
    ("prepress", "🎨  印刷出版",  "最高品質 · 300 dpi+", "#7c5cfc"),
]

def fmt_bytes(b):
    if b < 1024: return f"{b} B"
    if b < 1024**2: return f"{b/1024:.1f} KB"
    return f"{b/1024**2:.2f} MB"

STYLE = """
QWidget { background: #0f0f12; color: #e8e8f0; font-family: -apple-system; }
QLabel  { background: transparent; }
#title   { font-size: 22px; font-weight: 700; }
#subtitle{ font-size: 13px; color: #55556a; }
#dropzone {
    background: #1a1a20;
    border: 2px dashed #2a2a35;
    border-radius: 14px;
}
#dropzone:hover { border-color: #7c5cfc; }
#fileinfo {
    background: #1a1a20;
    border: 1.5px solid #2dd4a0;
    border-radius: 10px;
}
#sectionlabel { font-size: 11px; color: #55556a; letter-spacing: 1px; }
#preset {
    background: #1a1a20;
    border: 1.5px solid #2a2a35;
    border-radius: 10px;
    text-align: left;
    padding: 10px 14px;
}
#preset:hover { border-color: #3a3a50; }
#compressbtn {
    background: #7c5cfc;
    border: none;
    border-radius: 10px;
    color: white;
    font-size: 15px;
    font-weight: 700;
    padding: 13px;
}
#compressbtn:hover   { background: #8f70fd; }
#compressbtn:disabled{ background: #2a2a35; color: #55556a; }
#resultbox {
    background: #1a1a20;
    border: 1.5px solid #2dd4a0;
    border-radius: 10px;
}
#downloadbtn {
    background: #0e1f18;
    border: 1.5px solid #2dd4a0;
    border-radius: 8px;
    color: #2dd4a0;
    font-size: 13px;
    font-weight: 700;
    padding: 10px;
}
#downloadbtn:hover { background: #122a1f; }
"""

class Worker(QObject):
    done  = pyqtSignal(str, int, int)
    error = pyqtSignal(str)

    def __init__(self, input_path, output_path, preset):
        super().__init__()
        self.input_path  = input_path
        self.output_path = output_path
        self.preset      = preset

    def run(self):
        try:
            result = subprocess.run([
                GS_PATH, "-sDEVICE=pdfwrite",
                "-dCompatibilityLevel=1.4",
                f"-dPDFSETTINGS=/{self.preset}",
                "-dNOPAUSE", "-dQUIET", "-dBATCH",
                f"-sOutputFile={self.output_path}",
                self.input_path
            ], capture_output=True, timeout=300)

            if result.returncode != 0:
                self.error.emit(result.stderr.decode())
                return

            orig = os.path.getsize(self.input_path)
            new  = os.path.getsize(self.output_path)
            self.done.emit(self.output_path, orig, new)
        except Exception as e:
            self.error.emit(str(e))


class DropZone(QFrame):
    fileDropped = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setObjectName("dropzone")
        self.setAcceptDrops(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(130)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon = QLabel("📄")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setFont(QFont("-apple-system", 36))
        icon.setStyleSheet("background:transparent;")

        lbl = QLabel("點擊選擇 PDF 檔案")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setFont(QFont("-apple-system", 13, QFont.Weight.Bold))
        lbl.setStyleSheet("background:transparent;")

        hint = QLabel("或將 PDF 拖曳到這裡")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setStyleSheet("background:transparent; color:#55556a; font-size:11px;")

        layout.addWidget(icon)
        layout.addWidget(lbl)
        layout.addWidget(hint)

    def mousePressEvent(self, e):
        path, _ = QFileDialog.getOpenFileName(self, "選擇 PDF", "", "PDF 檔案 (*.pdf)")
        if path:
            self.fileDropped.emit(path)

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()

    def dropEvent(self, e):
        urls = e.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            if path.lower().endswith(".pdf"):
                self.fileDropped.emit(path)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF 壓縮器")
        self.setFixedWidth(480)
        self.setStyleSheet(STYLE)
        self.selected_file   = None
        self.output_path     = None
        self.selected_preset = "ebook"
        self.preset_btns     = {}
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(0)

        # Title
        title = QLabel("PDF 壓縮器")
        title.setObjectName("title")
        sub = QLabel("使用 Ghostscript · 拖曳或選擇 PDF")
        sub.setObjectName("subtitle")
        root.addWidget(title)
        root.addWidget(sub)
        root.addSpacing(16)

        # Drop zone
        self.dropzone = DropZone()
        self.dropzone.fileDropped.connect(self._set_file)
        root.addWidget(self.dropzone)

        # File info (hidden)
        self.fileinfo = QFrame()
        self.fileinfo.setObjectName("fileinfo")
        fi = QHBoxLayout(self.fileinfo)
        fi.setContentsMargins(12, 8, 12, 8)
        icon = QLabel("📄")
        icon.setFont(QFont("-apple-system", 20))
        icon.setStyleSheet("background:transparent;")
        fi.addWidget(icon)
        col = QVBoxLayout()
        self.fname_lbl = QLabel("")
        self.fname_lbl.setStyleSheet("background:transparent; color:#2dd4a0; font-weight:700; font-size:13px;")
        self.fsize_lbl = QLabel("")
        self.fsize_lbl.setStyleSheet("background:transparent; color:#55556a; font-size:11px;")
        col.addWidget(self.fname_lbl)
        col.addWidget(self.fsize_lbl)
        fi.addLayout(col)
        fi.addStretch()
        clr = QPushButton("✕")
        clr.setStyleSheet("background:transparent; color:#55556a; border:none; font-size:16px;")
        clr.setCursor(Qt.CursorShape.PointingHandCursor)
        clr.clicked.connect(self._clear_file)
        fi.addWidget(clr)
        self.fileinfo.hide()
        root.addWidget(self.fileinfo)

        root.addSpacing(18)

        # Presets
        sec = QLabel("壓縮等級")
        sec.setObjectName("sectionlabel")
        root.addWidget(sec)
        root.addSpacing(8)

        row1 = QHBoxLayout(); row1.setSpacing(8)
        row2 = QHBoxLayout(); row2.setSpacing(8)
        for i, (val, name, desc, color) in enumerate(PRESETS):
            btn = QPushButton()
            btn.setObjectName("preset")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            btn.setFixedHeight(62)
            inner = QVBoxLayout(btn)
            inner.setContentsMargins(12, 8, 12, 8)
            inner.setSpacing(2)
            n = QLabel(name)
            n.setStyleSheet("background:transparent; font-weight:700; font-size:13px;")
            d = QLabel(desc)
            d.setStyleSheet("background:transparent; color:#55556a; font-size:10px;")
            inner.addWidget(n)
            inner.addWidget(d)
            btn.clicked.connect(lambda checked, v=val: self._select_preset(v))
            self.preset_btns[val] = (btn, color, n)
            (row1 if i < 2 else row2).addWidget(btn)

        root.addLayout(row1)
        root.addSpacing(8)
        root.addLayout(row2)
        self._update_preset_ui()

        root.addSpacing(18)

        # Compress button
        self.compress_btn = QPushButton("開始壓縮")
        self.compress_btn.setObjectName("compressbtn")
        self.compress_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.compress_btn.setFixedHeight(48)
        self.compress_btn.setEnabled(False)
        self.compress_btn.clicked.connect(self._compress)
        root.addWidget(self.compress_btn)

        # Status
        self.status_lbl = QLabel("")
        self.status_lbl.setObjectName("statuslabel")
        self.status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_lbl.setStyleSheet("color:#55556a; font-size:12px;")
        root.addSpacing(10)
        root.addWidget(self.status_lbl)

        # Result box
        self.result_box = QFrame()
        self.result_box.setObjectName("resultbox")
        rb = QVBoxLayout(self.result_box)
        rb.setContentsMargins(14, 10, 14, 12)
        rb.setSpacing(4)
        self.res_title = QLabel("✅ 壓縮完成！")
        self.res_title.setStyleSheet("background:transparent; color:#2dd4a0; font-weight:700; font-size:13px;")
        self.res_stats = QLabel("")
        self.res_stats.setStyleSheet("background:transparent; color:#55556a; font-size:11px;")
        rb.addWidget(self.res_title)
        rb.addWidget(self.res_stats)
        self.reveal_btn = QPushButton("📂  在 Finder 中顯示")
        self.reveal_btn.setObjectName("downloadbtn")
        self.reveal_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.reveal_btn.setFixedHeight(40)
        self.reveal_btn.clicked.connect(self._reveal)
        rb.addSpacing(4)
        rb.addWidget(self.reveal_btn)
        self.result_box.hide()
        root.addWidget(self.result_box)
        root.addSpacing(8)

    def _set_file(self, path):
        self.selected_file = path
        self.fname_lbl.setText(os.path.basename(path))
        self.fsize_lbl.setText(fmt_bytes(os.path.getsize(path)))
        self.dropzone.hide()
        self.fileinfo.show()
        self.result_box.hide()
        self.status_lbl.setText("")
        self.compress_btn.setEnabled(True)
        self.adjustSize()

    def _clear_file(self):
        self.selected_file = None
        self.fileinfo.hide()
        self.dropzone.show()
        self.result_box.hide()
        self.status_lbl.setText("")
        self.compress_btn.setEnabled(False)
        self.adjustSize()

    def _select_preset(self, val):
        self.selected_preset = val
        self._update_preset_ui()

    def _update_preset_ui(self):
        for val, (btn, color, n_lbl) in self.preset_btns.items():
            if val == self.selected_preset:
                btn.setStyleSheet(f"#preset{{background:#1a1a20; border:2px solid {color}; border-radius:10px; text-align:left; padding:10px 14px;}}")
                n_lbl.setStyleSheet(f"background:transparent; font-weight:700; font-size:13px; color:{color};")
            else:
                btn.setStyleSheet("#preset{background:#1a1a20; border:1.5px solid #2a2a35; border-radius:10px; text-align:left; padding:10px 14px;}")
                n_lbl.setStyleSheet("background:transparent; font-weight:700; font-size:13px; color:#e8e8f0;")

    def _compress(self):
        if not self.selected_file: return
        if not os.path.exists(GS_PATH):
            self.status_lbl.setStyleSheet("color:#f25f5c; font-size:12px;")
            self.status_lbl.setText(f"❌ 找不到 Ghostscript：{GS_PATH}")
            return

        base, ext = os.path.splitext(self.selected_file)
        output = f"{base}_compressed_{self.selected_preset}{ext}"

        self.compress_btn.setEnabled(False)
        self.compress_btn.setText("壓縮中…")
        self.result_box.hide()
        self.status_lbl.setStyleSheet("color:#55556a; font-size:12px;")
        self.status_lbl.setText("⏳ Ghostscript 處理中，請稍候…")

        worker = Worker(self.selected_file, output, self.selected_preset)
        worker.done.connect(self._on_done)
        worker.error.connect(self._on_error)
        threading.Thread(target=worker.run, daemon=True).start()

    def _on_done(self, output, orig, new):
        self.output_path = output
        reduction = (1 - new / orig) * 100
        self.res_stats.setText(
            f"原始：{fmt_bytes(orig)}　→　壓縮後：{fmt_bytes(new)}　（縮小 {reduction:.1f}%）")
        self.status_lbl.setText("")
        self.result_box.show()
        self.compress_btn.setEnabled(True)
        self.compress_btn.setText("再次壓縮")
        self.adjustSize()

    def _on_error(self, msg):
        self.status_lbl.setStyleSheet("color:#f25f5c; font-size:12px;")
        self.status_lbl.setText(f"❌ 失敗：{msg}")
        self.compress_btn.setEnabled(True)
        self.compress_btn.setText("重試")

    def _reveal(self):
        if self.output_path and os.path.exists(self.output_path):
            subprocess.run(["open", "-R", self.output_path])


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    w = MainWindow()
    w.show()
    sys.exit(app.exec())
