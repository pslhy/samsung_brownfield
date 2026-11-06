# 실습용 AI 프롬프트

사내 LLM이나 Codex에 그대로 넣어 쓸 수 있는 프롬프트입니다. `{ }` 안은 실제 파일 내용으로 바꿉니다.

노트북에서는 `lab.codex("P-1", save="mine/RingEventQueue.dfy")`처럼 부르면 `{ }`를 채운 프롬프트를 Codex CLI(`codex exec`)에 보내고, 답을 셀 아래에 보여 주고, `save=`가 있으면 답의 코드 블록을 그 파일에 저장합니다. 파일 경로가 아닌 자리는 이름으로 넘깁니다(띄어쓰기는 `_`): `lab.codex("P-2", 파일="mine/RingEventQueue.dfy", 오류=lab.dafny_errors("mine/RingEventQueue.dfy"))`. Codex가 없으면 `lab.prompt("P-1")`로 프롬프트만 출력해 복사합니다.

AI의 결과는 사람이 계약을 읽고, 도구(Dafny 검증, 차분 테스트, 영향 분석)로 확인합니다. AI가 계약(requires/ensures)을 마음대로 바꾸지 않았는지는 항상 diff로 봅니다.

---

## P-1. Java 클래스를 Dafny로 (실습 B-1)

일부러 짧게 씁니다. 결과가 잘 옮겨졌는지는 프롬프트로 강제하지 않고, 계약 읽기와 차분 테스트로 판단합니다.

```
다음 Java 클래스를 Dafny로 만들어 줘. dafny verify가 통과해야 해.

{legacy/src/main/java/com/dxlab/homehub/queue/RingEventQueue.java}
```

결과는 `mine/RingEventQueue.dfy`로 저장합니다.

## P-1b. 차분 테스트용 연결 코드 (실습 B-1)

```
방금 만든 Dafny 코드를 `dafny build -t java`로 Java로 컴파일한다.
컴파일된 클래스를 아래 Java 인터페이스에 연결하는 클래스를 만들어 줘.

- 클래스 이름: difftest.MyQueueAdapter (package difftest), 인자 없는 public 생성자
- 인터페이스 difftest.QueueModel을 구현한다
- 하는 일은 형식 변환뿐이다. 동작을 보태거나 고치지 마라.
- 참고: Dafny의 int는 Java에서 java.math.BigInteger, 여러 값을 돌려주는 메서드는 dafny.Tuple2,
  datatype은 정적 메서드 create(...)로 만들고 dtor_필드이름()으로 읽는다.
  Dafny 생성자는 new 클래스() 다음에 __ctor(...)를 부른다.
  컴파일된 Java 클래스의 패키지: Dafny 코드를 module 없이 썼으면 _System, module M 안에 썼으면 M이다.

인터페이스:
{difftest/src/difftest/QueueModel.java}

Dafny 코드:
{mine/RingEventQueue.dfy}
```

`make difftest-mine`에서 컴파일 오류가 나면 오류 메시지를 그대로 붙여 넣고 고치게 합니다. 예시 답은 `scenarios/b1-ai-sample/MyQueueAdapter.java`입니다.

## P-2. 검증 실패 고치기: 계약은 고정 (실습 B, C)

```
아래 Dafny 파일이 검증에 실패한다. 오류 메시지를 보고 고쳐라.

- requires / ensures / modifies / reads 줄은 한 글자도 바꾸지 마라.
- 바꿔도 되는 것: 메서드 본문, 루프 불변식(invariant), assert, 보조정리(lemma) 추가.
- 계약을 바꾸지 않고는 증명할 수 없다고 판단되면, 고치지 말고 그 이유와 반례가 되는 입력을 설명하라.

파일:
{파일}
오류:
{오류}
```

AI가 사후조건을 약하게 바꿔서 "통과"시키는 것이 가장 흔한 실패입니다. 결과를 받으면 계약 줄이 그대로인지 diff로 먼저 확인합니다.

## P-3. Java 변경을 Dafny 모델에 반영하기 (실습 C, D)

```
Java 코드가 아래 diff처럼 바뀌었다. 기존 Dafny 모델에서, 바뀐 Java 메서드에 대응하는 Dafny 메서드의
본문을 새 Java 코드대로 다시 써라.

- 대응표: {formal/mapping.tsv}
- 계약(requires/ensures)은 바꾸지 마라. 변경 요청서가 승인한 변화가 있으면 그것만 바꾸고, 바꾼 줄을 따로 보고하라.
- 새 Java 코드를 그대로 옮긴 모델이 검증에 실패하면, 모델을 억지로 맞추지 말고 Java 코드의 문제로 보고하라.

변경 요청서: {scenarios/req1/README.md}
Java diff: {diff}
기존 Dafny 모델: {formal/...}
```

## P-4. 도구가 고른 테스트 걸러 내기 (실습 A)

```
영향 분석 도구가 아래 diff를 보고 "다시 돌릴 테스트" 목록을 냈다.
이 도구는 놓치지 않으려고 넓게 잡기 때문에, 바뀐 코드를 실제로는 거치지 않는 테스트도 들어 있을 수 있다.
아래 테스트 코드를 보고, 목록의 테스트마다 실행 중에 diff에서 바뀐 메서드가 한 번이라도 불리는지 판단하라.
테스트가 무엇을 검증하는지는 따지지 마라. 바뀐 메서드가 한 번이라도 실행되면 "남김"이다
(다른 클래스 안에서 불려도 마찬가지다. 예: 테스트가 만든 Dispatcher나 HomeHub가 안에서 대기열의 offer, poll을 부름).
바뀐 클래스를 만들지도 쓰지도 않는 테스트, 또는 바뀐 메서드에 닿기 전에 끝나는 테스트만 "뺌"이다.
답은 아래 표 하나로만 써라. 목록의 모든 테스트를 한 줄씩 적어라.

| 테스트 | 판단(남김/뺌) | 이유(한 줄) |

[도구가 고른 테스트]
{테스트 목록}

[diff]
{diff}

[테스트 코드]
{테스트 코드}
```

AI가 "뺌"이라고 한 테스트가 정말 빼도 되는지는 테스트 코드를 보고 확인합니다. AI도 틀릴 수 있습니다.

## P-5. 정리 규칙 적용 (실습 E)

```
다음 정리 규칙을 아래 Java 코드에서 적용할 수 있는 곳마다 모두 적용하라. 바꾼 파일 전체를 보여 줘라.

규칙: {규칙}

코드:
{코드}
```

결과를 받으면 두 가지를 봅니다. (1) AI가 규칙이 같은 뜻이 되는 조건을 자리마다 확인했는가(확인했다고 말했는가, 실제로 조건이 깨지는 자리를 건너뛰었는가), (2) `make rewrite-check`처럼 테스트·동작 기록·무작위 비교로 동작이 같은지.

## P-6. 메시지 하나의 처리 경로 (참고: 지금은 실습에서 쓰지 않음)

```
아래는 가전 허브 프로그램 HomeHub의 Java 소스 전체다.
허브를 기본 설정(new HubConfig())으로 새로 시작하고, 다음 줄들을 차례로 넣었다. "!drain"은 대기열에 쌓인 이벤트를 모두 처리하라는 명령이다.

{앞 메시지}

그다음 아래 메시지 하나를 넣고(HomeHub.ingest), 대기열이 빌 때까지 처리했다(HomeHub.drain).

{메시지}

1. 이 마지막 메시지를 넣고 처리하는 동안 실행되는 메서드를, 처음 실행되는 순서대로 모두 나열하라. "클래스.메서드" 형식으로 써라.
2. 처리가 끝난 뒤 바뀐 상태(기기 상태, 전력, 감사 로그)를 적어라.
3. 이 메시지 때문에 새로 만들어지는 이벤트가 있는가? 있다면 어디서 만들어져 어디서 처리되는가?

{소스}
```

AI의 답을 `make path`의 실행 기록과 비교합니다. 순서가 그럴듯해도 빠진 메서드(게터, 생성자)나 실제로는 실행되지 않은 메서드가 있는지, 3번의 연결(온도 보고 → 과열 이벤트 → 안전 처리)을 맞혔는지 봅니다.
