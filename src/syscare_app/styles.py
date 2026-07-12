APP_QSS = """
* {
  font-family: Inter, SF Pro Display, Segoe UI, Ubuntu, Arial;
  font-size: 13px;
  letter-spacing: 0px;
}
QMainWindow, QWidget#Root {
  background: #111318;
  color: #eef2f6;
}
QWidget {
  color: #eef2f6;
}
QLabel {
  color: #eef2f6;
}
QFrame#Sidebar {
  background: #151922;
  border-right: 1px solid #262b36;
}
QFrame#Hero {
  background: #17211f;
  border: 1px solid #28453d;
  border-radius: 8px;
}
QLabel#LogoMark {
  background: #26d6a4;
  color: #07110e;
  border-radius: 14px;
  font-weight: 800;
  font-size: 18px;
}
QLabel#AppTitle {
  font-size: 18px;
  font-weight: 800;
}
QLabel#PageTitle {
  font-size: 26px;
  font-weight: 800;
}
QLabel#HeroTitle {
  font-size: 22px;
  font-weight: 800;
}
QLabel#HealthScore {
  background: #26d6a4;
  color: #06231c;
  border-radius: 48px;
  font-size: 30px;
  font-weight: 900;
}
QLabel#Muted, QLabel[muted="true"] {
  color: #94a3b8;
}
QPushButton {
  background: #242936;
  color: #eef2f6;
  border: 1px solid #323947;
  border-radius: 8px;
  padding: 9px 12px;
  font-weight: 650;
}
QPushButton:hover {
  background: #2d3444;
  border-color: #415166;
}
QPushButton:pressed {
  background: #1e2430;
}
QPushButton:disabled {
  color: #667085;
  background: #1a1d25;
  border-color: #252a34;
}
QPushButton[primary="true"] {
  background: #26d6a4;
  color: #06231c;
  border-color: #26d6a4;
}
QPushButton[primary="true"]:hover {
  background: #45e1b5;
}
QPushButton[danger="true"] {
  background: #3a1f27;
  color: #ffc7d1;
  border-color: #7f2f42;
}
QPushButton[nav="true"] {
  text-align: left;
  border: 0;
  border-radius: 8px;
  background: transparent;
  padding: 11px 12px;
  font-weight: 750;
}
QPushButton[nav="true"]:checked {
  background: #263126;
  color: #b9f8df;
}
QFrame[card="true"] {
  background: #181d26;
  border: 1px solid #2a303c;
  border-radius: 8px;
}
QLineEdit, QComboBox {
  background: #10131a;
  color: #eef2f6;
  border: 1px solid #303746;
  border-radius: 8px;
  padding: 9px 10px;
}
QLineEdit:focus, QComboBox:focus, QTextEdit:focus, QTableWidget:focus, QListWidget:focus {
  border-color: #26d6a4;
}
QTableWidget, QListWidget, QTextEdit {
  background: #11161f;
  alternate-background-color: #171c25;
  color: #eef2f6;
  border: 1px solid #2a303c;
  border-radius: 8px;
  gridline-color: #252b36;
  selection-background-color: #264236;
  selection-color: #eafff7;
}
QTableWidget::item {
  padding: 6px;
}
QHeaderView::section {
  background: #1d222d;
  color: #aeb9c8;
  border: 0;
  padding: 8px;
  font-weight: 700;
}
QProgressBar {
  background: #10131a;
  color: #eef2f6;
  border: 1px solid #303746;
  border-radius: 8px;
  text-align: center;
  height: 14px;
}
QProgressBar::chunk {
  background: #26d6a4;
  border-radius: 7px;
}
QCheckBox {
  color: #eef2f6;
  spacing: 8px;
}
QCheckBox::indicator {
  width: 16px;
  height: 16px;
}
QCheckBox::indicator:unchecked {
  background: #10131a;
  border: 1px solid #465266;
  border-radius: 4px;
}
QCheckBox::indicator:checked {
  background: #26d6a4;
  border: 1px solid #26d6a4;
  border-radius: 4px;
}
QScrollBar:vertical {
  background: transparent;
  width: 10px;
}
QScrollBar::handle:vertical {
  background: #344052;
  border-radius: 5px;
}
"""
