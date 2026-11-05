| 항목 | 넣은 쪽 | 판단 | 맞은 쪽 | 근거 |
|---|---|---|---|---|
| HomeHub#drain | 도구 | 영향 있음 | 도구 | `drain()`이 `step()`을 호출하고, `step()`이 변경된 큐 연산을 거친다. |
| HomeHub#flushDerived | 도구 | 영향 있음 | 도구 | `rules.takeOutbox()` 결과를 `dispatcher.submit()`으로 변경된 큐에 넣는다. |
| HomeHub#ingest | 도구 | 영향 있음 | 도구 | `dispatcher.submit()`이 변경된 `EventQueue` 구현의 `offer()`를 호출한다. |
| HomeHub#step | 도구 | 영향 있음 | 도구 | `dispatcher.dispatchOne()`이 변경된 큐의 `poll()`을 호출한다. |
| HomeHub#submit | 도구 | 영향 있음 | 도구 | `dispatcher.submit()`이 변경된 큐의 `offer()`를 호출한다. |
| HomeHub#tick | 도구 | 영향 있음 | 도구 | `watchdog.check()`가 큐의 `size()`를 사용하고, 조건 충족 시 `recovery.clear/snapshot/offer`를 호출한다. |
| HubMain#main | 도구 | 영향 있음 | 도구 | `new HomeHub(config)`가 변경된 `RingEventQueue` 생성자를 호출한다. |
| HubMain#run | 도구 | 영향 있음 | 도구 | `hub.step/drain/ingest`를 통해 변경된 큐 동작에 도달한다. |
| DeviceRegistry#byKind | 도구 | 없음 | AI | 변경된 큐 값이 이 메서드로 전달되는 경로가 없다. |
| DeviceRegistry#get | 도구 | 없음 | AI | 큐 변경값은 `DeviceRegistry#get`의 인자·반환값·필드에 도달하지 않는다. |
| DeviceStateMachine#next | 도구 | 없음 | AI | 상태 머신 입력은 `DeviceStatus`, `EventType`이며 큐 변경값이 아니다. |
| Dispatcher#drain | 도구 | 영향 있음 | 도구 | 반복되는 `dispatchOne()`이 변경된 큐의 `poll()`을 호출한다. |
| Dispatcher#getDispatchedCount | 도구 | 없음 | AI | `dispatchedCount`는 큐 변경값과 연결되지 않는다. |
| HandlerRegistry#dispatch | 도구 | 없음 | AI | 큐에서 꺼낸 이벤트는 같더라도 변경된 줄의 값이 이 메서드 내부 출력으로 흐르는 경로가 없다. |
| DeviceStatusHandler#handle | 도구 | 없음 | AI | 핸들러는 `Event`와 장치 상태를 사용하며 큐의 인덱스·count 값은 전달되지 않는다. |
| SafetyHandler#handle | 도구 | 없음 | AI | 큐 변경값이 이벤트 필드나 안전 처리 조건으로 흐르지 않는다. |
| TemperatureHandler#handle | 도구 | 없음 | AI | 온도 처리는 `Event#getValue()`를 사용하고 큐 내부 값은 사용하지 않는다. |
| Device#getConsecutiveHighTemp | 도구 | 없음 | AI | 장치 필드 getter이며 큐 변경값과 무관하다. |
| Device#getDoorOpenedAt | 도구 | 없음 | AI | 장치 필드 getter이며 큐 변경값과 무관하다. |
| Device#getFirmware | 도구 | 없음 | AI | 장치 필드 getter이며 큐 변경값과 무관하다. |
| Device#getLastSeen | 도구 | 없음 | AI | 장치 필드 getter이며 큐 변경값과 무관하다. |
| Device#getLastTemp | 도구 | 없음 | AI | 장치 필드 getter이며 큐 변경값과 무관하다. |
| Device#getStatus | 도구 | 없음 | AI | 장치 상태 getter이며 큐 변경값과 무관하다. |
| Device#isDoorOpen | 도구 | 없음 | AI | 장치 필드 getter이며 큐 변경값과 무관하다. |
| Device#setConsecutiveHighTemp | 도구 | 없음 | AI | setter 인자는 온도 처리 계산값이고 큐 변경값이 아니다. |
| Device#setDoorOpen | 도구 | 없음 | AI | 인자는 이벤트의 문 상태·timestamp이며 큐 변경값이 아니다. |
| Device#setFirmware | 도구 | 없음 | AI | 인자는 `Event#attr("fw")` 값이며 큐 변경값이 아니다. |
| Device#setLastSeen | 도구 | 없음 | AI | 인자는 이벤트 timestamp이며 큐 변경값이 아니다. |
| Device#setLastTemp | 도구 | 없음 | AI | 인자는 이벤트 온도값이며 큐 변경값이 아니다. |
| Device#setStatus | 도구 | 없음 | AI | 인자는 상태 머신·안전 핸들러의 상태값이며 큐 변경값이 아니다. |
| Device#toString | 도구 | 없음 | AI | 장치 필드만 반환하며 큐 변경값과 무관하다. |
| Event#<init> | 도구 | 없음 | AI | 생성자 인자는 큐 내부 인덱스가 아니라 호출자가 제공한 이벤트 필드다. |
| Event#attr | 도구 | 없음 | AI | 속성 맵 조회이며 큐 변경값이 흐르지 않는다. |
| Event#equals | 도구 | 없음 | AI | 비교값은 `seq`, `deviceId`이고 큐 변경값이 아니다. |
| Event#getAttrs | 도구 | 없음 | AI | 이벤트의 attrs 필드만 반환한다. |
| Event#getDeviceId | 도구 | 없음 | AI | 이벤트 필드 getter이며 큐 변경값과 무관하다. |
| Event#getSeq | 도구 | 없음 | AI | 이벤트 seq getter이며 큐 내부 count/head와 무관하다. |
| Event#getTimestamp | 도구 | 없음 | AI | 이벤트 timestamp getter이며 큐 변경값과 무관하다. |
| Event#getType | 도구 | 없음 | AI | 이벤트 type getter이며 큐 변경값과 무관하다. |
| Event#getValue | 도구 | 없음 | AI | 이벤트 value getter이며 큐 변경값과 무관하다. |
| Event#hashCode | 도구 | 없음 | AI | `seq`, `deviceId`만 계산에 사용한다. |
| Event#toString | 도구 | 없음 | AI | 이벤트 필드만 문자열에 쓴다. |
| AuditLog#contains | 도구 | 없음 | AI | 감사 로그 문자열을 검사하며 큐 변경값이 기록값으로 흐르지 않는다. |
| AuditLog#count | 도구 | 없음 | AI | 감사 로그의 기존 문자열만 검사한다. |
| AuditLog#dump | 도구 | 없음 | AI | 감사 로그 엔트리만 출력한다. |
| AuditLog#note | 도구 | 없음 | AI | 인자는 호출부의 태그·문자열이며 큐 변경값이 아니다. |
| AuditLog#record | 도구 | 없음 | AI | 기록되는 이벤트는 큐 위치값이 아닌 이벤트 객체다. |
| AuditLog#size | 도구 | 없음 | AI | 감사 로그 크기이며 큐 count와 별개다. |
| AuditLog#tail | 도구 | 없음 | AI | 감사 로그 엔트리만 반환한다. |
| Metrics#get | 도구 | 없음 | AI | 메트릭 카운터는 큐 내부 `head/count`와 연결되지 않는다. |
| Metrics#increment | 도구 | 없음 | AI | 증가값은 항상 1이며 큐 변경값이 아니다. |
| Metrics#isEmpty | 도구 | 없음 | AI | 메트릭 맵 상태만 검사한다. |
| Metrics#reset | 도구 | 없음 | AI | 메트릭 맵만 비운다. |
| Metrics#snapshot | 도구 | 없음 | AI | 메트릭 맵만 문자열화한다. |
| Watchdog#getHighWaterChecks | 도구 | 없음 | AI | watchdog 카운터는 큐 `size/capacity` 결과의 파생값이지만 변경된 줄의 값이 직접 흐르지는 않는다. |
| PowerBudget#headroom | 도구 | 없음 | AI | 전력 맵의 부하와 cap만 계산한다. |
| PowerBudget#isIdle | 도구 | 없음 | AI | 전력 맵의 실행 장치 수만 검사한다. |
| PowerBudget#isRunning | 도구 | 없음 | AI | 전력 맵에 장치 ID가 있는지만 검사한다. |
| PowerBudget#runningDevices | 도구 | 없음 | AI | 전력 맵의 키만 반환한다. |
| PowerBudget#stop | 도구 | 없음 | AI | 장치 ID로 전력 맵을 수정하며 큐 변경값과 무관하다. |
| PowerBudget#stopAll | 도구 | 없음 | AI | 전력 맵만 비운다. |
| PowerBudget#totalLoad | 도구 | 없음 | AI | 전력 맵의 watt 값만 합산한다. |
| PowerBudget#tryStart | 도구 | 없음 | AI | 전력 맵과 watts 인자만 사용한다. |
| RuleEngine#afterDispatch | 도구 | 없음 | AI | 큐 변경값이 아니라 디스패치된 `Event`와 장치 상태를 사용한다. |
| RuleEngine#isLatched | 도구 | 없음 | AI | 래치 집합만 조회한다. |
| RuleEngine#takeOutbox | 도구 | 없음 | AI | outbox의 이벤트만 복사·삭제한다. |
| RingEventQueue#<init> | AI | 영향 있음 | 도구 | 생성자의 `capacity`로 변경된 `buf`가 만들어지고 이후 모든 큐 결과에 영향을 준다. |
| DispatcherTest#testNullIsInvalid | 도구 | 없음 | AI | `submit(null)`은 `queue.offer` 전에 null 검사로 즉시 반환한다. |
| EventParserTest#testAttributes | 도구 | 없음 | AI | parser가 생성한 이벤트를 검사하며 큐를 사용하지 않는다. |
| EventParserTest#testBasicLine | 도구 | 없음 | AI | parser와 Event 필드만 검사한다. |
| EventParserTest#testCelsiusTemperature | 도구 | 없음 | AI | 온도 정규화 결과만 검사한다. |
| EventParserTest#testFahrenheitIsNormalized | 도구 | 없음 | AI | 화씨→섭씨 계산만 검사한다. |
| EventParserTest#testUnknownCode | 도구 | 없음 | AI | `EventType.fromCode` 결과만 검사한다. |
| HandlersTest#testCycleEndReleasesPower | 도구 | 없음 | AI | 핸들러를 직접 호출하며 큐를 거치지 않는다. |
| HandlersTest#testHeavyLoadNeedsPower | 도구 | 없음 | AI | 핸들러와 전력 예산을 직접 검사하며 큐를 사용하지 않는다. |
| HandlersTest#testHighTemperatureIsCounted | 도구 | 없음 | AI | `TemperatureHandler.handle`을 직접 호출한다. |
| HandlersTest#testLeakStopsRunningWasher | 도구 | 없음 | AI | 두 핸들러를 직접 호출하며 큐 경로가 없다. |
| HandlersTest#testUnknownDevice | 도구 | 없음 | AI | 핸들러 직접 호출 결과만 검사한다. |
| HomeHubTest#testInvalidLineIsDropped | 도구 | 없음 | AI | 잘못된 입력은 parser에서 null이 되어 큐 호출 전에 반환된다. |
| PowerBudgetTest#testDenyOverCap | 도구 | 없음 | AI | `PowerBudget`를 직접 생성·호출하며 큐와 무관하다. |
| PowerBudgetTest#testGrantWithinCap | 도구 | 없음 | AI | 전력 예산만 직접 검사한다. |
| PowerBudgetTest#testIdempotentStart | 도구 | 없음 | AI | 전력 예산만 직접 검사한다. |
| PowerBudgetTest#testRejectInvalidWatts | 도구 | 없음 | AI | 전력 예산의 watts 검증만 검사한다. |
| PowerBudgetTest#testStopReleases | 도구 | 없음 | AI | 전력 예산만 직접 검사한다. |

도구가 틀린 항목들의 공통 원인: 호출 그래프·타입 의존성만 넓게 따라가 실제 변경값(`head`, `count`, 큐 원소)이 반환값·필드·조건·검사값으로 흐르지 않는 메서드까지 과대포함했다.

AI가 틀린 항목들의 공통 원인: `RingEventQueue`의 생성자 변경이 `buf`의 크기와 이후 모든 큐 상태의 기반이 된다는 데이터 흐름을 놓쳤다.