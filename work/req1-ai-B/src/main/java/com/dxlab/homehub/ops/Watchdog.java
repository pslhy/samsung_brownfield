package com.dxlab.homehub.ops;

import com.dxlab.homehub.queue.EventQueue;

/**
 * Detects a stuck dispatcher: the queue stays at or above 75% of the logical limit
 * (dispatch.maxPending) for `threshold` consecutive checks.
 * REQ-1: the queue's capacity() is now its current allocation and may grow, so it can no
 * longer be used as the reference.
 */
public final class Watchdog {
    private final EventQueue queue;
    private final AuditLog audit;
    private final int threshold;
    private final int limit;
    private int highWaterChecks;

    public Watchdog(EventQueue queue, AuditLog audit, int threshold, int limit) {
        this.limit = limit;
        this.queue = queue;
        this.audit = audit;
        this.threshold = threshold;
    }

    public boolean check() {
        if (queue.size() * 4 >= limit * 3) {
            highWaterChecks++;
        } else {
            highWaterChecks = 0;
        }
        if (highWaterChecks >= threshold) {
            audit.note("WATCHDOG", "stuck size=" + queue.size());
            highWaterChecks = 0;
            return true;
        }
        return false;
    }

    public int getHighWaterChecks() {
        return highWaterChecks;
    }
}
