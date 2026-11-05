package com.dxlab.homehub.rules;

import com.dxlab.homehub.device.DeviceRegistry;
import com.dxlab.homehub.dispatch.DispatchListener;
import com.dxlab.homehub.model.Device;
import com.dxlab.homehub.model.DeviceKind;
import com.dxlab.homehub.model.DeviceStatus;
import com.dxlab.homehub.model.Event;
import com.dxlab.homehub.model.EventType;
import com.dxlab.homehub.ops.AuditLog;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

/**
 * Home automation rules evaluated after each dispatched event.
 * Derived events are not submitted here (no re-entrancy); HomeHub collects them from the outbox.
 */
public final class RuleEngine implements DispatchListener {
    public static final long DERIVED_SEQ_BASE = 1000000L;

    private final DeviceRegistry devices;
    private final AuditLog audit;
    private final int overheatAfterReports;
    private final long doorOpenAlertMillis;
    private final List<Event> outbox = new ArrayList<Event>();
    private final Set<String> overheatLatched = new HashSet<String>();
    private long nextSeq = DERIVED_SEQ_BASE;

    public RuleEngine(DeviceRegistry devices, AuditLog audit, int overheatAfterReports, long doorOpenAlertMillis) {
        this.devices = devices;
        this.audit = audit;
        this.overheatAfterReports = overheatAfterReports;
        this.doorOpenAlertMillis = doorOpenAlertMillis;
    }

    public void afterDispatch(Event e) {
        Device d = devices.get(e.getDeviceId());
        if (d == null) return;

        // R1: fridge overheat after N consecutive high reports (latched until temperature is normal)
        if (e.getType() == EventType.TEMP_REPORT && d.getKind() == DeviceKind.FRIDGE) {
            if (d.getConsecutiveHighTemp() >= overheatAfterReports) {
                if (!overheatLatched.contains(d.getId())) {
                    overheatLatched.add(d.getId());
                    outbox.add(new Event(nextSeq++, d.getId(), EventType.OVERHEAT,
                            d.getLastTemp().intValue(), e.getTimestamp()));
                    audit.record("RULE_OVERHEAT", e);
                }
            } else if (d.getConsecutiveHighTemp() == 0) {
                overheatLatched.remove(d.getId());
            }
        }

        // R2: door left open
        if (e.getType() == EventType.HEARTBEAT && d.isDoorOpen()
                && e.getTimestamp() - d.getDoorOpenedAt() >= doorOpenAlertMillis) {
            audit.note("DOOR_LEFT_OPEN", d.getId());
        }

        // R3: washer finished -> suggest dryer
        if (e.getType() == EventType.CYCLE_END && d.getKind() == DeviceKind.WASHER) {
            List<Device> dryers = devices.byKind(DeviceKind.DRYER);
            if (!dryers.isEmpty() && dryers.get(0).getStatus() == DeviceStatus.IDLE) {
                audit.note("SUGGEST_DRYER", dryers.get(0).getId());
            }
        }
    }

    public List<Event> takeOutbox() {
        List<Event> out = new ArrayList<Event>(outbox);
        outbox.clear();
        return out;
    }

    public boolean isLatched(String deviceId) {
        return overheatLatched.contains(deviceId);
    }
}
