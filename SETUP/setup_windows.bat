@echo off
rem ============================================================================
rem  setup_windows.bat - HomeHub lab: install JDK 11, Dafny 4.11.0, Python 3.13 and the Codex CLI on Windows
rem  (macOS: setup_mac.sh). Run the setup with:  python SETUP\setup.py   (it runs this script)
rem  No Python on this PC yet: double-click this file instead. It installs Python too.
rem
rem  Lives in <lab folder>\SETUP\ and sets up <lab folder> (the folder above it).
rem  Downloads are kept here in SETUP\.
rem
rem  Official downloads only (adoptium, dafny-lang, python.org), no installer window, no
rem  package manager, no administrator rights (no UAC). Double-click it or let setup.py run it:
rem  it runs as your current user and then
rem    1. JDK 11     Eclipse Temurin 11.0.32.1+1 zip -> <lab folder>\jdk\
rem                  (the javac that built the committed legacy\build: the same bytecode, see A-1)
rem    2. Dafny      4.11.0 zip                     -> <lab folder>\dafny\
rem    3. Python     uses a python.exe on PATH when it is 3.8 or newer (no install; skipped:
rem                  ones inside a user profile and the Microsoft Store stub, since every
rem                  account must run it); only otherwise unpacks 3.13.17 zip (python.org)
rem                  -> <lab folder>\python\. Then makes <lab folder>\.venv with that Python
rem                  and installs jupyterlab into it (pip, from PyPI; brings ipykernel, nbconvert)
rem    4. Prints the versions
rem    5. Codex CLI (optional): OpenAI's installer (https://chatgpt.com/codex/install.ps1). It installs into
rem       one account (%LOCALAPPDATA%\Programs\OpenAI\Codex\bin, user PATH),
rem       in this same window as your current user. Existing account login state is unchanged.
rem       Skipped when Codex is already installed and signed in (codex login status); otherwise installs,
rem       or updates an install that is not signed in. A failure here does not stop the setup.
rem       --skip-codex: skip step 5.  --update-codex: run the installer even when Codex is already there.
rem       Later, or to update: SETUP\setup_windows.bat --update-codex
rem  A download is skipped when its file is already in SETUP\.
rem  A part that is already installed is skipped; delete its folder to reinstall.
rem  Put the lab folder somewhere your account can write.
rem  No environment variable of this PC is changed (only Codex's installer adds itself to the user PATH):
rem  make.cmd (SETUP\make_fallback.py) and the notebooks (notebooks\lab.py) put jdk\ and dafny\ first on PATH.
rem ============================================================================
setlocal

rem ---- options: setup_windows.bat [--skip-codex | --update-codex]
set "HH_CODEX=auto"
for %%A in (%*) do (
  if /i "%%~A"=="--skip-codex" set "HH_CODEX=skip"
  if /i "%%~A"=="--update-codex" set "HH_CODEX=update"
)

rem ---- continue as the current user; no elevation
set "HERE=%~dp0"
set "HERE=%HERE:~0,-1%"
rem  the lab folder (project root) is the folder above SETUP\
for %%I in ("%HERE%\..") do set "ROOT=%%~fI"
cd /d "%ROOT%"
set "PS=powershell -NoProfile -ExecutionPolicy Bypass -Command"

set "JDK_NAME=OpenJDK11U-jdk_x64_windows_hotspot_11.0.32.1_1.zip"
set "JDK_URL=https://github.com/adoptium/temurin11-binaries/releases/download/jdk-11.0.32.1+1/OpenJDK11U-jdk_x64_windows_hotspot_11.0.32.1_1.zip"
set "DAFNY_NAME=dafny-4.11.0-x64-windows-2022.zip"
set "DAFNY_URL=https://github.com/dafny-lang/dafny/releases/download/v4.11.0/dafny-4.11.0-x64-windows-2022.zip"
set "PY_NAME=python-3.13.17-amd64.zip"
set "PY_URL=https://www.python.org/ftp/python/3.13.17/python-3.13.17-amd64.zip"
set "HH_PYF=%TEMP%\homehub_python_found.txt"

echo ==== HomeHub lab setup (Windows, current user) ====
echo Lab folder: %ROOT%
echo.

rem ---------------------------------------------------------------- 1. JDK
echo [1/5] JDK 11 (Eclipse Temurin 11.0.32.1+1)
if exist "%ROOT%\jdk\bin\javac.exe" goto :jdk_skip
call :fetch "%JDK_NAME%" "%JDK_URL%" "about 190 MB"
if errorlevel 1 goto :fail
call :unzip "%JDK_NAME%" "jdk" "bin\javac.exe"
if errorlevel 1 goto :fail
goto :dafny
:jdk_skip
echo       skipped: already installed (%ROOT%\jdk)

rem ---------------------------------------------------------------- 2. Dafny
:dafny
echo [2/5] Dafny 4.11.0
if exist "%ROOT%\dafny\dafny.exe" goto :dafny_skip
call :fetch "%DAFNY_NAME%" "%DAFNY_URL%" "about 66 MB"
if errorlevel 1 goto :fail
call :unzip "%DAFNY_NAME%" "dafny" "dafny.exe"
if errorlevel 1 goto :fail
goto :python
:dafny_skip
echo       skipped: already installed (%ROOT%\dafny)

rem ---------------------------------------------------------------- 3. Python
:python
echo [3/5] Python 3.8 or newer, .venv and Jupyter
rem  python.exe on PATH first (not in a user profile, not the Store stub), then the one
rem  this script unpacked; the one found is written to HH_PYF
set "HH_ROOT=%ROOT%"
del /q "%HH_PYF%" >nul 2>&1
%PS% "$c = @(Get-Command python.exe -All -CommandType Application -ErrorAction SilentlyContinue | Where-Object { $_.Source -notlike '*\WindowsApps\*' -and $_.Source -notlike '*\Users\*' } | ForEach-Object { $_.Source }); $own = $env:HH_ROOT + '\python\python.exe'; if (Test-Path -LiteralPath $own) { $c += $own }; foreach ($p in $c) { & $p -c 'import sys; sys.exit(sys.version_info < (3, 8))' 2>$null; $ok = ($LASTEXITCODE -eq 0); $v = ((& $p --version 2>&1) | Out-String).Trim(); if ($ok) { Write-Host ('      found: ' + $p + ' (' + $v + '), no install needed'); [IO.File]::WriteAllBytes($env:HH_PYF, [Console]::OutputEncoding.GetBytes($p)); exit 0 }; Write-Host ('      too old: ' + $p + ' (' + $v + ')') }; exit 1"
if errorlevel 1 goto :python_install
set /p PY_EXE=<"%HH_PYF%"
del /q "%HH_PYF%" >nul 2>&1
goto :venv
:python_install
echo       no Python 3.8 or newer: unpacking Python 3.13.17 (python.org)
call :fetch "%PY_NAME%" "%PY_URL%" "about 30 MB"
if errorlevel 1 goto :fail
call :unzip "%PY_NAME%" "python" "python.exe"
if errorlevel 1 goto :fail
set "PY_EXE=%ROOT%\python\python.exe"

:venv
set "HH_VPY=%ROOT%\.venv\Scripts\python.exe"
if not exist "%HH_VPY%" goto :venv_make
"%HH_VPY%" -c "import sys" >nul 2>&1
if errorlevel 1 goto :venv_broken
%PS% "Write-Host ('      skipped: .venv already exists (' + ((& $env:HH_VPY --version 2>&1) | Out-String).Trim() + ')')"
goto :jupyter
:venv_broken
echo       .venv does not run (its Python was removed?): making it again
rd /s /q "%ROOT%\.venv"
:venv_make
echo       making %ROOT%\.venv ...
"%PY_EXE%" -m venv "%ROOT%\.venv"
if errorlevel 1 goto :fail_venv
echo       done: %HH_VPY%
:jupyter
echo       installing jupyterlab into .venv (pip, from PyPI) ...
"%HH_VPY%" -m pip install --disable-pip-version-check -q jupyterlab
if errorlevel 1 goto :fail_pip
echo       done: jupyterlab

rem ---------------------------------------------------------------- 4. versions
echo [4/5] Versions
"%ROOT%\jdk\bin\java.exe" -version
if errorlevel 1 goto :fail_run_java
"%ROOT%\jdk\bin\javac.exe" -version
if errorlevel 1 goto :fail_run_javac
"%ROOT%\dafny\dafny.exe" --version
if errorlevel 1 goto :fail_run_dafny
"%HH_VPY%" --version
if errorlevel 1 goto :fail_run_venv
call :codex
echo.
echo OK. Next:  make check-env   in cmd, in the lab folder: make.cmd runs SETUP\make_fallback.py
echo     Codex was installed now? Open a NEW cmd window (and restart VS Code / Jupyter) so codex is found.
goto :end


rem ============================================================================
rem  :codex   [5/5] Codex CLI with OpenAI's installer, for the account running this window
:codex
echo [5/5] Codex CLI - optional: skipped when already installed and signed in
if "%HH_CODEX%"=="update" goto :codex_install
if not "%HH_CODEX%"=="skip" goto :codex_check
echo       skipped --skip-codex: already installed and signed in
echo                to update:  SETUP\setup_windows.bat --update-codex
exit /b 0
:codex_check
where codex >nul 2>nul
if errorlevel 1 goto :codex_install
rem  call: an npm install is codex.cmd, and a .cmd started without call ends this script
call codex login status >nul 2>&1
if errorlevel 1 goto :codex_install
echo       skipped: already installed and signed in
echo                to update:  SETUP\setup_windows.bat --update-codex
exit /b 0
:codex_install
set "CODEX_NON_INTERACTIVE=1"
powershell -NoProfile -ExecutionPolicy Bypass -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; irm https://chatgpt.com/codex/install.ps1 | iex"
set "HH_RC=%errorlevel%"
set "CODEX_NON_INTERACTIVE="
if not "%HH_RC%"=="0" goto :codex_failed
echo       done. In a NEW cmd window, sign in once:  codex login
exit /b 0
:codex_failed
echo       WARNING: Codex was not installed or updated - internet/proxy, or chatgpt.com blocked?
echo                The lab works without it. Later:  SETUP\setup_windows.bat --update-codex
exit /b 0

rem  :fetch NAME URL SIZE_TEXT   -> SETUP\NAME
:fetch
set "HH_F=%HERE%\%~1"
set "HH_U=%~2"
if exist "%HH_F%" goto :fetch_check
echo       downloading %~2 (%~3)
where curl.exe >nul 2>nul
if errorlevel 1 goto :fetch_ps
curl.exe -L --fail --retry 3 --progress-bar --ssl-no-revoke -o "%HH_F%" "%HH_U%"
if not errorlevel 1 goto :fetch_check
echo       curl failed, trying PowerShell...
:fetch_ps
%PS% "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; $ProgressPreference = 'SilentlyContinue'; Invoke-WebRequest -Uri $env:HH_U -OutFile $env:HH_F -UseBasicParsing"
if errorlevel 1 goto :fetch_fail
:fetch_check
%PS% "Unblock-File -LiteralPath $env:HH_F" >nul 2>&1
echo       file OK: %~1
exit /b 0
:fetch_fail
del /q "%HH_F%" >nul 2>&1
echo.
echo ERROR: download failed. Check the internet connection and run the setup again:
echo        %~2
exit /b 1

rem  :unzip ZIP TARGET_DIR FILE_INSIDE   -> <lab folder>\TARGET_DIR (FILE_INSIDE must exist there)
:unzip
set "HH_Z=%HERE%\%~1"
set "HH_D=%ROOT%\%~2"
set "HH_IN=%~3"
set "HH_T=%ROOT%\_unpack_tmp"
echo       unpacking to %ROOT%\%~2 ...
%PS% "$ErrorActionPreference = 'Stop'; $t = $env:HH_T; $d = $env:HH_D; if (Test-Path $t) { Remove-Item $t -Recurse -Force }; New-Item -ItemType Directory $t | Out-Null; $ok = $false; $tar = Get-Command tar.exe -ErrorAction SilentlyContinue; if ($tar) { & $tar.Source -xf $env:HH_Z -C $t 2>$null; $ok = ($LASTEXITCODE -eq 0) }; if (-not $ok) { Remove-Item $t -Recurse -Force; New-Item -ItemType Directory $t | Out-Null; $ProgressPreference = 'SilentlyContinue'; Expand-Archive -LiteralPath $env:HH_Z -DestinationPath $t -Force }; $src = if (Test-Path (Join-Path $t $env:HH_IN)) { $t } else { Get-ChildItem $t -Directory | Where-Object { Test-Path (Join-Path $_.FullName $env:HH_IN) } | Select-Object -First 1 -ExpandProperty FullName }; if (-not $src) { throw ('no ' + $env:HH_IN + ' in the zip') }; if (Test-Path $d) { Remove-Item $d -Recurse -Force }; Move-Item $src $d; if (Test-Path $t) { Remove-Item $t -Recurse -Force }"
if errorlevel 1 goto :unzip_fail
echo       done: %ROOT%\%~2\%~3
exit /b 0
:unzip_fail
echo.
echo ERROR: could not unpack %~1. Delete it and run the setup again.
exit /b 1


rem ============================================================================
:fail_venv
echo.
echo ERROR: could not make .venv with %PY_EXE%.
goto :end_error
:fail_pip
echo.
echo ERROR: pip could not install jupyterlab into .venv (internet/proxy, or PyPI blocked?). Run the setup again.
goto :end_error
:fail_run_java
echo.
echo ERROR: java did not run.
goto :end_error
:fail_run_javac
echo.
echo ERROR: javac did not run.
goto :end_error
:fail_run_dafny
echo.
echo ERROR: dafny did not run.
goto :end_error
:fail_run_venv
echo.
echo ERROR: .venv\Scripts\python.exe did not run.
goto :end_error
:fail
goto :end_error

:end_error
endlocal
pause
exit /b 1

:end
endlocal
pause
exit /b 0
