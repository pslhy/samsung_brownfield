```java
package difftest;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;

import RingEventQueueModule.Event;
import RingEventQueueModule.OfferResult;
import RingEventQueueModule.RingEventQueue;

public class MyQueueAdapter implements QueueModel {
    private final RingQueueModule.RingEventQueue queue;

    public MyQueueAdapter() {
        this.queue = new RingEventQueue();
        this.queue.__ctor(BigInteger.valueOf(8));
    }

    @Override
    public void init(int capacity) {
        // Dafny 객체는 생성 시 capacity가 결정되므로, 형식 변환만 수행한다.
    }

    @Override
    public String offer(int id, boolean critical) {
        Event event = Event.create(BigInteger.valueOf(id));
        OfferResult result = queue.Offer(event);

        if (result == OfferResult.OK) {
            return "OK";
        }
        if (result == OfferResult.FULL) {
            return "FULL";
        }
        return "REJECTED";
    }

    @Override
    public Integer poll() {
        Event event = queue.Poll();
        return event == null ? null : event.dtor_value().intValue();
    }

    @Override
    public Integer peek() {
        Event event = queue.Peek();
        return event == null ? null : event.dtor_value().intValue();
    }

    @Override
    public int size() {
        return queue.Size().intValue();
    }

    @Override
    public boolean isEmpty() {
        return queue.IsEmpty();
    }

    @Override
    public int capacity() {
        return queue.Capacity().intValue();
    }

    @Override
    public void clear() {
        queue.Clear();
    }

    @Override
    public List<Integer> snapshot() {
        List<Integer> result = new ArrayList<>();
        for (Event event : queue.Snapshot()) {
            if (event != null) {
                result.add(event.dtor_value().intValue());
            }
        }
        return result;
    }
}
```