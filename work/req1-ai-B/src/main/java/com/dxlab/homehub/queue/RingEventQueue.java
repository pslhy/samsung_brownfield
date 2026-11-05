package com.dxlab.homehub.queue;

import com.dxlab.homehub.model.Event;

import java.util.ArrayList;
import java.util.List;

/**
 * Circular buffer that grows on demand (REQ-1).
 * Starts small to save memory and doubles its storage when full, up to maxCapacity.
 */
public final class RingEventQueue implements EventQueue {
    public static final int DEFAULT_CAPACITY = 8;
    public static final int MAX_CAPACITY = 32;

    private Event[] buf;
    private final int maxCapacity;
    private int head;
    private int count;

    public RingEventQueue() {
        this(DEFAULT_CAPACITY);
    }

    public RingEventQueue(int capacity) {
        this(capacity, Math.max(capacity, MAX_CAPACITY));
    }

    public RingEventQueue(int initialCapacity, int maxCapacity) {
        if (initialCapacity <= 0 || maxCapacity < initialCapacity) {
            throw new IllegalArgumentException("bad capacity: " + initialCapacity + "/" + maxCapacity);
        }
        this.buf = new Event[initialCapacity];
        this.maxCapacity = maxCapacity;
    }

    public OfferResult offer(Event e) {
        if (e == null) return OfferResult.REJECTED;
        if (count == buf.length) {
            if (buf.length >= maxCapacity) return OfferResult.FULL;
            grow();
        }
        buf[(head + count) % buf.length] = e;
        count++;
        return OfferResult.OK;
    }

    private void grow() {
        int newLength = Math.min(buf.length * 2, maxCapacity);
        Event[] bigger = new Event[newLength];
        for (int i = 0; i < count; i++) {
            bigger[i] = buf[(head + i) % buf.length];
        }
        buf = bigger;
        head = 0;
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

    public int maxCapacity() {
        return maxCapacity;
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
