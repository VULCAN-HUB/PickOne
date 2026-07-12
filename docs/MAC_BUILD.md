# PickOne macOS 빌드 가이드 (Mac 도착 시 그대로 따라하기)

> 이 문서는 **Mac 장비가 생기는 날 바로 작업**할 수 있도록 미리 준비해둔 런북입니다.
> 코드·스크립트·아이콘·설정은 Windows에서 이미 준비 완료(2026-06-13). Mac에서는 빌드만 하면 됩니다.

## 0. 왜 Mac이 필요한가

PyInstaller는 **크로스컴파일이 안 됩니다.** Windows에서 `.app`을 만들 수 없고, 반드시 macOS 실기(또는 클라우드 Mac/CI)에서 빌드해야 합니다. 코드 자체는 이미 크로스플랫폼이라 `python main.py`로 소스 실행은 Mac에서 바로 됩니다.

## 1. 준비물 확인 (이미 repo에 들어있음)

- `requirements.txt` — 의존성 한 줄 설치
- `build.spec` — 플랫폼 자동 인지(Mac이면 `.icns`+`.app` 번들 선택)
- `build_mac.sh` — Mac 빌드 스크립트
- `assets/pickone.icns` — Mac용 아이콘(512/1024 PNG에서 생성됨)
- 코드: 폰트 폴백(Apple SD Gothic Neo), file URL 표준화 등 Mac 대응 반영됨

## 2. 셋업 (Mac 터미널)

```bash
# Python 3.12 권장 (brew install python@3.12 또는 python.org)
cd <PickOne 폴더>
python3 -m venv venv
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt
```

## 3. 소스 실행으로 먼저 동작 확인

```bash
./venv/bin/python main.py
```
- 패키징/회수 탭, 드래그&드롭, 갤러리 생성, 한글 표시 확인
- 폰트: Pretendard 미설치 시 Apple SD Gothic Neo로 자동 폴백(정상)
- Rajdhani(로고 워드마크)가 없으면 시스템 폰트로 대체됨 — 정확한 로고를 원하면 Rajdhani 설치 또는 추후 폰트 번들링 검토

## 4. .app 빌드

```bash
chmod +x build_mac.sh
./build_mac.sh
```
산출물: `dist/PickOne.app`

## 5. 코드 서명 / 공증 (정식 배포 시)

미서명 `.app`은 Gatekeeper가 "확인되지 않은 개발자" 경고를 띄웁니다.

- **내부 테스트만**: Finder에서 `.app` 우클릭 → 열기 → 경고창에서 "열기" (한 번만)
- **고객 배포**: Apple Developer 계정($99/년) 필요
  1. `codesign --deep --force --options runtime --sign "Developer ID Application: <이름>" dist/PickOne.app`
  2. `ditto -c -k --keepParent dist/PickOne.app PickOne.zip`
  3. `xcrun notarytool submit PickOne.zip --apple-id <id> --team-id <team> --wait`
  4. `xcrun stapler staple dist/PickOne.app`
  5. 배포는 `.dmg` 또는 `.zip`으로

> 서명/공증은 **실제 PII(실명·Apple ID)가 들어가므로 코드·repo에 하드코딩하지 말 것.** 빌드 시점에 로컬에서만 입력. (글로벌 PII 보호 규칙)

## 6. 배포 포맷

- Windows: 단일 `PickOne.exe` (현행)
- macOS: `PickOne.app` → `.dmg`로 감싸 배포 권장(드래그 설치 UX)

## 알려진 차이 / 체크리스트

- [ ] 한글 파일명 NFC/NFD: 코드가 NFC 정규화하므로 Mac(NFD 파일시스템)에서도 매칭 OK — 실파일로 한 번 검증
- [ ] HEIC: `pillow-heif`가 Mac에서도 동작하는지 실파일 검증
- [ ] CR3 등 RAW 임베디드 프리뷰 추출(rawpy 미사용) Mac 확인
- [ ] 회수 폴더 생성 경로(`/Users/.../`) 정상 동작 확인
- [ ] 클라이언트 HTML은 이미 크로스플랫폼 — Safari/Chrome(Mac)에서 열기만 재확인

## 다른 프로젝트에도 적용

이 준비 패턴(플랫폼 인지 spec + build_mac.sh + icns + requirements + 이 문서)은 RawBaker·SnapStamp·E-sprite 등 Python/PyQt 프로젝트에 동일 적용 가능. vault `wiki/guidelines/cross-platform-prep.md` 참조.
