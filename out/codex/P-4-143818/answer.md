| 테스트 | 판단(남김/뺌) | 이유(한 줄) |
|---|---|---|
| DispatcherTest#testAcceptWhenSpace | 남김 | `submit`이 큐의 `offer`를 호출한다. |
| DispatcherTest#testAutoDrain | 남김 | 큐가 가득 차 `offer`와 `poll`이 호출된다. |
| DispatcherTest#testCriticalDrainsWhenAllCritical | 남김 | 큐의 `offer`, `snapshot`, `poll`이 호출된다. |
| DispatcherTest#testCriticalEvictsOldestNonCritical | 남김 | 큐의 `offer`, `snapshot`, `poll`이 호출된다. |
| DispatcherTest#testDrainDispatchesAll | 남김 | `drain`이 큐의 `poll`을 호출한다. |
| DispatcherTest#testNullIsInvalid | 뺌 | null 입력은 큐에 도달하기 전에 거부된다. |
| DispatcherTest#testRejectNonCriticalWhenFull | 남김 | 큐가 가득 찰 때 `offer`가 호출된다. |
| EventParserTest#testAttributes | 뺌 | 큐와 바뀐 메서드를 사용하지 않는다. |
| EventParserTest#testBasicLine | 뺌 | 큐와 바뀐 메서드를 사용하지 않는다. |
| EventParserTest#testCelsiusTemperature | 뺌 | 큐와 바뀐 메서드를 사용하지 않는다. |
| EventParserTest#testFahrenheitIsNormalized | 뺌 | 큐와 바뀐 메서드를 사용하지 않는다. |
| EventParserTest#testUnknownCode | 뺌 | 큐와 바뀐 메서드를 사용하지 않는다. |
| HandlersTest#testCycleEndReleasesPower | 뺌 | 큐와 바뀐 메서드를 사용하지 않는다. |
| HandlersTest#testHeavyLoadNeedsPower | 뺌 | 큐와 바뀐 메서드를 사용하지 않는다. |
| HandlersTest#testHighTemperatureIsCounted | 뺌 | 큐와 바뀐 메서드를 사용하지 않는다. |
| HandlersTest#testLeakStopsRunningWasher | 뺌 | 큐와 바뀐 메서드를 사용하지 않는다. |
| HandlersTest#testUnknownDevice | 뺌 | 큐와 바뀐 메서드를 사용하지 않는다. |
| HomeHubTest#testFridgeOverheatRaisesAlarm | 남김 | `ingest`와 `drain`을 통해 큐의 `offer`와 `poll`이 호출된다. |
| HomeHubTest#testInvalidLineIsDropped | 뺌 | 잘못된 입력이 큐에 도달하기 전에 삭제된다. |
| HomeHubTest#testLeakDuringWashCycle | 남김 | `ingest`와 `drain`을 통해 큐의 `offer`와 `poll`이 호출된다. |
| HomeHubTest#testWasherCycleEndToEnd | 남김 | `ingest`와 `drain`을 통해 큐의 `offer`와 `poll`이 호출된다. |
| HomeHubTest#testWatchdogRecoversStuckQueue | 남김 | 큐의 `offer`, `poll`, `clear`가 호출된다. |
| PowerBudgetTest#testDenyOverCap | 뺌 | 큐와 바뀐 메서드를 사용하지 않는다. |
| PowerBudgetTest#testGrantWithinCap | 뺌 | 큐와 바뀐 메서드를 사용하지 않는다. |
| PowerBudgetTest#testIdempotentStart | 뺌 | 큐와 바뀐 메서드를 사용하지 않는다. |
| PowerBudgetTest#testRejectInvalidWatts | 뺌 | 큐와 바뀐 메서드를 사용하지 않는다. |
| PowerBudgetTest#testStopReleases | 뺌 | 큐와 바뀐 메서드를 사용하지 않는다. |
| RingEventQueueTest#testClearAndSnapshot | 남김 | `offer`, `snapshot`, `clear`를 직접 호출한다. |
| RingEventQueueTest#testFifoOrder | 남김 | `offer`와 `poll`을 직접 호출한다. |
| RingEventQueueTest#testFullAtCapacity | 남김 | `offer`를 직접 호출한다. |
| RingEventQueueTest#testNullRejected | 남김 | `offer`를 직접 호출한다. |
| RingEventQueueTest#testPeekDoesNotRemove | 남김 | `offer`를 직접 호출한다. |
| RingEventQueueTest#testWrapAround | 남김 | `offer`와 `poll`을 직접 호출한다. |