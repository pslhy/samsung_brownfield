제공된 코드로 확인할 수 있는 영향 범위는 아래 7개 메서드입니다. 외부 호출부와 테스트 코드가 없으므로, **프로젝트 전체의 영향 메서드와 기존 테스트 이름을 모두 확정할 수는 없습니다.**

| 영향 메서드 | 영향 경로 |
|---|---|
| `com.dxlab.homehub.queue.RingEventQueue#offer(com.dxlab.homehub.model.Event)` | 직접 변경. `buf`, `count`를 갱신하며 `head`, `count`에 따라 저장 위치와 반환값을 결정 |
| `com.dxlab.homehub.queue.RingEventQueue#poll()` | 직접 변경. `buf`, `head`, `count`를 갱신하고 저장된 이벤트를 반환 |
| `com.dxlab.homehub.queue.RingEventQueue#clear()` | 직접 변경. `buf`, `head`, `count`를 초기화 |
| `com.dxlab.homehub.queue.RingEventQueue#snapshot()` | 직접 변경. `buf`, `head`, `count`를 읽어 이벤트 목록을 반환 |
| `com.dxlab.homehub.queue.RingEventQueue#peek()` | 변경된 `buf`, `head`, `count`를 읽어 반환 이벤트를 결정 |
| `com.dxlab.homehub.queue.RingEventQueue#size()` | 변경된 `count`를 반환 |
| `com.dxlab.homehub.queue.RingEventQueue#isEmpty()` | 변경된 `count`로 반환값을 결정 |

생성자 두 개와 `com.dxlab.homehub.queue.RingEventQueue#capacity()`는 변경된 값에 의존하지 않습니다. `capacity()`가 읽는 `buf.length`는 이번 변경으로 달라지지 않습니다.

다시 실행해야 할 테스트 범위는 다음과 같습니다. 아래는 기존 테스트명이 아니라 **검증해야 할 항목**입니다.

- **`offer`**: 정상 삽입, `null` 거부, 만원 시 `FULL`, 거부 시 상태 보존, 배열 끝을 넘는 삽입.
- **`poll`**: 빈 큐의 `null`, FIFO 순서, 마지막 원소 제거, 배열 끝에서 처음으로 이동, 제거 후 재삽입.
- **`peek`**: 빈 큐, 삽입·제거·순환·초기화 이후 반환값, 조회 시 상태 보존.
- **`size`·`isEmpty`**: 삽입 성공·삽입 거부·제거·초기화 이후 값.
- **`clear`**: 빈 큐·일부 채운 큐·가득 찬 큐·순환된 큐 초기화, 반복 초기화, 초기화 후 재사용.
- **`snapshot`**: 빈 큐·일부 채운 큐·가득 찬 큐·순환된 큐의 FIFO 목록, 초기화 후 빈 목록, 조회 시 상태 보존.
- **경계 및 복합 동작**: 용량 1, 비거듭제곱 용량, 여러 번 순환하는 삽입·제거·초기화 조합.
- **성능 검증**: 기존 큐 성능 테스트 및 REQ-2 검증. 특히 `clear()`는 기존 원소 수 기준 반복에서 배열 전체 초기화로 바뀌므로 빈 큐와 큰 용량도 포함.
- **외부 통합 테스트**: 위 메서드의 반환값이나 큐 상태를 이용하는 모든 소비자 테스트. 실제 소비자와 테스트 목록은 제공되지 않아 열거할 수 없음.

정상적인 단일 스레드 사용과 큐 불변식 아래에서는 FIFO 순서와 공개 반환값이 유지되는 변경입니다. 다만 `clear()` 이후 내부 `head`와 실행 비용은 달라지므로, **의존성상 영향 범위와 실제 기능 결과의 변경은 구분해야 합니다.**