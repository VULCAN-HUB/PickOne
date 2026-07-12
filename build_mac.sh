#!/bin/bash
# PickOne macOS 빌드 (Mac 실기에서만 동작 — PyInstaller는 크로스컴파일 불가)
# 사용:  chmod +x build_mac.sh && ./build_mac.sh
# 산출물: dist/PickOne.app
set -e
cd "$(dirname "$0")"

# venv 없으면 생성 + 의존성 설치
if [ ! -d "venv" ]; then
  echo "[1/3] venv 생성 + 의존성 설치"
  python3 -m venv venv
  ./venv/bin/pip install --upgrade pip
  ./venv/bin/pip install -r requirements.txt
fi

echo "[2/3] PyInstaller 빌드 (build.spec — Mac에서 .app 자동 선택)"
./venv/bin/python -m PyInstaller build.spec --noconfirm

echo "[3/3] 완료: dist/PickOne.app"
echo
echo "주의: 미서명 .app은 Gatekeeper 경고가 뜹니다."
echo "  - 테스트: Finder에서 우클릭 → 열기 → '열기'"
echo "  - 정식 배포: Apple Developer 계정($99/년) 필요 → codesign + notarytool 공증"
echo "    (상세는 docs/MAC_BUILD.md 참조)"
