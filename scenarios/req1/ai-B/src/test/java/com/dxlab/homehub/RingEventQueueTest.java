package com.dxlab.homehub;

import com.dxlab.homehub.model.Event;
import com.dxlab.homehub.model.EventType;
import com.dxlab.homehub.queue.OfferResult;
import com.dxlab.homehub.queue.RingEventQueue;
import com.dxlab.homehub.testkit.Check;

public class RingEventQueueTest {

    static Event ev(long seq) {
        return new Event(seq, "tv-1", EventType.HEARTBEAT, 0, seq);
    }

    public void testFifoOrder() {
        RingEventQueue q = new RingEventQueue(4);
        q.offer(ev(1));
        q.offer(ev(2));
        q.offer(ev(3));
        Check.eq(1L, q.poll().getSeq(), "first");
        Check.eq(2L, q.poll().getSeq(), "second");
        Check.eq(3L, q.poll().getSeq(), "third");
        Check.isNull(q.poll(), "empty");
    }

    public void testFullAtCapacity() {
        RingEventQueue q = new RingEventQueue(2, 2);
        Check.eq(OfferResult.OK, q.offer(ev(1)), "1");
        Check.eq(OfferResult.OK, q.offer(ev(2)), "2");
        Check.eq(OfferResult.FULL, q.offer(ev(3)), "3");
        Check.eq(2, q.size(), "size unchanged");
    }

    public void testGrowsBeyondInitialCapacity() {
        RingEventQueue q = new RingEventQueue(8);
        for (int i = 1; i <= 32; i++) {
            Check.eq(OfferResult.OK, q.offer(ev(i)), "offer " + i);
        }
        for (int i = 1; i <= 32; i++) {
            Check.eq((long) i, q.poll().getSeq(), "fifo " + i);
        }
    }

    public void testFullAtMaxCapacity() {
        RingEventQueue q = new RingEventQueue(2, 4);
        for (int i = 1; i <= 4; i++) {
            Check.eq(OfferResult.OK, q.offer(ev(i)), "offer " + i);
        }
        Check.eq(OfferResult.FULL, q.offer(ev(5)), "full at max");
    }

    public void testNullRejected() {
        RingEventQueue q = new RingEventQueue(2);
        Check.eq(OfferResult.REJECTED, q.offer(null), "null");
        Check.eq(0, q.size(), "size");
    }

    public void testWrapAround() {
        RingEventQueue q = new RingEventQueue(3);
        q.offer(ev(1));
        q.offer(ev(2));
        q.poll();
        q.offer(ev(3));
        q.offer(ev(4));
        Check.eq(2L, q.poll().getSeq(), "2");
        Check.eq(3L, q.poll().getSeq(), "3");
        Check.eq(4L, q.poll().getSeq(), "4");
    }

    public void testPeekDoesNotRemove() {
        RingEventQueue q = new RingEventQueue(2);
        q.offer(ev(7));
        Check.eq(7L, q.peek().getSeq(), "peek");
        Check.eq(1, q.size(), "size");
    }

    public void testClearAndSnapshot() {
        RingEventQueue q = new RingEventQueue(4);
        q.offer(ev(1));
        q.offer(ev(2));
        Check.eq(2, q.snapshot().size(), "snapshot");
        q.clear();
        Check.isTrue(q.isEmpty(), "cleared");
        Check.eq(4, q.capacity(), "capacity");
    }
}
