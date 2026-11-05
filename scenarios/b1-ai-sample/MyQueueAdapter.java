package difftest;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;

import RingEventQueueModel.Event;
import RingEventQueueModel.RingEventQueue;

/** Example answer to docs/PROMPTS.md P-1b: connects RingEventQueue.dfy (compiled to Java) to DiffTest. */
public final class MyQueueAdapter implements QueueModel {
    private final RingEventQueue q = new RingEventQueue();

    public void init(int capacity) {
        q.__ctor(BigInteger.valueOf(capacity));
    }

    public String offer(int id, boolean critical) {
        return q.Offer(Event.create(BigInteger.valueOf(id), critical)).is_OK() ? "OK" : "FULL";
    }

    public Integer poll() {
        dafny.Tuple2<?, ?> t = q.Poll();
        return (Boolean) t.dtor__1() ? ((Event) t.dtor__0()).dtor_id().intValue() : null;
    }

    public Integer peek() {
        dafny.Tuple2<?, ?> t = q.Peek();
        return (Boolean) t.dtor__1() ? ((Event) t.dtor__0()).dtor_id().intValue() : null;
    }

    public int size() {
        return q.Size().intValue();
    }

    public boolean isEmpty() {
        return q.IsEmpty();
    }

    public int capacity() {
        return q.Capacity().intValue();
    }

    public void clear() {
        q.Clear();
    }

    public List<Integer> snapshot() {
        dafny.DafnySequence<? extends Event> s = q.Snapshot();
        List<Integer> out = new ArrayList<Integer>();
        for (int i = 0; i < s.length(); i++) {
            out.add(s.select(i).dtor_id().intValue());
        }
        return out;
    }
}
