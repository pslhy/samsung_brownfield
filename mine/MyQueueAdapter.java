package difftest;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.IdentityHashMap;
import java.util.List;
import java.util.Map;

public class MyQueueAdapter implements QueueModel {
    private _module.RingEventQueue queue;
    private final Map<_module.Event, Integer> ids = new IdentityHashMap<>();

    public MyQueueAdapter() {
    }

    @Override
    public void init(int capacity) {
        queue = new _module.RingEventQueue();
        queue.__ctor(BigInteger.valueOf(capacity));
        ids.clear();
    }

    @Override
    public String offer(int id, boolean critical) {
        // Dafny의 Event에는 필드가 없으므로 critical을 표현할 수 없다.
        // id는 반환된 Event의 객체 동일성을 통해 Java 값으로 변환한다.
        _module.Event event = new _module.Event();
        _module.OfferResult result = queue.offer(event);

        if (result.is_OK()) {
            ids.put(event, id);
            return "OK";
        }
        if (result.is_FULL()) {
            return "FULL";
        }
        return "REJECTED";
    }

    @Override
    public Integer poll() {
        _module.Event event = queue.poll();
        return event == null ? null : ids.remove(event);
    }

    @Override
    public Integer peek() {
        _module.Event event = queue.peek();
        return event == null ? null : ids.get(event);
    }

    @Override
    public int size() {
        return queue.size().intValueExact();
    }

    @Override
    public boolean isEmpty() {
        return queue.isEmpty();
    }

    @Override
    public int capacity() {
        return queue.capacity().intValueExact();
    }

    @Override
    public void clear() {
        queue.clear();
        ids.clear();
    }

    @Override
    public List<Integer> snapshot() {
        dafny.DafnySequence<_module.Event> events = queue.snapshot();
        List<Integer> result = new ArrayList<>(events.length());
        for (int i = 0; i < events.length(); i++) {
            _module.Event event = events.select(i);
            result.add(event == null ? null : ids.get(event));
        }
        return result;
    }
}
