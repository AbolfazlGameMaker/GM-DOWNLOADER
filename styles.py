# styles.py

QSS_STYLE = """
QMainWindow {
    background-color: #080a0f;
}

#MainContent {
    background-color: #0d1117;
    border-radius: 25px;
    border: 1px solid #30363d;
}

QLabel#AppTitle {
    font-size: 36px;
    font-weight: 900;
    color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00f2fe, stop:1 #4facfe);
    padding: 20px;
    letter-spacing: 5px;
}

/* Table Style */
QTableWidget {
    background-color: #161b22;
    border: 1px solid #30363d;
    border-radius: 15px;
    color: #e6edf3;
    gridline-color: #21262d;
    font-family: 'Segoe UI';
    font-size: 13px;
    outline: none;
}

QHeaderView::section {
    background-color: #0d1117;
    color: #58a6ff;
    padding: 15px;
    border: none;
    font-weight: bold;
    text-transform: uppercase;
}

/* Inputs */
QLineEdit {
    background-color: #0d1117;
    border: 2px solid #30363d;
    border-radius: 15px;
    padding: 15px;
    color: #ffffff;
    font-size: 14px;
}

QLineEdit:focus {
    border: 2px solid #00f2fe;
}

/* Main Action Button */
QPushButton#AddBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00c6ff, stop:1 #0072ff);
    color: white;
    border-radius: 15px;
    font-weight: bold;
    padding: 15px 30px;
    font-size: 15px;
}

QPushButton#AddBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00f2fe, stop:1 #4facfe);
}

/* Progress Bar with Animation Feel */
QProgressBar {
    background-color: #21262d;
    border-radius: 10px;
    text-align: center;
    color: white;
    height: 20px;
    font-weight: bold;
    border: 1px solid #30363d;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00f2fe, stop:0.5 #4facfe, stop:1 #00f2fe);
    border-radius: 10px;
}

/* Control Buttons */
QPushButton.ControlBtn {
    background-color: #21262d;
    border: 1px solid #30363d;
    color: #c9d1d9;
    padding: 8px 15px;
    border-radius: 8px;
    font-weight: bold;
}

QPushButton.StopBtn:hover { background-color: #d29922; color: #000; border-color: #d29922; }
QPushButton.ResumeBtn:hover { background-color: #238636; color: #fff; border-color: #238636; }
QPushButton.CancelBtn:hover { background-color: #f85149; color: #fff; border-color: #f85149; }
QPushButton.OpenBtn { background-color: #1f6feb; color: white; border-radius: 8px; font-weight: bold; }
"""
