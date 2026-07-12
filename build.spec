# -*- mode: python ; coding: utf-8 -*-
# PyInstaller 6.x. Windows(.exe) / macOS(.app) 동시 지원 — 빌드되는 OS에 맞춰 자동 선택.
# Windows: build.bat 로 빌드.  macOS: build_mac.sh 로 빌드(Mac 실기에서만 가능).
import sys

is_mac = sys.platform == 'darwin'

a = Analysis(
    ['main.py'],
    pathex=['src'],
    binaries=[],
    datas=[('src/pickone/template/selector.html', 'pickone/template'),
           ('assets/pickone_icon.png', 'assets')],
    hiddenimports=['pillow_heif'],
    hookspath=[],
    runtime_hooks=[],
    excludes=['tkinter', 'numpy', 'matplotlib'],
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, a.binaries, a.datas,
    name='PickOne',
    icon=('assets/pickone.icns' if is_mac else 'assets/pickone.ico'),
    # version_info.txt 는 Windows 전용 리소스 포맷 → Mac 빌드에선 제외
    version=(None if is_mac else 'version_info.txt'),
    console=False,
    upx=False,
)

if is_mac:
    # macOS .app 번들 — 고해상도 지원, 번들 식별자는 브랜드명(Unknown) 기반(PII 아님)
    app = BUNDLE(
        exe,
        name='PickOne.app',
        icon='assets/pickone.icns',
        bundle_identifier='com.unknown8563.pickone',
        info_plist={
            'CFBundleDisplayName': 'PickOne',
            'CFBundleShortVersionString': '0.1.0',
            'CFBundleVersion': '0.1.0',
            'NSHighResolutionCapable': True,
            'NSHumanReadableCopyright': '(C) 2026 Unknown',
            'LSApplicationCategoryType': 'public.app-category.photography',
        },
    )
