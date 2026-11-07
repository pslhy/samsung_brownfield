# 실습 준비하기

세 단계면 됩니다. 설치는 한 번만 하면 됩니다.

## 준비 도구 두 가지

| 도구 | 하는 일 | 언제 |
|---|---|---|
| `SETUP/setup.py` | macOS와 Windows 모두 **같은 버전의 도구**로 실습하도록 설치와 환경 설정을 자동으로 합니다. JDK 11, Dafny 4.11, Python 가상환경과 JupyterLab을 실습 폴더 안에 설치하고 PATH 등 환경변수를 설정합니다. Codex CLI(선택)는 내 계정에 설치합니다 | 실습 자료를 받으면 **가장 먼저** 한 번 |
| `make.cmd` | make와 bash가 없는 Windows에서 `make`를 대신합니다. cmd에서 `make 대상 변수=값`을 치면 Makefile과 같은 일을 하는 `SETUP\make_fallback.py`가 돕니다. 그래서 문서와 주피터 노트북의 `make` 명령을 Windows에서도 그대로 씁니다 | Windows에서 실습 폴더 맨 위에서 `make …`를 칠 때 (따로 실행할 필요 없음) |

## 1. 실습 자료 받기

```
git clone https://github.com/pslhy/samsung_brownfield
```

zip으로 받았으면 압축을 풉니다. Windows에서는 `C:\lab`처럼 **모든 계정이 읽을 수 있는 곳**에 둡니다(설치가 관리자 권한으로 돌기 때문입니다).

## 2. 설치하기

| | 이렇게 합니다 |
|---|---|
| Windows | `SETUP\setup_windows.bat`을 **더블클릭**합니다. 또는 cmd에서 실습 폴더로 들어가 `python SETUP\setup.py` |
| macOS | 터미널에서 실습 폴더로 들어가 `python3 SETUP/setup.py` |

- 관리자 권한을 묻습니다. Windows는 UAC 창에서 "예", macOS는 내 암호를 넣습니다.
- 설치되는 것: JDK 11(`jdk/`), Dafny 4.11(`dafny/`), Python 가상환경과 JupyterLab(`.venv/`)은 실습 폴더 안에, Codex CLI(선택)는 내 계정에 설치됩니다. Windows에 Python이 없으면 Python도 설치합니다.
- **설치 전에 열어 둔 터미널과 VS Code는 설치가 끝난 뒤 모두 껐다가 다시 켜야** 새 환경변수가 적용됩니다.
- 시간이 몇 분 걸립니다(수백 MB를 내려받습니다). 끝나면 버전이 출력됩니다.
- Codex를 처음 설치했으면 한 번 로그인합니다: `codex login`

## 3. 실습 시작하기

**설치가 끝나면 터미널과 VS Code를 모두 닫고 새로 엽니다.** 설치가 바꾼 설정(PATH)은 새로 연 창에만 적용됩니다.

### 주피터 노트북으로 (기본)

1. VS Code에 **Python**, **Jupyter** 확장을 설치합니다.
2. `notebooks/0_시작하기.ipynb`를 엽니다.
3. 오른쪽 위 **커널 선택**에서 실습 폴더의 **`.venv`** 를 고릅니다. 다른 Python을 고르면 실습 도구가 안 돌 수 있습니다.
4. 위에서부터 셀을 클릭하고 **Shift+Enter**로 실행합니다. `lab.run("check-env")` 셀에서 아래처럼 나오면 준비가 끝났습니다.
   - 버전: `openjdk version "11.0.32.1"`, `dafny: 4.11...`
   - 경로: java, javac, dafny가 **모두 실습 폴더 안**. "실습 폴더 밖"이라고 나오면 보조강사를 부릅니다.

### 터미널에서 직접 (자습)

`docs/자습가이드.md`를 따라 javac, java, dafny를 직접 실행합니다. **터미널을 열 때마다, 실습 폴더 맨 위에서** 아래 세 줄을 먼저 붙여 넣습니다. PC에 다른 JDK나 Dafny가 있어도 실습 폴더의 것을 쓰게 합니다.

Windows (cmd):
```
set "JAVA_HOME=%CD%\jdk"
set "DAFNY=%CD%\dafny\dafny.exe"
set "PATH=%CD%\jdk\bin;%CD%\dafny;%PATH%"
```

macOS (bash, zsh):
```
export JAVA_HOME="$PWD/jdk/Contents/Home"
export DAFNY="$PWD/dafny/dafny"
export PATH="$JAVA_HOME/bin:$PWD/dafny:$PATH"
```

확인: `javac -version`이 `javac 11.0.32.1`이고, `where javac dafny`(macOS: `command -v javac dafny`)의 첫 줄이 실습 폴더 안이면 됩니다.

## 잘 안될 때

| 증상 | 해 볼 것 |
|---|---|
| `python`을 찾을 수 없다고 나옴 (Windows) | `SETUP\setup_windows.bat`을 더블클릭합니다. Python도 같이 설치합니다 |
| 버전이나 경로가 예전 것으로 나옴 | 터미널·VS Code를 완전히 닫고 새로 엽니다. 주피터 노트북은 커널을 다시 시작합니다 |
| 설치가 중간에 멈췄음 | 다시 실행합니다. 이미 된 부분은 건너뜁니다 |
| 하나를 처음부터 다시 설치하고 싶음 | 그 폴더(`jdk/`, `dafny/`, `.venv/`)를 지우고 다시 실행합니다 |
| Codex만 다시 설치·업데이트 | `python SETUP\setup.py --update-codex` (macOS: `python3 SETUP/setup.py --update-codex`) |
| Linux | 지원하지 않습니다. `setup.py`를 실행하면 직접 설치할 것을 알려 줍니다 |

그래도 안 되면 보조강사를 부릅니다.
