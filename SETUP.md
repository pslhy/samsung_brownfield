# 실습 준비하기

세 단계면 됩니다. 설치는 한 번만 하면 됩니다. 노트북은 **브라우저 또는 VS Code 중 하나**로 실행합니다.

Windows 명령은 모두 **명령 프롬프트(cmd)** 기준입니다. 시작 메뉴에서 `cmd`를 검색해 엽니다. 프롬프트가 `PS`로 시작하면 PowerShell이니 `cmd`를 입력하고 Enter를 눌러 바꿉니다(VS Code 터미널도 같음).

## 준비 도구

| 도구 | 하는 일 | 언제 |
|---|---|---|
| `SETUP/setup.py` | 운영체제를 확인하고 맞는 설치 스크립트를 실행합니다. Codex CLI(선택)는 내 계정에 설치합니다 | macOS·Windows 공통 |
| `SETUP/setup_windows.bat` | Windows 설치 스크립트입니다. 더블클릭으로도 실행하며 Python이 없으면 함께 설치합니다 | Windows 선택: Python이 없을 때 |
| `make.cmd` | make와 bash가 없는 Windows에서 실습 명령을 실행합니다. 설치된 `.venv`의 Python을 사용합니다 | 실습 폴더 맨 위의 cmd에서 `make 대상`으로 실행(macOS와 같은 명령) |

## 1. 실습 자료 받기

```
git clone https://github.com/pslhy/samsung_brownfield
```

zip으로 받았으면 압축을 풉니다. Windows는 **내 계정이 쓸 수 있는 폴더**에 둡니다.

## 2. 설치하기

터미널에서 실습 폴더 맨 위로 들어가 실행합니다. macOS는 `python3 SETUP/setup.py`, Windows(cmd)는 `python SETUP\setup.py`입니다. macOS는 관리자 암호를 묻고, Windows는 관리자 권한 없이 설치합니다. PC의 PATH 같은 환경변수는 바꾸지 않습니다. `make`와 주피터노트북이 실습 폴더의 JDK·Dafny를 알아서 씁니다.

**Windows 선택: 더블클릭.** Python이 없으면 `SETUP\setup_windows.bat`을 더블클릭합니다. `setup.py`와 같은 설치이고 Python도 함께 설치합니다.

- 설치되는 것: JDK 11(`jdk/`), Dafny 4.11(`dafny/`), Python 가상환경과 JupyterLab(`.venv/`)은 실습 폴더 안에, Codex CLI(선택)는 내 계정에 설치됩니다. Windows BAT가 사용할 Python을 찾지 못하면 미리 빌드된 Python ZIP(약 30 MB)을 받아 `python/`에 풉니다. Python 소스 빌드는 하지 않습니다.
- **`.venv`는 설치 스크립트가 자동 생성**합니다. JupyterLab을 설치하면서 Python 셀 실행에 필요한 **ipykernel도 함께 설치**합니다. 별도로 `.venv`를 만들거나 `pip install jupyterlab`을 실행할 필요 없습니다.
- **VS Code와 VS Code 확장은 설치 스크립트에 포함되지 않습니다.** 브라우저로 실습할 때는 필요 없으며, VS Code를 사용할 때만 아래 절차로 설치합니다.
- **Codex를 새로 설치했으면 열어 둔 터미널 앱과 VS Code를 모두 종료하고 다시 실행해야** `codex`를 찾습니다. Windows Terminal은 탭만 새로 여는 대신 앱 전체를 종료하고 다시 엽니다.
- 시간이 몇 분 걸립니다(수백 MB를 내려받습니다). 끝나면 버전이 출력됩니다.
- 배치 파일 실행 시 Python 설치가 너무 오래 걸리면 cmd에 `python`을 입력해 보세요. Microsoft Store가 열리면 안내에 따라 Python을 설치할 수 있습니다. 단, 현재 실습 BAT는 Store의 Python을 재사용하지 않고 실습용 Python을 별도로 설치합니다.
- Codex를 처음 설치했으면 한 번 로그인합니다: `codex login`

## 3. 실습 시작하기

설치를 마친 뒤 **브라우저 또는 VS Code 중 하나**를 선택합니다. 두 방법 모두 설치 단계에서 만든 같은 `.venv`를 사용합니다.

### 브라우저에서 실습하기

1. 새 cmd를 열고 **`make.cmd`가 있는 실습 폴더 맨 위**로 이동합니다. 아래 경로는 예시이므로 실제 받은 폴더로 바꿉니다. 공백·한글이 있는 경로도 따옴표로 감쌉니다.

   ```bat
   cd /d "C:\lab\samsung_brownfield"
   ```

2. 아래 명령을 입력합니다. `.venv`를 수동으로 활성화할 필요 없습니다. macOS도 같은 명령입니다.

   ```bat
   make notebook
   ```

3. 브라우저에 열린 **JupyterLab**의 파일 목록에서 `0_시작하기.ipynb`를 엽니다. 이미 `notebooks` 폴더를 기준으로 열립니다. 브라우저가 자동으로 열리지 않으면 터미널에 표시된 `http://localhost:.../lab?token=...` 등의 주소를 그대로 브라우저 주소창에 붙여 넣습니다.
4. 위에서부터 셀을 선택하고 **Shift+Enter**로 실행합니다.
5. 실습 중에는 서버를 실행한 cmd 창을 열어 둡니다. 종료할 때는 노트북을 저장한 뒤 해당 창에서 **Ctrl+C**를 누르고 종료 확인이 나오면 응답합니다.

Windows에서 `make`를 치면 실습 폴더의 `make.cmd`가 실행됩니다. `make.cmd`는 `.venv\Scripts\python.exe`를 사용하고, `notebook` 대상은 `.venv\Scripts\jupyter.exe lab`을 실행합니다. 설치된 가상환경을 **사용**하는 명령이며, 가상환경을 새로 만드는 명령은 아닙니다. `.venv`가 없다면 먼저 2절의 설치를 완료합니다.

### VS Code에서 실습하기 (선택)

1. VS Code가 없으면 [공식 다운로드 페이지](https://code.visualstudio.com/download)에서 운영체제·CPU에 맞는 버전을 설치합니다. Windows는 **User Installer**로 현재 사용자에게 설치할 수 있습니다. 이미 설치되어 있으면 이 단계는 건너뜁니다.
2. VS Code를 실행하고 왼쪽 **Extensions(확장)** 아이콘을 클릭합니다. 검색창에 `Python`을 입력해 **Microsoft**가 게시한 **Python**(`ms-python.python`) 확장을 설치합니다. 이어서 `Jupyter`를 검색해 **Microsoft**의 **Jupyter**(`ms-toolsai.jupyter`) 확장을 설치합니다. 검색 결과 순서 대신 확장 이름·게시자를 확인합니다.
3. VS Code를 완전히 종료했다가 다시 실행합니다. **File → Open Folder(파일 → 폴더 열기)**에서 `make.cmd`와 `.venv`가 있는 **실습 폴더 전체**를 엽니다.
4. 왼쪽 파일 탐색기에서 `notebooks/0_시작하기.ipynb`를 엽니다.
5. 노트북 오른쪽 위 **Select Kernel(커널 선택)**을 클릭합니다. 필요하면 **Select Another Kernel(다른 커널 선택) → Python Environments(Python 환경)**로 들어가 **이미 만들어진 `.venv`**를 선택합니다. Windows에서는 실행 파일 경로가 `<실습 폴더>\.venv\Scripts\python.exe`, macOS에서는 `<실습 폴더>/.venv/bin/python`인지 확인합니다. 메뉴 이름은 표시 언어·버전에 따라 조금 다를 수 있습니다.
6. 셀을 선택하고 **Shift+Enter**로 실행합니다. VS Code에서는 별도로 `make notebook`을 실행할 필요 없습니다.

`.venv`가 목록에 없다면 실습 폴더 전체를 열었는지와 설치가 성공했는지 확인합니다. 파일은 있는데 감지되지 않으면 명령 팔레트의 **Python: Select Interpreter → Enter interpreter path**에서 위 Python 파일을 지정하고, 노트북의 **Select Kernel**에서도 해당 환경을 다시 선택합니다. 설치가 끝났다면 **Create Environment로 새 `.venv`를 만들 필요 없습니다.**

### 두 방법 공통: 실습 도구 확인

`0_시작하기.ipynb`의 셀을 위에서부터 실행하고 `lab.run("check-env")` 결과를 확인합니다.

- 버전: `openjdk version "11.0.32.1"`, `dafny: 4.11...`, JupyterLab 버전이 표시됩니다.
- 경로: java, javac, dafny가 **모두 실습 폴더 안**이어야 합니다. "실습 폴더 밖"이라고 나오면 보조강사를 부릅니다.

### 터미널에서 직접 (자습)

`docs/자습가이드.md`를 따라 javac, java, dafny를 직접 실행합니다. 설치는 PC의 PATH를 바꾸지 않으므로 **터미널을 열 때마다, 실습 폴더 맨 위에서** 아래 세 줄을 먼저 붙여 넣습니다. PC에 다른 JDK나 Dafny가 있어도 실습 폴더의 것을 쓰게 합니다. `make`만 쓸 때는 필요 없습니다.

Windows (cmd):

```bat
set "JAVA_HOME=%CD%\jdk"
set "DAFNY=%CD%\dafny\dafny.exe"
set "PATH=%CD%\jdk\bin;%CD%\dafny;%PATH%"
```

macOS (bash, zsh):

```sh
export JAVA_HOME="$PWD/jdk/Contents/Home"
export DAFNY="$PWD/dafny/dafny"
export PATH="$JAVA_HOME/bin:$PWD/dafny:$PATH"
```

확인: `javac -version`이 `javac 11.0.32.1`이고, `where javac dafny`(macOS: `command -v javac dafny`)의 첫 줄이 실습 폴더 안이면 됩니다.

## 잘 안될 때

| 증상 | 해 볼 것 |
|---|---|
| `python`을 찾을 수 없다고 나옴 (Windows) | `SETUP\setup_windows.bat`을 더블클릭합니다. Python도 같이 설치합니다 |
| `make`를 찾을 수 없다고 나옴 (Windows) | 프롬프트가 `PS`로 시작하면 `cmd`를 입력해 cmd로 바꿉니다. 그다음 `dir make.cmd`로 현재 폴더에 `make.cmd`가 있는지 확인하고, 없으면 실습 폴더 맨 위로 이동합니다. 계속 실패하면 입력한 명령과 오류 문구 전체를 보조강사에게 전달합니다 |
| `.venv`가 없거나 Jupyter/ipykernel을 찾을 수 없음 | Windows는 `dir .venv\Scripts\python.exe`로 확인합니다. 2절에서 선택한 설치 스크립트를 다시 실행해 성공 여부를 확인합니다. 이미 설치했다면 커널이 해당 `.venv`인지 확인합니다 |
| 브라우저가 자동으로 열리지 않음 | 서버를 실행한 터미널의 Jupyter 접속 주소를 브라우저에 붙여 넣습니다 |
| 버전이나 경로가 예전 것으로 나옴 | 터미널 앱·VS Code를 완전히 종료하고 다시 실행합니다. 노트북은 커널을 다시 시작합니다 |
| 설치가 중간에 멈췄음 | 다시 실행합니다. 이미 된 부분은 건너뜁니다 |
| 하나를 처음부터 다시 설치하고 싶음 | 그 폴더(`jdk/`, `dafny/`, `.venv/`)를 지우고 다시 실행합니다 |
| Codex만 다시 설치·업데이트 | Windows는 **PowerShell**에서 `irm https://chatgpt.com/codex/install.ps1 \| iex`, macOS는 `curl -fsSL https://chatgpt.com/codex/install.sh \| sh`. 또는 `python3 SETUP/setup.py --update-codex`(Windows: `SETUP\setup_windows.bat --update-codex`) |
| Linux | 지원하지 않습니다. `setup.py`를 실행하면 직접 설치할 것을 알려 줍니다 |

셀 실행에 문제가 생겨 사용 중인 Python 환경을 확인해야 할 때는 임시 코드 셀에서 아래를 실행합니다.

```python
import sys
print(sys.executable)
```

Windows는 `<실습 폴더>\.venv\Scripts\python.exe`, macOS는 `<실습 폴더>/.venv/bin/python`이 나와야 합니다. 다른 경로라면 실습용 커널을 다시 선택합니다.

그래도 안 되면 보조강사를 부릅니다.

공식 안내: [Windows용 VS Code 설치](https://code.visualstudio.com/docs/setup/windows), [VS Code의 노트북 커널 선택](https://code.visualstudio.com/docs/datascience/jupyter-kernel-management).
