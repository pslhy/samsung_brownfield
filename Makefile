# HomeHub Brownfield AI Development lab
# Requirements: bash, make, JDK 11+ (javac, javap, jdeps), python3, Dafny 4.11 (dafny on PATH).
# Optional: jupyter (notebooks), codex CLI (lab.codex in the notebooks).
# Run `make help` for the target list.

SHELL   := /bin/bash
# the lab's own JDK and Dafny (SETUP/) first on PATH: SETUP changes no PATH of the PC (make_fallback.py the same)
export PATH := $(CURDIR)/jdk/Contents/Home/bin:$(CURDIR)/dafny:$(PATH)
JAVA    ?= java
JAVAC   ?= javac
PY      ?= python3
DAFNY   ?= dafny

LEGACY  := legacy
OUT     := out
BUILD   := build
WORK    := work
JFLAGS  := -nowarn -Xlint:-options -encoding UTF-8

LEGACY_CP   := $(LEGACY)/build/classes
LEGACY_TCP  := $(LEGACY)/build/test-classes
FORMAL      := formal/Types.dfy formal/RingQueue.dfy formal/Dispatcher.dfy formal/PowerBudget.dfy
WORKLOADS   := normal_day burst fridge_firmware

# A "variant" is a copy of legacy/ with a directory copied on top of it: an overlay from
# scenarios/..., or your own edited copy of the project (e.g. V=mywork after `cp -r legacy mywork`).
V      ?=
VNAME   = $(subst /,-,$(patsubst scenarios/%,%,$(V)))
VDIR    = $(WORK)/$(VNAME)

.PHONY: help check-env build test trace golden clean verify-all \
        variant variant-test impact ingest path state config \
        verify model difftest difftest-mine difftest-sample dispatcher-sample \
        req1 req1-tests req1-verify req1-difftest \
        reverify req1-tests-run req1-verify-run req1-difftest-run show report \
        rewrite-check rules smoke notebook

help:
	@echo "준비    : make check-env | build | test | trace"
	@echo "구조    : make path MSG='4|fridge-2|TEMP|14|180000|unit=C' | state | config KEY=temp.highCelsius (참고용)"
	@echo "실습 A  : make trace | ingest MSG='5|fridge-2|TEMP|38|60000' | impact V=scenarios/req2/ai [WHY=클래스#메서드]"
	@echo "          make impact V=scenarios/req1/ai-A WHY=ops.Watchdog#check | impact V=scenarios/a3-sort"
	@echo "          make impact V=scenarios/req2/ai SCOPE=legacy/src/main/java/com/dxlab/homehub/queue/RingEventQueue.java"
	@echo "실습 B  : make verify | model | difftest"
	@echo "          make difftest-mine DFY=mine/RingEventQueue.dfy ADAPTER=mine/MyQueueAdapter.java"
	@echo "          make difftest-sample   (AI 결과 예시로 같은 과정)"
	@echo "          make dispatcher-sample (예시 대기열 위의 Dispatcher 모델 검증)"
	@echo "실습 C  : make req1   (= req1-tests, req1-verify, req1-difftest)"
	@echo "실습 D  : make reverify REQ=req2|req1"
	@echo "실습 E  : make rewrite-check R=IsEmpty|ForEach|InlineVariable|All | make rules"
	@echo "노트북  : make notebook (Jupyter로 실습 노트북 열기, notebooks/0_시작하기.ipynb부터)"
	@echo "보고서  : make report (목록 열기) | make show V=<폴더> (바뀐 코드) | HH_OPEN=0 이면 자동으로 열지 않음"
	@echo "강사    : make verify-all (통과해야 하는 Dafny 증명 전부) | make smoke (전체)"

check-env: ENV_OS = $(shell uname -s)
check-env: ENV_APT = $(shell command -v apt-get 2>/dev/null)
check-env:
	@echo "java : $$($(JAVA) -version 2>&1 | head -1)"; $(JAVA) -version >/dev/null 2>&1 || echo '  $(if $(filter Darwin,$(ENV_OS)),brew install --cask temurin@21,$(if $(ENV_APT),sudo apt install openjdk-21-jdk,배포판의 패키지 관리자로 JDK 11 이상 설치))'
	@echo "javac: $$($(JAVAC) -version 2>&1)"; $(JAVAC) -version >/dev/null 2>&1 || echo '  $(if $(filter Darwin,$(ENV_OS)),brew install --cask temurin@21,$(if $(ENV_APT),sudo apt install openjdk-21-jdk,배포판의 패키지 관리자로 JDK 11 이상 설치))'
	@echo "py   : $$($(PY) --version 2>&1)"; $(PY) --version >/dev/null 2>&1 || echo '  $(if $(filter Darwin,$(ENV_OS)),brew install python3,$(if $(ENV_APT),sudo apt install python3 python3-pip python3-venv,배포판의 패키지 관리자로 Python 3·pip·venv 설치))'
	@echo "dafny: $$($(DAFNY) --version 2>&1 | head -1)"; $(DAFNY) --version >/dev/null 2>&1 || echo '  https://github.com/dafny-lang/dafny/releases/tag/v4.11.0 에서 $(if $(filter Darwin,$(ENV_OS)),Mac용 ZIP 설치 후 해당 폴더에서 ./allow_on_mac.sh 실행,Linux용 ZIP 설치)'
	@$(DAFNY) --version >/dev/null 2>&1 || { echo '  압축을 푼 뒤 dafny 실행 파일이 있는 디렉터리로 이동해서 실행하세요:'; echo '    export PATH="$$PWD:$$PATH"'; echo '  새 터미널에서도 유지하려면 현재 디렉터리의 절대경로(pwd 출력)를 $(if $(filter Darwin,$(ENV_OS)),~/.zshrc,Bash는 ~/.bashrc · Zsh는 ~/.zshrc)에 export PATH="절대경로:$$PATH" 형태로 추가하세요.'; echo '  확인: dafny --version'; }
	@echo "jupyter: $$(jupyter --version 2>/dev/null | grep -m1 -i 'jupyterlab\|notebook' || echo '없음 (python3 -m venv .venv 후 source .venv/bin/activate 후 python -m pip install jupyterlab ipykernel, 또는 VS Code의 Python·Jupyter 확장)')"
	@echo "codex: $$(codex --version 2>/dev/null || echo '없음 (선택: $(if $(filter Darwin,$(ENV_OS)),brew install --cask codex,Node.js·npm 설치 후 npm install -g @openai/codex), 이후 codex login)') $$(command -v codex >/dev/null && codex login status 2>&1 | head -1 | sed 's/^/· /' 2>/dev/null)"

# ---------------------------------------------------------------- build / test

$(LEGACY_CP)/.stamp: $(shell find $(LEGACY)/src -name '*.java')
	@rm -rf $(LEGACY)/build && mkdir -p $(LEGACY_CP) $(LEGACY_TCP)
	@$(JAVAC) $(JFLAGS) --release 8 -d $(LEGACY_CP) $$(find $(LEGACY)/src/main/java -name '*.java')
	@$(JAVAC) $(JFLAGS) --release 8 -cp $(LEGACY_CP) -d $(LEGACY_TCP) $$(find $(LEGACY)/src/test/java -name '*.java')
	@touch $@
	@echo "built $(LEGACY)"

# A-1 compares bytecode, so a direct req2/ai impact run builds both sides with the same javac.
REBUILD_LEGACY ?= $(if $(and $(filter impact,$(MAKECMDGOALS)),$(filter scenarios/req2/ai,$(V))),1,0)
ifeq ($(REBUILD_LEGACY),1)
.PHONY: force-legacy-build
$(LEGACY_CP)/.stamp: force-legacy-build
endif

build: $(LEGACY_CP)/.stamp

RAW    := $(OUT)/raw
REPORT  = $(PY) tools/report.py
DRUN    = DAFNY=$(DAFNY) $(PY) tools/dafny_run.py
# HH_OPEN=1 opens each report in the browser (open / xdg-open / wslview); HH_OPEN=0 to turn off
export HH_OPEN ?= 1

test: build
	@mkdir -p $(RAW); $(JAVA) -cp $(LEGACY_CP):$(LEGACY_TCP) com.dxlab.homehub.testkit.TestRunner > $(RAW)/test.txt; st=$$?; tail -1 $(RAW)/test.txt; \
	$(REPORT) --out test --title "기존 테스트" --lead "레거시 코드의 테스트 38개를 실행한 결과입니다." \
	  --command "make test" --sec tests "테스트" $(RAW)/test.txt pass; exit $$st

# characterization tests: compare observable traces with the golden files (TRACE_CP = another build)
trace: build
	@mkdir -p $(RAW); $(PY) tools/trace_check.py --cp $(or $(TRACE_CP),$(LEGACY_CP)) --json $(RAW)/trace.json $(WORKLOADS); st=$$?; \
	$(REPORT) --out $(or $(TRACE_NAME),trace) --title "동작 기록 비교" \
	  --lead "입력 파일(legacy/workloads)을 넣고 한 줄마다 나온 상태를, 미리 저장해 둔 기록(golden)과 비교합니다. 다른 줄은 다른 낱말에 표시합니다." \
	  --command "make trace$(if $(TRACE_CP), TRACE_CP=$(TRACE_CP))" --sec trace "기록 비교 ($(or $(TRACE_CP),legacy))" $(RAW)/trace.json -; exit $$st

golden: build
	@mkdir -p golden; for w in $(WORKLOADS); do \
	  $(JAVA) -cp $(LEGACY_CP) com.dxlab.homehub.app.HubMain $(LEGACY)/workloads/$$w.txt > golden/$$w.trace; done
	@echo "golden traces regenerated from legacy"

# ---------------------------------------------------------------- session 2: change impact (def-use)

variant:
	@[ -n "$(V)" ] || { echo "usage: make variant V=scenarios/<...>"; exit 2; }
	@rm -rf $(VDIR) && mkdir -p $(WORK) && cp -r $(LEGACY) $(VDIR) && cp -r $(V)/. $(VDIR)/
	@rm -rf $(VDIR)/build $(VDIR)/target && mkdir -p $(VDIR)/build/classes $(VDIR)/build/test-classes
	@$(JAVAC) $(JFLAGS) --release 8 -d $(VDIR)/build/classes $$(find $(VDIR)/src/main/java -name '*.java')
	@$(JAVAC) $(JFLAGS) --release 8 -cp $(VDIR)/build/classes -d $(VDIR)/build/test-classes $$(find $(VDIR)/src/test/java -name '*.java')
	@echo "built variant $(VDIR)  (diff: diff -ru $(LEGACY)/src $(VDIR)/src)"

variant-test: variant
	@mkdir -p $(RAW); $(JAVA) -cp $(VDIR)/build/classes:$(VDIR)/build/test-classes com.dxlab.homehub.testkit.TestRunner > $(RAW)/test-$(VNAME).txt; st=$$?; \
	tail -1 $(RAW)/test-$(VNAME).txt; [ "$(NOREPORT)" = 1 ] || $(REPORT) --out test-$(VNAME) --title "테스트: $(V)" \
	  --lead "$(V)를 레거시에 덮어쓴 빌드의 테스트 결과입니다." --command "make variant-test V=$(V)" \
	  --sec srcdiff "바뀐 코드" "$(LEGACY)/src|$(VDIR)/src" - --sec tests "테스트" $(RAW)/test-$(VNAME).txt -; exit $$st

# one message through a fresh hub: result, state change, executed source lines (JDK debugger interface)
# make ingest MSG='5|fridge-2|TEMP|38|60000'   (or a file of setup lines + the message: INGEST_IN=...)
INGEST_IN ?= $(RAW)/ingest-input.txt
ingest: build
	@mkdir -p $(RAW) $(BUILD)/tools; $(JAVAC) $(JFLAGS) -d $(BUILD)/tools -cp $(LEGACY_CP) tools/java/IngestOne.java tools/java/LineTracer.java
	@$(if $(MSG),printf '%s\n' '$(MSG)' > $(INGEST_IN);) \
	$(JAVA) -cp $(BUILD)/tools LineTracer $(LEGACY_CP):$(BUILD)/tools $(INGEST_IN) > $(RAW)/ingest.json && \
	$(REPORT) --out ingest --title "메시지 하나 넣어 보기" --lead "새로 시작한 허브에 메시지 한 줄을 넣고, 결과와 바뀐 상태, 실제로 실행된 코드 줄을 보여 줍니다." \
	  --command "make ingest MSG='$$(tail -1 $(INGEST_IN))'" --sec ingest "처리 결과" $(RAW)/ingest.json -

# the structure of the legacy code (reference; the lab uses docs/homehub_구조.html)
# make path MSG='...'  one message handled to the end (the queue drained): call graph vs the methods that ran
#                      (or a file of setup lines + the message: PATH_IN=...)
PATH_IN ?= $(RAW)/path-input.txt
path: build
	@mkdir -p $(RAW) $(BUILD)/tools; $(JAVAC) $(JFLAGS) -d $(BUILD)/tools -cp $(LEGACY_CP) tools/java/IngestOne.java tools/java/LineTracer.java
	@$(if $(MSG),printf '%s\n' '$(MSG)' > $(PATH_IN);) \
	$(JAVA) -cp $(BUILD)/tools LineTracer $(LEGACY_CP):$(BUILD)/tools $(PATH_IN) drain > $(RAW)/path.json && \
	$(PY) tools/structure.py path --classes $(LEGACY_CP) --src $(LEGACY)/src/main/java --trace $(RAW)/path.json --html path \
	  --command "make path MSG='$$(tail -1 $(PATH_IN))'"

# who changes and who reads each piece of shared state
state: build
	@$(PY) tools/structure.py state --classes $(LEGACY_CP) --src $(LEGACY)/src/main/java --html state --command "make state"

# make config KEY=temp.highCelsius   where a configuration value may flow
config: build
	@[ -n "$(KEY)" ] || { echo "usage: make config KEY=temp.highCelsius"; exit 2; }
	@$(PY) tools/structure.py config --classes $(LEGACY_CP) --src $(LEGACY)/src/main/java --key $(KEY) --html config-$(KEY) --command "make config KEY=$(KEY)"

# what a scenario folder changes, as a side-by-side diff page
show: variant
	@$(REPORT) --out show-$(VNAME) --title "바뀐 코드: $(V)" --lead "$(V)가 레거시에서 바꾼 파일입니다." \
	  --command "make show V=$(V)" --sec srcdiff "바뀐 코드" "$(LEGACY)/src|$(VDIR)/src" -

# WHY=클래스#메서드 : only the reasons for that method (impact-<V>-why.html)
# SCOPE=소스 파일    : analyze only that file, as if nothing else existed (impact-<V>-scope.html); e.g. to compare
#                      with an AI that was given only that file
ISUF = $(if $(SCOPE),-scope)$(if $(WHY),-why)
impact: build variant
	@mkdir -p $(OUT)
	@$(PY) tools/impact.py --base $(LEGACY_CP) $(LEGACY_TCP) --base-src $(LEGACY)/src/main/java $(LEGACY)/src/test/java \
	   --changed $(VDIR)/build/classes $(VDIR)/build/test-classes --changed-src $(VDIR)/src/main/java $(VDIR)/src/test/java \
	   --mapping formal/mapping.tsv --json $(OUT)/impact-$(VNAME).json --html impact-$(VNAME)$(ISUF) --title-v "$(V)" \
	   $(if $(WHY),--why $(WHY)) $(if $(SCOPE),--scope $(SCOPE)) > $(OUT)/impact-$(VNAME)$(ISUF).md

# ---------------------------------------------------------------- session 3: formalization, difftest

verify:
	@mkdir -p $(RAW); $(DRUN) --json $(RAW)/verify.json formal/dfyconfig.toml; st=$$?; \
	$(REPORT) --out verify --title "Dafny 기준 모델 검증" --lead "formal/의 대기열, Dispatcher, 전력 모델을 검증합니다." \
	  --command "make verify" --sec dafny "formal/ 전체" $(RAW)/verify.json pass; exit $$st

$(BUILD)/model/homehub_model.jar: $(FORMAL)
	@mkdir -p $(BUILD)/model
	@$(DAFNY) build -t java formal/dfyconfig.toml -o $(BUILD)/model/homehub_model > /dev/null
	@echo "Dafny 모델을 Java로 컴파일: $@"

model: $(BUILD)/model/homehub_model.jar

$(BUILD)/difftest/.stamp: build $(BUILD)/model/homehub_model.jar $(wildcard difftest/src/difftest/*.java)
	@mkdir -p $(BUILD)/difftest
	@$(JAVAC) $(JFLAGS) --release 11 -cp $(LEGACY_CP):$(BUILD)/model/homehub_model.jar -d $(BUILD)/difftest difftest/src/difftest/*.java
	@touch $@

DT_PAGE_LEAD = 같은 무작위 연산을 Java 클래스와 Java로 컴파일한 Dafny 모델에 넣고, 매 연산 뒤의 결과와 상태를 비교합니다. 다르면 같은 차이가 나는 가장 짧은 연산열을 보여 줍니다.
difftest: $(BUILD)/difftest/.stamp
	@mkdir -p $(RAW); $(JAVA) -cp $(or $(JAVA_CP),$(LEGACY_CP)):$(or $(MODEL_JAR),$(BUILD)/model/homehub_model.jar):$(BUILD)/difftest difftest.DiffTest $(or $(WHAT),all) --json $(RAW)/difftest.json $(DT_ARGS); st=$$?; \
	$(REPORT) --out difftest --title "차분 테스트: Java와 Dafny 모델" --lead "$(DT_PAGE_LEAD)" \
	  --command "make difftest$(if $(JAVA_CP), JAVA_CP=$(JAVA_CP))$(if $(WHAT), WHAT=$(WHAT))" \
	  --sec difftest "$(or $(JAVA_CP),legacy) vs 모델" $(RAW)/difftest.json -; exit $$st

# Your own (AI-written) Dafny model of RingEventQueue + its adapter (docs/PROMPTS.md P-1, P-1b).
# DFY may list several files. The adapter must be class difftest.MyQueueAdapter.
DFY     ?= mine/RingEventQueue.dfy
ADAPTER ?= mine/MyQueueAdapter.java
difftest-mine: $(BUILD)/difftest/.stamp
	@for f in $(DFY) $(ADAPTER); do [ -f $$f ] || { echo "아직 없습니다: $$f  (노트북의 lab.codex 셀을 실행하거나 AI 결과를 붙여 넣으세요)"; exit 2; }; \
	  if grep -q "여기에 붙여 넣기" $$f; then echo "아직 AI 결과를 붙여 넣지 않았습니다: $$f"; exit 2; fi; done
	@rm -rf $(BUILD)/mine $(RAW)/mine-* && mkdir -p $(BUILD)/mine/classes $(RAW)
	@$(DRUN) --json $(RAW)/mine-verify.json $(DFY); \
	if $(DAFNY) build -t java --no-verify --allow-warnings $(DFY) -o $(BUILD)/mine/mymodel > $(RAW)/mine-build.txt 2>&1 && \
	   $(JAVAC) $(JFLAGS) --release 11 -cp $(BUILD)/mine/mymodel.jar:$(BUILD)/difftest -d $(BUILD)/mine/classes $(ADAPTER) >> $(RAW)/mine-build.txt 2>&1; then \
	  echo "연결 코드 컴파일: 성공"; \
	  $(JAVA) -Dqueue.adapter=difftest.MyQueueAdapter -cp $(BUILD)/mine/mymodel.jar:$(BUILD)/mine/classes:$(LEGACY_CP):$(BUILD)/difftest difftest.DiffTest queue --json $(RAW)/mine-difftest.json $(DT_ARGS); \
	else echo "Java 컴파일 또는 연결 코드 컴파일 실패: 보고서를 보세요"; fi; \
	$(REPORT) --out difftest-mine --title "내 Dafny 모델 확인" \
	  --lead "AI가 만든 Dafny 모델($(DFY))을 검증하고, 연결 코드($(ADAPTER))로 레거시 RingEventQueue와 차분 테스트합니다. 계약은 실습 안내서 B-1의 확인 목록으로 직접 읽어 판단합니다." \
	  --command "make difftest-mine DFY=$(DFY) ADAPTER=$(ADAPTER)" \
	  --sec dafny "1. Dafny 검증" $(RAW)/mine-verify.json pass \
	  --sec text "2. Java로 컴파일, 연결 코드 컴파일 (메시지)" $(RAW)/mine-build.txt - \
	  --sec difftest "3. 차분 테스트: 레거시 RingEventQueue vs 내 모델" $(RAW)/mine-difftest.json $(or $(DT_EXPECT),pass)

# the same with the example AI output in scenarios/b1-ai-sample/
difftest-sample:
	@$(MAKE) -s --no-print-directory difftest-mine DFY=scenarios/b1-ai-sample/RingEventQueue.dfy ADAPTER=scenarios/b1-ai-sample/MyQueueAdapter.java

# B-2: the Dispatcher model written on top of the example queue model (same names: elems, Event, buf.Length)
dispatcher-sample:
	@mkdir -p $(RAW); $(DRUN) --json $(RAW)/dispatcher-sample.json scenarios/b1-ai-sample/RingEventQueue.dfy scenarios/b1-ai-sample/Dispatcher.dfy; st=$$?; \
	$(REPORT) --out dispatcher-sample --title "Dispatcher 모델 검증" --lead "예시 대기열 모델(RingEventQueue.dfy)을 가져다 쓰는 Dispatcher 모델(Dispatcher.dfy)을 함께 검증합니다." \
	  --command "make dispatcher-sample" --sec dafny "scenarios/b1-ai-sample/" $(RAW)/dispatcher-sample.json pass; exit $$st

# ---------------------------------------------------------------- session 4: REQ-1 verified evolution

REQ1 := scenarios/req1
REQ1_MODEL_JAR := $(BUILD)/model-req1/homehub_model.jar

$(REQ1_MODEL_JAR): $(REQ1)/model/RingQueue.dfy $(REQ1)/model/Dispatcher.dfy
	@mkdir -p $(BUILD)/model-req1
	@$(DAFNY) build -t java formal/Types.dfy $(REQ1)/model/RingQueue.dfy $(REQ1)/model/Dispatcher.dfy formal/PowerBudget.dfy -o $(BUILD)/model-req1/homehub_model > /dev/null

REQ1_CODE = --sec srcdiff "패치 A가 바꾼 코드" "$(LEGACY)/src|$(WORK)/req1-ai-A/src" - \
	  --sec srcdiff "패치 B가 바꾼 코드" "$(LEGACY)/src|$(WORK)/req1-ai-B/src" -
REQ1_TESTS = --sec tests "테스트: 패치 A" $(RAW)/test-req1-ai-A.txt pass \
	  --sec tests "테스트: 패치 B" $(RAW)/test-req1-ai-B.txt pass
REQ1_VERIFY = --sec dafny "Dafny: 패치 A의 대기열 모델" $(RAW)/req1-v1.json fail \
	  --sec dafny "Dafny: 패치 B의 대기열 + Dispatcher 모델" $(RAW)/req1-v3.json pass
REQ1_DIFF = --sec difftest "차분 테스트: 패치 A vs 변경 요청 1 모델" $(RAW)/req1-dt-A.json fail \
	  --sec difftest "차분 테스트: 패치 B vs 변경 요청 1 모델" $(RAW)/req1-dt-B.json pass \
	  --sec difftest "차분 테스트: 레거시 vs 변경 요청 1 모델 (승인된 동작 변화)" $(RAW)/req1-dt-legacy.json fail

req1-tests-run:
	@for v in ai-A ai-B; do printf "%-6s " $$v; $(MAKE) -s --no-print-directory variant-test V=$(REQ1)/$$v NOREPORT=1 2>/dev/null | tail -1; done

req1-verify-run:
	@mkdir -p $(RAW)
	-@$(DRUN) --json $(RAW)/req1-v1.json formal/Types.dfy $(REQ1)/model/RingQueue_A.dfy
	-@$(DRUN) --json $(RAW)/req1-v3.json formal/Types.dfy $(REQ1)/model/RingQueue.dfy $(REQ1)/model/Dispatcher.dfy formal/PowerBudget.dfy

req1-difftest-run: $(BUILD)/difftest/.stamp $(REQ1_MODEL_JAR)
	@mkdir -p $(RAW); for v in ai-A ai-B; do $(MAKE) -s variant V=$(REQ1)/$$v >/dev/null; done
	-@$(JAVA) -cp $(WORK)/req1-ai-A/build/classes:$(REQ1_MODEL_JAR):$(BUILD)/difftest difftest.DiffTest queue --json $(RAW)/req1-dt-A.json | head -1
	-@$(JAVA) -cp $(WORK)/req1-ai-B/build/classes:$(REQ1_MODEL_JAR):$(BUILD)/difftest difftest.DiffTest all --json $(RAW)/req1-dt-B.json
	-@$(JAVA) -cp $(LEGACY_CP):$(REQ1_MODEL_JAR):$(BUILD)/difftest difftest.DiffTest queue --json $(RAW)/req1-dt-legacy.json | head -1

REQ1_LEAD = 변경 요청 1(대기열 늘리기)에 대한 AI 패치 A·B를 테스트, Dafny, 차분 테스트로 차례로 판단합니다. 각 결과 옆의 표시는 실습이 예상한 결과와 같은지입니다.
req1-tests: req1-tests-run
	@$(REPORT) --out req1-tests --title "변경 요청 1: 테스트" --lead "$(REQ1_LEAD)" --command "make req1-tests" $(REQ1_CODE) $(REQ1_TESTS)
req1-verify: req1-verify-run
	@$(REPORT) --out req1-verify --title "변경 요청 1: Dafny" --lead "$(REQ1_LEAD)" --command "make req1-verify" $(REQ1_VERIFY)
req1-difftest: req1-difftest-run
	@$(REPORT) --out req1-difftest --title "변경 요청 1: 차분 테스트" --lead "$(REQ1_LEAD)" --command "make req1-difftest" $(REQ1_DIFF)
req1: req1-tests-run req1-verify-run req1-difftest-run
	@$(REPORT) --out req1 --title "변경 요청 1: 대기열 늘리기" --lead "$(REQ1_LEAD)" --command "make req1" \
	  $(REQ1_CODE) $(REQ1_TESTS) $(REQ1_VERIFY) $(REQ1_DIFF)

# every Dafny check that is expected to PASS, with full output (run this first on a new machine)
verify-all:
	@mkdir -p $(RAW)
	-@$(DRUN) --json $(RAW)/va-1.json formal/dfyconfig.toml
	-@$(DRUN) --json $(RAW)/va-2.json formal/Types.dfy $(REQ1)/model/RingQueue.dfy $(REQ1)/model/Dispatcher.dfy formal/PowerBudget.dfy
	-@$(DRUN) --json $(RAW)/va-3.json formal/Types.dfy scenarios/req2/model/RingQueue.dfy formal/Dispatcher.dfy formal/PowerBudget.dfy
	-@$(DRUN) --json $(RAW)/va-5.json rewrite/RewriteRules.dfy
	@$(REPORT) --out verify-all --title "Dafny 증명 전체 점검" --lead "이 실습에서 통과해야 하는 Dafny 증명을 모두 돌립니다. 새 PC에서 먼저 실행하세요. 시간 초과(timed out)가 나면 강사에게 알려 주세요." \
	  --command "make verify-all" --sec dafny "기준 모델 (formal/)" $(RAW)/va-1.json pass \
	  --sec dafny "변경 요청 1 모델" $(RAW)/va-2.json pass --sec dafny "변경 요청 2 모델" $(RAW)/va-3.json pass \
	  --sec dafny "정리 규칙의 조건" $(RAW)/va-5.json pass

# ---------------------------------------------------------------- session 5: impact-guided re-verification

REQ ?= req2
NEWFORMAL_req2 := formal/Types.dfy scenarios/req2/model/RingQueue.dfy formal/Dispatcher.dfy formal/PowerBudget.dfy
NEWFORMAL_req1 := formal/Types.dfy scenarios/req1/model/RingQueue.dfy scenarios/req1/model/Dispatcher.dfy formal/PowerBudget.dfy
JAVAV_req2 := scenarios/req2/ai
JAVAV_req1 := scenarios/req1/ai-B

reverify: build
	@HH_OPEN=0 $(MAKE) -s impact V=$(JAVAV_$(REQ)) REBUILD_LEGACY=0 > /dev/null
	@$(PY) tools/reverify.py --old $(FORMAL) --new $(NEWFORMAL_$(REQ)) \
	   --java-impact $(OUT)/impact-$(subst /,-,$(patsubst scenarios/%,%,$(JAVAV_$(REQ)))).json \
	   --mapping formal/mapping.tsv --run --html reverify-$(REQ) --label "$(REQ)" > $(OUT)/reverify-$(REQ).md

# ---------------------------------------------------------------- session 5: semantics-preserving rewriting

# R = rule name: scenarios/rw/<R> holds the code after applying that cleanup rule everywhere
#     (IsEmpty, ForEach, InlineVariable, or All = all three)
R ?= All
rewrite-check: $(BUILD)/difftest/.stamp
	@mkdir -p $(RAW); $(MAKE) -s variant V=scenarios/rw/$(R) >/dev/null; d=$(WORK)/rw-$(R); \
	$(JAVA) -cp $$d/build/classes:$$d/build/test-classes com.dxlab.homehub.testkit.TestRunner > $(RAW)/rw-$(R)-test.txt; tail -1 $(RAW)/rw-$(R)-test.txt; \
	$(PY) tools/trace_check.py --cp $$d/build/classes --json $(RAW)/rw-$(R)-trace.json --save $(BUILD)/rw-$(R) $(WORKLOADS); \
	$(JAVA) -cp $(BUILD)/difftest difftest.HubDiff $(LEGACY_CP) $$d/build/classes --keep $(OUT)/hubdiff-$(R).txt --json $(RAW)/rw-$(R)-hub.json | head -1; \
	$(REPORT) --out rewrite-check-$(R) --title "정리 규칙 적용 확인: $(R)" \
	  --lead "정리 규칙을 코드 전체에 적용한 결과가 동작을 바꾸지 않았는지 세 가지로 확인합니다: 기존 테스트, 기록해 둔 동작, 무작위 입력으로 레거시와 비교." \
	  --command "make rewrite-check R=$(R)" \
	  --sec srcdiff "바뀐 코드" "$(LEGACY)/src|$$d/src" - \
	  --sec tests "1. 기존 테스트" $(RAW)/rw-$(R)-test.txt - \
	  --sec trace "2. 기록해 둔 동작" $(RAW)/rw-$(R)-trace.json - \
	  --sec hubdiff "3. 무작위 입력으로 레거시와 비교" $(RAW)/rw-$(R)-hub.json -

rules:
	@mkdir -p $(RAW); $(DRUN) --json $(RAW)/rules.json rewrite/RewriteRules.dfy; st=$$?; \
	$(REPORT) --out rules --title "정리 규칙의 조건 증명" --lead "rewrite/RewriteRules.dfy: 규칙마다 같음 보조정리(조건은 requires)와, 조건부 규칙은 조건이 없을 때의 반례 보조정리." \
	  --command "make rules" --sec dafny "RewriteRules.dfy" $(RAW)/rules.json pass; exit $$st

# ---------------------------------------------------------------- everything (instructor smoke test)

smoke: export HH_OPEN = 0
smoke: check-env test trace verify-all difftest difftest-sample req1 rules
	@$(MAKE) -s ingest MSG='5|fridge-2|TEMP|38|60000'
	@printf '1|fridge-2|PWR_ON|0|0\n2|fridge-2|TEMP|12|60000|unit=C\n3|fridge-2|TEMP|13|120000|unit=C\n!drain\n4|fridge-2|TEMP|14|180000|unit=C\n' > $(OUT)/raw/path-input.txt; $(MAKE) -s path
	@$(MAKE) -s state; for k in temp.highCelsius rules.doorOpenAlertMillis; do $(MAKE) -s config KEY=$$k; done
	@for v in req2/ai req1/ai-A a3-sort; do $(MAKE) -s impact V=scenarios/$$v; done
	@$(MAKE) -s variant-test V=scenarios/req1/ai-A-oldtests NOREPORT=1 || echo "  (예상대로 5개 실패: AI가 테스트를 고치기 전)"
	@for c in req2 req1; do $(MAKE) -s reverify REQ=$$c; done
	@for r in IsEmpty ForEach InlineVariable All; do $(MAKE) -s rewrite-check R=$$r; done
	@echo; echo "모든 보고서: $(OUT)/html/index.html"

# the lab notebooks (notebooks/0_시작하기.ipynb first)
notebook:
	@command -v jupyter >/dev/null || { echo "Jupyter가 없습니다. pip install jupyterlab 으로 설치하거나, VS Code에서 notebooks/ 의 .ipynb 파일을 여세요."; exit 2; }
	@cd notebooks && HH_OPEN=0 jupyter lab

# open the list of all reports
report:
	@$(PY) -c "import sys; sys.path.insert(0,'tools'); import report, json; report.write_index(json.load(open('$(OUT)/html/_index.json'))); report.maybe_open('$(OUT)/html/index.html')"

clean:
	rm -rf $(LEGACY)/build $(BUILD) $(OUT) $(WORK) notebooks/__pycache__ notebooks/.ipynb_checkpoints
