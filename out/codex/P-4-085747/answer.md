| 테스트 | 판단(남김/뺌) | 이유(한 줄) |
|---|---|---|
| DispatcherTest#testAcceptWhenSpace | 남김 | Dispatcher가 RingEventQueue.offer를 호출한다. |
| DispatcherTest#testAutoDrain | 남김 | Dispatcher가 offer와 poll을 호출한다. |
| DispatcherTest#testCriticalDrainsWhenAllCritical | 남김 | Dispatcher가 큐에 offer하고 drain 과정에서 poll한다. |
| DispatcherTest#testCriticalEvictsOldestNonCritical | 남김 | Dispatcher가 큐의 offer, snapshot, poll을 호출한다. |
| DispatcherTest#testDrainDispatchesAll | 남김 | Dispatcher의 drain이 큐의 poll을 호출한다. |
| DispatcherTest#testNullIsInvalid | 뺌 | null 입력은 큐에 도달하기 전에 거부된다. |
| DispatcherTest#testRejectNonCriticalWhenFull | 남김 | Dispatcher가 큐의 offer를 호출한다. |
| EventParserTest#testAttributes | 뺌 | RingEventQueue 또는 변경 메서드를 사용하지 않는다. |
| EventParserTest#testBasicLine | 뺌 | RingEventQueue 또는 변경 메서드를 사용하지 않는다. |
| EventParserTest#testCelsiusTemperature | 뺌 | RingEventQueue 또는 변경 메서드를 사용하지 않는다. |
| EventParserTest#testFahrenheitIsNormalized | 뺌 | RingEventQueue 또는 변경 메서드를 사용하지 않는다. |
| EventParserTest#testUnknownCode | 뺌 | RingEventQueue 또는 변경 메서드를 사용하지 않는다. |
| HandlersTest#testCycleEndReleasesPower | 뺌 | 핸들러와 PowerBudget만 사용하고 RingEventQueue를 사용하지 않는다. |
| HandlersTest#testHeavyLoadNeedsPower | 뺌 | 핸들러와 PowerBudget만 사용하고 RingEventQueue를 사용하지 않는다. |
| HandlersTest#testHighTemperatureIsCounted | 뺌 | TemperatureHandler만 사용하고 RingEventQueue를 사용하지 않는다. |
| HandlersTest#testLeakStopsRunningWasher | 뺌 | 핸들러와 PowerBudget만 사용하고 RingEventQueue를 사용하지 않는다. |
| HandlersTest#testUnknownDevice | 뺌 | 핸들러와 레지스트리만 사용하고 RingEventQueue를 사용하지 않는다. |
| HomeHubTest#testFridgeOverheatRaisesAlarm | 남김 | HomeHub의 ingest와 drain 경로가 큐의 offer와 poll을 호출한다. |
| HomeHubTest#testInvalidLineIsDropped | 뺌 | 잘못된 입력이 큐에 도달하기 전에 종료된다. |
| HomeHubTest#testLeakDuringWashCycle | 남김 | HomeHub의 ingest와 drain 경로가 큐의 offer와 poll을 호출한다. |
| HomeHubTest#testWasherCycleEndToEnd | 남김 | HomeHub의 ingest와 drain 경로가 큐의 offer와 poll을 호출한다. |
| HomeHubTest#testWatchdogRecoversStuckQueue | 남김 | HomeHub가 큐의 offer, clear, snapshot, poll을 호출한다. |
| PowerBudgetTest#testDenyOverCap | 뺌 | PowerBudget만 사용하고 RingEventQueue를 사용하지 않는다. |
| PowerBudgetTest#testGrantWithinCap | 뺌 | PowerBudget만 사용하고 RingEventQueue를 사용하지 않는다. |
| PowerBudgetTest#testIdempotentStart | 뺌 | PowerBudget만 사용하고 RingEventQueue를 사용하지 않는다. |
| PowerBudgetTest#testRejectInvalidWatts | 뺌 | PowerBudget만 사용하고 RingEventQueue를 사용하지 않는다. |
| PowerBudgetTest#testStopReleases | 뺌 | PowerBudget만 사용하고 RingEventQueue를 사용하지 않는다. |
| RingEventQueueTest#testClearAndSnapshot | 남김 | RingEventQueue의 snapshot과 clear를 직접 호출한다. |
| RingEventQueueTest#testFifoOrder | 남김 | RingEventQueue의 offer와 poll을 직접 호출한다. |
| RingEventQueueTest#testFullAtCapacity | 남김 | RingEventQueue의 offer를 직접 호출한다. |
| RingEventQueueTest#testNullRejected | 남김 | RingEventQueue의 offer를 직접 호출한다. |
| RingEventQueueTest#testPeekDoesNotRemove | 뺌 | peek만 호출하고 diff에서 바뀐 메서드는 호출하지 않는다. |
| RingEventQueueTest#testWrapAround | 남김 | RingEventQueue의 offer와 poll을 직접 호출한다. |