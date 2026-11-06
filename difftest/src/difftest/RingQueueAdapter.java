package difftest;

import java.util.ArrayList;
import java.util.List;

/** QueueModel adapter for formal/RingQueue.dfy (Dafny module RingQueueModel, class RingQueue). */
public final class RingQueueAdapter implements QueueModel {
    private final RingQueueModel.RingQueue q = new RingQueueModel.RingQueue();

    public void init(int capacity) {
        q.__ctor(capacity);
    }

    public String offer(int id, boolean critical) {
        return q.Offer(Types.Event.create(id, critical)).is_OK() ? "OK" : "FULL";
    }

    public Integer poll() {
        dafny.Tuple2<?, ?> t = q.Poll();
        return (Boolean) t.dtor__0() ? ((Types.Event) t.dtor__1()).dtor_id() : null;
    }

    public Integer peek() {
        dafny.Tuple2<?, ?> t = q.Peek();
        return (Boolean) t.dtor__0() ? ((Types.Event) t.dtor__1()).dtor_id() : null;
    }

    public int size() {
        return q.Size();
    }

    public boolean isEmpty() {
        return q.IsEmpty();
    }

    public int capacity() {
        return q.GetCapacity();
    }

    public void clear() {
        q.Clear();
    }

    public List<Integer> snapshot() {
        dafny.DafnySequence<? extends Types.Event> s = q.Snapshot();
        List<Integer> out = new ArrayList<Integer>();
        for (int i = 0; i < s.length(); i++) {
            out.add(s.select(i).dtor_id());
        }
        return out;
    }
}
