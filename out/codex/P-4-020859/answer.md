제공된 코드에서 **변경 및 필드·반환값의 흐름을 기준으로 영향을 받는 메서드는 7개**입니다. 외부 호출 코드와 테스트 코드가 없으므로, 프로젝트 전체의 영향 메서드나 실제 테스트 이름까지 모두 확정할 수는 없습니다.

| 메서드 | 영향 경로 |
|---|---|
| `com.dxlab.homehub.queue.RingEventQueue#offer(com.dxlab.homehub.model.Event)` | 직접 변경. `buf`에 기록하는 인덱스 계산 변경. 변경된 `head`, `count`를 사용하므로 후속 삽입에도 영향 |
| `com.dxlab.homehub.queue.RingEventQueue#poll()` | 직접 변경. `head` 갱신 방식 변경. `buf`, `head`, `count`를 읽어 반환 이벤트 결정 |
| `com.dxlab.homehub.queue.RingEventQueue#clear()` | 직접 변경. `poll()` 반복 호출에서 배열 초기화 및 `head`, `count` 재설정으로 변경 |
| `com.dxlab.homehub.queue.RingEventQueue#snapshot()` | 직접 변경. 배열 순회 인덱스 계산 변경. 큐 상태가 반환 리스트로 전달됨 |
| `com.dxlab.homehub.queue.RingEventQueue#peek()` | 간접 영향. 변경 메서드가 기록한 `buf`, `head`, `count`에 따라 반환 이벤트 결정 |
| `com.dxlab.homehub.queue.RingEventQueue#size()` | 간접 영향. 변경 메서드가 갱신하는 `count`를 반환 |
| `com.dxlab.homehub.queue.RingEventQueue#isEmpty()` | 간접 영향. 변경 메서드가 갱신하는 `count`로 결과 결정 |

`com.dxlab.homehub.queue.RingEventQueue#capacity()`는 변경되지 않는 `buf.length`만 반환하므로 영향 대상에서 제외합니다. 생성자도 변경된 상태를 소비하지 않으므로 제외합니다.

정상적인 단일 스레드 사용에서 인덱스 계산은 기존과 동등합니다. `clear()` 이후 내부 `head`는 기존과 달라질 수 있지만, 공개 메서드의 논리적인 결과는 같아야 합니다. 위 목록은 **결과가 실제로 달라진다고 확정한 목록이 아니라, 변경의 정확성을 검증해야 하는 영향 범위**입니다.

다시 실행해야 할 테스트 범위는 다음과 같습니다. 아래는 실제 테스트 메서드명이 아니라 필요한 검증 항목입니다.

| 테스트 범위 | 검증 항목 |
|---|---|
| 삽입 | 정상 삽입, `null` 거부, 가득 찼을 때 `FULL`, 실패 시 기존 상태 유지 |
| 인출 | FIFO 순서, 빈 큐에서 `null`, 마지막 원소 인출 후 상태 |
| 순환 경계 | `head`가 배열 끝에서 0으로 이동, 인출 후 재삽입 시 삽입 위치 순환, 여러 바퀴 반복 |
| 용량 경계 | 용량 1, 기본 용량 8, 2의 거듭제곱이 아닌 용량에서 동일한 동작 |
| 초기화 | 빈 큐·일부 찬 큐·가득 찬 큐·순환된 큐의 `clear()`, 반복 `clear()` |
| 초기화 후 재사용 | `clear()` 후 삽입·인출·다시 가득 채우기, 이전 이벤트가 반환되지 않음 |
| 상태 조회 | 각 변경 연산 전후 `peek()`, `size()`, `isEmpty()` 결과 및 조회가 상태를 바꾸지 않음 |
| 스냅샷 | 빈 큐·일반 큐·순환된 큐의 원소와 순서, `clear()` 전후 결과, 반환 리스트와 큐의 구조적 독립성 |
| 혼합 연산 | `offer → poll → offer → snapshot → clear → offer` 등의 연속 동작에서 순서·크기 일관성 |
| 성능 요구 | 삽입·인출·스냅샷의 변경 경로 성능, `clear()`의 용량별 실행 비용 |

외부 코드가 있다면, 위 7개 메서드의 직접 호출자뿐 아니라 **반환 이벤트·반환 리스트·크기·비어 있음 여부·삽입 결과를 필드에 저장하거나 다시 반환하고, 이후 분기나 출력에 사용하는 메서드와 그 테스트까지** 추적해야 합니다. 그 이름은 제공된 코드만으로 열거할 수 없습니다.