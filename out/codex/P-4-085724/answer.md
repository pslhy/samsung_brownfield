| 테스트 | 판단(남김/뺌) | 이유(한 줄) |
|---|---|---|
| DispatcherTest#testAcceptWhenSpace | 남김 | submit 중 RingEventQueue.offer가 호출된다. |
| DispatcherTest#testAutoDrain | 남김 | submit 및 자동 drain 중 offer와 poll이 호출된다. |
| DispatcherTest#testCriticalDrainsWhenAllCritical | 남김 | 큐가 가득 차 critical 처리 중 poll과 offer가 호출된다. |
| DispatcherTest#testCriticalEvictsOldestNonCritical | 남김 | critical 제출 중 큐의 poll과 offer가 호출된다. |
| DispatcherTest#testDrainDispatchesAll | 남김 | drain이 큐의 poll을 호출한다. |
| DispatcherTest#testNullIsInvalid | 뺌 | null 검증에서 종료되어 큐 메서드가 호출되지 않는다. |
| DispatcherTest#testRejectNonCriticalWhenFull | 남김 | 세 번의 정상 submit에서 offer가 호출된다. |
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
| HomeHubTest#testFridgeOverheatRaisesAlarm | 남김 | HomeHub ingest와 drain을 통해 offer와 poll이 호출된다. |
| HomeHubTest#testInvalidLineIsDropped | 뺌 | 잘못된 입력에서 큐에 도달하기 전에 종료된다. |
| HomeHubTest#testLeakDuringWashCycle | 남김 | HomeHub ingest와 drain을 통해 offer와 poll이 호출된다. |
| HomeHubTest#testWasherCycleEndToEnd | 남김 | HomeHub ingest와 drain을 통해 offer와 poll이 호출된다. |
| HomeHubTest#testWatchdogRecoversStuckQueue | 남김 | HomeHub의 큐 복구 과정에서 offer, poll, clear가 호출된다. |
| PowerBudgetTest#testDenyOverCap | 뺌 | RingEventQueue를 만들거나 사용하지 않는다. |
| PowerBudgetTest#testGrantWithinCap | 뺌 | RingEventQueue를 만들거나 사용하지 않는다. |
| PowerBudgetTest#testIdempotentStart | 뺌 | RingEventQueue를 만들거나 사용하지 않는다. |
| PowerBudgetTest#testRejectInvalidWatts | 뺌 | RingEventQueue를 만들거나 사용하지 않는다. |
| PowerBudgetTest#testStopReleases | 뺌 | RingEventQueue를 만들거나 사용하지 않는다. |
| RingEventQueueTest#testClearAndSnapshot | 남김 | snapshot과 clear가 변경된 메서드들을 직접 호출한다. |
| RingEventQueueTest#testFifoOrder | 남김 | offer와 poll을 직접 호출한다. |
| RingEventQueueTest#testFullAtCapacity | 남김 | offer를 직접 호출한다. |
| RingEventQueueTest#testNullRejected | 남김 | offer(null)이 변경된 offer 메서드를 호출한다. |
| RingEventQueueTest#testPeekDoesNotRemove | 남김 | offer를 직접 호출한다. |
| RingEventQueueTest#testWrapAround | 남김 | offer와 poll을 직접 호출한다. |