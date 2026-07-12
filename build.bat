@echo off
rem PickOne single-exe build (ASCII junction C:\pkbuild to avoid non-ASCII path issues)
if exist C:\pkbuild rmdir C:\pkbuild
mklink /J C:\pkbuild "%~dp0." >nul
set PY=C:\pkbuild\venv\Scripts\python.exe
pushd C:\pkbuild
"%PY%" -m PyInstaller build.spec --noconfirm
set RC=%ERRORLEVEL%
popd
if %RC% NEQ 0 exit /b %RC%
echo Build done: dist\PickOne.exe
