# HomeHub Brownfield AI Development 실습

삼성 DX 설계 전문가 과정 "Brownfield AI Development: 레거시 분석과 안전한 소프트웨어 진화"의 실습 자료입니다.

대상은 이 실습을 위해 만든 가상의 가전 허브 프로그램 **HomeHub**의 레거시 Java 8 코드입니다(30개 타입, 약 1,600줄, 테스트 38개). 이 코드 위에서 "AI가 고친 코드가 기존 동작을 지켰는지 확인하는 방법"을 실습합니다.

| 실습 | 내용 |
|---|---|
| A | 현재 동작 기록, def-use 기반 변경 영향 분석과 그 한계 |
| B | AI로 Dafny 모델 만들기, 계약 읽기, 차분 테스트 |
| C | 테스트를 다 통과한 AI 패치 2개 판단하기 (변경 요청 1: 대기열 늘리기) |
| D | 바뀐 것의 종류(본문 / 계약)로 Dafny 재검증 범위 정하기 (변경 요청 1·2) |
| E | 조건부 정리 규칙을 조건이 깨지는 곳에 적용하면 동작이 바뀌는 것 확인 |

**실습은 `notebooks/`의 Jupyter 노트북으로 진행합니다.** 설명을 읽고 셀을 실행하면(Shift+Enter) 결과 보고서가 바로 아래에 나옵니다. `docs/LAB_GUIDE.md`는 같은 내용을 읽기용으로 정리한 것입니다.

| 노트북 | 내용 |
|---|---|
| `0_시작하기.ipynb` | 실습 소개, HomeHub 구조 지도(`lab.structure()`), 환경 확인 |
| `A_변경영향.ipynb` | 현재 동작 기록, def-use 영향 분석과 그 한계 |
| `B_Dafny모델.ipynb` | AI로 Dafny 모델 만들기, 계약 읽기, 차분 테스트 |
| `C_변경요청1.ipynb` | 테스트를 다 통과한 AI 패치 2개 판단하기 |
| `D_재검증범위.ipynb` | 바뀐 것의 종류로 재검증 범위 줄이기 |
| `E_정리규칙.ipynb` | 정리 규칙을 코드 전체에 적용하고 확인하기 |

**처음이면 먼저 [`SETUP.md`](SETUP.md)대로 실습 환경을 설치합니다.** JDK 11, Dafny 4.11, Python과 Jupyter를 실습 폴더에 한 번에 설치합니다(macOS·Windows).

노트북 여는 방법 (둘 중 하나)
- Jupyter: `pip install jupyterlab` 후 실습 폴더에서 `make notebook`
- VS Code: Python 확장과 Jupyter 확장을 설치하고 `notebooks/0_시작하기.ipynb`를 엽니다. 커널은 Python 3를 고릅니다.

Windows는 `SETUP.md`대로 설치하면 cmd와 노트북에서 같은 `make` 명령을 그대로 씁니다(cmd는 `make.cmd`, 노트북은 `lab.py`가 `SETUP/make_fallback.py`로 실행).

## 빠른 시작

```
make check-env     # java, javac, python3, dafny 확인
make test          # 기존 테스트 38개
make verify-all    # 통과해야 하는 Dafny 증명 전부 (1~2분)
make help          # 실습별 명령
make smoke         # (강사) 모든 실습을 한 번에 실행, 약 3~4분
make report        # 지금까지 만든 결과 보고서 목록 열기
```

각 `make` 명령은 터미널에 한두 줄 요약만 찍고, 자세한 결과를 브라우저용 보고서(`out/html/*.html`, 목록은 `out/html/index.html`)로 만들어 엽니다. 자동으로 열지 않으려면 `HH_OPEN=0`을 붙입니다. 보고서는 인터넷 연결 없이 열립니다.

필요한 것: JDK 11, Python 3, Dafny 4.11, Jupyter(또는 VS Code + Jupyter 확장). 모두 [`SETUP.md`](SETUP.md)대로 설치합니다. macOS는 make(Command Line Tools)도 필요합니다.
선택: Codex CLI(`npm install -g @openai/codex` 후 `codex login`. 노트북에서 AI 프롬프트를 바로 보내고 결과를 받는 `lab.codex`).

## 폴더

| 폴더 | 내용 |
|---|---|
| `legacy/` | 레거시 소스, 테스트, 작업 부하 파일(가전 메시지 기록) |
| `golden/` | 레거시의 현재 동작 기록(특성화 테스트 기준) |
| `tools/` | `impact.py`(변경 영향 보고서), `structure.py`(처리 경로, 공유 상태, 설정값: `make path`, `make state`, `make config`), `structure_page.py`(구조 지도 `docs/homehub_구조.html` 생성), `sdg.py`(프로그램 전체 의존 그래프와 슬라이스), `defuse.py`(메서드 하나의 def-use 의존 그래프), `bytecode.py`(javap로 클래스 읽기), `java/`(메시지 하나의 실행 줄 기록: `make ingest`, `make path`), `reverify.py`(재검증 범위), `report.py`(HTML 보고서), `trace_check.py`, `dafny_run.py` |
| `formal/` | Dafny 기준 모델(대기열, Dispatcher, 전력), Java↔Dafny 대응표 `mapping.tsv` |
| `difftest/` | 차분 테스트: `DiffTest`(Java vs 모델), `QueueModel`(모델 연결 인터페이스), `HubDiff`(빌드 vs 빌드) |
| `scenarios/req1` | 변경 요청 1: 대기열 늘리기 (AI 패치 A·B, 모델) |
| `scenarios/req2` | 변경 요청 2: 대기열 연산 빠르게 (`%` 제거) |
| `scenarios/a3-sort` | 실습 A-2 ②: 영향 분석이 못 찾는 변경 (정렬 기준) |
| `scenarios/b1-ai-sample` | 실습 B-1의 AI 결과 예시(Dafny 모델 + 연결 코드) |
| `scenarios/rw` | 정리 규칙 세 개를 코드 전체에 적용한 결과(실습 E) |
| `rewrite/` | 정리 규칙의 조건 증명(`RewriteRules.dfy`) |
| `notebooks/` | 실습 노트북 6개와 도우미 `lab.py` |
| `mine/` | 실습 B-1에서 AI가 만든 파일을 두는 곳 |
| `docs/` | `homehub_구조.html`(HomeHub 구조 지도: 눌러서 확대하는 C4 그림, 0_시작하기에서 띄움. `tools/structure_page.py`가 만듦), `LAB_GUIDE.md`(읽기용 안내서), `PROMPTS.md`(AI 프롬프트), `INSTRUCTOR_NOTES.md`(강사용: 답, 확인 현황), `img/` |

## 세션과 명령

| 세션 | 실습 | 주요 명령 |
|---|---|---|
| 2 구조·의존성·변경 영향 | A | `make trace`, `make ingest MSG='5|fridge-2|TEMP|38|60000'`, `make impact V=scenarios/req2/ai`, `make impact V=scenarios/req1/ai-A WHY=ops.Watchdog#check`, `make impact V=scenarios/a3-sort` |
| 3 AI 형식화 | B | `make difftest-mine` 또는 `make difftest-sample`, `make verify`, `make difftest` |
| 4 검증된 변경 | C | `make req1` (`req1-tests`, `req1-verify`, `req1-difftest`) |
| 5 검증 비용 줄이기 | D, E | `make reverify REQ=req2|req1`, `make rewrite-check R=IsEmpty|ForEach|InlineVariable|All`, `make rules` |

## 확인 현황

모두 실행해 확인했습니다. 다만 노트북의 Codex 셀(`lab.codex`)은 OpenAI에 접속할 수 없는 환경에서 만들어 실제 호출은 확인하지 못했습니다. 자세한 내용과 수업 전 확인 명령은 `docs/INSTRUCTOR_NOTES.md` 3절에 있습니다.
