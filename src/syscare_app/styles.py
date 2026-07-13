APP_QSS = """
* {
  font-family: Inter, SF Pro Display, Segoe UI, Ubuntu, Arial;
  font-size: 13px;
  letter-spacing: 0px;
}
QMainWindow, QWidget#Root {
  background: #f4f7fb;
  color: #172033;
}
QWidget {
  color: #172033;
}
QDialog, QMessageBox, QFileDialog {
  background: #ffffff;
  color: #172033;
}
QLabel {
  color: #172033;
}
QMessageBox QLabel {
  color: #172033;
  background: transparent;
}
QMessageBox QPushButton, QDialog QPushButton, QFileDialog QPushButton {
  min-width: 88px;
}
QFrame#Header {
  background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ffffff, stop:0.7 #ffffff, stop:1 #f2f7ff);
  border-bottom: 1px solid #dbe3ee;
}
QFrame#Hero {
  background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #e9fff7, stop:0.52 #f4fbff, stop:1 #fff8ed);
  border: 1px solid #aee9d4;
  border-radius: 8px;
}
QLabel#LogoImage {
  background: #e9fff6;
  border: 1px solid #b8ead8;
  border-radius: 12px;
  padding: 4px;
}
QLabel#LogoMark {
  background: #19c391;
  color: #05261d;
  border-radius: 12px;
  font-weight: 900;
  font-size: 18px;
}
QLabel#AppTitle {
  font-size: 18px;
  font-weight: 850;
  color: #172033;
}
QLabel#PageTitle {
  font-size: 28px;
  font-weight: 850;
  color: #111827;
}
QLabel#HeroTitle {
  font-size: 22px;
  font-weight: 850;
  color: #12372d;
}
QLabel#HealthScore {
  background: qradialgradient(cx:0.35, cy:0.28, radius:0.95, fx:0.28, fy:0.22, stop:0 #48e6b8, stop:1 #19c391);
  color: #05261d;
  border-radius: 48px;
  font-size: 30px;
  font-weight: 900;
}
QLabel#HeaderMetric {
  background: #edf6ff;
  color: #173b63;
  border: 1px solid #cce1ff;
  border-radius: 8px;
  padding: 10px 12px;
  font-weight: 700;
}
QLabel#TempSummary {
  background: #f8fbff;
  color: #173b63;
  border: 1px solid #dbeafe;
  border-radius: 8px;
  padding: 10px 12px;
  font-size: 15px;
  font-weight: 850;
}
QLabel#Muted, QLabel[muted="true"] {
  color: #64748b;
}
QPushButton {
  background: #ffffff;
  color: #223047;
  border: 1px solid #c5d0df;
  border-radius: 8px;
  padding: 10px 13px;
  font-weight: 700;
}
QPushButton:hover {
  background: #f6fffb;
  border-color: #18b989;
  color: #0f3b31;
}
QPushButton:pressed {
  background: #dff7ef;
}
QPushButton:disabled {
  color: #94a3b8;
  background: #f8fafc;
  border-color: #e2e8f0;
}
QPushButton[primary="true"] {
  background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #14bd8a, stop:1 #22d3a2);
  color: #05261d;
  border-color: #10b981;
}
QPushButton[primary="true"]:hover {
  background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #22d3a2, stop:1 #4adebd);
}
QPushButton[danger="true"] {
  background: #fff1f2;
  color: #b4233c;
  border-color: #fecdd3;
}
QPushButton[danger="true"]:hover {
  background: #ffe4e6;
}
QPushButton[nav="true"] {
  border: 0;
  border-radius: 8px;
  background: transparent;
  padding: 9px 10px;
  font-weight: 800;
  color: #475569;
}
QPushButton[nav="true"]:hover {
  background: #eef6ff;
  color: #173b63;
}
QPushButton[nav="true"]:checked {
  background: #dff7ef;
  color: #08795f;
}
QFrame[card="true"] {
  background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ffffff, stop:1 #fbfdff);
  border: 1px solid #d4dfec;
  border-radius: 8px;
}
QLineEdit, QComboBox {
  background: #ffffff;
  color: #172033;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  padding: 9px 10px;
}
QLineEdit:focus, QComboBox:focus, QTextEdit:focus, QTableWidget:focus, QListWidget:focus {
  border-color: #19c391;
  background: #fbfffd;
}
QTableWidget, QListWidget, QTextEdit {
  background: #ffffff;
  alternate-background-color: #f8fafc;
  color: #172033;
  border: 1px solid #d8e2ee;
  border-radius: 8px;
  gridline-color: #e6edf5;
  selection-background-color: #d7f5ec;
  selection-color: #0f2d25;
}
QTableWidget::item {
  padding: 6px;
}
QTableWidget::item:hover {
  background: #eefaf6;
}
QHeaderView::section {
  background: #eef4fb;
  color: #475569;
  border: 0;
  border-bottom: 1px solid #dbe3ee;
  padding: 8px;
  font-weight: 800;
}
QProgressBar {
  background: #eef2f7;
  color: #172033;
  border: 1px solid #d7dee9;
  border-radius: 8px;
  text-align: center;
  height: 14px;
}
QProgressBar::chunk {
  background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #12b981, stop:0.55 #22d3a2, stop:1 #60a5fa);
  border-radius: 7px;
}
QCheckBox {
  color: #172033;
  spacing: 8px;
}
QCheckBox::indicator {
  width: 16px;
  height: 16px;
}
QCheckBox::indicator:unchecked {
  background: #ffffff;
  border: 1px solid #94a3b8;
  border-radius: 4px;
}
QCheckBox::indicator:checked {
  background: #19c391;
  border: 1px solid #19c391;
  border-radius: 4px;
}
QScrollBar:vertical {
  background: transparent;
  width: 10px;
}
QScrollBar::handle:vertical {
  background: #cbd5e1;
  border-radius: 5px;
}
QMenu {
  background: #ffffff;
  color: #172033;
  border: 1px solid #dbe3ee;
}
QMenu::item {
  padding: 8px 22px;
}
QMenu::item:selected {
  background: #e7f8f2;
}
QToolTip {
  background: #ffffff;
  color: #172033;
  border: 1px solid #b8c7d9;
  border-radius: 6px;
  padding: 7px 9px;
}
"""
