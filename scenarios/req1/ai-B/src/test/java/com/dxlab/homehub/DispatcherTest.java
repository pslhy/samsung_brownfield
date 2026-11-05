package com.dxlab.homehub;

import com.dxlab.homehub.dispatch.Dispatcher;
import com.dxlab.homehub.dispatch.HandlerRegistry;
import com.dxlab.homehub.dispatch.SubmitResult;
import com.dxlab.homehub.model.Event;
import com.dxlab.homehub.model.EventType;
import com.dxlab.homehub.ops.AuditLog;
import com.dxlab.homehub.ops.Metrics;
import com.dxlab.homehub.queue.RingEventQueue;
import com.dxlab.homehub.testkit.Check;

public class DispatcherTest {
    private final RingEventQueue queue = new RingEventQueue(3, 3);
    private final Metrics metrics = new Metrics();
    private final AuditLog audit = new AuditLog();

    private Dispatcher dispatcher(boolean autoDrain) {
        return new Dispatcher(queue, new HandlerRegistry(), metrics, audit, autoDrain);
    }

    static Event normal(long seq) {
        return new Event(seq, "tv-1", EventType.HEARTBEAT, 0, seq);
    }

    static Event leak(long seq) {
        return new Event(seq, "leak-1", EventType.LEAK_DETECTED, 1, seq);
    }

    public void testAcceptWhenSpace() {
        Dispatcher d = dispatcher(false);
        Check.eq(SubmitResult.ACCEPTED, d.submit(normal(1)), "accepted");
        Check.eq(1, queue.size(), "queued");
    }

    public void testRejectNonCriticalWhenFull() {
        Dispatcher d = dispatcher(false);
        d.submit(normal(1));
        d.submit(normal(2));
        d.submit(normal(3));
        Check.eq(SubmitResult.REJECTED_FULL, d.submit(normal(4)), "rejected");
        Check.eq(1, metrics.get("submit.rejected"), "metric");
    }

    public void testCriticalEvictsOldestNonCritical() {
        Dispatcher d = dispatcher(false);
        d.submit(normal(1));
        d.submit(normal(2));
        d.submit(normal(3));
        Check.eq(SubmitResult.ACCEPTED_EVICTED, d.submit(leak(4)), "evicted");
        Check.eq(3, queue.size(), "size");
        Check.isTrue(audit.contains("EVICT:1@"), "victim is the oldest");
    }

    public void testCriticalDrainsWhenAllCritical() {
        Dispatcher d = dispatcher(false);
        d.submit(leak(1));
        d.submit(leak(2));
        d.submit(leak(3));
        Check.eq(SubmitResult.ACCEPTED_DRAINED, d.submit(leak(4)), "drained");
        Check.eq(1L, d.getDispatchedCount(), "one dispatched");
    }

    public void testAutoDrain() {
        Dispatcher d = dispatcher(true);
        d.submit(normal(1));
        d.submit(normal(2));
        d.submit(normal(3));
        Check.eq(SubmitResult.ACCEPTED_DRAINED, d.submit(normal(4)), "drained");
    }

    public void testNullIsInvalid() {
        Check.eq(SubmitResult.INVALID, dispatcher(false).submit(null), "invalid");
    }

    public void testLogicalLimitAboveInitialCapacity() {
        RingEventQueue growing = new RingEventQueue(2, 32);
        Dispatcher d = new Dispatcher(growing, new HandlerRegistry(), metrics, audit, false, 5);
        for (int i = 1; i <= 5; i++) {
            Check.eq(SubmitResult.ACCEPTED, d.submit(normal(i)), "accepted " + i);
        }
        Check.eq(SubmitResult.REJECTED_FULL, d.submit(normal(6)), "limit 5 enforced");
        Check.eq(SubmitResult.ACCEPTED_EVICTED, d.submit(leak(7)), "critical evicts");
    }

    public void testDrainDispatchesAll() {
        Dispatcher d = dispatcher(false);
        d.submit(normal(1));
        d.submit(normal(2));
        Check.eq(2, d.drain(), "drained");
        Check.isTrue(queue.isEmpty(), "empty");
    }
}
