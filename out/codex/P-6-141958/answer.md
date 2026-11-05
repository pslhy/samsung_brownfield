마지막 메시지 직전에는 `fridge-2`가 `IDLE`, 최근 온도가 `13°C`, 연속 고온 횟수가 `2`입니다. 대기열은 비어 있고 전력 사용량은 `0W`입니다.

**1. 실행되는 메서드 — 각 메서드의 최초 호출 순서**

제공된 소스에 정의된 메서드를 대상으로, 반복 호출은 한 번만 적었습니다. Java 표준 라이브러리 메서드와 생성자는 아래 목록에서 제외했습니다.

```text
HomeHub.ingest
EventParser.parse
EventType.fromCode
EventParser.parseAttrs
Dispatcher.submit
RingEventQueue.offer
Metrics.increment
HomeHub.flushDerived
RuleEngine.takeOutbox
HomeHub.drain
HomeHub.step
Dispatcher.dispatchOne
RingEventQueue.poll
HandlerRegistry.dispatch
Event.getType
TemperatureHandler.handle
Event.getDeviceId
DeviceRegistry.get
Event.getTimestamp
Device.setLastSeen
Event.getValue
Device.setLastTemp
Device.getConsecutiveHighTemp
Device.setConsecutiveHighTemp
CountingHandler.handle
RuleEngine.afterDispatch
Device.getKind
Device.getId
Device.getLastTemp
AuditLog.record
Event.getSeq
SafetyHandler.handle
Device.setStatus
PowerBudget.stop
```

생성자까지 포함하면, `EventParser.parseAttrs` 이후 원본 이벤트를 만드는 **6인자 `Event` 생성자**가 실행됩니다. 이후 `RuleEngine.afterDispatch`에서 파생 이벤트를 만들 때 **5인자 `Event` 생성자 → 6인자 `Event` 생성자**가 실행됩니다.

`HomeHub.drain`은 원본 TEMP와 파생 OVERHEAT를 처리하므로 **`2`를 반환**합니다. 마지막으로 빈 대기열을 확인하는 `step()`에서도 `dispatchOne()`과 `flushDerived()`가 호출됩니다.

**2. 처리 후 상태**

| 항목 | 직전 → 처리 후 |
|---|---|
| `fridge-2.status` | `IDLE` → `ERROR` |
| `fridge-2.lastSeen` | `120000` → `180000` |
| `fridge-2.lastTemp` | `13` → `14` |
| `fridge-2.consecutiveHighTemp` | `2` → `3` |
| 과열 래치 | `false` → `true` |
| 전력 사용량 | `0W` → `0W` (`4000W` 한도) |
| 대기열 | 빈 상태 → 빈 상태 |

다른 기기는 모두 `OFF` 그대로입니다. `PowerBudget.stop("fridge-2")`가 호출되지만 기존 전력 할당이 없어 사용량은 그대로입니다.

감사 로그에는 다음 두 항목이 순서대로 추가됩니다.

```text
RULE_OVERHEAT:4@fridge-2
OVERHEAT_ALARM:1000000@fridge-2
```

따라서 전체 감사 로그는 다음과 같습니다.

```text
STATE:fridge-2:OFF->IDLE
RULE_OVERHEAT:4@fridge-2
OVERHEAT_ALARM:1000000@fridge-2
```

`IDLE->ERROR`에 대한 `STATE` 로그는 생성되지 않습니다. `SafetyHandler`가 상태를 직접 변경하기 때문입니다.

**3. 새로 생성되는 이벤트**

**OVERHEAT 이벤트 하나**가 생성됩니다.

```text
seq=1000000, deviceId=fridge-2, type=OVERHEAT,
value=14, timestamp=180000, attrs={}
```

처리 경로는 다음과 같습니다.

1. `TemperatureHandler.handle`이 연속 고온 횟수를 `3`으로 올립니다.
2. `RuleEngine.afterDispatch`가 기본 임계 횟수 `3`에 도달했음을 확인하고, 이벤트를 만들어 `outbox`에 넣습니다.
3. `HomeHub.flushDerived`가 `RuleEngine.takeOutbox`로 꺼내 `Dispatcher.submit`을 통해 대기열에 넣습니다.
4. 다음 `HomeHub.step`에서 `Dispatcher.dispatchOne → HandlerRegistry.dispatch → SafetyHandler.handle`로 처리되어 기기가 `ERROR`가 됩니다. `CountingHandler.handle`과 `RuleEngine.afterDispatch`도 실행되며, 추가 이벤트는 생성되지 않습니다.