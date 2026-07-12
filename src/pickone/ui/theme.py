# -*- coding: utf-8 -*-
"""다크테마 스타일시트 + About 다이얼로그 (RawBaker 공통 브랜드 패턴)."""
import os
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtWidgets import (
    QDialog, QDialogButtonBox, QHBoxLayout, QLabel, QVBoxLayout, QWidget,
)

ACCENT = "#D35400"
QSS = """
* { font-family: 'Pretendard', 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif; font-size: 13px; }
QMainWindow, QWidget { background: #111111; color: #e8e8e8; }
QTabWidget::pane { border: 1px solid #2a2a2a; }
QTabBar::tab { background: #1b1b1b; color: #9a9a9a; padding: 9px 26px; font-weight: bold; }
QTabBar::tab:selected { color: #D35400; border-bottom: 2px solid #D35400; }
QPushButton { background: #1b1b1b; border: 1px solid #2a2a2a; border-radius: 6px; padding: 8px 16px; }
QPushButton:hover { border-color: #D35400; }
QPushButton#primary { background: #D35400; color: white; font-weight: bold; border: none; }
QPushButton#primary:disabled { background: #553015; color: #aaa; }
QLineEdit, QSpinBox, QComboBox, QTextEdit, QPlainTextEdit {
  background: #1b1b1b; border: 1px solid #2a2a2a; border-radius: 5px; padding: 6px; color: #e8e8e8; }
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus { border-color: #D35400; }
QProgressBar { background: #1b1b1b; border: 1px solid #2a2a2a; border-radius: 5px; text-align: center; color: #e8e8e8; }
QProgressBar::chunk { background: #D35400; border-radius: 4px; }
QListWidget, QTableWidget { background: #161616; border: 1px solid #2a2a2a; }
QLabel#dropzone { border: 2px dashed #3a3a3a; border-radius: 10px; color: #9a9a9a;
  padding: 30px; font-size: 15px; }
QLabel#dropzone[drag="true"] { border-color: #D35400; color: #D35400; }
QLabel#h2 { font-size: 15px; font-weight: bold; color: #D35400; padding-top: 6px; }
QGroupBox { border: 1px solid #2a2a2a; border-radius: 8px; margin-top: 10px; padding-top: 16px; }
QGroupBox::title { color: #D35400; subcontrol-origin: margin; left: 10px; }
"""


def asset_path(name):
    base = getattr(sys, "_MEIPASS",
                   os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    return os.path.join(base, "assets", name)


def show_about(parent):
    from .. import RELEASE_LABEL
    dlg = QDialog(parent)
    dlg.setWindowTitle("About PickOne")
    dlg.setFixedSize(360, 365)
    dlg.setStyleSheet("background:#111111; color:#CCCCCC;")

    layout = QVBoxLayout(dlg)
    layout.setSpacing(0)
    layout.setContentsMargins(0, 0, 0, 0)

    banner = QWidget()
    banner.setFixedHeight(90)
    banner.setStyleSheet(
        "background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
        "stop:0 #C0390B, stop:1 #D35400);")
    b_lay = QHBoxLayout(banner)
    b_lay.setContentsMargins(20, 0, 20, 0)

    icon = asset_path("pickone_icon.png")
    if os.path.exists(icon):
        pm = QPixmap(icon).scaled(60, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        ll = QLabel(); ll.setPixmap(pm)
        b_lay.addWidget(ll); b_lay.addSpacing(12)

    nc = QVBoxLayout()
    an = QLabel("PickOne"); an.setFont(QFont("Rajdhani", 22, QFont.Bold))
    an.setStyleSheet("color:#FFFFFF;")
    sn = QLabel("One Gallery, One Pick")
    sn.setStyleSheet("color:rgba(255,255,255,0.6); font-size:11px;")
    nc.addWidget(an); nc.addWidget(sn)
    b_lay.addLayout(nc); b_lay.addStretch()
    layout.addWidget(banner)

    body = QWidget(); body.setStyleSheet("background:#111111;")
    b2 = QVBoxLayout(body)
    b2.setContentsMargins(28, 24, 28, 16); b2.setSpacing(10)

    def info_row(lbl, val, vc="#CCCCCC"):
        h = QHBoxLayout()
        l = QLabel(lbl); l.setStyleSheet("color:#555555; font-size:11px;"); l.setFixedWidth(70)
        v = QLabel(val); v.setStyleSheet("color:{}; font-size:12px; font-weight:bold;".format(vc))
        h.addWidget(l); h.addWidget(v); h.addStretch()
        return h

    def yt_row():
        h = QHBoxLayout()
        lbl = QLabel("유튜브")
        lbl.setStyleSheet("color:#555555; font-size:11px;")
        lbl.setFixedWidth(70)
        link = QLabel(
            '<a href="https://www.youtube.com/@unknown8563" '
            'style="color:#FF4444; text-decoration:none; font-size:12px; font-weight:bold;">'
            '▶  @unknown8563</a>')
        link.setOpenExternalLinks(True)
        link.setToolTip("https://www.youtube.com/@unknown8563")
        h.addWidget(lbl); h.addWidget(link); h.addStretch()
        return h

    b2.addLayout(info_row("프로젝트", "PROJECT 03", ACCENT))
    b2.addLayout(info_row("제작", "Unknown"))
    b2.addLayout(info_row("연도", "2026"))
    b2.addLayout(info_row("버전", RELEASE_LABEL))
    b2.addLayout(yt_row())
    b2.addLayout(info_row("엔진", "PyQt5 · Pillow · pillow-heif"))
    b2.addLayout(info_row("플랫폼", "Windows 10/11 64-bit"))
    b2.addSpacing(8)
    desc = QLabel("사진을 단일 HTML 갤러리로 패키징해 보내고\n셀렉 결과로 원본을 자동 회수하는 포터블 프로그램.")
    desc.setStyleSheet("color:#555555; font-size:11px;"); desc.setWordWrap(True)
    b2.addWidget(desc); b2.addStretch()
    layout.addWidget(body, stretch=1)

    btn_box = QDialogButtonBox(QDialogButtonBox.Ok)
    btn_box.setStyleSheet(
        "QPushButton { background:#D35400; color:#fff; border:none;"
        " border-radius:4px; padding:6px 24px; font-size:12px; }"
        "QPushButton:hover { background:#E67E22; }")
    btn_box.accepted.connect(dlg.accept)
    cb = QWidget(); cb.setStyleSheet("background:#0D0D0D; border-top:1px solid #1E1E1E;")
    cl = QHBoxLayout(cb); cl.setContentsMargins(16, 8, 16, 8)
    cl.addStretch(); cl.addWidget(btn_box)
    layout.addWidget(cb)

    dlg.exec_()
