# -*- coding: utf-8 -*-
"""UI 스모크 — offscreen으로 탭 생성·위젯 구성 검증 (목표용량/대상위치 등, GUI 없이)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
os.environ["QT_QPA_PLATFORM"] = "offscreen"

import pytest

pyqt = pytest.importorskip("PyQt5.QtWidgets")

# venv 직접 실행 시 Qt 플랫폼 플러그인 경로 누락 방어
import PyQt5  # noqa: E402

_plug = os.path.join(os.path.dirname(PyQt5.__file__), "Qt5", "plugins")
if os.path.isdir(_plug):
    os.environ.setdefault("QT_PLUGIN_PATH", _plug)
    os.environ.setdefault("QT_QPA_PLATFORM_PLUGIN_PATH", os.path.join(_plug, "platforms"))

_app = None


def _ensure_app():
    global _app
    from PyQt5.QtWidgets import QApplication
    _app = QApplication.instance() or QApplication([])
    return _app


def test_pack_tab_v020_widgets():
    _ensure_app()
    from pickone.ui.pack_tab import PackTab
    t = PackTab()
    assert t.goal_spin.value() == 0 and t.goal_spin.text() == "제한 없음"
    assert t.target_mb.value() == 0 and t.target_mb.text() == "자동 (화질 우선)"
    assert not hasattr(t, "channel") and not hasattr(t, "keep_html")


def test_recover_tab_v020_widgets():
    _ensure_app()
    from pickone.ui.recover_tab import RecoverTab
    r = RecoverTab()
    assert hasattr(r, "loc_edit") and hasattr(r, "name_edit")
    assert not hasattr(r, "dst_edit")
    assert r.result_name == ""
