package com.dxlab.homehub;

import com.dxlab.homehub.device.DeviceStateMachine;
import com.dxlab.homehub.model.DeviceStatus;
import com.dxlab.homehub.model.EventType;
import com.dxlab.homehub.testkit.Check;

public class DeviceStateMachineTest {

    public void testNormalCycle() {
        DeviceStatus s = DeviceStatus.OFF;
        s = DeviceStateMachine.next(s, EventType.POWER_ON);
        Check.eq(DeviceStatus.IDLE, s, "on");
        s = DeviceStateMachine.next(s, EventType.CYCLE_START);
        Check.eq(DeviceStatus.RUNNING, s, "running");
        s = DeviceStateMachine.next(s, EventType.CYCLE_END);
        Check.eq(DeviceStatus.IDLE, s, "idle");
    }

    public void testErrorIsSticky() {
        DeviceStatus s = DeviceStateMachine.next(DeviceStatus.RUNNING, EventType.LEAK_DETECTED);
        Check.eq(DeviceStatus.ERROR, s, "error");
        Check.eq(DeviceStatus.ERROR, DeviceStateMachine.next(s, EventType.POWER_ON), "sticky");
        Check.eq(DeviceStatus.OFF, DeviceStateMachine.next(s, EventType.POWER_OFF), "power off");
    }

    public void testOffIgnoresCycle() {
        Check.eq(DeviceStatus.OFF, DeviceStateMachine.next(DeviceStatus.OFF, EventType.CYCLE_START), "off");
    }
}
