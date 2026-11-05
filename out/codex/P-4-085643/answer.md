| 테스트 | 판단(남김/뺌) | 이유(한 줄) |
|---|---|---|
| DispatcherTest#testAcceptWhenSpace | 뺌 | RingEventQueue를 사용하지만 변경된 동작 경로를 검증하지 않음 |
| DispatcherTest#testAutoDrain | 뺌 | 큐의 변경된 동작을 직접 검증하지 않음 |
| DispatcherTest#testCriticalDrainsWhenAllCritical | 뺌 | 큐를 사용하지만 변경된 동작을 특정하지 않음 |
| DispatcherTest#testCriticalEvictsOldestNonCritical | 뺌 | 큐를 사용하지만 변경된 동작을 특정하지 않음 |
| DispatcherTest#testDrainDispatchesAll | 뺌 | 큐를 사용하지만 변경된 동작을 특정하지 않음 |
| DispatcherTest#testNullIsInvalid | 뺌 | 큐에 이벤트를 넣지 않아 변경된 큐 코드를 거치지 않음 |
| DispatcherTest#testRejectNonCriticalWhenFull | 남김 | offer()의 변경된 삽입 경로를 통해 큐를 채움 |
| EventParserTest#testAttributes | 뺌 | RingEventQueue와 변경된 클래스를 사용하지 않음 |
| EventParserTest#testBasicLine | 뺌 | RingEventQueue와 변경된 클래스를 사용하지 않음 |
| EventParserTest#testCelsiusTemperature | 뺌 | RingEventQueue와 변경된 클래스를 사용하지 않음 |
| EventParserTest#testFahrenheitIsNormalized | 뺌 | RingEventQueue와 변경된 클래스를 사용하지 않음 |
| EventParserTest#testUnknownCode | 뺌 | RingEventQueue와 변경된 클래스를 사용하지 않음 |
| HandlersTest#testCycleEndReleasesPower | 뺌 | RingEventQueue와 변경된 클래스를 사용하지 않음 |
| HandlersTest#testHeavyLoadNeedsPower | 뺌 | RingEventQueue와 변경된 클래스를 사용하지 않음 |
| HandlersTest#testHighTemperatureIsCounted | 뺌 | RingEventQueue와 변경된 클래스를 사용하지 않음 |
| HandlersTest#testLeakStopsRunningWasher | 뺌 | RingEventQueue와 변경된 클래스를 사용하지 않음 |
| HandlersTest#testUnknownDevice | 뺌 | RingEventQueue와 변경된 클래스를 사용하지 않음 |
| HomeHubTest#testFridgeOverheatRaisesAlarm | 남김 | HomeHub의 ingest와 drain을 통해 큐의 삽입·poll 경로를 실행함 |
| HomeHubTest#testInvalidLineIsDropped | 뺌 | 잘못된 입력이 큐에 들어가지 않아 변경된 코드를 거치지 않음 |
| HomeHubTest#testLeakDuringWashCycle | 남김 | HomeHub의 ingest와 drain을 통해 큐의 삽입·poll 경로를 실행함 |
| HomeHubTest#testWasherCycleEndToEnd | 남김 | HomeHub의 ingest와 drain을 통해 큐의 삽입·poll 경로를 실행함 |
| HomeHubTest#testWatchdogRecoversStuckQueue | 남김 | 큐가 가득 찬 상태에서 critical 이벤트 처리와 clear/snapshot 경로를 실행함 |
| PowerBudgetTest#testDenyOverCap | 뺌 | RingEventQueue와 변경된 클래스를 사용하지 않음 |
| PowerBudgetTest#testGrantWithinCap | 뺌 | RingEventQueue와 변경된 클래스를 사용하지 않음 |
| PowerBudgetTest#testIdempotentStart | 뺌 | RingEventQueue와 변경된 클래스를 사용하지 않음 |
| PowerBudgetTest#testRejectInvalidWatts | 뺌 | RingEventQueue와 변경된 클래스를 사용하지 않음 |
| PowerBudgetTest#testStopReleases | 뺌 | RingEventQueue와 변경된 클래스를 사용하지 않음 |
| RingEventQueueTest#testClearAndSnapshot | 남김 | 변경된 clear()와 snapshot()을 직접 실행함 |
| RingEventQueueTest#testFifoOrder | 남김 | 변경된 poll() 경로를 직접 실행함 |
| RingEventQueueTest#testFullAtCapacity | 남김 | 변경된 offer()의 삽입·용량 경로를 직접 실행함 |
| RingEventQueueTest#testNullRejected | 뺌 | null 조기 반환만 검증해 변경된 코드를 거치지 않음 |
| RingEventQueueTest#testPeekDoesNotRemove | 뺌 | 변경된 offer()의 핵심 삽입 경로를 충분히 거치지 않음 |
| RingEventQueueTest#testWrapAround | 남김 | 변경된 offer()와 poll()의 래핑 경로를 직접 실행함 |