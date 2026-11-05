# 변경 영향 보고서 (def-use 기반, 시스템 의존 그래프)

## 1. 바뀐 줄

- [변경] DispatcherTest#<init>()  (변경 전 DispatcherTest.java:14; 변경 후 DispatcherTest.java:14)
- [변경] RingEventQueueTest#testClearAndSnapshot()  (변경 후 RingEventQueueTest.java:78,79,80,81,82,83,84,85)
- [변경] RingEventQueueTest#testFullAtCapacity()  (변경 전 RingEventQueueTest.java:27,31,32; 변경 후 RingEventQueueTest.java:27,32)
- [추가] RingEventQueueTest#testFullAtMaxCapacity()  (변경 후 RingEventQueueTest.java:45,46,47,49)
- [추가] RingEventQueueTest#testGrowsBeyondInitialCapacity()  (변경 후 RingEventQueueTest.java:35,36,37,39,40,42)
- [변경] RingEventQueueTest#testNullRejected()  (변경 후 RingEventQueueTest.java:53,54,55,56)
- [변경] RingEventQueueTest#testPeekDoesNotRemove()  (변경 후 RingEventQueueTest.java:71,72,73,74,75)
- [변경] RingEventQueueTest#testWrapAround()  (변경 후 RingEventQueueTest.java:59,60,61,62,63,64,65,66,67,68)
- [변경] queue.RingEventQueue#<init>(int)  (변경 전 RingEventQueue.java:24,25,27; 변경 후 RingEventQueue.java:26,27)
- [추가] queue.RingEventQueue#<init>(int,int)  (변경 후 RingEventQueue.java:29,30,31,33,34)
- [추가] queue.RingEventQueue#grow()  (변경 후 RingEventQueue.java:49,50,51,52)
- [추가] queue.RingEventQueue#maxCapacity()  (변경 후 RingEventQueue.java:78)
- [변경] queue.RingEventQueue#offer(model.Event)  (변경 전 RingEventQueue.java:32,35; 변경 후 RingEventQueue.java:39,40,41)

## 2. 값이 달라질 수 있는 데이터 (26)

- ops.AuditLog.entries의 내용  <- 쓰는 메서드: app.HomeHub#drain(), app.HomeHub#flushDerived(), app.HomeHub#tick(), dispatch.Dispatcher#dispatchOne(), dispatch.Dispatcher#drain(), dispatch.Dispatcher#submit(model.Event), dispatch.HandlerRegistry#dispatch(model.Event), handlers.DeviceStatusHandler#handle(model.Event), handlers.SafetyHandler#handle(model.Event), handlers.TemperatureHandler#handle(model.Event), ops.AuditLog#note(String,String), ops.AuditLog#record(String,model.Event), ops.RecoveryManager#recover(), ops.Watchdog#check(), rules.RuleEngine#afterDispatch(model.Event)
- ops.Metrics.counters의 내용  <- 쓰는 메서드: app.HomeHub#drain(), app.HomeHub#flushDerived(), app.HomeHub#tick(), dispatch.Dispatcher#dispatchOne(), dispatch.Dispatcher#drain(), dispatch.Dispatcher#submit(model.Event), dispatch.HandlerRegistry#dispatch(model.Event), handlers.DeviceStatusHandler#handle(model.Event), handlers.SafetyHandler#handle(model.Event), handlers.TemperatureHandler#handle(model.Event), ops.Metrics#increment(String), ops.Metrics#reset()
- power.PowerBudget.running의 내용  <- 쓰는 메서드: app.HomeHub#drain(), app.HomeHub#flushDerived(), dispatch.Dispatcher#dispatchOne(), dispatch.Dispatcher#drain(), dispatch.Dispatcher#submit(model.Event), dispatch.HandlerRegistry#dispatch(model.Event), handlers.DeviceStatusHandler#handle(model.Event), handlers.SafetyHandler#handle(model.Event), power.PowerBudget#stop(String), power.PowerBudget#stopAll(), power.PowerBudget#tryStart(String,int)
- queue.RingEventQueue.buf의 내용  <- 쓰는 메서드: app.HomeHub#drain(), app.HomeHub#flushDerived(), app.HomeHub#tick(), dispatch.Dispatcher#drain(), dispatch.Dispatcher#evictOldestNonCritical(), dispatch.Dispatcher#submit(model.Event), ops.RecoveryManager#recover(), queue.RingEventQueue#<init>(int), queue.RingEventQueue#<init>(int,int), queue.RingEventQueue#clear(), queue.RingEventQueue#grow(), queue.RingEventQueue#offer(model.Event), queue.RingEventQueue#poll()
- rules.RuleEngine.outbox의 내용  <- 쓰는 메서드: app.HomeHub#drain(), app.HomeHub#flushDerived(), dispatch.Dispatcher#dispatchOne(), dispatch.Dispatcher#drain(), dispatch.Dispatcher#submit(model.Event), rules.RuleEngine#afterDispatch(model.Event), rules.RuleEngine#takeOutbox()
- rules.RuleEngine.overheatLatched의 내용  <- 쓰는 메서드: app.HomeHub#drain(), app.HomeHub#flushDerived(), dispatch.Dispatcher#dispatchOne(), dispatch.Dispatcher#drain(), dispatch.Dispatcher#submit(model.Event), rules.RuleEngine#afterDispatch(model.Event)
- 필드 dispatch.Dispatcher.dispatchedCount  <- 쓰는 메서드: app.HomeHub#drain(), app.HomeHub#flushDerived(), dispatch.Dispatcher#dispatchOne(), dispatch.Dispatcher#drain(), dispatch.Dispatcher#submit(model.Event)
- 필드 model.Device.consecutiveHighTemp  <- 쓰는 메서드: app.HomeHub#drain(), app.HomeHub#flushDerived(), dispatch.Dispatcher#dispatchOne(), dispatch.Dispatcher#drain(), dispatch.Dispatcher#submit(model.Event), dispatch.HandlerRegistry#dispatch(model.Event), handlers.TemperatureHandler#handle(model.Event), model.Device#setConsecutiveHighTemp(int)
- 필드 model.Device.doorOpen  <- 쓰는 메서드: app.HomeHub#drain(), app.HomeHub#flushDerived(), dispatch.Dispatcher#dispatchOne(), dispatch.Dispatcher#drain(), dispatch.Dispatcher#submit(model.Event), dispatch.HandlerRegistry#dispatch(model.Event), handlers.DeviceStatusHandler#handle(model.Event), model.Device#setDoorOpen(boolean,long)
- 필드 model.Device.doorOpenedAt  <- 쓰는 메서드: app.HomeHub#drain(), app.HomeHub#flushDerived(), dispatch.Dispatcher#dispatchOne(), dispatch.Dispatcher#drain(), dispatch.Dispatcher#submit(model.Event), dispatch.HandlerRegistry#dispatch(model.Event), handlers.DeviceStatusHandler#handle(model.Event), model.Device#setDoorOpen(boolean,long)
- 필드 model.Device.firmware  <- 쓰는 메서드: app.HomeHub#drain(), app.HomeHub#flushDerived(), dispatch.Dispatcher#dispatchOne(), dispatch.Dispatcher#drain(), dispatch.Dispatcher#submit(model.Event), dispatch.HandlerRegistry#dispatch(model.Event), handlers.DeviceStatusHandler#handle(model.Event), model.Device#setFirmware(String)
- 필드 model.Device.lastSeen  <- 쓰는 메서드: app.HomeHub#drain(), app.HomeHub#flushDerived(), dispatch.Dispatcher#dispatchOne(), dispatch.Dispatcher#drain(), dispatch.Dispatcher#submit(model.Event), dispatch.HandlerRegistry#dispatch(model.Event), handlers.DeviceStatusHandler#handle(model.Event), handlers.TemperatureHandler#handle(model.Event), model.Device#setLastSeen(long)
- 필드 model.Device.lastTemp  <- 쓰는 메서드: app.HomeHub#drain(), app.HomeHub#flushDerived(), dispatch.Dispatcher#dispatchOne(), dispatch.Dispatcher#drain(), dispatch.Dispatcher#submit(model.Event), dispatch.HandlerRegistry#dispatch(model.Event), handlers.TemperatureHandler#handle(model.Event), model.Device#setLastTemp(Integer)
- 필드 model.Device.status  <- 쓰는 메서드: app.HomeHub#drain(), app.HomeHub#flushDerived(), dispatch.Dispatcher#dispatchOne(), dispatch.Dispatcher#drain(), dispatch.Dispatcher#submit(model.Event), dispatch.HandlerRegistry#dispatch(model.Event), handlers.DeviceStatusHandler#handle(model.Event), handlers.SafetyHandler#handle(model.Event), model.Device#setStatus(model.DeviceStatus)
- 필드 model.Event.attrs  <- 쓰는 메서드: app.HomeHub#drain(), app.HomeHub#flushDerived(), dispatch.Dispatcher#dispatchOne(), dispatch.Dispatcher#drain(), dispatch.Dispatcher#submit(model.Event)
- 필드 model.Event.deviceId  <- 쓰는 메서드: app.HomeHub#drain(), app.HomeHub#flushDerived(), dispatch.Dispatcher#dispatchOne(), dispatch.Dispatcher#drain(), dispatch.Dispatcher#submit(model.Event), model.Event#<init>(long,String,model.EventType,int,long,java.util.Map), rules.RuleEngine#afterDispatch(model.Event)
- 필드 model.Event.seq  <- 쓰는 메서드: app.HomeHub#drain(), app.HomeHub#flushDerived(), dispatch.Dispatcher#dispatchOne(), dispatch.Dispatcher#drain(), dispatch.Dispatcher#submit(model.Event), model.Event#<init>(long,String,model.EventType,int,long,java.util.Map), rules.RuleEngine#afterDispatch(model.Event)
- 필드 model.Event.timestamp  <- 쓰는 메서드: app.HomeHub#drain(), app.HomeHub#flushDerived(), dispatch.Dispatcher#dispatchOne(), dispatch.Dispatcher#drain(), dispatch.Dispatcher#submit(model.Event), model.Event#<init>(long,String,model.EventType,int,long,java.util.Map), rules.RuleEngine#afterDispatch(model.Event)
- 필드 model.Event.type  <- 쓰는 메서드: app.HomeHub#drain(), app.HomeHub#flushDerived(), dispatch.Dispatcher#dispatchOne(), dispatch.Dispatcher#drain(), dispatch.Dispatcher#submit(model.Event), model.Event#<init>(long,String,model.EventType,int,long,java.util.Map), rules.RuleEngine#afterDispatch(model.Event)
- 필드 model.Event.value  <- 쓰는 메서드: app.HomeHub#drain(), app.HomeHub#flushDerived(), dispatch.Dispatcher#dispatchOne(), dispatch.Dispatcher#drain(), dispatch.Dispatcher#submit(model.Event), model.Event#<init>(long,String,model.EventType,int,long,java.util.Map), rules.RuleEngine#afterDispatch(model.Event)
- 필드 ops.Watchdog.highWaterChecks  <- 쓰는 메서드: ops.Watchdog#check()
- 필드 queue.RingEventQueue.buf  <- 쓰는 메서드: app.HomeHub#drain(), app.HomeHub#flushDerived(), app.HomeHub#tick(), dispatch.Dispatcher#evictOldestNonCritical(), dispatch.Dispatcher#submit(model.Event), ops.RecoveryManager#recover(), queue.RingEventQueue#<init>(int), queue.RingEventQueue#<init>(int,int), queue.RingEventQueue#grow(), queue.RingEventQueue#offer(model.Event)
- 필드 queue.RingEventQueue.count  <- 쓰는 메서드: app.HomeHub#drain(), app.HomeHub#flushDerived(), app.HomeHub#tick(), dispatch.Dispatcher#drain(), dispatch.Dispatcher#evictOldestNonCritical(), dispatch.Dispatcher#submit(model.Event), ops.RecoveryManager#recover(), queue.RingEventQueue#clear(), queue.RingEventQueue#offer(model.Event), queue.RingEventQueue#poll()
- 필드 queue.RingEventQueue.head  <- 쓰는 메서드: app.HomeHub#drain(), app.HomeHub#flushDerived(), app.HomeHub#tick(), dispatch.Dispatcher#drain(), dispatch.Dispatcher#evictOldestNonCritical(), dispatch.Dispatcher#submit(model.Event), queue.RingEventQueue#clear(), queue.RingEventQueue#poll()
- 필드 queue.RingEventQueue.maxCapacity  <- 쓰는 메서드: queue.RingEventQueue#<init>(int,int)
- 필드 rules.RuleEngine.nextSeq  <- 쓰는 메서드: app.HomeHub#drain(), app.HomeHub#flushDerived(), dispatch.Dispatcher#dispatchOne(), dispatch.Dispatcher#drain(), dispatch.Dispatcher#submit(model.Event), rules.RuleEngine#afterDispatch(model.Event)

## 3. 출력이 달라질 수 있는 메서드 (86)

- app.HomeHub#<init>(app.HubConfig): 예외
- app.HomeHub#drain(): ops.AuditLog.entries의 내용에 쓰는 값, ops.Metrics.counters의 내용에 쓰는 값, power.PowerBudget.running의 내용에 쓰는 값, queue.RingEventQueue.buf의 내용에 쓰는 값, rules.RuleEngine.outbox
- app.HomeHub#flushDerived(): ops.AuditLog.entries의 내용에 쓰는 값, ops.Metrics.counters의 내용에 쓰는 값, power.PowerBudget.running의 내용에 쓰는 값, queue.RingEventQueue.buf의 내용에 쓰는 값, rules.RuleEngine.outbox
- app.HomeHub#ingest(String): 반환값
- app.HomeHub#observable(): 반환값
- app.HomeHub#step(): 반환값
- app.HomeHub#submit(model.Event): 반환값
- app.HomeHub#tick(): ops.AuditLog.entries의 내용에 쓰는 값, ops.Metrics.counters의 내용에 쓰는 값, queue.RingEventQueue.buf의 내용에 쓰는 값, 필드 queue.RingEventQueue.buf에 쓰는 값, 필드 queue.RingEventQueue.c
- app.HubMain#main(String[]): 예외
- app.HubMain#run(app.HomeHub,String,java.io.PrintStream): 예외
- device.DeviceRegistry#byKind(model.DeviceKind): 반환값
- device.DeviceRegistry#get(String): 반환값
- device.DeviceStateMachine#next(model.DeviceStatus,model.EventType): 반환값
- dispatch.Dispatcher#dispatchOne(): ops.AuditLog.entries의 내용에 쓰는 값, ops.Metrics.counters의 내용에 쓰는 값, power.PowerBudget.running의 내용에 쓰는 값, rules.RuleEngine.outbox의 내용에 쓰는 값, rules.RuleEngine.overhea
- dispatch.Dispatcher#drain(): ops.AuditLog.entries의 내용에 쓰는 값, ops.Metrics.counters의 내용에 쓰는 값, power.PowerBudget.running의 내용에 쓰는 값, queue.RingEventQueue.buf의 내용에 쓰는 값, rules.RuleEngine.outbox
- dispatch.Dispatcher#evictOldestNonCritical(): queue.RingEventQueue.buf의 내용에 쓰는 값, 반환값, 필드 queue.RingEventQueue.buf에 쓰는 값, 필드 queue.RingEventQueue.count에 쓰는 값, 필드 queue.RingEventQueue.head에 쓰는 값
- dispatch.Dispatcher#getDispatchedCount(): 반환값
- dispatch.Dispatcher#submit(model.Event): ops.AuditLog.entries의 내용에 쓰는 값, ops.Metrics.counters의 내용에 쓰는 값, power.PowerBudget.running의 내용에 쓰는 값, queue.RingEventQueue.buf의 내용에 쓰는 값, rules.RuleEngine.outbox
- dispatch.HandlerRegistry#dispatch(model.Event): ops.AuditLog.entries의 내용에 쓰는 값, ops.Metrics.counters의 내용에 쓰는 값, power.PowerBudget.running의 내용에 쓰는 값, 반환값, 필드 model.Device.consecutiveHighTemp에 쓰는 값, 필드 model.De
- handlers.DeviceStatusHandler#handle(model.Event): ops.AuditLog.entries의 내용에 쓰는 값, ops.Metrics.counters의 내용에 쓰는 값, power.PowerBudget.running의 내용에 쓰는 값, 필드 model.Device.doorOpenedAt에 쓰는 값, 필드 model.Device.doorOpe
- handlers.SafetyHandler#handle(model.Event): ops.AuditLog.entries의 내용에 쓰는 값, ops.Metrics.counters의 내용에 쓰는 값, power.PowerBudget.running의 내용에 쓰는 값, 필드 model.Device.status에 쓰는 값
- handlers.TemperatureHandler#handle(model.Event): ops.AuditLog.entries의 내용에 쓰는 값, ops.Metrics.counters의 내용에 쓰는 값, 필드 model.Device.consecutiveHighTemp에 쓰는 값, 필드 model.Device.lastSeen에 쓰는 값, 필드 model.Device.lastT
- model.Device#getConsecutiveHighTemp(): 반환값
- model.Device#getDoorOpenedAt(): 반환값
- model.Device#getFirmware(): 반환값
- model.Device#getLastSeen(): 반환값
- model.Device#getLastTemp(): 반환값
- model.Device#getStatus(): 반환값
- model.Device#isDoorOpen(): 반환값
- model.Device#setConsecutiveHighTemp(int): 필드 model.Device.consecutiveHighTemp에 쓰는 값
- model.Device#setDoorOpen(boolean,long): 필드 model.Device.doorOpenedAt에 쓰는 값, 필드 model.Device.doorOpen에 쓰는 값
- model.Device#setFirmware(String): 필드 model.Device.firmware에 쓰는 값
- model.Device#setLastSeen(long): 필드 model.Device.lastSeen에 쓰는 값
- model.Device#setLastTemp(Integer): 필드 model.Device.lastTemp에 쓰는 값
- model.Device#setStatus(model.DeviceStatus): 필드 model.Device.status에 쓰는 값
- model.Device#toString(): 반환값
- model.Event#<init>(long,String,model.EventType,int,long,java.util.Map): 필드 model.Event.deviceId에 쓰는 값, 필드 model.Event.seq에 쓰는 값, 필드 model.Event.timestamp에 쓰는 값, 필드 model.Event.type에 쓰는 값, 필드 model.Event.value에 쓰는 값
- model.Event#attr(String): 반환값
- model.Event#equals(Object): 반환값
- model.Event#getAttrs(): 반환값
- model.Event#getDeviceId(): 반환값
- model.Event#getSeq(): 반환값
- model.Event#getTimestamp(): 반환값
- model.Event#getType(): 반환값
- model.Event#getValue(): 반환값
- model.Event#hashCode(): 반환값
- model.Event#toString(): 반환값
- ops.AuditLog#contains(String): 반환값
- ops.AuditLog#count(String): 반환값
- ops.AuditLog#dump(): 반환값
- ops.AuditLog#note(String,String): ops.AuditLog.entries의 내용에 쓰는 값
- ops.AuditLog#record(String,model.Event): ops.AuditLog.entries의 내용에 쓰는 값
- ops.AuditLog#size(): 반환값
- ops.AuditLog#tail(int): 반환값
- ops.Metrics#get(String): 반환값
- ops.Metrics#increment(String): ops.Metrics.counters의 내용에 쓰는 값
- ops.Metrics#isEmpty(): 반환값
- ops.Metrics#reset(): ops.Metrics.counters의 내용에 쓰는 값
- ops.Metrics#snapshot(): 반환값
- ops.RecoveryManager#recover(): ops.AuditLog.entries의 내용에 쓰는 값, queue.RingEventQueue.buf의 내용에 쓰는 값, 반환값, 필드 queue.RingEventQueue.buf에 쓰는 값, 필드 queue.RingEventQueue.count에 쓰는 값
- ops.Watchdog#check(): ops.AuditLog.entries의 내용에 쓰는 값, 반환값, 필드 ops.Watchdog.highWaterChecks에 쓰는 값
- ops.Watchdog#getHighWaterChecks(): 반환값
- power.PowerBudget#headroom(): 반환값
- power.PowerBudget#isIdle(): 반환값
- power.PowerBudget#isRunning(String): 반환값
- power.PowerBudget#runningDevices(): 반환값
- power.PowerBudget#stop(String): power.PowerBudget.running의 내용에 쓰는 값
- power.PowerBudget#stopAll(): power.PowerBudget.running의 내용에 쓰는 값
- power.PowerBudget#totalLoad(): 반환값
- power.PowerBudget#tryStart(String,int): power.PowerBudget.running의 내용에 쓰는 값, 반환값
- queue.RingEventQueue#<init>(): 예외
- queue.RingEventQueue#<init>(int): queue.RingEventQueue.buf의 내용에 쓰는 값, 예외, 필드 queue.RingEventQueue.buf에 쓰는 값
- queue.RingEventQueue#<init>(int,int): queue.RingEventQueue.buf의 내용에 쓰는 값, 예외, 필드 queue.RingEventQueue.buf에 쓰는 값, 필드 queue.RingEventQueue.maxCapacity에 쓰는 값
- queue.RingEventQueue#capacity(): 반환값
- queue.RingEventQueue#clear(): queue.RingEventQueue.buf의 내용에 쓰는 값, 필드 queue.RingEventQueue.count에 쓰는 값, 필드 queue.RingEventQueue.head에 쓰는 값
- queue.RingEventQueue#grow(): queue.RingEventQueue.buf의 내용에 쓰는 값, 필드 queue.RingEventQueue.buf에 쓰는 값
- queue.RingEventQueue#isEmpty(): 반환값
- queue.RingEventQueue#maxCapacity(): 반환값
- queue.RingEventQueue#offer(model.Event): queue.RingEventQueue.buf의 내용에 쓰는 값, 반환값, 필드 queue.RingEventQueue.buf에 쓰는 값, 필드 queue.RingEventQueue.count에 쓰는 값
- queue.RingEventQueue#peek(): 반환값
- queue.RingEventQueue#poll(): queue.RingEventQueue.buf의 내용에 쓰는 값, 반환값, 필드 queue.RingEventQueue.count에 쓰는 값, 필드 queue.RingEventQueue.head에 쓰는 값
- queue.RingEventQueue#size(): 반환값
- queue.RingEventQueue#snapshot(): 반환값
- rules.RuleEngine#afterDispatch(model.Event): ops.AuditLog.entries의 내용에 쓰는 값, rules.RuleEngine.outbox의 내용에 쓰는 값, rules.RuleEngine.overheatLatched의 내용에 쓰는 값, 필드 model.Event.deviceId에 쓰는 값, 필드 model.Event.seq
- rules.RuleEngine#isLatched(String): 반환값
- rules.RuleEngine#takeOutbox(): rules.RuleEngine.outbox의 내용에 쓰는 값, 반환값

## 4. 다시 돌릴 테스트 (35 / 40)

- DispatcherTest#testAcceptWhenSpace()
- DispatcherTest#testAutoDrain()
- DispatcherTest#testCriticalDrainsWhenAllCritical()
- DispatcherTest#testCriticalEvictsOldestNonCritical()
- DispatcherTest#testDrainDispatchesAll()
- DispatcherTest#testNullIsInvalid()
- DispatcherTest#testRejectNonCriticalWhenFull()
- EventParserTest#testAttributes()
- EventParserTest#testBasicLine()
- EventParserTest#testCelsiusTemperature()
- EventParserTest#testFahrenheitIsNormalized()
- EventParserTest#testUnknownCode()
- HandlersTest#testCycleEndReleasesPower()
- HandlersTest#testHeavyLoadNeedsPower()
- HandlersTest#testHighTemperatureIsCounted()
- HandlersTest#testLeakStopsRunningWasher()
- HandlersTest#testUnknownDevice()
- HomeHubTest#testFridgeOverheatRaisesAlarm()
- HomeHubTest#testInvalidLineIsDropped()
- HomeHubTest#testLeakDuringWashCycle()
- HomeHubTest#testWasherCycleEndToEnd()
- HomeHubTest#testWatchdogRecoversStuckQueue()
- PowerBudgetTest#testDenyOverCap()
- PowerBudgetTest#testGrantWithinCap()
- PowerBudgetTest#testIdempotentStart()
- PowerBudgetTest#testRejectInvalidWatts()
- PowerBudgetTest#testStopReleases()
- RingEventQueueTest#testClearAndSnapshot()
- RingEventQueueTest#testFifoOrder()
- RingEventQueueTest#testFullAtCapacity()
- RingEventQueueTest#testFullAtMaxCapacity()
- RingEventQueueTest#testGrowsBeyondInitialCapacity()
- RingEventQueueTest#testNullRejected()
- RingEventQueueTest#testPeekDoesNotRemove()
- RingEventQueueTest#testWrapAround()

## 왜 영향받는가: ops.Watchdog#check

- ops.Watchdog#check()의 ops.AuditLog.entries의 내용에 쓰는 값
    바뀐 줄 queue.RingEventQueue#offer(model.Event):41  grow();
      ↓ 필드 queue.RingEventQueue.buf에 저장했다가 읽음
    → queue.RingEventQueue#capacity():74  return buf.length;
      ↓ queue.RingEventQueue#capacity()의 반환값으로
    → ops.Watchdog#check():22  if (queue.size() * 4 >= queue.capacity() * 3) {
      ↓ 위 줄의 조건에 따라 실행 여부가 달라짐
    → ops.Watchdog#check():23  highWaterChecks++;
      ↓ 필드 ops.Watchdog.highWaterChecks에 저장했다가 읽음
    → ops.Watchdog#check():27  if (highWaterChecks >= threshold) {
      ↓ 위 줄의 조건에 따라 실행 여부가 달라짐
    → ops.Watchdog#check():28  audit.note("WATCHDOG", "stuck size=" + queue.size());
    (다른 이유)
    바뀐 줄 queue.RingEventQueue#grow():52  buf = bigger;
      ↓ 필드 queue.RingEventQueue.buf에 저장했다가 읽음
    → queue.RingEventQueue#capacity():74  return buf.length;
      ↓ queue.RingEventQueue#capacity()의 반환값으로
    → ops.Watchdog#check():22  if (queue.size() * 4 >= queue.capacity() * 3) {
      ↓ 위 줄의 조건에 따라 실행 여부가 달라짐
    → ops.Watchdog#check():23  highWaterChecks++;
      ↓ 필드 ops.Watchdog.highWaterChecks에 저장했다가 읽음
    → ops.Watchdog#check():27  if (highWaterChecks >= threshold) {
      ↓ 위 줄의 조건에 따라 실행 여부가 달라짐
    → ops.Watchdog#check():28  audit.note("WATCHDOG", "stuck size=" + queue.size());
    (다른 이유)
    바뀐 줄 queue.RingEventQueue#<init>(int,int):33  this.buf = new Event[initialCapacity];
      ↓ queue.RingEventQueue.buf의 내용에 저장했다가 읽음
    → queue.RingEventQueue#snapshot():94  out.add(buf[(head + i) % buf.length]);
    → queue.RingEventQueue#snapshot():96  return out;
      ↓ queue.RingEventQueue#snapshot()의 반환값으로 → queue.RingEventQueue#offer(model.Event)의 1번째 인자로
    → queue.RingEventQueue#offer(model.Event):38  if (e == null) return OfferResult.REJECTED;
      ↓ 위 줄의 조건에 따라 실행 여부가 달라짐
    → queue.RingEventQueue#offer(model.Event):39  if (count == buf.length) {
      ↓ 위 줄의 조건에 따라 실행 여부가 달라짐
    → queue.RingEventQueue#offer(model.Event):40  if (buf.length >= maxCapacity) return OfferResult.FULL;
      ↓ 위 줄의 조건에 따라 실행 여부가 달라짐
    → queue.RingEventQueue#offer(model.Event):41  grow();
      ↓ 필드 queue.RingEventQueue.buf에 저장했다가 읽음
    → queue.RingEventQueue#capacity():74  return buf.length;
      ↓ queue.RingEventQueue#capacity()의 반환값으로
    → ops.Watchdog#check():22  if (queue.size() * 4 >= queue.capacity() * 3) {
      ↓ 위 줄의 조건에 따라 실행 여부가 달라짐
    → ops.Watchdog#check():23  highWaterChecks++;
      ↓ 필드 ops.Watchdog.highWaterChecks에 저장했다가 읽음
    → ops.Watchdog#check():27  if (highWaterChecks >= threshold) {
      ↓ 위 줄의 조건에 따라 실행 여부가 달라짐
    → ops.Watchdog#check():28  audit.note("WATCHDOG", "stuck size=" + queue.size());
- ops.Watchdog#check()의 필드 ops.Watchdog.highWaterChecks에 쓰는 값
    바뀐 줄 queue.RingEventQueue#offer(model.Event):39  if (count == buf.length) {
      ↓ 위 줄의 조건에 따라 실행 여부가 달라짐
    → queue.RingEventQueue#offer(model.Event):44  count++;
      ↓ 필드 queue.RingEventQueue.count에 저장했다가 읽음
    → queue.RingEventQueue#size():70  return count;
      ↓ queue.RingEventQueue#size()의 반환값으로
    → ops.Watchdog#check():22  if (queue.size() * 4 >= queue.capacity() * 3) {
      ↓ 위 줄의 조건에 따라 실행 여부가 달라짐
    → ops.Watchdog#check():23  highWaterChecks++;
    (다른 이유)
    바뀐 줄 queue.RingEventQueue#<init>(int,int):33  this.buf = new Event[initialCapacity];
      ↓ 필드 queue.RingEventQueue.buf에 저장했다가 읽음
    → queue.RingEventQueue#capacity():74  return buf.length;
      ↓ queue.RingEventQueue#capacity()의 반환값으로
    → ops.Watchdog#check():22  if (queue.size() * 4 >= queue.capacity() * 3) {
      ↓ 위 줄의 조건에 따라 실행 여부가 달라짐
    → ops.Watchdog#check():23  highWaterChecks++;
    (다른 이유)
    바뀐 줄 queue.RingEventQueue#grow():52  buf = bigger;
      ↓ 필드 queue.RingEventQueue.buf에 저장했다가 읽음
    → queue.RingEventQueue#capacity():74  return buf.length;
      ↓ queue.RingEventQueue#capacity()의 반환값으로
    → ops.Watchdog#check():22  if (queue.size() * 4 >= queue.capacity() * 3) {
      ↓ 위 줄의 조건에 따라 실행 여부가 달라짐
    → ops.Watchdog#check():23  highWaterChecks++;
- ops.Watchdog#check()의 반환값
    바뀐 줄 queue.RingEventQueue#offer(model.Event):41  grow();
      ↓ 필드 queue.RingEventQueue.buf에 저장했다가 읽음
    → queue.RingEventQueue#capacity():74  return buf.length;
      ↓ queue.RingEventQueue#capacity()의 반환값으로
    → ops.Watchdog#check():22  if (queue.size() * 4 >= queue.capacity() * 3) {
      ↓ 위 줄의 조건에 따라 실행 여부가 달라짐
    → ops.Watchdog#check():23  highWaterChecks++;
      ↓ 필드 ops.Watchdog.highWaterChecks에 저장했다가 읽음
    → ops.Watchdog#check():27  if (highWaterChecks >= threshold) {
      ↓ 위 줄의 조건에 따라 실행 여부가 달라짐
    → ops.Watchdog#check():30  return true;
    (다른 이유)
    바뀐 줄 queue.RingEventQueue#grow():52  buf = bigger;
      ↓ 필드 queue.RingEventQueue.buf에 저장했다가 읽음
    → queue.RingEventQueue#capacity():74  return buf.length;
      ↓ queue.RingEventQueue#capacity()의 반환값으로
    → ops.Watchdog#check():22  if (queue.size() * 4 >= queue.capacity() * 3) {
      ↓ 위 줄의 조건에 따라 실행 여부가 달라짐
    → ops.Watchdog#check():23  highWaterChecks++;
      ↓ 필드 ops.Watchdog.highWaterChecks에 저장했다가 읽음
    → ops.Watchdog#check():27  if (highWaterChecks >= threshold) {
      ↓ 위 줄의 조건에 따라 실행 여부가 달라짐
    → ops.Watchdog#check():30  return true;
    (다른 이유)
    바뀐 줄 queue.RingEventQueue#<init>(int,int):33  this.buf = new Event[initialCapacity];
      ↓ queue.RingEventQueue.buf의 내용에 저장했다가 읽음
    → queue.RingEventQueue#snapshot():94  out.add(buf[(head + i) % buf.length]);
    → queue.RingEventQueue#snapshot():96  return out;
      ↓ queue.RingEventQueue#snapshot()의 반환값으로 → queue.RingEventQueue#offer(model.Event)의 1번째 인자로
    → queue.RingEventQueue#offer(model.Event):38  if (e == null) return OfferResult.REJECTED;
      ↓ 위 줄의 조건에 따라 실행 여부가 달라짐
    → queue.RingEventQueue#offer(model.Event):39  if (count == buf.length) {
      ↓ 위 줄의 조건에 따라 실행 여부가 달라짐
    → queue.RingEventQueue#offer(model.Event):40  if (buf.length >= maxCapacity) return OfferResult.FULL;
      ↓ 위 줄의 조건에 따라 실행 여부가 달라짐
    → queue.RingEventQueue#offer(model.Event):41  grow();
      ↓ 필드 queue.RingEventQueue.buf에 저장했다가 읽음
    → queue.RingEventQueue#capacity():74  return buf.length;
      ↓ queue.RingEventQueue#capacity()의 반환값으로
    → ops.Watchdog#check():22  if (queue.size() * 4 >= queue.capacity() * 3) {
      ↓ 위 줄의 조건에 따라 실행 여부가 달라짐
    → ops.Watchdog#check():23  highWaterChecks++;
      ↓ 필드 ops.Watchdog.highWaterChecks에 저장했다가 읽음
    → ops.Watchdog#check():27  if (highWaterChecks >= threshold) {
      ↓ 위 줄의 조건에 따라 실행 여부가 달라짐
    → ops.Watchdog#check():30  return true;
