package com.dxlab.homehub;

import com.dxlab.homehub.device.DeviceRegistry;
import com.dxlab.homehub.handlers.DeviceStatusHandler;
import com.dxlab.homehub.handlers.SafetyHandler;
import com.dxlab.homehub.handlers.TemperatureHandler;
import com.dxlab.homehub.model.Device;
import com.dxlab.homehub.model.DeviceKind;
import com.dxlab.homehub.model.DeviceStatus;
import com.dxlab.homehub.model.Event;
import com.dxlab.homehub.model.EventType;
import com.dxlab.homehub.ops.AuditLog;
import com.dxlab.homehub.ops.Metrics;
import com.dxlab.homehub.power.PowerBudget;
import com.dxlab.homehub.testkit.Check;

public class HandlersTest {
    private final DeviceRegistry devices = new DeviceRegistry();
    private final PowerBudget power = new PowerBudget(4000);
    private final AuditLog audit = new AuditLog();
    private final Metrics metrics = new Metrics();

    public HandlersTest() {
        devices.register("washer-1", DeviceKind.WASHER);
        devices.register("dryer-1", DeviceKind.DRYER);
        devices.register("fridge-1", DeviceKind.FRIDGE);
    }

    static Event ev(long seq, String dev, EventType t, int v) {
        return new Event(seq, dev, t, v, seq * 1000);
    }

    public void testHeavyLoadNeedsPower() {
        DeviceStatusHandler h = new DeviceStatusHandler(devices, power, audit, metrics);
        h.handle(ev(1, "washer-1", EventType.POWER_ON, 0));
        h.handle(ev(2, "washer-1", EventType.CYCLE_START, 0));
        Check.eq(DeviceStatus.RUNNING, devices.get("washer-1").getStatus(), "running");
        Check.eq(2000, power.totalLoad(), "granted");
        h.handle(ev(3, "dryer-1", EventType.POWER_ON, 0));
        h.handle(ev(4, "dryer-1", EventType.CYCLE_START, 0));
        Check.eq(DeviceStatus.IDLE, devices.get("dryer-1").getStatus(), "denied stays idle");
        Check.isTrue(audit.contains("POWER_DENIED:4@"), "audited");
    }

    public void testCycleEndReleasesPower() {
        DeviceStatusHandler h = new DeviceStatusHandler(devices, power, audit, metrics);
        h.handle(ev(1, "washer-1", EventType.POWER_ON, 0));
        h.handle(ev(2, "washer-1", EventType.CYCLE_START, 0));
        h.handle(ev(3, "washer-1", EventType.CYCLE_END, 0));
        Check.isTrue(power.isIdle(), "released");
    }

    public void testUnknownDevice() {
        new DeviceStatusHandler(devices, power, audit, metrics).handle(ev(1, "ghost", EventType.POWER_ON, 0));
        Check.eq(1, metrics.get("device.unknown"), "unknown");
    }

    public void testHighTemperatureIsCounted() {
        TemperatureHandler h = new TemperatureHandler(devices, metrics, audit, 10);
        h.handle(ev(1, "fridge-1", EventType.TEMP_REPORT, 11));
        h.handle(ev(2, "fridge-1", EventType.TEMP_REPORT, 12));
        h.handle(ev(3, "fridge-1", EventType.TEMP_REPORT, 13));
        Device f = devices.get("fridge-1");
        Check.eq(3, f.getConsecutiveHighTemp(), "three high readings");
        h.handle(ev(4, "fridge-1", EventType.TEMP_REPORT, 4));
        Check.eq(0, f.getConsecutiveHighTemp(), "reset");
    }

    public void testLeakStopsRunningWasher() {
        DeviceStatusHandler h = new DeviceStatusHandler(devices, power, audit, metrics);
        h.handle(ev(1, "washer-1", EventType.POWER_ON, 0));
        h.handle(ev(2, "washer-1", EventType.CYCLE_START, 0));
        new SafetyHandler(devices, power, audit, metrics).handle(ev(3, "leak-1", EventType.LEAK_DETECTED, 1));
        Check.eq(DeviceStatus.ERROR, devices.get("washer-1").getStatus(), "stopped");
        Check.isTrue(power.isIdle(), "power released");
    }
}
