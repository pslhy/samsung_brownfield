package com.dxlab.homehub.queue;

import com.dxlab.homehub.model.Event;

import java.util.List;

/** Pending-event queue between ingestion and dispatch. FIFO. */
public interface EventQueue {

    /** Appends e. Returns FULL (and changes nothing) when size() == capacity(); REJECTED for null. */
    OfferResult offer(Event e);

    /** Removes and returns the oldest event, or null when empty. */
    Event poll();

    /** Returns the oldest event without removing it, or null when empty. */
    Event peek();

    int size();

    int capacity();

    boolean isEmpty();

    void clear();

    /** Copy of the pending events, oldest first. */
    List<Event> snapshot();
}
