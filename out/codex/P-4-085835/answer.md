| 테스트 | 판단(남김/뺌) | 이유(한 줄) |
|---|---|---|
| DispatcherTest#testAcceptWhenSpace | 남김 | Dispatcher가 queue.offer를 호출한다. |
| DispatcherTest#testAutoDrain | 남김 | Dispatcher가 queue.offer와 poll을 호출한다. |
| DispatcherTest#testCriticalDrainsWhenAllCritical | 남김 | Dispatcher가 queue.offer, poll을 호출한다. |
| DispatcherTest#testCriticalEvictsOldestNonCritical | 남김 | Dispatcher가 queue.offer, poll을 호출한다. |
| DispatcherTest#testDrainDispatchesAll | 남김 | Dispatcher의 drain이 queue.poll을 호출한다. |
| DispatcherTest#testNullIsInvalid | 뺌 | null 입력에서 종료되어 queue 메서드를 호출하지 않는다. |
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
| HomeHubTest#testInvalidLineIsDropped | 뺌 | 잘못된 입력에서 queue에 도달하기 전에 종료된다. |
| HomeHubTest#testLeakDuringWashCycle | 남김 | HomeHub 내부 Dispatcher가 queue.offer와 poll을 호출한다. |
| HomeHubTest#testWasherCycleEndToEnd | 남김 | HomeHub 내부 Dispatcher가 queue.offer와 poll을 호출한다. |
| HomeHubTest#testWatchdogRecoversStuckQueue | 남김 | HomeHub가 queue.offer, poll 및 clear를 호출한다. |
| PowerBudgetTest#testDenyOverCap | 뺌 | RingEventQueue를 만들거나 사용하지 않는다. |
| PowerBudgetTest#testGrantWithinCap | 뺌 | RingEventQueue를 만들거나 사용하지 않는다. |
| PowerBudgetTest#testIdempotentStart | 뺌 | RingEventQueue를 만들거나 사용하지 않는다. |
| PowerBudgetTest#testRejectInvalidWatts | 뺌 | RingEventQueue를 만들거나 사용하지 않는다. |
| PowerBudgetTest#testStopReleases | 뺌 | RingEventQueue를 만들거나 사용하지 않는다. |
| RingEventQueueTest#testClearAndSnapshot | 남김 | queue의 offer, snapshot, clear가 변경 메서드를 호출한다. |
| RingEventQueueTest#testFifoOrder | 남김 | queue의 offer와 poll이 변경 메서드다. |
| RingEventQueueTest#testFullAtCapacity | 남김 | queue의 offer가 변경 메서드다. |
| RingEventQueueTest#testNullRejected | 남김 | queue의 offer가 변경 메서드다. |
| RingEventQueueTest#testPeekDoesNotRemove | 남김 | queue의 offer가 변경 메서드다. |
| RingEventQueueTest#testWrapAround | 남김 | queue의 offer와 poll이 변경 메서드다. |