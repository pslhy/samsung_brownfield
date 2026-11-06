| 테스트 | 판단(남김/뺌) | 이유(한 줄) |
|---|---|---|
| DispatcherTest#testAcceptWhenSpace | 남김 | `submit`이 큐의 `offer`를 호출한다. |
| DispatcherTest#testAutoDrain | 남김 | 큐가 가득 차며 `offer`와 `poll`이 실행된다. |
| DispatcherTest#testCriticalDrainsWhenAllCritical | 남김 | 임계 이벤트 제출 중 `offer`, `poll`이 실행된다. |
| DispatcherTest#testCriticalEvictsOldestNonCritical | 남김 | 큐의 `offer`, `snapshot`, `poll`이 실행된다. |
| DispatcherTest#testDrainDispatchesAll | 남김 | `drain`에서 큐의 `poll`이 실행된다. |
| DispatcherTest#testNullIsInvalid | 뺌 | null 입력에서 큐에 도달하지 않고 끝난다. |
| DispatcherTest#testRejectNonCriticalWhenFull | 남김 | 큐가 가득 차도록 `offer`가 실행된다. |
| EventParserTest#testAttributes | 뺌 | 이벤트 파싱만 하며 큐를 사용하지 않는다. |
| EventParserTest#testBasicLine | 뺌 | 이벤트 파싱만 하며 큐를 사용하지 않는다. |
| EventParserTest#testCelsiusTemperature | 뺌 | 이벤트 파싱만 하며 큐를 사용하지 않는다. |
| EventParserTest#testFahrenheitIsNormalized | 뺌 | 이벤트 파싱만 하며 큐를 사용하지 않는다. |
| EventParserTest#testUnknownCode | 뺌 | 이벤트 파싱만 하며 큐를 사용하지 않는다. |
| HandlersTest#testCycleEndReleasesPower | 뺌 | 핸들러와 전력 관리만 사용하며 큐를 사용하지 않는다. |
| HandlersTest#testHeavyLoadNeedsPower | 뺌 | 핸들러와 전력 관리만 사용하며 큐를 사용하지 않는다. |
| HandlersTest#testHighTemperatureIsCounted | 뺌 | 온도 핸들러만 사용하며 큐를 사용하지 않는다. |
| HandlersTest#testLeakStopsRunningWasher | 뺌 | 핸들러와 전력 관리만 사용하며 큐를 사용하지 않는다. |
| HandlersTest#testUnknownDevice | 뺌 | 핸들러와 레지스트리만 사용하며 큐를 사용하지 않는다. |
| HomeHubTest#testFridgeOverheatRaisesAlarm | 남김 | `ingest`와 `drain` 과정에서 큐의 `offer`, `poll`이 실행된다. |
| HomeHubTest#testInvalidLineIsDropped | 뺌 | 잘못된 입력이 파서에서 탈락해 큐에 도달하지 않는다. |
| HomeHubTest#testLeakDuringWashCycle | 남김 | `ingest`와 `drain` 과정에서 큐의 `offer`, `poll`이 실행된다. |
| HomeHubTest#testWasherCycleEndToEnd | 남김 | `ingest`와 `drain` 과정에서 큐의 `offer`, `poll`이 실행된다. |
| HomeHubTest#testWatchdogRecoversStuckQueue | 남김 | 이벤트 제출과 watchdog 처리 중 큐의 `offer`, `poll`, `clear`, `snapshot`이 실행된다. |
| PowerBudgetTest#testDenyOverCap | 뺌 | 전력 예산만 사용하며 큐를 사용하지 않는다. |
| PowerBudgetTest#testGrantWithinCap | 뺌 | 전력 예산만 사용하며 큐를 사용하지 않는다. |
| PowerBudgetTest#testIdempotentStart | 뺌 | 전력 예산만 사용하며 큐를 사용하지 않는다. |
| PowerBudgetTest#testRejectInvalidWatts | 뺌 | 전력 예산만 사용하며 큐를 사용하지 않는다. |
| PowerBudgetTest#testStopReleases | 뺌 | 전력 예산만 사용하며 큐를 사용하지 않는다. |
| RingEventQueueTest#testClearAndSnapshot | 남김 | `offer`, `snapshot`, `clear`가 실행된다. |
| RingEventQueueTest#testFifoOrder | 남김 | `offer`와 `poll`이 실행된다. |
| RingEventQueueTest#testFullAtCapacity | 남김 | 용량 초과까지 `offer`가 실행된다. |
| RingEventQueueTest#testNullRejected | 남김 | 큐의 `offer(null)`이 실행된다. |
| RingEventQueueTest#testPeekDoesNotRemove | 뺌 | `peek`와 `offer`만 실행하며 diff의 변경 메서드를 호출하지 않는다. |
| RingEventQueueTest#testWrapAround | 남김 | 순환 동작으로 `offer`와 `poll`이 실행된다. |