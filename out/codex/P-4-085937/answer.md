| 테스트 | 판단(남김/뺌) | 이유(한 줄) |
|---|---|---|
| DispatcherTest#testAcceptWhenSpace | 남김 | submit이 RingEventQueue.offer를 호출한다. |
| DispatcherTest#testAutoDrain | 남김 | submit과 자동 drain에서 offer와 poll이 호출된다. |
| DispatcherTest#testCriticalDrainsWhenAllCritical | 남김 | submit 과정에서 offer와 poll이 호출된다. |
| DispatcherTest#testCriticalEvictsOldestNonCritical | 남김 | submit 과정에서 offer와 poll이 호출된다. |
| DispatcherTest#testDrainDispatchesAll | 남김 | submit과 drain에서 offer와 poll이 호출된다. |
| DispatcherTest#testNullIsInvalid | 뺌 | null 입력은 큐 메서드에 도달하지 않고 끝난다. |
| DispatcherTest#testRejectNonCriticalWhenFull | 남김 | submit 과정에서 offer가 호출된다. |
| EventParserTest#testAttributes | 뺌 | RingEventQueue를 만들거나 사용하지 않는다. |
| EventParserTest#testBasicLine | 뺌 | RingEventQueue를 만들거나 사용하지 않는다. |
| EventParserTest#testCelsiusTemperature | 뺌 | RingEventQueue를 만들거나 사용하지 않는다. |
| EventParserTest#testFahrenheitIsNormalized | 뺌 | RingEventQueue를 만들거나 사용하지 않는다. |
| EventParserTest#testUnknownCode | 뺌 | RingEventQueue를 만들거나 사용하지 않는다. |
| HandlersTest#testCycleEndReleasesPower | 뺌 | RingEventQueue를 만들거나 사용하지 않는다. |
| HandlersTest#testHeavyLoadNeedsPower | 뺌 | RingEventQueue를 만들거나 사용하지 않는다. |
| HandlersTest#testHighTemperatureIsCounted | 뺌 | RingEventQueue를 만들거나 사용하지 않는다. |
| HandlersTest#testLeakStopsRunningWasher | 뺌 | RingEventQueue를 만들거나 사용하지 않는다. |
| HandlersTest#testUnknownDevice | 뺌 | RingEventQueue를 만들거나 사용하지 않는다. |
| HomeHubTest#testFridgeOverheatRaisesAlarm | 남김 | HomeHub의 ingest와 drain이 큐의 offer와 poll을 호출한다. |
| HomeHubTest#testInvalidLineIsDropped | 뺌 | 잘못된 입력은 큐에 제출되기 전에 끝난다. |
| HomeHubTest#testLeakDuringWashCycle | 남김 | HomeHub의 ingest와 drain이 큐의 offer와 poll을 호출한다. |
| HomeHubTest#testWasherCycleEndToEnd | 남김 | HomeHub의 ingest와 drain이 큐의 offer와 poll을 호출한다. |
| HomeHubTest#testWatchdogRecoversStuckQueue | 남김 | HomeHub의 ingest와 tick이 큐의 offer, poll, clear 등을 호출한다. |
| PowerBudgetTest#testDenyOverCap | 뺌 | RingEventQueue를 만들거나 사용하지 않는다. |
| PowerBudgetTest#testGrantWithinCap | 뺌 | RingEventQueue를 만들거나 사용하지 않는다. |
| PowerBudgetTest#testIdempotentStart | 뺌 | RingEventQueue를 만들거나 사용하지 않는다. |
| PowerBudgetTest#testRejectInvalidWatts | 뺌 | RingEventQueue를 만들거나 사용하지 않는다. |
| PowerBudgetTest#testStopReleases | 뺌 | RingEventQueue를 만들거나 사용하지 않는다. |
| RingEventQueueTest#testClearAndSnapshot | 남김 | snapshot과 clear가 변경된 메서드다. |
| RingEventQueueTest#testFifoOrder | 남김 | offer와 poll이 호출된다. |
| RingEventQueueTest#testFullAtCapacity | 남김 | offer가 호출된다. |
| RingEventQueueTest#testNullRejected | 남김 | offer가 호출된다. |
| RingEventQueueTest#testPeekDoesNotRemove | 남김 | offer가 호출된다. |
| RingEventQueueTest#testWrapAround | 남김 | offer와 poll이 호출된다. |