package com.dxlab.homehub.device;

import com.dxlab.homehub.model.DeviceStatus;
import com.dxlab.homehub.model.EventType;

/**
 * Appliance lifecycle:
 *
 *   OFF --PWR_ON--> IDLE --CYC_S--> RUNNING --CYC_E--> IDLE
 *   any --PWR_OFF--> OFF
 *   any (except OFF) --LEAK/OVHT--> ERROR      (ERROR is left only by PWR_OFF)
 */
public final class DeviceStateMachine {
    private DeviceStateMachine() {
    }

    public static DeviceStatus next(DeviceStatus s, EventType t) {
        if (t == EventType.POWER_OFF) return DeviceStatus.OFF;
        switch (s) {
            case OFF:
                if (t == EventType.POWER_ON) return DeviceStatus.IDLE;
                return DeviceStatus.OFF;
            case IDLE:
                if (t == EventType.CYCLE_START) return DeviceStatus.RUNNING;
                if (t.isCritical()) return DeviceStatus.ERROR;
                return DeviceStatus.IDLE;
            case RUNNING:
                if (t == EventType.CYCLE_END) return DeviceStatus.IDLE;
                if (t.isCritical()) return DeviceStatus.ERROR;
                return DeviceStatus.RUNNING;
            case ERROR:
            default:
                return DeviceStatus.ERROR;
        }
    }

    public static boolean isLegal(DeviceStatus from, EventType t) {
        return next(from, t) != from || t == EventType.HEARTBEAT || t == EventType.TEMP_REPORT;
    }
}
