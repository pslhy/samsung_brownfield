package com.dxlab.homehub.handlers;

import com.dxlab.homehub.dispatch.EventHandler;
import com.dxlab.homehub.model.Event;
import com.dxlab.homehub.ops.Metrics;

/** Fallback handler: per-type event counters. */
public final class CountingHandler implements EventHandler {
    private final Metrics metrics;

    public CountingHandler(Metrics metrics) {
        this.metrics = metrics;
    }

    public String name() {
        return "counting";
    }

    public void handle(Event e) {
        metrics.increment("evt." + e.getType().name().toLowerCase());
    }
}
