# -*- coding: utf-8 -*-
"""패키징 모드 탭 — 드롭 → 설정 → 프리뷰 생성·HTML 빌드(QThread)."""
import os
import webbrowser
from pathlib import Path

from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QSpinBox,
    QPushButton, QProgressBar, QFileDialog, QListWidget, QMessageBox,
    QGroupBox, QFormLayout,
)

from ..scanner import scan
from ..preview import generate_previews, fit_to_target, Q_AUTO
from ..builder import build_gallery


class BuildWorker(QThread):
    progress = pyqtSignal(int, int)
    done = pyqtSignal(list, list)   # files, errors
    failed = pyqtSignal(str)

    def __init__(self, items, cfg):
        super().__init__()
        self.items = items
        self.cfg = cfg

    def run(self):
        try:
            target = self.cfg["target_bytes"]
            if target > 0:
                fit = fit_to_target(self.items, target)
                pv = generate_previews(
                    self.items, thumb_px=fit["thumb_px"], large_px=fit["large_px"],
                    quality=fit["quality"],
                    progress_cb=lambda d, t: self.progress.emit(d, t))
            else:
                pv = generate_previews(
                    self.items, thumb_px=600, large_px=1400, quality=Q_AUTO,
                    progress_cb=lambda d, t: self.progress.emit(d, t))
            files = build_gallery(
                self.items, pv,
                title=self.cfg["title"], goal=self.cfg["goal"],
                notice=self.cfg["notice"], out_dir=self.cfg["out_dir"])
            errors = ["{} — {}".format(i.display, i.error) for i in self.items if i.error]
            self.done.emit(files, errors)
        except Exception as e:
            self.failed.emit(str(e))


class PackTab(QWidget):
    def __init__(self):
        super().__init__()
        self.items = []
        self.worker = None
        self._build_ui()
        self.setAcceptDrops(True)

    def _build_ui(self):
        lay = QVBoxLayout(self)

        self.drop = QLabel("📁 사진 폴더 또는 파일을 여기에 드래그하세요\n(하위 폴더 전부 수집 · 사진만 / 영상 제외)")
        self.drop.setObjectName("dropzone")
        self.drop.setAlignment(Qt.AlignCenter)
        self.drop.mousePressEvent = lambda e: self.pick_folder()
        lay.addWidget(self.drop)

        g = QGroupBox("갤러리 설정")
        form = QFormLayout(g)
        self.title_edit = QLineEdit("셀렉 갤러리")
        self.goal_spin = QSpinBox(); self.goal_spin.setRange(0, 9999); self.goal_spin.setValue(0)
        self.goal_spin.setSpecialValueText("제한 없음")
        self.notice_edit = QLineEdit("원하시는 사진을 골라 '결과 파일 저장'을 눌러 보내주세요.")
        self.target_mb = QSpinBox(); self.target_mb.setRange(0, 20000); self.target_mb.setValue(0)
        self.target_mb.setSpecialValueText("자동 (화질 우선)")
        form.addRow("제목", self.title_edit)
        form.addRow("목표 장수", self.goal_spin)
        form.addRow("안내 문구", self.notice_edit)
        form.addRow("목표 파일 용량(MB)", self.target_mb)
        lay.addWidget(g)

        out_row = QHBoxLayout()
        self.out_edit = QLineEdit(os.path.join(os.path.expanduser("~"), "Desktop"))
        btn_out = QPushButton("출력 폴더…")
        btn_out.clicked.connect(self.pick_out)
        out_row.addWidget(QLabel("출력")); out_row.addWidget(self.out_edit); out_row.addWidget(btn_out)
        lay.addLayout(out_row)

        self.btn_build = QPushButton("🛠 갤러리 HTML 생성")
        self.btn_build.setObjectName("primary")
        self.btn_build.setEnabled(False)
        self.btn_build.clicked.connect(self.start_build)
        lay.addWidget(self.btn_build)

        self.bar = QProgressBar(); self.bar.setVisible(False)
        lay.addWidget(self.bar)
        self.result = QListWidget()
        self.result.itemDoubleClicked.connect(
            lambda it: webbrowser.open(Path(it.data(Qt.UserRole)).as_uri()) if it.data(Qt.UserRole) else None)
        lay.addWidget(self.result, 1)

    # --- 입력 ---
    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()
            self.drop.setProperty("drag", True); self._repolish()

    def dragLeaveEvent(self, e):
        self.drop.setProperty("drag", False); self._repolish()

    def dropEvent(self, e):
        self.drop.setProperty("drag", False); self._repolish()
        paths = [u.toLocalFile() for u in e.mimeData().urls() if u.isLocalFile()]
        if paths:
            self.load_paths(paths)

    def _repolish(self):
        self.drop.style().unpolish(self.drop); self.drop.style().polish(self.drop)

    def pick_folder(self):
        d = QFileDialog.getExistingDirectory(self, "사진 폴더 선택")
        if d:
            self.load_paths([d])

    def pick_out(self):
        d = QFileDialog.getExistingDirectory(self, "출력 폴더 선택", self.out_edit.text())
        if d:
            self.out_edit.setText(d)

    def load_paths(self, paths):
        self.items = scan(paths)
        n = len(self.items)
        self.drop.setText("✅ {}장 수집됨 — 다시 드래그하면 교체".format(n) if n
                          else "사진을 찾지 못했습니다. 다른 폴더를 드래그하세요")
        self.btn_build.setEnabled(n > 0)
        if paths and n:
            base = os.path.basename(os.path.normpath(paths[0]))
            if self.title_edit.text() == "셀렉 갤러리":
                self.title_edit.setText(base)

    # --- 빌드 ---
    def start_build(self):
        title = self.title_edit.text().strip() or "셀렉 갤러리"
        self.last_target = self.target_mb.value() * 1024 * 1024
        cfg = dict(title=title, goal=self.goal_spin.value(),
                   notice=self.notice_edit.text().strip(),
                   out_dir=self.out_edit.text().strip(),
                   target_bytes=self.last_target)
        self.btn_build.setEnabled(False)
        self.bar.setVisible(True); self.bar.setValue(0)
        self.result.clear()
        self.worker = BuildWorker(self.items, cfg)
        self.worker.progress.connect(lambda d, t: (self.bar.setMaximum(t), self.bar.setValue(d)))
        self.worker.done.connect(self.on_done)
        self.worker.failed.connect(self.on_failed)
        self.worker.start()

    def on_done(self, files, errors):
        from PyQt5.QtWidgets import QListWidgetItem
        self.bar.setVisible(False)
        self.btn_build.setEnabled(True)
        for f in files:
            mb = f["bytes"] / (1024 * 1024)
            item = QListWidgetItem("📦 {}  ({}장, {:.1f}MB)".format(
                os.path.basename(f["html"]), f["count"], mb))
            item.setData(Qt.UserRole, f["html"])
            self.result.addItem(item)
            if getattr(self, "last_target", 0) and f["bytes"] > self.last_target:
                self.result.addItem("⚠ 목표 용량({:.0f}MB)을 약간 초과({:.1f}MB) — 더 낮은 목표를 지정하거나 그대로 사용하세요".format(
                    self.last_target / (1024 * 1024), mb))
        for err in errors:
            self.result.addItem("⚠ 제외됨: " + err)
        self.result.addItem("💡 더블클릭 = 브라우저 미리보기")
        QMessageBox.information(self, "완료", "갤러리 HTML 생성 완료")

    def on_failed(self, msg):
        self.bar.setVisible(False)
        self.btn_build.setEnabled(True)
        QMessageBox.critical(self, "오류", msg)
