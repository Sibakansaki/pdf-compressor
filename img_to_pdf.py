import sys
import os
import re
import threading
from PIL import Image
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QProgressBar
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt6.QtGui import QFont

STYLE = """
QWidget { background: #f5f5f7; color: #1d1d1f; font-family: -apple-system; }
QLabel  { background: transparent; }
#title  { font-size: 15px; font-weight: 600; }
#status { font-size: 12px; color: #86868b; }
#progressbar {
    background: #d1d1d6;
    border: none;
    border-radius: 4px;
    height: 6px;
}
#progressbar::chunk {
    background: #0071e3;
    border-radius: 4px;
}
"""

class Worker(QObject):
    progress = pyqtSignal(int, str)
    done     = pyqtSignal(str)
    error    = pyqtSignal(str)

    def __init__(self, files):
        super().__init__()
        self.files = files

    def run(self):
        try:
            total = len(self.files)
            images = []

            import tempfile, io
            temp_jpegs = []
            for i, f in enumerate(self.files):
                self.progress.emit(int((i / total) * 90), f"處理第 {i+1} / {total} 張圖片")
                img = Image.open(f).convert('RGB')
                img = img.resize((int(img.width * 0.7), int(img.height * 0.7)), Image.LANCZOS)
                buf = io.BytesIO()
                img.save(buf, format='JPEG', quality=70, optimize=True)
                buf.seek(0)
                temp_jpegs.append(Image.open(buf).copy())

            self.progress.emit(95, "產生 PDF 中...")
            output = os.path.join(os.path.dirname(self.files[0]), 'output_compressed.pdf')
            temp_jpegs[0].save(output, save_all=True, append_images=temp_jpegs[1:])

            self.progress.emit(100, "完成！")
            self.done.emit(output)
        except Exception as e:
            import traceback
            self.error.emit(traceback.format_exc())


class ProgressWindow(QWidget):
    def __init__(self, files):
        super().__init__()
        self.files = files
        self.setWindowTitle("製作 PDF")
        self.setFixedSize(360, 100)
        self.setStyleSheet(STYLE)
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(6)

        self.title_lbl = QLabel("製作 PDF")
        self.title_lbl.setObjectName("title")
        layout.addWidget(self.title_lbl)

        self.status_lbl = QLabel(f"準備處理 {len(files)} 張圖片...")
        self.status_lbl.setObjectName("status")
        layout.addWidget(self.status_lbl)

        self.bar = QProgressBar()
        self.bar.setObjectName("progressbar")
        self.bar.setFixedHeight(8)
        self.bar.setRange(0, 100)
        self.bar.setValue(0)
        self.bar.setTextVisible(False)
        layout.addWidget(self.bar)

        self.show()
        QTimer.singleShot(300, self._start)

    def _start(self):
        self.worker = Worker(self.files)
        self.worker.progress.connect(self._on_progress)
        self.worker.done.connect(self._on_done)
        self.worker.error.connect(self._on_error)
        threading.Thread(target=self.worker.run, daemon=True).start()

    def _on_progress(self, value, msg):
        self.bar.setValue(value)
        self.status_lbl.setText(msg)

    def _on_done(self, output):
        self.bar.setValue(100)
        self.status_lbl.setText("✅ 完成！PDF 已儲存在原始資料夾")
        QTimer.singleShot(2000, self.close)

    def _on_error(self, msg):
        self.status_lbl.setStyleSheet("color:#cc0000; font-size:12px;")
        self.status_lbl.setText(f"失敗：{msg}")
        # Write to log file
        import traceback
        log_path = os.path.expanduser("~/Desktop/img_to_pdf_error.txt")
        with open(log_path, "w") as f:
            f.write(msg)
        # Don't auto close so user can read
        self.setFixedSize(360, 140)


def main():
    raw = sys.argv[1:]
    files = sorted(
        [f for f in raw if f.lower().endswith(('.jpg', '.jpeg', '.png'))],
        key=lambda x: [int(c) if c.isdigit() else c.lower()
                       for c in re.split(r'(\d+)', os.path.basename(x))]
    )
    if not files:
        sys.exit(0)

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = ProgressWindow(files)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
