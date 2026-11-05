package com.dxlab.homehub.ops;

import com.dxlab.homehub.model.Event;
import com.dxlab.homehub.queue.EventQueue;

import java.util.List;

/** Recovery after a watchdog alarm: drop pending non-critical events, keep critical ones in order. */
public final class RecoveryManager {
    private final EventQueue queue;
    private final Metrics metrics;
    private final AuditLog audit;

    public RecoveryManager(EventQueue queue, Metrics metrics, AuditLog audit) {
        this.queue = queue;
        this.metrics = metrics;
        this.audit = audit;
    }

    /** Returns the number of dropped events. */
    public int recover() {
        List<Event> pending = queue.snapshot();
        queue.clear();
        int kept = 0;
        for (int i = 0; i < pending.size(); i++) {
            Event e = pending.get(i);
            if (e.isCritical()) {
                queue.offer(e);
                kept++;
            } else {
                audit.record("RECOVERY_DROP", e);
            }
        }
        metrics.increment("recovery.count");
        audit.note("RECOVER", "kept=" + kept + ",dropped=" + (pending.size() - kept));
        return pending.size() - kept;
    }
}
