# -*- coding: utf-8 -*-
import os

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon, QPixmap
from PyQt5.QtWidgets import (
    QHBoxLayout, QLabel, QMainWindow, QPushButton, QTabWidget, QVBoxLayout,
    QWidget,
)

from .. import APP_NAME, RELEASE_LABEL
from .theme import QSS, asset_path, show_about
from .pack_tab import PackTab
from .recover_tab import RecoverTab


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("{} — {} — Unknown".format(APP_NAME, RELEASE_LABEL))
        self.resize(860, 700)
        self.setStyleSheet(QSS)
        icon = asset_path("pickone_icon.png")
        if os.path.exists(icon):
            self.setWindowIcon(QIcon(icon))

        central = QWidget()
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._make_header())

        tabs = QTabWidget()
        tabs.addTab(PackTab(), "📦 패키징")
        tabs.addTab(RecoverTab(), "📥 회수")
        root.addWidget(tabs, stretch=1)
        self.setCentralWidget(central)

    def _make_header(self) -> QWidget:
        w = QWidget()
        w.setFixedHeight(44)
        w.setStyleSheet("background:#111111; border-bottom:1px solid #222222;")
        layout = QHBoxLayout(w)
        layout.setContentsMargins(12, 4, 12, 4)

        logo = asset_path("pickone_icon.png")
        if os.path.exists(logo):
            pm = QPixmap(logo).scaled(36, 36, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            lbl = QLabel(); lbl.setPixmap(pm); lbl.setFixedSize(40, 40)
            layout.addWidget(lbl)
            layout.addSpacing(6)

        pick_lbl = QLabel("Pick")
        pick_lbl.setFont(QFont("Rajdhani", 22, QFont.Bold))
        pick_lbl.setStyleSheet("color:#FFFFFF;")
        one_lbl = QLabel("One")
        one_lbl.setFont(QFont("Rajdhani", 22, QFont.Bold))
        one_lbl.setStyleSheet("color:#D35400;")
        tagline = QLabel("One Gallery, One Pick | Select & Retrieve")
        tagline.setStyleSheet("color:#555555; font-size:11px;")

        layout.addWidget(pick_lbl)
        layout.addWidget(one_lbl)
        layout.addSpacing(16)
        layout.addWidget(tagline)
        layout.addStretch()

        credit_lbl = QLabel("PROJECT 03  ·  Unknown")
        credit_lbl.setStyleSheet("color:#3A3A3A; font-size:11px; letter-spacing:1px;")
        layout.addWidget(credit_lbl)
        layout.addSpacing(8)

        about_btn = QPushButton("?")
        about_btn.setFixedSize(22, 22)
        about_btn.setToolTip("About PickOne")
        about_btn.setStyleSheet("""
            QPushButton {
                background:transparent; color:#444444;
                border:1px solid #333333; border-radius:11px;
                font-size:12px; font-weight:bold; padding:0;
            }
            QPushButton:hover { color:#D35400; border-color:#D35400; }
        """)
        about_btn.clicked.connect(lambda: show_about(self))
        layout.addWidget(about_btn)
        return w
