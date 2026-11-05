package com.dxlab.homehub.dispatch;

import com.dxlab.homehub.model.Event;

/** Called after all handlers have processed an event. */
public interface DispatchListener {
    void afterDispatch(Event e);
}
