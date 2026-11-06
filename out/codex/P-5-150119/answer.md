한 번만 참조되는 지역 변수는 `evictOldestNonCritical()`의 `n`이지만, 반복 중 큐 크기가 바뀌므로 `queue.size()`로 인라인하면 동작이 달라집니다. 안전하게 적용할 곳이 없어 코드를 유지했습니다.

```java
package com.dxlab.homehub.dispatch;

import com.dxlab.homehub.model.Event;
import com.dxlab.homehub.ops.AuditLog;
import com.dxlab.homehub.ops.Metrics;
import com.dxlab.homehub.queue.EventQueue;
import com.dxlab.homehub.queue.OfferResult;

/**
 * Admission and dispatch of device events.
 *
 * Back-pressure policy (approved by the safety review, SR-2017-11):
 *  - A critical event (leak, overheat) is never rejected. If the queue is full, the oldest
 *    non-critical event is evicted; if every queued event is critical, one is dispatched now.
 *  - A non-critical event is rejected when the queue is full, unless autoDrainOnFull is set,
 *    in which case one queued event is dispatched now to make room.
 *  - The relative order of the events that stay in the queue never changes.
 */
public final class Dispatcher {
    private final EventQueue queue;
    private final HandlerRegistry handlers;
    private final Metrics metrics;
    private final AuditLog audit;
    private final boolean autoDrainOnFull;
    private DispatchListener listener;
    private long dispatchedCount;

    public Dispatcher(EventQueue queue, HandlerRegistry handlers, Metrics metrics, AuditLog audit,
                      boolean autoDrainOnFull) {
        this.queue = queue;
        this.handlers = handlers;
        this.metrics = metrics;
        this.audit = audit;
        this.autoDrainOnFull = autoDrainOnFull;
    }

    public void setListener(DispatchListener listener) {
        this.listener = listener;
    }

    public SubmitResult submit(Event e) {
        if (e == null) {
            metrics.increment("submit.invalid");
            return SubmitResult.INVALID;
        }
        OfferResult r = queue.offer(e);
        if (r == OfferResult.OK) {
            metrics.increment("submit.accepted");
            return SubmitResult.ACCEPTED;
        }
        if (r == OfferResult.REJECTED) {
            metrics.increment("submit.invalid");
            return SubmitResult.INVALID;
        }
        // FULL
        metrics.increment("queue.full");
        if (e.isCritical()) {
            Event victim = evictOldestNonCritical();
            if (victim != null) {
                audit.record("EVICT", victim);
                metrics.increment("submit.evicted");
                queue.offer(e);
                return SubmitResult.ACCEPTED_EVICTED;
            }
            dispatchOne();
            queue.offer(e);
            metrics.increment("submit.drained");
            return SubmitResult.ACCEPTED_DRAINED;
        }
        if (autoDrainOnFull) {
            dispatchOne();
            queue.offer(e);
            metrics.increment("submit.drained");
            return SubmitResult.ACCEPTED_DRAINED;
        }
        metrics.increment("submit.rejected");
        audit.record("REJECT", e);
        return SubmitResult.REJECTED_FULL;
    }

    /**
     * Removes the oldest non-critical event and keeps the others in their original order.
     * Implemented by rotating the whole queue once.
     */
    Event evictOldestNonCritical() {
        int n = queue.size();
        Event victim = null;
        for (int i = 0; i < n; i++) {
            Event x = queue.poll();
            if (victim == null && !x.isCritical()) {
                victim = x;
                continue;
            }
            queue.offer(x);
        }
        return victim;
    }

    /** Dispatches the oldest queued event. Returns it, or null if the queue was empty. */
    public Event dispatchOne() {
        Event e = queue.poll();
        if (e == null) return null;
        handlers.dispatch(e);
        dispatchedCount++;
        metrics.increment("dispatch.count");
        if (listener != null) {
            listener.afterDispatch(e);
        }
        return e;
    }

    public int drain() {
        int n = 0;
        while (dispatchOne() != null) {
            n++;
        }
        return n;
    }

    public long getDispatchedCount() {
        return dispatchedCount;
    }

    public void resetCounters() {
        dispatchedCount = 0;
    }
}
```