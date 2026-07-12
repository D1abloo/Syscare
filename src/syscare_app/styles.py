APP_QSS = """
* {
  font-family: Inter, SF Pro Display, Segoe UI, Ubuntu, Arial;
  font-size: 13px;
  letter-spacing: 0px;
}
QMainWindow, QWidget#Root {
  background: #f6f8fb;
  color: #172033;
}
QWidget {
  color: #172033;
}
QLabel {
  color: #172033;
}
QFrame#Header {
  background: #ffffff;
  border-bottom: 1px solid #dbe3ee;
}
QFrame#Hero {
  background: #eefaf6;
  border: 1px solid #bfe8d8;
  border-radius: 8px;
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
  background: #19c391;
  color: #05261d;
  border-radius: 48px;
  font-size: 30px;
  font-weight: 900;
}
QLabel#HeaderMetric {
  background: #eef4ff;
  color: #244169;
  border: 1px solid #d7e5ff;
  border-radius: 8px;
  padding: 8px 10px;
  font-weight: 700;
}
QLabel#Muted, QLabel[muted="true"] {
  color: #64748b;
}
QPushButton {
  background: #ffffff;
  color: #223047;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  padding: 9px 12px;
  font-weight: 700;
}
QPushButton:hover {
  background: #f1f5f9;
  border-color: #94a3b8;
}
QPushButton:pressed {
  background: #e2e8f0;
}
QPushButton:disabled {
  color: #94a3b8;
  background: #f8fafc;
  border-color: #e2e8f0;
}
QPushButton[primary="true"] {
  background: #19c391;
  color: #05261d;
  border-color: #19c391;
}
QPushButton[primary="true"]:hover {
  background: #2ed0a0;
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
  background: #f1f5f9;
}
QPushButton[nav="true"]:checked {
  background: #e7f8f2;
  color: #08795f;
}
QFrame[card="true"] {
  background: #ffffff;
  border: 1px solid #dbe3ee;
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
}
QTableWidget, QListWidget, QTextEdit {
  background: #ffffff;
  alternate-background-color: #f8fafc;
  color: #172033;
  border: 1px solid #dbe3ee;
  border-radius: 8px;
  gridline-color: #e6edf5;
  selection-background-color: #dff7ef;
  selection-color: #0f2d25;
}
QTableWidget::item {
  padding: 6px;
}
QHeaderView::section {
  background: #f1f5f9;
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
  background: #19c391;
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
"""
