# 변경 요청 2: 대기열 연산 빠르게

## 요청 내용 (플랫폼팀)

허브 칩(MCU)을 측정해 보니 정수 나눗셈(`%`)이 느리다는 보고가 있었습니다.

- `RingEventQueue`의 offer / poll / snapshot에서 `%` 연산을 없앤다.
- `clear()`가 poll을 반복하지 않고 배열을 한 번에 비우게 한다.
- 동작은 바꾸지 않는다.

## 제공되는 파일

| 파일 | 내용 |
|---|---|
| `ai/` | 위 내용을 반영한 AI 패치 `RingEventQueue.java` (바뀐 메서드 4개: offer, poll, clear, snapshot) |
| `model/RingQueue.dfy` | Java 변경에 맞춰 고친 Dafny 모델. 바뀐 Java 메서드 4개에 대응하는 Dafny 메서드 4개의 **본문**을 새 Java 코드대로 다시 썼습니다(주석 `REQ-2`). 계약은 그대로입니다. |

## 실습에서 볼 것

- 실습 A-1: `make impact V=scenarios/req2/ai` — 바뀐 메서드 4개, 출력이 달라질 수 있는 메서드 79개, 다시 돌릴 테스트 33/38.
- 실습 D: `make reverify REQ=req2` — 49개 중 4개(바뀐 본문)만 다시 증명. Dispatcher·전력 메서드는 Java 영향 분석에는 들지만 다시 증명할 필요가 없음.
- 차분 테스트: `make variant V=scenarios/req2/ai` 후 `make difftest JAVA_CP=work/req2-ai/build/classes` — 새 Java와 모델이 일치하는지.
