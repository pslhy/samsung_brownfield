아래는 **변경으로 인한 잠재적 회귀 영향 범위**다. 정상적인 큐 불변식에서는 기존 코드와 새 코드의 FIFO 결과가 같아야 한다. 그러나 인덱스 계산이나 초기화에 오류가 생기면 `buf/head/count → 반환 이벤트·큐 크기 → 디스패치 → 장치·전력·규칙·로그·메트릭`으로 영향이 전파되므로, 직접 호출자만으로 범위를 제한하면 안 된다.

파라미터 타입은 완전 수식명으로 표기했다. 생성자, 인터페이스 선언, JDK 메서드와 테스트 보조 함수는 실행 결과를 관찰하는 운영 메서드 목록에서 제외했다.

**1. 변경 메서드와 큐 필드를 통해 영향을 받는 메서드**

```text
com.dxlab.homehub.queue.RingEventQueue#offer(com.dxlab.homehub.model.Event)
com.dxlab.homehub.queue.RingEventQueue#poll()
com.dxlab.homehub.queue.RingEventQueue#clear()
com.dxlab.homehub.queue.RingEventQueue#snapshot()
com.dxlab.homehub.queue.RingEventQueue#peek()
com.dxlab.homehub.queue.RingEventQueue#size()
com.dxlab.homehub.queue.RingEventQueue#isEmpty()
```

`peek()`는 `buf/head`, `size()`와 `isEmpty()`는 `count`를 읽는다. `capacity()`는 변경되지 않는 배열 길이만 읽으므로 결과 영향 대상이 아니다.

**2. 큐 반환값·상태를 사용하는 메서드와 상위 실행 경로**

```text
com.dxlab.homehub.dispatch.Dispatcher#submit(com.dxlab.homehub.model.Event)
com.dxlab.homehub.dispatch.Dispatcher#evictOldestNonCritical()
com.dxlab.homehub.dispatch.Dispatcher#dispatchOne()
com.dxlab.homehub.dispatch.Dispatcher#drain()
com.dxlab.homehub.dispatch.Dispatcher#getDispatchedCount()
com.dxlab.homehub.ops.RecoveryManager#recover()
com.dxlab.homehub.ops.Watchdog#check()
com.dxlab.homehub.ops.Watchdog#getHighWaterChecks()
com.dxlab.homehub.app.HomeHub#ingest(java.lang.String)
com.dxlab.homehub.app.HomeHub#submit(com.dxlab.homehub.model.Event)
com.dxlab.homehub.app.HomeHub#step()
com.dxlab.homehub.app.HomeHub#drain()
com.dxlab.homehub.app.HomeHub#tick()
com.dxlab.homehub.app.HomeHub#flushDerived()
com.dxlab.homehub.app.HomeHub#observable()
com.dxlab.homehub.app.HubMain#run(com.dxlab.homehub.app.HomeHub, java.lang.String, java.io.PrintStream)
com.dxlab.homehub.app.HubMain#main(java.lang.String[])
```

특히 `getDispatchedCount()`와 `getHighWaterChecks()`는 큐를 직접 호출하지 않아도, 앞선 실행이 바꾼 필드를 반환하므로 포함한다.

**3. 반환 이벤트와 디스패치 여부·순서가 전파되는 처리 경로**

```text
com.dxlab.homehub.dispatch.HandlerRegistry#dispatch(com.dxlab.homehub.model.Event)
com.dxlab.homehub.handlers.CountingHandler#handle(com.dxlab.homehub.model.Event)
com.dxlab.homehub.handlers.DeviceStatusHandler#handle(com.dxlab.homehub.model.Event)
com.dxlab.homehub.handlers.TemperatureHandler#handle(com.dxlab.homehub.model.Event)
com.dxlab.homehub.handlers.SafetyHandler#handle(com.dxlab.homehub.model.Event)
com.dxlab.homehub.device.DeviceStateMachine#next(com.dxlab.homehub.model.DeviceStatus, com.dxlab.homehub.model.EventType)
com.dxlab.homehub.rules.RuleEngine#afterDispatch(com.dxlab.homehub.model.Event)
com.dxlab.homehub.rules.RuleEngine#takeOutbox()
com.dxlab.homehub.rules.RuleEngine#isLatched(java.lang.String)
```

`RuleEngine`의 `outbox`, `overheatLatched`, `nextSeq`도 영향 경로다. 따라서 파생 이벤트의 내용·순서·발행 여부와 이후 큐 처리까지 다시 영향을 받을 수 있다.

**4. 장치 필드 쓰기와 후속 관찰 메서드**

```text
com.dxlab.homehub.model.Device#setStatus(com.dxlab.homehub.model.DeviceStatus)
com.dxlab.homehub.model.Device#getStatus()
com.dxlab.homehub.model.Device#setLastSeen(long)
com.dxlab.homehub.model.Device#getLastSeen()
com.dxlab.homehub.model.Device#setLastTemp(java.lang.Integer)
com.dxlab.homehub.model.Device#getLastTemp()
com.dxlab.homehub.model.Device#setConsecutiveHighTemp(int)
com.dxlab.homehub.model.Device#getConsecutiveHighTemp()
com.dxlab.homehub.model.Device#setDoorOpen(boolean, long)
com.dxlab.homehub.model.Device#isDoorOpen()
com.dxlab.homehub.model.Device#getDoorOpenedAt()
com.dxlab.homehub.model.Device#setFirmware(java.lang.String)
com.dxlab.homehub.model.Device#getFirmware()
com.dxlab.homehub.model.Device#toString()
```

장치 객체를 반환하는 다음 메서드도 **반환 객체 내부 상태를 통한 관찰 경로**다. 반환 객체의 식별자나 목록 구성 자체가 바뀐다는 뜻은 아니다.

```text
com.dxlab.homehub.device.DeviceRegistry#get(java.lang.String)
com.dxlab.homehub.device.DeviceRegistry#all()
com.dxlab.homehub.device.DeviceRegistry#byKind(com.dxlab.homehub.model.DeviceKind)
```

**5. 전력 상태를 통한 영향**

```text
com.dxlab.homehub.power.PowerBudget#tryStart(java.lang.String, int)
com.dxlab.homehub.power.PowerBudget#stop(java.lang.String)
com.dxlab.homehub.power.PowerBudget#totalLoad()
com.dxlab.homehub.power.PowerBudget#headroom()
com.dxlab.homehub.power.PowerBudget#isRunning(java.lang.String)
com.dxlab.homehub.power.PowerBudget#isIdle()
com.dxlab.homehub.power.PowerBudget#runningDevices()
```

이벤트 순서가 달라지면 전력 승인 여부와 `running` 맵이 달라지고, 이후 이벤트의 승인 여부까지 전파된다.

**6. 메트릭·감사 로그를 통한 영향**

```text
com.dxlab.homehub.ops.Metrics#increment(java.lang.String)
com.dxlab.homehub.ops.Metrics#get(java.lang.String)
com.dxlab.homehub.ops.Metrics#isEmpty()
com.dxlab.homehub.ops.Metrics#snapshot()
com.dxlab.homehub.ops.AuditLog#record(java.lang.String, com.dxlab.homehub.model.Event)
com.dxlab.homehub.ops.AuditLog#note(java.lang.String, java.lang.String)
com.dxlab.homehub.ops.AuditLog#size()
com.dxlab.homehub.ops.AuditLog#contains(java.lang.String)
com.dxlab.homehub.ops.AuditLog#count(java.lang.String)
com.dxlab.homehub.ops.AuditLog#tail(int)
com.dxlab.homehub.ops.AuditLog#dump()
```

**7. 영향받은 객체를 외부로 노출하는 반환 경로**

다음 getter는 같은 객체 참조를 반환하지만, 그 객체를 통해 관찰하는 상태가 달라질 수 있다.

```text
com.dxlab.homehub.app.HomeHub#getQueue()
com.dxlab.homehub.app.HomeHub#getMetrics()
com.dxlab.homehub.app.HomeHub#getAudit()
com.dxlab.homehub.app.HomeHub#getDevices()
com.dxlab.homehub.app.HomeHub#getPower()
com.dxlab.homehub.app.HomeHub#getDispatcher()
com.dxlab.homehub.app.HomeHub#getRules()
```

반면 파서·설정, 장치 등록 수·종류, 핸들러 등록 정보, 고정 전력 한도는 이 변경으로부터 값이 흘러오는 경로가 없다. 독립적인 초기화·리셋 메서드와 불변 이벤트의 단순 접근자는 별도 영향 메서드로 확대하지 않았다.

**다시 돌려야 할 기존 테스트: 총 16개**

큐 단위 테스트 6개:

```text
com.dxlab.homehub.RingEventQueueTest#testFifoOrder()
com.dxlab.homehub.RingEventQueueTest#testFullAtCapacity()
com.dxlab.homehub.RingEventQueueTest#testNullRejected()
com.dxlab.homehub.RingEventQueueTest#testWrapAround()
com.dxlab.homehub.RingEventQueueTest#testPeekDoesNotRemove()
com.dxlab.homehub.RingEventQueueTest#testClearAndSnapshot()
```

디스패처 테스트 6개:

```text
com.dxlab.homehub.DispatcherTest#testAcceptWhenSpace()
com.dxlab.homehub.DispatcherTest#testRejectNonCriticalWhenFull()
com.dxlab.homehub.DispatcherTest#testCriticalEvictsOldestNonCritical()
com.dxlab.homehub.DispatcherTest#testCriticalDrainsWhenAllCritical()
com.dxlab.homehub.DispatcherTest#testAutoDrain()
com.dxlab.homehub.DispatcherTest#testDrainDispatchesAll()
```

통합 테스트 4개:

```text
com.dxlab.homehub.HomeHubTest#testWasherCycleEndToEnd()
com.dxlab.homehub.HomeHubTest#testFridgeOverheatRaisesAlarm()
com.dxlab.homehub.HomeHubTest#testWatchdogRecoversStuckQueue()
com.dxlab.homehub.HomeHubTest#testLeakDuringWashCycle()
```

`DispatcherTest#testNullIsInvalid()`와 `HomeHubTest#testInvalidLineIsDropped()`는 변경된 큐 메서드에 도달하기 전에 반환하므로 제외한다. `HandlersTest`, `PowerBudgetTest`, `DeviceStateMachineTest`는 운영 환경의 전파 경로에 있는 클래스를 검증하지만, 해당 테스트 자체는 큐를 사용하지 않아 이번 변경의 회귀를 검출하지 못한다. `EventParserTest`도 제외한다.

기존 테스트에는 **감긴 상태의 snapshot 순서**, **비어 있지 않고 head가 0이 아닌 큐의 clear 후 재사용**, **용량 1에서 반복 순환**, **복구 후 남은 critical 이벤트 순서**의 직접 검증이 부족하다. 기존 16개 재실행과 별도로 이 경우들을 추가하면 변경 경계를 더 정확히 검증할 수 있다.