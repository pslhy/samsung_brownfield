package com.dxlab.homehub.dispatch;

import com.dxlab.homehub.model.Event;
import com.dxlab.homehub.model.EventType;

import java.util.ArrayList;
import java.util.EnumMap;
import java.util.List;
import java.util.Map;

/** Routes each event to the handlers registered for its type, then to the fallback handler. */
public final class HandlerRegistry {
    private final Map<EventType, List<EventHandler>> byType =
            new EnumMap<EventType, List<EventHandler>>(EventType.class);
    private EventHandler fallback;

    public void register(EventType type, EventHandler h) {
        List<EventHandler> list = byType.get(type);
        if (list == null) {
            list = new ArrayList<EventHandler>();
            byType.put(type, list);
        }
        list.add(h);
    }

    public void setFallback(EventHandler h) {
        this.fallback = h;
    }

    public int dispatch(Event e) {
        int handled = 0;
        List<EventHandler> list = byType.get(e.getType());
        if (list != null) {
            for (int i = 0; i < list.size(); i++) {
                list.get(i).handle(e);
                handled++;
            }
        }
        if (fallback != null) {
            fallback.handle(e);
        }
        return handled;
    }

    public int handlerCount(EventType type) {
        List<EventHandler> list = byType.get(type);
        return list == null ? 0 : list.size();
    }
}
