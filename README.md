# HomeHub Brownfield AI Development 실습

삼성 DX 설계 전문가 과정 "Brownfield AI Development: 레거시 분석과 안전한 소프트웨어 진화"의 실습 자료입니다.

## 읽는 순서

1. **이 README**: 실습 소개
2. **[SETUP.md](SETUP.md)**: 실습 준비(설치, 노트북 여는 법). macOS·Windows 공통이며, 수업 전에 마칩니다.
3. **`notebooks/`의 노트북**: 수업 시간의 실습. `0_시작하기`부터 `A` → `E` 순서로 진행합니다.

[docs/자습_GUIDE.md](docs/자습_GUIDE.md)는 수업 시간용이 아닙니다. 수업이 끝난 뒤 따로 하는 **복습·자습용**으로, 노트북이 대신해 주던 명령(javac, java, dafny와 실습 도구)을 macOS나 WSL(Windows의 Linux) 터미널에서 직접 실행하며 같은 실습을 처음부터 다시 따라갑니다.

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

## 폴더

| 폴더 | 내용 |
|---|---|
| `notebooks/` | 실습 노트북 6개와 노트북 도우미 `lab.py` |
| `legacy/` | 실습 대상인 레거시 Java 코드: 소스, 테스트 38개, 작업 부하 파일(가전 메시지 기록) |
| `golden/` | 레거시의 지금 동작을 기록해 둔 출력. 고친 코드의 출력과 비교하는 기준입니다 |
| `scenarios/req1/` | 변경 요청 1 "대기열 늘리기"(평소 8칸, 몰릴 때 최대 32칸). AI가 서로 다르게 만든 패치 두 개(`ai-A`, `ai-B`)가 들어 있습니다. 둘 다 테스트를 모두 통과하지만, A는 대기열이 한 바퀴 돈 뒤 늘리면 이벤트를 잃는 버그가 있습니다. 각 패치에 맞춘 Dafny 모델(`model/`)도 있습니다 |
| `scenarios/req2/` | 변경 요청 2 "대기열 연산 빠르게". AI가 대기열 코드에서 `%` 연산을 없앤 패치(`ai/`, 동작은 그대로)와, 그 코드에 맞춰 메서드 본문만 고친 Dafny 모델(`model/`) |
| `scenarios/a3-sort/` | 실습 A-2 ②: AI가 기기 목록의 정렬 기준을 "종류 → 이름"으로 바꾼 패치. 영향 분석 도구는 영향을 못 찾지만 동작 기록 비교에서는 드러납니다 |
| `scenarios/b1-ai-sample/` | 실습 B-1: AI에게 레거시 대기열의 Dafny 모델과 연결 코드를 만들게 한 결과 예시 |
| `scenarios/rw/` | 실습 E: AI에게 코드 정리 규칙 세 개(`isEmpty()`로 바꾸기, for-each로 바꾸기, 변수 인라인)를 코드 전체에 적용하게 한 결과. 규칙마다 한 폴더, 셋 다 적용한 `All/` |
| `formal/` | 레거시를 옮겨 적은 Dafny 기준 모델(대기열, Dispatcher, 전력)과 Java↔Dafny 대응표 `mapping.tsv` |
| `difftest/` | 차분 테스트 도구: Java와 Dafny 모델(`DiffTest`), 두 빌드끼리(`HubDiff`)에 같은 입력을 넣고 결과를 비교 |
| `rewrite/` | 실습 E의 정리 규칙이 "같은 뜻"이 되는 조건의 Dafny 증명(`RewriteRules.dfy`) |
| `mine/` | 실습 B-1에서 AI가 만든 파일을 두는 곳 |
| `tools/` | 분석 도구(영향 분석, 재검증 범위, 보고서 등). `make`와 노트북이 부르므로 직접 실행할 일은 없습니다(자습_GUIDE에서는 직접 실행) |
| `docs/` | `자습_GUIDE.md`(수업 후 복습·자습), `PROMPTS.md`(AI 프롬프트), `homehub_구조.html`(HomeHub 구조 지도, 0_시작하기에서 띄움), `LAB_GUIDE.md`(읽기용 안내서) |
| `SETUP/`, `make.cmd` | 설치 도구와 Windows용 `make`. `SETUP.md` 참고 |
| `jdk/`, `dafny/`, `.venv/` | 설치가 만드는 JDK 11, Dafny 4.11, Python 가상환경 |
| `out/`, `work/`, `build/` | 실습이 만드는 결과 보고서와 작업 폴더. 모범 답안으로 만든 결과가 미리 들어 있습니다 |

## 터미널 명령 (참고)

노트북에서는 셀이 이 명령들을 대신 실행하므로 따로 칠 필요가 없습니다. 실습 폴더 맨 위의 터미널(Windows는 cmd)에서 치며, macOS·Windows 같은 명령입니다.

```
make check-env     # java, javac, python3, dafny 확인
make test          # 기존 테스트 38개
make verify-all    # 통과해야 하는 Dafny 증명 전부 (1~2분)
make help          # 실습별 명령
make report        # 지금까지 만든 결과 보고서 목록 열기
```

각 `make` 명령은 터미널에 한두 줄 요약만 찍고, 자세한 결과를 브라우저용 보고서(`out/html/*.html`, 목록은 `out/html/index.html`)로 만들어 엽니다. 보고서를 자동으로 열지 않으려면 명령 끝에 붙입니다: `make test HH_OPEN=0`. 보고서는 인터넷 연결 없이 열립니다.

| 실습 | 주요 명령 |
|---|---|
| A | `make trace`, `make ingest "MSG=5\|fridge-2\|TEMP\|38\|60000"`, `make impact V=scenarios/req2/ai`, `make impact V=scenarios/req1/ai-A WHY=ops.Watchdog#check`, `make impact V=scenarios/a3-sort` |
| B | `make difftest-sample`, `make difftest-mine`, `make verify`, `make difftest` |
| C | `make req1` (나눠서: `make req1-tests`, `make req1-verify`, `make req1-difftest`) |
| D | `make reverify REQ=req2`, `make reverify REQ=req1` |
| E | `make rewrite-check R=All` (`R`에는 규칙 하나 `IsEmpty`, `ForEach`, `InlineVariable`도 됨), `make rules` |

`MSG=`처럼 값에 `|`가 들어가면 위처럼 큰따옴표로 감쌉니다(cmd에서도 됨).
