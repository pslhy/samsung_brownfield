| 항목 | 넣은 쪽 | 판단 | 맞은 쪽 | 근거 |
|---|---|---|---|---|
| `HomeHub#drain` | 도구 | 영향 있음 | 도구 | `drain`이 `step`을 호출하고 `step`이 변경된 큐의 `dispatchOne` 경로를 탄다. |
| `HomeHub#flushDerived` | 도구 | 영향 있음 | 도구 | `rules.takeOutbox()` 결과를 `dispatcher.submit`으로 큐에 넣는다. |
| `HomeHub#ingest` | 도구 | 영향 있음 | 도구 | 파싱 후 `dispatcher.submit`을 호출해 변경된 큐에 이벤트를 넣는다. |
| `HomeHub#step` | 도구 | 영향 있음 | 도구 | `dispatcher.dispatchOne()`이 변경된 큐의 `poll`을 사용한다. |
| `HomeHub#submit` | 도구 | 영향 있음 | 도구 | `dispatcher.submit(e)`가 변경된 큐의 `offer`를 사용한다. |
| `HomeHub#tick` | 도구 | 영향 있음 | 도구 | `watchdog.check()`가 큐의 `size`를 읽고, 회복 시 `queue.clear/snapshot/offer`를 사용한다. |
| `HubMain#main` | 도구 | 영향 있음 | 도구 | `main`이 `new HomeHub(config)`를 생성해 변경된 `RingEventQueue` 생성자를 실행한다. |
| `HubMain#run` | 도구 | 영향 있음 | 도구 | 입력 명령이 `hub.step/drain/tick/ingest`로 이어져 변경 큐를 사용한다. |
| `DeviceRegistry#byKind` | 도구 | 영향 있음 | 도구 | 직접 변경 큐를 사용하지 않으므로 영향 없음 | AI |
| `DeviceRegistry#get` | 도구 | 영향 없음 | AI | 큐와 무관하게 `devices.get(id)`만 수행한다. |
| `DeviceStateMachine#next` | 도구 | 영향 없음 | AI | 큐와 무관한 상태 전이 계산만 수행한다. |
| `Dispatcher#dispatchOne` | 도구 | 영향 있음 | 도구 | `queue.poll()`이 변경된 `RingEventQueue#poll`을 호출한다. |
| `Dispatcher#drain` | 도구 | 영향 있음 | 도구 | 반복적으로 변경된 큐의 `dispatchOne/poll` 경로를 탄다. |
| `Dispatcher#getDispatchedCount` | 도구 | 영향 없음 | AI | 변경된 값이나 큐를 읽지 않고 `dispatchedCount`만 반환한다. |
| `Dispatcher#submit` | 도구 | 영향 있음 | 도구 | `queue.offer`, `queue.size` 경로가 변경 큐에 의존한다. |
| `HandlerRegistry#dispatch` | 도구 | 영향 없음 | AI | 이벤트 핸들러 호출만 하며 큐를 참조하지 않는다. |
| `DeviceStatusHandler#handle` | 도구 | 영향 없음 | AI | 디바이스·전력·감사·메트릭만 갱신하고 큐를 참조하지 않는다. |
| `SafetyHandler#handle` | 도구 | 영향 없음 | AI | 디바이스·전력·감사·메트릭만 갱신하고 큐를 참조하지 않는다. |
| `TemperatureHandler#handle` | 도구 | 영향 없음 | AI | 디바이스 온도와 메트릭만 갱신하고 큐를 참조하지 않는다. |
| `Device#getConsecutiveHighTemp` | 도구 | 영향 없음 | AI | 큐와 무관하게 디바이스 필드만 반환한다. |
| `Device#getDoorOpenedAt` | 도구 | 영향 없음 | AI | 큐와 무관하게 디바이스 필드만 반환한다. |
| `Device#getFirmware` | 도구 | 영향 없음 | AI | 큐와 무관하게 디바이스 필드만 반환한다. |
| `Device#getLastSeen` | 도구 | 영향 없음 | AI | 큐와 무관하게 디바이스 필드만 반환한다. |
| `Device#getLastTemp` | 도구 | 영향 없음 | AI | 큐와 무관하게 디바이스 필드만 반환한다. |
| `Device#getStatus` | 도구 | 영향 없음 | AI | 큐와 무관하게 디바이스 필드만 반환한다. |
| `Device#isDoorOpen` | 도구 | 영향 없음 | AI | 큐와 무관하게 디바이스 필드만 반환한다. |
| `Device#setConsecutiveHighTemp` | 도구 | 영향 없음 | AI | 큐와 무관하게 디바이스 필드만 변경한다. |
| `Device#setDoorOpen` | 도구 | 영향 없음 | AI | 큐와 무관하게 디바이스 필드만 변경한다. |
| `Device#setFirmware` | 도구 | 영향 없음 | AI | 큐와 무관하게 디바이스 필드만 변경한다. |
| `Device#setLastSeen` | 도구 | 영향 없음 | AI | 큐와 무관하게 디바이스 필드만 변경한다. |
| `Device#setLastTemp` | 도구 | 영향 없음 | AI | 큐와 무관하게 디바이스 필드만 변경한다. |
| `Device#setStatus` | 도구 | 영향 없음 | AI | 큐와 무관하게 디바이스 필드만 변경한다. |
| `Device#toString` | 도구 | 영향 없음 | AI | 큐와 무관하게 디바이스 필드 문자열만 만든다. |
| `Event#<init>` | 도구 | 영향 없음 | AI | 큐에 저장될 수 있는 객체를 만들지만 생성자 내부 값은 큐 변경값을 거치지 않는다. |
| `Event#attr` | 도구 | 영향 없음 | AI | 이벤트의 `attrs`만 조회한다. |
| `Event#equals` | 도구 | 영향 없음 | AI | 이벤트 식별 필드만 비교하며 큐 변경값을 거치지 않는다. |
| `Event#getAttrs` | 도구 | 영향 없음 | AI | 이벤트의 불변 `attrs`만 반환한다. |
| `Event#getDeviceId` | 도구 | 영향 없음 | AI | 이벤트 필드만 반환한다. |
| `Event#getSeq` | 도구 | 영향 없음 | AI | 이벤트 필드만 반환한다. |
| `Event#getTimestamp` | 도구 | 영향 없음 | AI | 이벤트 필드만 반환한다. |
| `Event#getType` | 도구 | 영향 없음 | AI | 이벤트 필드만 반환한다. |
| `Event#getValue` | 도구 | 영향 없음 | AI | 이벤트 필드만 반환한다. |
| `Event#hashCode` | 도구 | 영향 없음 | AI | 이벤트 식별 필드만 계산한다. |
| `Event#toString` | 도구 | 영향 없음 | AI | 이벤트 필드만 문자열화한다. |
| `AuditLog#contains` | 도구 | 영향 없음 | AI | 감사 로그의 기존 문자열만 검사한다. |
| `AuditLog#count` | 도구 | 영향 없음 | AI | 감사 로그의 기존 문자열만 센다. |
| `AuditLog#dump` | 도구 | 영향 없음 | AI | 감사 로그만 문자열로 반환한다. |
| `AuditLog#note` | 도구 | 영향 없음 | AI | 감사 로그 필드만 변경한다. |
| `AuditLog#record` | 도구 | 영향 없음 | AI | 감사 로그 필드만 변경한다. |
| `AuditLog#size` | 도구 | 영향 없음 | AI | 감사 로그 크기만 반환한다. |
| `AuditLog#tail` | 도구 | 영향 없음 | AI | 감사 로그의 일부만 복사한다. |
| `Metrics#get` | 도구 | 영향 없음 | AI | 메트릭 카운터만 조회한다. |
| `Metrics#increment` | 도구 | 영향 없음 | AI | 메트릭 카운터만 변경한다. |
| `Metrics#isEmpty` | 도구 | 영향 없음 | AI | 메트릭 맵만 검사한다. |
| `Metrics#reset` | 도구 | 영향 없음 | AI | 메트릭 맵만 비운다. |
| `Metrics#snapshot` | 도구 | 영향 없음 | AI | 메트릭 맵만 문자열화한다. |
| `Watchdog#check` | 도구 | 영향 있음 | 도구 | `queue.size()`를 조건과 감사 메시지에 사용한다. |
| `Watchdog#getHighWaterChecks` | 도구 | 영향 없음 | AI | 큐를 읽지 않고 자체 카운터만 반환한다. |
| `PowerBudget#headroom` | 도구 | 영향 없음 | AI | 전력 맵과 `capWatts`만 계산한다. |
| `PowerBudget#isIdle` | 도구 | 영향 없음 | AI | 전력 맵만 검사한다. |
| `PowerBudget#isRunning` | 도구 | 영향 없음 | AI | 전력 맵만 검사한다. |
| `PowerBudget#runningDevices` | 도구 | 영향 없음 | AI | 전력 맵만 정렬·복사한다. |
| `PowerBudget#stop` | 도구 | 영향 없음 | AI | 전력 맵만 변경한다. |
| `PowerBudget#stopAll` | 도구 | 영향 없음 | AI | 전력 맵만 비운다. |
| `PowerBudget#totalLoad` | 도구 | 영향 없음 | AI | 전력 맵만 합산한다. |
| `PowerBudget#tryStart` | 도구 | 영향 없음 | AI | 전력 맵과 전력 한도만 사용한다. |
| `RingEventQueue#isEmpty` | 도구 | 영향 있음 | 도구 | 변경된 `count`를 반환한다. |
| `RingEventQueue#peek` | 도구 | 영향 있음 | 도구 | 변경된 `head/count/buf`를 통해 반환값을 결정한다. |
| `RingEventQueue#size` | 도구 | 영향 있음 | 도구 | 변경된 큐의 `count`를 반환한다. |
| `RuleEngine#afterDispatch` | 도구 | 영향 없음 | AI | 디바이스 상태와 이벤트만 사용하고 큐를 참조하지 않는다. |
| `RuleEngine#isLatched` | 도구 | 영향 없음 | AI | `overheatLatched`만 조회한다. |
| `RuleEngine#takeOutbox` | 도구 | 영향 없음 | AI | 룰 엔진의 `outbox`만 복사·초기화한다. |
| `RingEventQueue#<init>` | AI만 | 영향 있음 | AI | 생성자가 변경 파일의 `buf`를 초기화하며, 이후 모든 큐 동작의 저장 구조를 결정한다. |
| `DispatcherTest#testAcceptWhenSpace` | 도구 | 영향 있음 | 도구 | `dispatcher.submit`이 변경된 `offer`와 `size`를 사용한다. |
| `DispatcherTest#testNullIsInvalid` | 도구 | 영향 없음 | AI | `submit(null)`은 큐에 도달하기 전에 `e == null`에서 반환한다. |
| `DispatcherTest#testRejectNonCriticalWhenFull` | 도구 | 영향 있음 | 도구 | 큐 포화와 `submit.rejected` 결과가 `offer/size`에 의존한다. |
| `EventParserTest#testAttributes` | 도구 | 영향 없음 | AI | 파서와 `Event.attr`만 검사하고 큐를 사용하지 않는다. |
| `EventParserTest#testBasicLine` | 도구 | 영향 없음 | AI | 파서와 이벤트 필드만 검사한다. |
| `EventParserTest#testCelsiusTemperature` | 도구 | 영향 없음 | AI | 파서의 섭씨 값과 이벤트 값만 검사한다. |
| `EventParserTest#testFahrenheitIsNormalized` | 도구 | 영향 없음 | AI | 파서의 화씨 변환과 이벤트 값만 검사한다. |
| `EventParserTest#testUnknownCode` | 도구 | 영향 없음 | AI | 파서와 `EventType`만 검사한다. |
| `HandlersTest#testCycleEndReleasesPower` | 도구 | 영향 없음 | AI | 핸들러와 `PowerBudget`만 사용하고 큐를 만들지 않는다. |
| `HandlersTest#testHeavyLoadNeedsPower` | 도구 | 영향 없음 | AI | 핸들러·디바이스·전력·감사만 사용한다. |
| `HandlersTest#testHighTemperatureIsCounted` | 도구 | 영향 없음 | AI | 온도 핸들러와 디바이스 필드만 검사한다. |
| `HandlersTest#testLeakStopsRunningWasher` | 도구 | 영향 없음 | AI | 안전 핸들러와 전력·디바이스만 검사한다. |
| `HandlersTest#testUnknownDevice` | 도구 | 영향 없음 | AI | 알 수 없는 디바이스 처리와 메트릭만 검사한다. |
| `HomeHubTest#testFridgeOverheatRaisesAlarm` | 도구 | 영향 있음 | 도구 | `HomeHub.ingest/drain`이 큐의 `offer/poll`을 통해 온도·파생 과열 이벤트를 처리한다. |
| `HomeHubTest#testInvalidLineIsDropped` | 도구 | 영향 없음 | AI | 잘못된 입력은 `parser.parse` 후 `dispatcher.submit` 없이 반환된다. |
| `HomeHubTest#testLeakDuringWashCycle` | 도구 | 영향 있음 | 도구 | 세 이벤트의 수신·배출 순서가 변경된 큐의 `offer/poll`에 의존한다. |
| `HomeHubTest#testWasherCycleEndToEnd` | 도구 | 영향 있음 | 도구 | ingest와 drain이 변경된 큐를 거쳐 상태·전력 결과를 만든다. |
| `PowerBudgetTest#testDenyOverCap` | 도구 | 영향 없음 | AI | 전력 한도 계산만 검사한다. |
| `PowerBudgetTest#testGrantWithinCap` | 도구 | 영향 없음 | AI | 전력 grant와 `totalLoad`만 검사한다. |
| `PowerBudgetTest#testIdempotentStart` | 도구 | 영향 없음 | AI | 전력 맵의 중복 시작 처리만 검사한다. |
| `PowerBudgetTest#testRejectInvalidWatts` | 도구 | 영향 없음 | AI | `tryStart`의 인자 검증만 검사한다. |
| `PowerBudgetTest#testStopReleases` | 도구 | 영향 없음 | AI | 전력 맵의 제거와 headroom만 검사한다. |
| `RingEventQueueTest#testNullRejected` | 도구 | 영향 있음 | 도구 | `offer(null)`은 변경된 큐 메서드 자체를 실행하며 반환값과 크기를 검사한다. |
| `RingEventQueueTest#testPeekDoesNotRemove` | 도구 | 영향 있음 | 도구 | 변경된 `offer`, `peek`, `size`의 결과를 직접 검사한다. |

도구가 틀린 항목의 공통 원인: 변경된 큐 구현과 호출 그래프를 따라가며 큐와 무관한 메서드·테스트까지 과도하게 확장했다.

AI가 틀린 항목의 공통 원인: `RingEventQueue` 생성자와 큐의 직접 메서드 호출을 영향 경로에서 누락했다.