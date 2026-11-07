# SETUP: 실습 환경 설치 도구

이 폴더에는 실습 PC를 준비하는 파일이 들어 있습니다. **설치 방법은 실습 폴더 맨 위의 `SETUP.md`를 보세요.** 직접 실행하는 파일은 `setup.py` 하나입니다(Windows에 Python이 없으면 `setup_windows.bat` 더블클릭).

| 파일 | 직접 실행 | 하는 일 |
|---|---|---|
| `setup.py` | ○ | 설치의 시작점입니다. 이 PC에 무엇이 있는지(`jdk/`, `dafny/`, `.venv/`, PATH의 java·javac·dafny, Codex) 먼저 보여 준 뒤, OS에 맞는 설치 스크립트를 실행합니다 |
| `setup_mac.sh` | | macOS 설치. `setup.py`가 관리자 권한(sudo)으로 실행합니다 |
| `setup_windows.bat` | Python이 없을 때만 | Windows 설치. `setup.py`가 실행합니다. 더블클릭하면 Python도 함께 설치합니다 |
| `make_fallback.py` | | 이 실습에서만 쓰는 make·bash 호환 레이어입니다(범용 make가 아님). make와 bash가 없는 Windows에서 이 실습 Makefile의 대상을 같은 결과로 Python으로 실행합니다. cmd에서 `make …`를 치면 실습 폴더 맨 위의 `make.cmd`가 이 파일을 부르고, 주피터 노트북의 `lab.run`도 Windows에서는 이 파일을 부릅니다 |
| `*.tar.gz`, `*.zip`, `*.pkg` | | 설치할 때 내려받은 JDK·Dafny·Python 파일입니다 |

설치가 하는 일(두 OS 같음):

1. JDK 11을 `jdk/`에 풉니다. 저장소의 `legacy/build`를 만든 javac와 같은 버전입니다.
2. Dafny 4.11을 `dafny/`에 풉니다.
3. Python 가상환경 `.venv/`를 만들고 JupyterLab을 넣습니다.
4. PATH, `JAVA_HOME`, `DAFNY` 환경변수를 설정합니다.
5. 설치된 버전을 보여 줍니다.
6. Codex CLI(선택)를 내 계정에 설치하거나 업데이트합니다.

이미 설치된 부분은 건너뜁니다.
