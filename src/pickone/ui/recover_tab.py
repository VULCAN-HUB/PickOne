# -*- coding: utf-8 -*-
"""회수 모드 탭 — 결과 .json 드롭/텍스트 붙여넣기(누적) → 파싱 미리보기 → 복사."""
import os

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QPlainTextEdit, QListWidget, QFileDialog, QMessageBox, QCheckBox,
)

from ..scanner import scan
from ..recovery import RecoverySession, parse_any, copy_selected, safe_folder_name


class RecoverTab(QWidget):
    def __init__(self):
        super().__init__()
        self.session = RecoverySession()
        self.mapping = {}
        self.matched = []
        self.result_name = ""  # 돌려받은 결과 파일 이름(확장자 제외) — 폴더명 기본값
        self._build_ui()
        self.setAcceptDrops(True)

    def _build_ui(self):
        lay = QVBoxLayout(self)

        # 1. 원본 폴더
        src_row = QHBoxLayout()
        self.src_edit = QLineEdit()
        self.src_edit.setPlaceholderText("① 원본 사진 폴더 (패키징 때 사용한 폴더)")
        btn_src = QPushButton("원본 폴더…")
        btn_src.clicked.connect(self.pick_src)
        src_row.addWidget(self.src_edit); src_row.addWidget(btn_src)
        lay.addLayout(src_row)

        # 2. 결과 입력
        self.drop = QLabel("② 클라이언트가 보낸 결과 파일(.json)을 여기에 드래그\n또는 아래에 회신 텍스트 붙여넣기 (여러 묶음 누적 가능)")
        self.drop.setObjectName("dropzone")
        self.drop.setAlignment(Qt.AlignCenter)
        lay.addWidget(self.drop)

        self.text = QPlainTextEdit()
        self.text.setPlaceholderText("폴백: 회신 텍스트 붙여넣기 후 [텍스트 추가]")
        self.text.setMaximumHeight(90)
        lay.addWidget(self.text)
        row = QHBoxLayout()
        btn_add = QPushButton("텍스트 추가")
        btn_add.clicked.connect(self.add_text)
        btn_clear = QPushButton("입력 초기화")
        btn_clear.clicked.connect(self.reset_session)
        row.addWidget(btn_add); row.addWidget(btn_clear); row.addStretch()
        lay.addLayout(row)

        # 3. 파싱 미리보기
        lay.addWidget(QLabel("③ 파싱 미리보기 — 확인 후 복사 실행"))
        self.preview = QListWidget()
        lay.addWidget(self.preview, 1)

        # 4. 대상 위치 + 폴더 이름 + 실행
        loc_row = QHBoxLayout()
        self.loc_edit = QLineEdit()
        self.loc_edit.setPlaceholderText("④ 셀렉본을 담을 상위 폴더(대상 위치)")
        btn_loc = QPushButton("대상 위치…")
        btn_loc.clicked.connect(self.pick_loc)
        loc_row.addWidget(self.loc_edit); loc_row.addWidget(btn_loc)
        lay.addLayout(loc_row)
        name_row = QHBoxLayout()
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("폴더 이름 (비우면 받은 결과 파일 이름으로 생성)")
        self.name_edit.textChanged.connect(lambda _: self.refresh())
        name_row.addWidget(QLabel("폴더 이름")); name_row.addWidget(self.name_edit)
        lay.addLayout(name_row)
        self.save_notes = QCheckBox("별점·메모를 _셀렉결과.txt 로 함께 저장")
        self.save_notes.setChecked(True)
        lay.addWidget(self.save_notes)
        self.btn_copy = QPushButton("📋 선택본 복사 실행 (원본 보존)")
        self.btn_copy.setObjectName("primary")
        self.btn_copy.setEnabled(False)
        self.btn_copy.clicked.connect(self.do_copy)
        lay.addWidget(self.btn_copy)

    # --- 입력 ---
    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()

    def dropEvent(self, e):
        for u in e.mimeData().urls():
            p = u.toLocalFile()
            if p.lower().endswith((".json", ".txt")):
                try:
                    with open(p, encoding="utf-8") as f:
                        self.session.add(parse_any(f.read()))
                    if not self.result_name:
                        self.result_name = os.path.splitext(os.path.basename(p))[0]
                except Exception as ex:
                    QMessageBox.warning(self, "파일 오류", "{}: {}".format(os.path.basename(p), ex))
        if self.result_name and not self.name_edit.text().strip():
            self.name_edit.setText(self.result_name)
        self.refresh()

    def add_text(self):
        t = self.text.toPlainText().strip()
        if not t:
            return
        r = parse_any(t)
        if not r.entries:
            QMessageBox.warning(self, "파싱 실패", "파일명을 찾지 못했습니다. 회신 내용을 확인하세요.")
            return
        self.session.add(r)
        self.text.clear()
        self.refresh()

    def reset_session(self):
        self.session = RecoverySession()
        self.result_name = ""
        self.refresh()

    def pick_src(self):
        d = QFileDialog.getExistingDirectory(self, "원본 폴더 선택")
        if d:
            self.src_edit.setText(d)
            self.refresh()

    def pick_loc(self):
        d = QFileDialog.getExistingDirectory(self, "대상 위치 선택")
        if d:
            self.loc_edit.setText(d)
            self.refresh()

    # --- 미리보기·매칭 ---
    def refresh(self):
        self.preview.clear()
        self.matched = []
        src = self.src_edit.text().strip()
        if src and os.path.isdir(src):
            items = scan([src])
            self.mapping = {i.uid: i for i in items}
        entries = self.session.all_entries()
        if not entries:
            self.btn_copy.setEnabled(False)
            return
        missing = self.session.missing_parts()
        if missing:
            self.preview.addItem("⚠ 누락된 묶음: {} — 해당 회신도 받아서 추가하세요".format(
                ", ".join(str(m) for m in missing)))
        if not self.mapping:
            self.preview.addItem("ℹ 회신 {}건 파싱됨 — ① 원본 폴더를 지정하면 매칭합니다".format(len(entries)))
            self.btn_copy.setEnabled(False)
            return
        matched, unmatched = self.session.match(self.mapping)
        self.matched = matched
        for m in matched:
            extra = ""
            if m.entry.star:
                extra += "  ★" + str(m.entry.star)
            if m.entry.memo:
                extra += "  ✎" + m.entry.memo
            self.preview.addItem("✓ {}{}".format(m.item.display, extra))
        for u in unmatched:
            self.preview.addItem("✗ 미매칭: " + u)
        self.preview.addItem("— 매칭 {} / 미매칭 {} —".format(len(matched), len(unmatched)))
        self.btn_copy.setEnabled(bool(matched) and bool(self.loc_edit.text().strip()))

    def do_copy(self):
        loc = self.loc_edit.text().strip()
        if not loc:
            QMessageBox.warning(self, "위치 없음", "대상 위치를 지정하세요.")
            return
        folder = safe_folder_name(self.name_edit.text().strip() or self.result_name)
        dest = os.path.join(loc, folder)
        if os.path.isdir(dest):
            ans = QMessageBox.question(
                self, "폴더 존재",
                "기존 폴더 '{}'에 추가됩니다. 계속할까요?".format(folder))
            if ans != QMessageBox.Yes:
                return
        report = copy_selected(self.matched, dest, save_notes=self.save_notes.isChecked())
        msg = "복사 성공 {}장\n위치: {}".format(report["success"], dest)
        if report["renamed_dupes"]:
            msg += "\n파일명 중복 {}건 → _2 형식으로 변경".format(report["renamed_dupes"])
        if report["failed"]:
            msg += "\n실패:\n" + "\n".join(report["failed"])
        QMessageBox.information(self, "회수 완료", msg)
