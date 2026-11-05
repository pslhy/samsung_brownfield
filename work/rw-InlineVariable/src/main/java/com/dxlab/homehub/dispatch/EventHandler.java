package com.dxlab.homehub.dispatch;

import com.dxlab.homehub.model.Event;

public interface EventHandler {
    void handle(Event e);

    String name();
}
