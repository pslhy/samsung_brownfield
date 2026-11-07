# SETUP: 실습 환경 설치

실습 PC를 준비할 때 쓰는 폴더입니다. **직접 실행하는 파일은 `setup.py` 하나입니다.** 명령은 모두 실습 폴더 맨 위에서 실행합니다.

## 사용법

| 하려는 일 | macOS | Windows (cmd) |
|---|---|---|
| 처음 설치 | `python3 SETUP/setup.py` | `python SETUP\setup.py` |
| Codex 다시 설치·업데이트 | `python3 SETUP/setup.py --update-codex` | `python SETUP\setup.py --update-codex` |

### 처음 설치: `setup.py`

- 이 PC에 무엇이 있는지 먼저 보여 준 뒤, OS에 맞는 설치 스크립트를 실행합니다. 관리자 권한을 묻습니다(macOS는 sudo 암호, Windows는 UAC 창).
- 설치하는 것: JDK 11(`jdk/`, 저장소의 `legacy/build`를 만든 javac와 같은 버전), Dafny 4.11(`dafny/`), Python 가상환경과 Jupyter(`.venv/`), Codex CLI(선택). JDK와 Dafny는 PATH에도 등록합니다.
- 이미 설치된 부분은 건너뜁니다. 다시 설치하려면 그 폴더(`jdk/`, `dafny/`, `.venv/`)를 지우고 다시 실행합니다.
- Codex는 설치돼 있고, 로그인돼 있고, 0.147.0 이상이면 건너뜁니다. Codex 설치가 실패해도 나머지 설치는 계속됩니다. 처음 설치한 뒤에는 `codex login`으로 한 번 로그인합니다.
- 내려받은 파일은 이 폴더에 남습니다. 인터넷이 막힌 PC에는 같은 파일을 이 폴더에 넣어 두면 내려받지 않고 씁니다(SHA-256으로 확인).
- 끝나면 **새 터미널을 열고**(VS Code와 Jupyter도 다시 시작) `make check-env`로 확인합니다.
- Windows에 Python이 아직 없으면 `setup.py` 대신 `SETUP\setup_windows.bat`을 더블클릭합니다. Python도 함께 설치합니다.
- Linux는 지원하지 않습니다. `setup.py`를 실행하면 직접 설치할 것을 알려 줍니다.

## 파일

| 파일 | 직접 실행 | 하는 일 |
|---|---|---|
| `setup.py` | ○ | 설치의 시작점입니다. 이 PC의 상태(`jdk/`, `dafny/`, `.venv/`, PATH의 java·javac·dafny, make, Codex)를 보고, OS에 맞는 스크립트를 옵션(`--skip-codex` / `--update-codex`)과 함께 실행합니다 |
| `setup_mac.sh` | | macOS 설치 6단계. `setup.py`가 sudo로 실행합니다 |
| `setup_windows.bat` | Python이 없을 때만 | Windows 설치 6단계. `setup.py`가 실행합니다 |
| `make_fallback.py` | | Windows용 `make`입니다. Windows에는 make가 없고 Makefile은 bash가 필요해서, Makefile과 같은 대상·변수·결과를 Python으로 냅니다. Windows cmd에서 `make …`를 치면 실습 폴더 맨 위의 `make.cmd`가 이 파일을 부르고, 노트북의 `lab.run`도 Windows에서는 이 파일을 부릅니다 |
| `*.tar.gz`, `*.zip`, `*.pkg` | | 설치 스크립트가 내려받은 JDK·Dafny·Python 파일. git에 올리지 않습니다 |

## 고칠 때 (강사용)

- Makefile이 기준입니다. Makefile의 대상을 바꾸면 `make_fallback.py`도 맞추고, `make smoke`와 `python3 SETUP/make_fallback.py smoke`의 결과가 같은지 확인합니다.
- Codex 최소 버전은 `setup.py`의 `CODEX_MIN_VERSION`입니다.
