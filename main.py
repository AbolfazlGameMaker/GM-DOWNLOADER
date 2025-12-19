import sys
import os
import time
import requests
import threading
from concurrent.futures import ThreadPoolExecutor
from PySide6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QWidget, QPushButton, QLineEdit, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QProgressBar, QFileDialog, QLabel)
from PySide6.QtCore import Qt, Signal, QObject, QTimer
from styles import QSS_STYLE

class DownloadSignals(QObject):
    progress = Signal(int, float, str, str, str) # row, percent, speed, size, eta
    status = Signal(int, str)
    remove_row = Signal(int)
    finished = Signal(int, str)

class DownloadWorker:
    def __init__(self, url, path, row, signals, threads=16):
        self.url = url
        self.path = path
        self.row = row
        self.signals = signals
        self.threads = threads
        self.total_size = 0
        self.downloaded = 0
        self.is_paused = False
        self.is_cancelled = False
        self.lock = threading.Lock()
        self.executor = None
        self.start_time = 0

    def download_segment(self, start, end):
        try:
            # مدیریت Resume در سطح سگمنت
            current_pos = start
            headers = {"Range": f"bytes={start}-{end}"}
            
            with requests.get(self.url, headers=headers, stream=True, timeout=20) as r:
                r.raise_for_status()
                with open(self.path, "r+b") as f:
                    f.seek(start)
                    for chunk in r.iter_content(chunk_size=1024*128):
                        if self.is_cancelled:
                            return
                        while self.is_paused:
                            if self.is_cancelled: return
                            time.sleep(0.5)
                        
                        if chunk:
                            f.write(chunk)
                            with self.lock:
                                self.downloaded += len(chunk)
        except Exception as e:
            print(f"Segment Error: {e}")

    def run(self):
        try:
            # گرفتن اطلاعات فایل
            res = requests.head(self.url, allow_redirects=True, timeout=15)
            self.total_size = int(res.headers.get('content-length', 0))
            
            # رزرو فضا روی هارد (Pre-allocation)
            if not os.path.exists(self.path) or os.path.getsize(self.path) != self.total_size:
                with open(self.path, "wb") as f:
                    f.truncate(self.total_size)

            self.start_time = time.time()
            seg_size = self.total_size // self.threads
            
            self.executor = ThreadPoolExecutor(max_workers=self.threads)
            for i in range(self.threads):
                start = i * seg_size
                end = self.total_size - 1 if i == self.threads - 1 else start + seg_size - 1
                self.executor.submit(self.download_segment, start, end)

            while self.downloaded < self.total_size:
                if self.is_cancelled:
                    break
                
                if not self.is_paused:
                    time.sleep(0.4)
                    elapsed = time.time() - self.start_time
                    speed = self.downloaded / (elapsed if elapsed > 0 else 1)
                    percent = (self.downloaded / self.total_size) * 100
                    
                    size_txt = f"{self.downloaded/1024/1024:.1f} / {self.total_size/1024/1024:.1f} MB"
                    speed_txt = f"{speed/1024/1024:.2f} MB/s"
                    eta = (self.total_size - self.downloaded) / (speed if speed > 0 else 1)
                    eta_txt = f"{int(eta)}s remaining"
                    
                    self.signals.progress.emit(self.row, percent, speed_txt, size_txt, eta_txt)
                else:
                    time.sleep(0.5)

            if not self.is_cancelled:
                self.signals.status.emit(self.row, "Completed")
                self.signals.finished.emit(self.row, self.path)
            
        except Exception as e:
            self.signals.status.emit(self.row, "Error")
        finally:
            if self.executor:
                self.executor.shutdown(wait=False)

class GM_Ultimate_Pro(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GM DOWNLOADER ULTIMATE PRO v6.0")
        self.resize(1300, 850)
        self.setStyleSheet(QSS_STYLE)
        
        self.workers = {}
        self.last_clipboard_link = ""
        
        self.signals = DownloadSignals()
        self.signals.progress.connect(self.update_table_row)
        self.signals.status.connect(self.update_row_status)
        self.signals.remove_row.connect(self.handle_row_removal)
        self.signals.finished.connect(self.handle_finished)
        
        # Clipboard Timer (Auto-Catch)
        self.cb_timer = QTimer()
        self.cb_timer.timeout.connect(self.monitor_clipboard)
        self.cb_timer.start(1000)
        
        self.init_ui()

    def init_ui(self):
        main_widget = QWidget()
        main_widget.setObjectName("MainContent")
        self.setCentralWidget(main_widget)
        
        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        # Header
        title = QLabel("GM DOWNLOADER ULTIMATE")
        title.setObjectName("AppTitle")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Input Area
        input_layout = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Paste URL here or copy to clipboard for auto-detect...")
        
        add_btn = QPushButton("ADD TASK")
        add_btn.setObjectName("AddBtn")
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.clicked.connect(self.add_new_download)
        
        input_layout.addWidget(self.url_input)
        input_layout.addWidget(add_btn)
        layout.addLayout(input_layout)

        # Download Table
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["File Name", "Progress", "Size / Total", "Speed", "ETA", "Actions"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.table)

    def monitor_clipboard(self):
        cb_text = QApplication.clipboard().text().strip()
        if cb_text.startswith("http") and cb_text != self.last_clipboard_link:
            self.url_input.setText(cb_text)
            self.last_clipboard_link = cb_text

    def add_new_download(self):
        url = self.url_input.text().strip()
        if not url: return
        
        default_name = url.split('/')[-1].split('?')[0] or "downloaded_file"
        save_path, _ = QFileDialog.getSaveFileName(self, "Save As", default_name)
        
        if save_path:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # ستون اول: نام فایل
            self.table.setItem(row, 0, QTableWidgetItem(os.path.basename(save_path)))
            
            # ستون دوم: پروگرس بار
            pbar = QProgressBar()
            self.table.setCellWidget(row, 1, pbar)
            
            # ستون‌های وضعیت
            for i in range(2, 5):
                item = QTableWidgetItem("--")
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, i, item)

            # ستون ششم: دکمه‌های کنترلی
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(0, 0, 0, 0)
            
            stop_btn = QPushButton("Pause")
            stop_btn.setProperty("class", "ControlBtn StopBtn")
            stop_btn.clicked.connect(lambda: self.toggle_download(row, stop_btn))
            
            cancel_btn = QPushButton("Cancel")
            cancel_btn.setProperty("class", "ControlBtn CancelBtn")
            cancel_btn.clicked.connect(lambda: self.cancel_download(row))
            
            actions_layout.addWidget(stop_btn)
            actions_layout.addWidget(cancel_btn)
            self.table.setCellWidget(row, 5, actions_widget)

            # ایجاد ورکر و شروع دانلود
            worker = DownloadWorker(url, save_path, row, self.signals)
            self.workers[row] = worker
            threading.Thread(target=worker.run, daemon=True).start()
            self.url_input.clear()

    def toggle_download(self, row, btn):
        if row in self.workers:
            w = self.workers[row]
            w.is_paused = not w.is_paused
            if w.is_paused:
                btn.setText("Resume")
                btn.setProperty("class", "ControlBtn ResumeBtn")
                self.table.item(row, 2).setText("Paused")
            else:
                btn.setText("Pause")
                btn.setProperty("class", "ControlBtn StopBtn")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def cancel_download(self, row):
        if row in self.workers:
            self.workers[row].is_cancelled = True
            # حذف با تاخیر برای جلوگیری از کرش ایندکس
            QTimer.singleShot(100, lambda: self.signals.remove_row.emit(row))

    def handle_row_removal(self, row_index):
        if row_index < self.table.rowCount():
            self.table.removeRow(row_index)
            # بازنشانی ایندکس‌های ورکرها بعد از حذف یک ردیف
            new_workers = {}
            for r, w in self.workers.items():
                if r > row_index:
                    w.row -= 1
                    new_workers[r-1] = w
                elif r < row_index:
                    new_workers[r] = w
            self.workers = new_workers

    def update_table_row(self, row, percent, speed, size_info, eta):
        try:
            self.table.cellWidget(row, 1).setValue(int(percent))
            self.table.item(row, 2).setText(size_info)
            self.table.item(row, 3).setText(speed)
            self.table.item(row, 4).setText(eta)
        except: pass

    def update_row_status(self, row, status):
        try:
            self.table.item(row, 2).setText(status)
            if status == "Completed":
                self.table.item(row, 2).setForeground(Qt.green)
        except: pass

    def handle_finished(self, row, file_path):
        try:
            open_btn = QPushButton("Open Folder")
            open_btn.setProperty("class", "OpenBtn")
            open_btn.clicked.connect(lambda: os.startfile(os.path.dirname(file_path)))
            self.table.setCellWidget(row, 5, open_btn)
        except: pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GM_Ultimate_Pro()
    window.show()
    sys.exit(app.exec())
    