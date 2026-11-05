package com.dxlab.homehub.queue;

import com.dxlab.homehub.model.Event;

import java.util.ArrayList;
import java.util.List;

/**
 * Fixed-capacity circular buffer.
 * The hub runs on a 64MB board: the bound is intentional (see HW spec HUB-2016-03).
 */
public final class RingEventQueue implements EventQueue {
    public static final int DEFAULT_CAPACITY = 8;

    private final Event[] buf;
    private int head;
    private int count;

    public RingEventQueue() {
        this(DEFAULT_CAPACITY);
    }

    public RingEventQueue(int capacity) {
        if (capacity <= 0) {
            throw new IllegalArgumentException("capacity must be positive: " + capacity);
        }
        buf = new Event[capacity];
    }

    public OfferResult offer(Event e) {
        if (e == null) return OfferResult.REJECTED;
        if (count == buf.length) return OfferResult.FULL;
        buf[(head + count) % buf.length] = e;
        count++;
        return OfferResult.OK;
    }

    public Event poll() {
        if (count == 0) return null;
        Event e = buf[head];
        buf[head] = null;
        head = (head + 1) % buf.length;
        count--;
        return e;
    }

    public Event peek() {
        if (count == 0) return null;
        return buf[head];
    }

    public int size() {
        return count;
    }

    public int capacity() {
        return buf.length;
    }

    public boolean isEmpty() {
        return count == 0;
    }

    public void clear() {
        while (poll() != null) {
            // drain
        }
    }

    public List<Event> snapshot() {
        List<Event> out = new ArrayList<Event>();
        for (int i = 0; i < count; i++) {
            out.add(buf[(head + i) % buf.length]);
        }
        return out;
    }
}
