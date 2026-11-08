# 실습 준비하기

세 단계면 됩니다. 설치는 한 번만 하면 됩니다. 노트북은 **브라우저 또는 VS Code 중 하나**로 실행합니다.

Windows 명령은 모두 **명령 프롬프트(cmd)** 기준입니다. 시작 메뉴에서 `cmd`를 검색해 엽니다. 프롬프트가 `PS`로 시작하면 PowerShell이니 `cmd`를 입력하고 Enter를 눌러 바꿉니다(VS Code 터미널도 같음).

## 1. 실습 자료 받기

받은 zip 파일의 압축을 풉니다. Windows는 zip을 마우스 오른쪽 버튼으로 눌러 **모두 압축 풀기**를 고릅니다(zip 안에서 바로 실행하지 않습니다). **내 계정이 쓸 수 있는 폴더**(예: `C:\lab`, 바탕 화면)에 둡니다.

## 2. 설치하기

터미널을 열고 실습 폴더 맨 위로 들어갑니다. 아래 경로는 예시이므로 실제 폴더로 바꿉니다. 공백·한글이 있는 경로는 따옴표로 감쌉니다.

| | 터미널 열기 | 실습 폴더로 들어가기 |
|---|---|---|
| Windows | 시작 메뉴에서 `cmd` | `cd /d "C:\lab\samsung_brownfield"` |
| macOS | Spotlight(⌘+Space)에서 "터미널" | `cd ~/Desktop/samsung_brownfield` |

그다음 설치를 실행합니다.

| | 명령 |
|---|---|
| Windows | `python SETUP\setup.py` |
| macOS | `python3 SETUP/setup.py` |

**Windows에 Python이 없으면:** 위 명령 대신 `SETUP\setup_windows.bat`을 더블클릭합니다. `setup.py`와 같은 설치이고 Python도 함께 설치합니다.

- 설치되는 것: 실습 폴더 안에 JDK 11(`jdk/`), Dafny 4.11(`dafny/`), Python 가상환경과 JupyterLab(`.venv/`)이 생깁니다. Windows에 쓸 Python이 없으면 Python(`python/`)도 받습니다.
- **PC 설정은 바꾸지 않습니다.** PATH 같은 환경변수를 바꾸지 않고, `make`와 Jupyter 노트북이 실습 폴더의 JDK·Dafny를 알아서 씁니다.
- **관리자 권한:** Windows는 필요 없습니다. macOS는 관리자 암호를 묻습니다(Python을 새로 설치해야 할 때 macOS 설치 프로그램이 관리자 권한을 씁니다). 관리자 권한이 없는 PC면 강사에게 알립니다.
- **Codex CLI:** 노트북의 AI 셀(`lab.codex`)에서 쓰는 OpenAI의 명령줄 도구입니다. 설치가 내 계정에 자동으로 설치하고, 쓰려면 ChatGPT 계정으로 한 번 로그인합니다(`codex login`). 쓰지 않으려면 설치 명령 끝에 `--skip-codex`를 붙입니다. Codex 없이도 실습은 끝까지 할 수 있습니다.
- **Codex를 새로 설치했으면 열어 둔 터미널(cmd 창)과 VS Code를 모두 닫고 새로 열어야** `codex`를 찾습니다.
- 몇 분 걸립니다(수백 MB를 내려받습니다). 끝나면 설치된 버전이 출력됩니다.
- **VS Code는 설치하지 않습니다.** 브라우저로 실습할 때는 필요 없고, VS Code를 쓸 때만 아래 절차로 설치합니다.

## 3. 실습 시작하기

설치를 마친 뒤 **브라우저 또는 VS Code 중 하나**를 선택합니다. 두 방법 모두 설치가 만든 같은 `.venv`를 씁니다.

### 브라우저에서 실습하기

1. 2절처럼 터미널을 열고 실습 폴더 맨 위로 들어갑니다.
2. 아래 명령을 입력합니다. macOS·Windows 같은 명령이고, `.venv`를 따로 활성화할 필요 없습니다(Windows에서는 실습 폴더의 `make.cmd`가 실행됩니다).

   ```
   make notebook
   ```

3. 브라우저에 열린 **JupyterLab**의 파일 목록에서 `0_시작하기.ipynb`를 엽니다. 브라우저가 자동으로 열리지 않으면 터미널에 표시된 `http://localhost:.../lab?token=...` 주소를 브라우저 주소창에 붙여 넣습니다.
4. 위에서부터 셀을 선택하고 **Shift+Enter**로 실행합니다.
5. 실습 중에는 서버를 실행한 터미널 창을 열어 둡니다. 끝낼 때는 노트북을 저장한 뒤 그 창에서 **Ctrl+C**를 누르고, 종료 확인이 나오면 응답합니다.

### VS Code에서 실습하기 (선택)

1. VS Code가 없으면 [공식 다운로드 페이지](https://code.visualstudio.com/download)에서 운영체제·CPU에 맞는 버전을 설치합니다. Windows는 **User Installer**로 현재 사용자에게 설치할 수 있습니다.
2. VS Code 왼쪽의 **Extensions(확장)** 아이콘을 누르고, **Microsoft**가 게시한 **Python**(`ms-python.python`)과 **Jupyter**(`ms-toolsai.jupyter`) 확장을 설치합니다. 검색 결과 순서 대신 확장 이름·게시자를 확인합니다.
3. VS Code를 완전히 종료했다가 다시 실행합니다. **File → Open Folder(파일 → 폴더 열기)**에서 `.venv`가 있는 **실습 폴더 전체**를 엽니다.
4. 왼쪽 파일 탐색기에서 `notebooks/0_시작하기.ipynb`를 엽니다.
5. 노트북 오른쪽 위 **Select Kernel(커널 선택)**을 누릅니다. 필요하면 **Select Another Kernel(다른 커널 선택) → Python Environments(Python 환경)**에서 **이미 만들어진 `.venv`**를 고릅니다. 실행 파일 경로가 Windows는 `<실습 폴더>\.venv\Scripts\python.exe`, macOS는 `<실습 폴더>/.venv/bin/python`인지 확인합니다. 메뉴 이름은 표시 언어·버전에 따라 조금 다를 수 있습니다.
6. 셀을 선택하고 **Shift+Enter**로 실행합니다. VS Code에서는 `make notebook`을 실행할 필요 없습니다.

`.venv`가 목록에 없으면 실습 폴더 전체를 열었는지와 설치가 성공했는지 확인합니다. 파일은 있는데 감지되지 않으면 명령 팔레트의 **Python: Select Interpreter → Enter interpreter path**에서 위 Python 파일을 지정하고, 노트북의 **Select Kernel**에서도 그 환경을 다시 고릅니다. **Create Environment로 새 `.venv`를 만들 필요는 없습니다.**

### 두 방법 공통: 실습 도구 확인

`0_시작하기.ipynb`의 셀을 위에서부터 실행하고 `lab.run("check-env")` 결과를 확인합니다.

- 버전: `openjdk version "11.0.32.1"`, `dafny: 4.11...`, JupyterLab 버전이 표시됩니다.
- 경로: java, javac, dafny가 **모두 실습 폴더 안**이어야 합니다. "실습 폴더 밖"이라고 나오면 강사에게 알립니다.

### 수업 후 복습·자습

`docs/자습_GUIDE.md`를 macOS나 WSL(Windows의 Linux) 터미널에서 따라 합니다. 준비는 자습_GUIDE의 "필요한 것"에 있습니다.

## 잘 안될 때

| 증상 | 해 볼 것 |
|---|---|
| `python`을 찾을 수 없다고 나옴 (Windows) | `SETUP\setup_windows.bat`을 더블클릭합니다. Python도 같이 설치합니다 |
| `make`를 찾을 수 없다고 나옴 (Windows) | 프롬프트가 `PS`로 시작하면 `cmd`를 입력해 cmd로 바꿉니다. 그다음 `dir make.cmd`로 현재 폴더에 `make.cmd`가 있는지 확인하고, 없으면 실습 폴더 맨 위로 이동합니다 |
| `.venv`가 없거나 Jupyter/ipykernel을 찾을 수 없음 | 2절의 설치를 다시 실행해 성공하는지 봅니다. 이미 설치했다면 커널이 실습 폴더의 `.venv`인지 확인합니다 |
| 브라우저가 자동으로 열리지 않음 | 서버를 실행한 터미널의 Jupyter 접속 주소를 브라우저에 붙여 넣습니다 |
| 버전이나 경로가 예전 것으로 나옴 | 터미널과 VS Code를 모두 닫고 다시 엽니다. 노트북은 커널을 다시 시작합니다 |
| 설치가 중간에 멈췄음 | 다시 실행합니다. 이미 된 부분은 건너뜁니다 |
| 하나를 처음부터 다시 설치하고 싶음 | 그 폴더(`jdk/`, `dafny/`, `.venv/`)를 지우고 다시 실행합니다 |
| Codex만 다시 설치·업데이트 | Windows는 **PowerShell**에서 `irm https://chatgpt.com/codex/install.ps1 \| iex`, macOS는 `curl -fsSL https://chatgpt.com/codex/install.sh \| sh`. 또는 `python3 SETUP/setup.py --update-codex`(Windows: `SETUP\setup_windows.bat --update-codex`) |
| Linux | 설치 도구는 지원하지 않습니다. `setup.py`를 실행하면 직접 설치할 것을 알려 줍니다 |

셀 실행에 문제가 생겨 사용 중인 Python 환경을 확인해야 할 때는 임시 코드 셀에서 아래를 실행합니다.

```python
import sys
print(sys.executable)
```

Windows는 `<실습 폴더>\.venv\Scripts\python.exe`, macOS는 `<실습 폴더>/.venv/bin/python`이 나와야 합니다. 다른 경로라면 실습용 커널을 다시 고릅니다.

그래도 안 되면 입력한 명령과 오류 문구 전체를 강사에게 전달합니다.

공식 안내: [Windows용 VS Code 설치](https://code.visualstudio.com/docs/setup/windows), [VS Code의 노트북 커널 선택](https://code.visualstudio.com/docs/datascience/jupyter-kernel-management).
