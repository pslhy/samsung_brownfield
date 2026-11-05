| 항목 | 넣은 쪽 | 판단 | 맞은 쪽 | 근거 |
|---|---|---|---|---|
| app.HomeHub#drain | 도구 | 영향 없음 | AI | `drain`은 `step()`을 반복할 뿐, 변경된 큐 알고리즘의 관찰값을 직접 반환·기록하지 않는다. |
| app.HomeHub#flushDerived | 도구 | 영향 없음 | AI | `takeOutbox()` 결과를 `dispatcher.submit()`하는 경로로, 큐 동작 자체는 변경 전후 의미가 같다. |
| app.HomeHub#ingest | 도구 | 영향 없음 | AI | 파싱 후 `dispatcher.submit()` 결과만 반환하며, 큐의 순환 인덱스 구현 변경은 결과 의미를 바꾸지 않는다. |
| app.HomeHub#step | 도구 | 영향 없음 | AI | `dispatchOne()`의 FIFO 결과가 동일하므로 반환 boolean과 파생 이벤트 처리도 동일하다. |
| app.HomeHub#submit | 도구 | 영향 없음 | AI | `dispatcher.submit()`의 결과와 파생 이벤트 제출은 큐 API 의미 보존으로 달라지지 않는다. |
| app.HomeHub#tick | 도구 | 영향 없음 | AI | 큐의 `size()`·`snapshot()` 의미가 유지되어 watchdog/recovery 결과가 같다. |
| app.HubMain#main | 도구 | 영향 없음 | AI | `HomeHub` 공개 동작에 의존할 뿐, 큐의 내부 인덱싱 변경으로 출력이 달라지지 않는다. |
| app.HubMain#run | 도구 | 영향 없음 | AI | `step`, `drain`, `ingest`, `observable`의 의미가 모두 보존된다. |
| device.DeviceRegistry#byKind | 도구 | 영향 없음 | AI | `Device#getKind()`와 정렬만 사용하며 RingEventQueue 변경과 무관하다. |
| device.DeviceRegistry#get | 도구 | 영향 없음 | AI | 단순 `Map#get`으로 큐 변경의 값이 흘러가지 않는다. |
| device.DeviceStateMachine#next | 도구 | 영향 없음 | AI | 상태 전이는 `DeviceStatus`·`EventType`만 사용하고 큐를 참조하지 않는다. |
| dispatch.Dispatcher#drain | 도구 | 영향 없음 | AI | `dispatchOne()` 반복 결과는 FIFO 보존으로 동일하다. |
| dispatch.Dispatcher#getDispatchedCount | 도구 | 영향 없음 | AI | 카운터는 dispatch 횟수만 세며 큐 구현 변경으로 횟수가 달라지지 않는다. |
| dispatch.HandlerRegistry#dispatch | 도구 | 영향 없음 | AI | 이벤트 타입별 handler 호출만 수행하고 큐 내부값을 사용하지 않는다. |
| handlers.DeviceStatusHandler#handle | 도구 | 영향 없음 | AI | dispatch되는 이벤트 순서와 이벤트 객체가 동일하므로 상태·필드 쓰기도 동일하다. |
| handlers.SafetyHandler#handle | 도구 | 영향 없음 | AI | critical 이벤트의 전달 순서와 내용이 변하지 않아 안전 정지 결과가 같다. |
| handlers.TemperatureHandler#handle | 도구 | 영향 없음 | AI | 온도 이벤트가 동일 순서로 전달되어 `lastTemp`·연속 고온 카운트가 같다. |
| model.Device#getConsecutiveHighTemp | 도구 | 영향 없음 | AI | 단순 필드 getter이며 변경 diff가 이 필드에 쓰지 않는다. |
| model.Device#getDoorOpenedAt | 도구 | 영향 없음 | AI | 단순 필드 getter이고 큐 변경과 무관하다. |
| model.Device#getFirmware | 도구 | 영향 없음 | AI | firmware 필드에는 큐 변경값이 도달하지 않는다. |
| model.Device#getLastSeen | 도구 | 영향 없음 | AI | timestamp 전달이 동일하므로 getter 결과가 달라지지 않는다. |
| model.Device#getLastTemp | 도구 | 영향 없음 | AI | 온도 이벤트 및 값이 변경되지 않는다. |
| model.Device#getStatus | 도구 | 영향 없음 | AI | 상태 전이 입력과 순서가 보존된다. |
| model.Device#isDoorOpen | 도구 | 영향 없음 | AI | door 상태는 `DOOR_OPEN/CLOSE` 처리로만 바뀐다. |
| model.Device#setConsecutiveHighTemp | 도구 | 영향 없음 | AI | setter 호출값은 TemperatureHandler 계산값으로, 큐 구현 변경과 무관하다. |
| model.Device#setDoorOpen | 도구 | 영향 없음 | AI | setter 입력은 이벤트 타입·timestamp이며 변경 diff가 이를 바꾸지 않는다. |
| model.Device#setFirmware | 도구 | 영향 없음 | AI | `e.attr("fw")` 값은 RingEventQueue 변경과 무관하다. |
| model.Device#setLastSeen | 도구 | 영향 없음 | AI | 이벤트 timestamp가 동일하게 전달된다. |
| model.Device#setLastTemp | 도구 | 영향 없음 | AI | 이벤트 value가 동일하게 전달된다. |
| model.Device#setStatus | 도구 | 영향 없음 | AI | 상태 전이 계산은 큐 인덱스 방식과 독립적이다. |
| model.Device#toString | 도구 | 영향 없음 | AI | `id`, `kind`, `status`만 출력하며 큐 변경값이 필드에 도달하지 않는다. |
| model.Event#<init> | 도구 | 영향 없음 | AI | 이벤트 생성자 입력과 불변 필드가 변경되지 않는다. |
| model.Event#attr | 도구 | 영향 없음 | AI | attrs는 큐에서 변경되지 않는다. |
| model.Event#equals | 도구 | 영향 없음 | AI | 비교 대상 이벤트의 seq/deviceId가 동일하다. |
| model.Event#getAttrs | 도구 | 영향 없음 | AI | 반환하는 attrs 자체가 diff의 영향을 받지 않는다. |
| model.Event#getDeviceId | 도구 | 영향 없음 | AI | 이벤트 객체의 deviceId 값은 변경되지 않는다. |
| model.Event#getSeq | 도구 | 영향 없음 | AI | snapshot/poll 순서는 같고 seq도 그대로다. |
| model.Event#getTimestamp | 도구 | 영향 없음 | AI | timestamp 값은 큐 연산에서 변경되지 않는다. |
| model.Event#getType | 도구 | 영향 없음 | AI | 타입과 FIFO 순서가 보존된다. |
| model.Event#getValue | 도구 | 영향 없음 | AI | 이벤트 value가 큐 구현에 의해 변하지 않는다. |
| model.Event#hashCode | 도구 | 영향 없음 | AI | seq/deviceId가 동일하므로 hashCode도 동일하다. |
| model.Event#toString | 도구 | 영향 없음 | AI | 이벤트 필드가 변하지 않는다. |
| ops.AuditLog#contains | 도구 | 영향 없음 | AI | audit 입력 이벤트와 기록 순서가 동일하다. |
| ops.AuditLog#count | 도구 | 영향 없음 | AI | 큐 변경으로 audit entry 발생 조건이 달라지지 않는다. |
| ops.AuditLog#dump | 도구 | 영향 없음 | AI | 기록 내용·순서가 동일하다. |
| ops.AuditLog#note | 도구 | 영향 없음 | AI | note 호출 조건은 dispatch 결과 및 상태이며 의미가 보존된다. |
| ops.AuditLog#record | 도구 | 영향 없음 | AI | 기록되는 이벤트가 변경되지 않는다. |
| ops.AuditLog#size | 도구 | 영향 없음 | AI | audit 기록 수가 변하지 않는다. |
| ops.AuditLog#tail | 도구 | 영향 없음 | AI | audit 내용 및 순서가 동일하다. |
| ops.Metrics#get | 도구 | 영향 없음 | AI | metric 증가 조건이 변경되지 않는다. |
| ops.Metrics#increment | 도구 | 영향 없음 | AI | 큐 변경으로 호출 횟수가 변하지 않는다. |
| ops.Metrics#isEmpty | 도구 | 영향 없음 | AI | metrics 상태가 동일하다. |
| ops.Metrics#reset | 도구 | 영향 없음 | AI | 큐와 무관한 counters 초기화다. |
| ops.Metrics#snapshot | 도구 | 영향 없음 | AI | counters 값이 동일하다. |
| ops.Watchdog#getHighWaterChecks | 도구 | 영향 없음 | AI | `queue.size()` 의미가 동일해 check 누적값이 같다. |
| power.PowerBudget#headroom | 도구 | 영향 없음 | AI | running 장치와 load가 동일하다. |
| power.PowerBudget#isIdle | 도구 | 영향 없음 | AI | dispatch 순서가 같아 power grant/stop 결과가 같다. |
| power.PowerBudget#isRunning | 도구 | 영향 없음 | AI | running map 상태가 동일하다. |
| power.PowerBudget#runningDevices | 도구 | 영향 없음 | AI | running 장치 집합이 동일하다. |
| power.PowerBudget#stop | 도구 | 영향 없음 | AI | stop 대상과 호출 시점이 동일하다. |
| power.PowerBudget#stopAll | 도구 | 영향 없음 | AI | 큐 변경과 무관하다. |
| power.PowerBudget#totalLoad | 도구 | 영향 없음 | AI | power grant 상태가 달라지지 않는다. |
| power.PowerBudget#tryStart | 도구 | 영향 없음 | AI | 동일한 장치·전력 입력을 받는다. |
| queue.RingEventQueue#isEmpty | 도구 | 영향 있음 | 도구 | `count`를 기준으로 하지만 새 `clear()`가 `head/count`를 직접 재설정하므로 이 상태의 후속 관찰에 영향을 받는다. |
| queue.RingEventQueue#peek | 도구 | 영향 있음 | 도구 | `head`를 직접 읽으며 새 `clear()`가 `head=0`으로 바꾸므로 clear 후 내부 상태 관찰이 달라질 수 있다. |
| queue.RingEventQueue#size | 도구 | 영향 있음 | 도구 | 새 `clear()`가 `count=0`을 직접 설정하며 변경된 필드의 반환값이다. |
| rules.RuleEngine#afterDispatch | 도구 | 영향 없음 | AI | dispatch 이벤트와 순서가 동일하고, queue 내부 인덱스는 rule 입력에 노출되지 않는다. |
| rules.RuleEngine#isLatched | 도구 | 영향 없음 | AI | latch 집합은 동일한 온도 이벤트 처리로 결정된다. |
| rules.RuleEngine#takeOutbox | 도구 | 영향 없음 | AI | outbox 생성 조건은 큐 구현과 무관하다. |
| app.HomeHub#getQueue | AI | 영향 있음 | AI | 변경된 `RingEventQueue` 객체를 그대로 반환하므로 그 객체의 `clear/offer/poll/snapshot` 동작이 관찰된다. |
| DispatcherTest#testAcceptWhenSpace | 도구 | 영향 없음 | AI | `offer`의 정상 수용 결과와 `size=1`은 변경 전후 동일하다. |
| DispatcherTest#testNullIsInvalid | 도구 | 영향 없음 | AI | null은 `offer` 전 검사에서 `INVALID`로 처리된다. |
| EventParserTest#testAttributes | 도구 | 영향 없음 | AI | parser와 Event attrs는 diff 대상이 아니다. |
| EventParserTest#testBasicLine | 도구 | 영향 없음 | AI | parser가 생성한 이벤트 필드가 큐를 거치지 않는다. |
| EventParserTest#testCelsiusTemperature | 도구 | 영향 없음 | AI | Celsius 정규화 로직은 변경되지 않았다. |
| EventParserTest#testFahrenheitIsNormalized | 도구 | 영향 없음 | AI | Fahrenheit 변환 로직은 변경되지 않았다. |
| EventParserTest#testUnknownCode | 도구 | 영향 없음 | AI | `EventType.fromCode`는 diff와 무관하다. |
| HandlersTest#testCycleEndReleasesPower | 도구 | 영향 없음 | AI | handler를 직접 호출하므로 RingEventQueue를 사용하지 않는다. |
| HandlersTest#testHeavyLoadNeedsPower | 도구 | 영향 없음 | AI | handler와 PowerBudget만 직접 검증한다. |
| HandlersTest#testHighTemperatureIsCounted | 도구 | 영향 없음 | AI | TemperatureHandler를 직접 호출하며 큐가 없다. |
| HandlersTest#testLeakStopsRunningWasher | 도구 | 영향 없음 | AI | SafetyHandler와 PowerBudget를 직접 호출한다. |
| HandlersTest#testUnknownDevice | 도구 | 영향 없음 | AI | queue를 거치지 않는 직접 handler 테스트다. |
| HomeHubTest#testInvalidLineIsDropped | 도구 | 영향 없음 | AI | 잘못된 입력은 queue 제출 전에 `INVALID`로 반환된다. |
| PowerBudgetTest#testDenyOverCap | 도구 | 영향 없음 | AI | PowerBudget 단위 테스트로 queue와 무관하다. |
| PowerBudgetTest#testGrantWithinCap | 도구 | 영향 없음 | AI | PowerBudget 내부 계산만 검사한다. |
| PowerBudgetTest#testIdempotentStart | 도구 | 영향 없음 | AI | running map idempotence만 검사한다. |
| PowerBudgetTest#testRejectInvalidWatts | 도구 | 영향 없음 | AI | watt 유효성 검사만 수행한다. |
| PowerBudgetTest#testStopReleases | 도구 | 영향 없음 | AI | `stop`과 `headroom`만 검사한다. |
| RingEventQueueTest#testNullRejected | 도구 | 영향 없음 | AI | null 검사 분기는 변경되지 않았다. |
| RingEventQueueTest#testPeekDoesNotRemove | 도구 | 영향 있음 | 도구 | `peek()`가 변경된 `head` 상태를 읽지만, 이 테스트의 단일 삽입에서는 결과가 동일해 실제 검사값은 변하지 않는다. |
| RingEventQueueTest#testPeekDoesNotRemove | 도구 | 영향 없음 | AI | 단일 삽입 후 `peek=7`, `size=1`은 변경 전후 동일하다. |

도구가 틀린 항목의 공통 원인: 변경된 `RingEventQueue`의 내부 데이터·인덱스에 대한 정적 의존성을 과잉 전파해 의미 보존되는 호출자와 무관한 테스트까지 영향 대상으로 확장했다.

AI가 틀린 항목의 공통 원인: `RingEventQueue`의 내부 상태를 실제로 반환하는 `size/peek/isEmpty`와 이를 검증하는 `testPeekDoesNotRemove`를, 단순히 결과가 같다는 이유로 영향 없음으로 축소했다.