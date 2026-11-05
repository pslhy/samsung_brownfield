# 변경 영향 보고서 (def-use 기반, 시스템 의존 그래프)

분석 범위: RingEventQueue.java 만 (다른 클래스의 코드와 테스트 코드는 없는 것으로 보고 분석함)

## 1. 바뀐 줄

- [변경] queue.RingEventQueue#clear()  (변경 전 RingEventQueue.java:65; 변경 후 RingEventQueue.java:70,71,72)
- [변경] queue.RingEventQueue#offer(model.Event)  (변경 전 RingEventQueue.java:33; 변경 후 RingEventQueue.java:35,36,37)
- [변경] queue.RingEventQueue#poll()  (변경 전 RingEventQueue.java:42; 변경 후 RingEventQueue.java:46,47)
- [변경] queue.RingEventQueue#snapshot()  (변경 전 RingEventQueue.java:71,72,73; 변경 후 RingEventQueue.java:77,79,80,81)

## 2. 값이 달라질 수 있는 데이터 (3)

- queue.RingEventQueue.buf의 내용  <- 쓰는 메서드: queue.RingEventQueue#clear(), queue.RingEventQueue#offer(model.Event), queue.RingEventQueue#poll()
- 필드 queue.RingEventQueue.count  <- 쓰는 메서드: queue.RingEventQueue#clear(), queue.RingEventQueue#offer(model.Event), queue.RingEventQueue#poll()
- 필드 queue.RingEventQueue.head  <- 쓰는 메서드: queue.RingEventQueue#clear(), queue.RingEventQueue#poll()

## 3. 출력이 달라질 수 있는 메서드 (7)

- queue.RingEventQueue#clear(): queue.RingEventQueue.buf의 내용에 쓰는 값, 필드 queue.RingEventQueue.count에 쓰는 값, 필드 queue.RingEventQueue.head에 쓰는 값
- queue.RingEventQueue#isEmpty(): 반환값
- queue.RingEventQueue#offer(model.Event): queue.RingEventQueue.buf의 내용에 쓰는 값, 반환값, 필드 queue.RingEventQueue.count에 쓰는 값
- queue.RingEventQueue#peek(): 반환값
- queue.RingEventQueue#poll(): queue.RingEventQueue.buf의 내용에 쓰는 값, 반환값, 필드 queue.RingEventQueue.count에 쓰는 값, 필드 queue.RingEventQueue.head에 쓰는 값
- queue.RingEventQueue#size(): 반환값
- queue.RingEventQueue#snapshot(): 반환값

## 4. 다시 돌릴 테스트

- (범위 안에 테스트 코드가 없어 고르지 않음)
