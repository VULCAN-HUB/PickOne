# -*- coding: utf-8 -*-
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

# venv 직접 실행 시 Qt 플랫폼 플러그인 경로 누락 방어 (RawBaker 동일 함정, frozen exe는 PyInstaller가 처리)
if not getattr(sys, "frozen", False):
    import PyQt5
    _plug = os.path.join(os.path.dirname(PyQt5.__file__), "Qt5", "plugins")
    if os.path.isdir(_plug):
        os.environ["QT_PLUGIN_PATH"] = _plug
        os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = os.path.join(_plug, "platforms")

from PyQt5.QtWidgets import QApplication  # noqa: E402

from pickone.ui.main_window import MainWindow  # noqa: E402


def main():
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
