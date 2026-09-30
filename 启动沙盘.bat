@echo off
chcp 65001 >nul
cd /d "%~dp0"
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
if exist ".venv\Scripts\python.exe" goto run

echo 正在创建虚拟环境并安装依赖，第一次会稍慢。
set "PY="
py -3.12 -c "import sys" >nul 2>&1 && set "PY=py -3.12"
if not defined PY py -3.11 -c "import sys" >nul 2>&1 && set "PY=py -3.11"
if not defined PY py -3.13 -c "import sys" >nul 2>&1 && set "PY=py -3.13"
if not defined PY python -c "import sys; raise SystemExit(0 if sys.version_info>=(3,11) else 1)" >nul 2>&1 && set "PY=python"
if not defined PY (
  echo 没有找到 Python 3.11 或更高版本。
  echo 请先安装 Python 3.12，并勾选 Add python.exe to PATH。
  pause
  exit /b 1
)
%PY% -m venv .venv
if errorlevel 1 (
  echo 创建运行环境失败。
  pause
  exit /b 1
)
.venv\Scripts\python.exe -m pip install -r "%~dp0..\运行依赖.txt"
if errorlevel 1 (
  echo 依赖安装失败。请检查网络后重新双击本文件。
  pause
  exit /b 1
)

:run
.venv\Scripts\python.exe -m streamlit run app.py
if errorlevel 1 pause
