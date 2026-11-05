package com.dxlab.homehub.ops;

import com.dxlab.homehub.queue.EventQueue;

/**
 * Detects a stuck dispatcher: the queue stays at or above 75% of its capacity
 * for `threshold` consecutive checks.
 */
public final class Watchdog {
    private final EventQueue queue;
    private final AuditLog audit;
    private final int threshold;
    private int highWaterChecks;

    public Watchdog(EventQueue queue, AuditLog audit, int threshold) {
        this.queue = queue;
        this.audit = audit;
        this.threshold = threshold;
    }

    public boolean check() {
        if (queue.size() * 4 >= queue.capacity() * 3) {
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
