@echo off
rem make.cmd - HomeHub lab on Windows, where there is no make (the Makefile needs bash).
rem "make TARGET VAR=value ..." as written in the documents runs "python SETUP\make_fallback.py TARGET VAR=value ...",
rem which does what the Makefile does. cmd looks in the current folder first, so run make in the lab folder.
rem A value with a pipe character in it needs double quotes around the whole argument, e.g.
rem   make path "MSG=4^|fridge-2^|TEMP^|14^|180000^|unit=C"   (without the carets)
setlocal
set "HH_PY=%~dp0.venv\Scripts\python.exe"
if not exist "%HH_PY%" set "HH_PY=python"
"%HH_PY%" "%~dp0SETUP\make_fallback.py" %*
exit /b %errorlevel%
