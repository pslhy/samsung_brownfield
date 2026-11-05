| 테스트 | 판단(남김/뺌) | 이유(한 줄) |
|---|---|---|
| DispatcherTest#testAcceptWhenSpace | 남김 | Dispatcher가 queue.offer를 호출한다. |
| DispatcherTest#testAutoDrain | 남김 | Dispatcher가 queue.offer 및 poll을 호출한다. |
| DispatcherTest#testCriticalDrainsWhenAllCritical | 남김 | Dispatcher가 queue.offer 및 poll을 호출한다. |
| DispatcherTest#testCriticalEvictsOldestNonCritical | 남김 | Dispatcher가 queue.offer 및 poll을 호출한다. |
| DispatcherTest#testDrainDispatchesAll | 남김 | Dispatcher가 queue.offer 및 poll을 호출한다. |
| DispatcherTest#testNullIsInvalid | 뺌 | null 입력은 큐 메서드 호출 전에 거부된다. |
| DispatcherTest#testRejectNonCriticalWhenFull | 남김 | Dispatcher가 queue.offer를 호출한다. |
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
| HomeHubTest#testFridgeOverheatRaisesAlarm | 남김 | HomeHub 내부 Dispatcher가 queue.offer와 poll을 호출한다. |
| HomeHubTest#testInvalidLineIsDropped | 뺌 | 잘못된 입력이 큐에 도달하기 전에 끝난다. |
| HomeHubTest#testLeakDuringWashCycle | 남김 | HomeHub 내부 Dispatcher가 queue.offer와 poll을 호출한다. |
| HomeHubTest#testWasherCycleEndToEnd | 남김 | HomeHub 내부 Dispatcher가 queue.offer와 poll을 호출한다. |
| HomeHubTest#testWatchdogRecoversStuckQueue | 남김 | HomeHub 내부 queue의 offer, poll 또는 snapshot을 호출한다. |
| PowerBudgetTest#testDenyOverCap | 뺌 | RingEventQueue를 만들거나 사용하지 않는다. |
| PowerBudgetTest#testGrantWithinCap | 뺌 | RingEventQueue를 만들거나 사용하지 않는다. |
| PowerBudgetTest#testIdempotentStart | 뺌 | RingEventQueue를 만들거나 사용하지 않는다. |
| PowerBudgetTest#testRejectInvalidWatts | 뺌 | RingEventQueue를 만들거나 사용하지 않는다. |
| PowerBudgetTest#testStopReleases | 뺌 | RingEventQueue를 만들거나 사용하지 않는다. |
| RingEventQueueTest#testClearAndSnapshot | 남김 | queue.offer, snapshot, clear를 직접 호출한다. |
| RingEventQueueTest#testFifoOrder | 남김 | queue.offer와 poll을 직접 호출한다. |
| RingEventQueueTest#testFullAtCapacity | 남김 | queue.offer를 직접 호출한다. |
| RingEventQueueTest#testNullRejected | 남김 | queue.offer를 직접 호출한다. |
| RingEventQueueTest#testPeekDoesNotRemove | 남김 | queue.offer를 직접 호출한다. |
| RingEventQueueTest#testWrapAround | 남김 | queue.offer와 poll을 직접 호출한다. |