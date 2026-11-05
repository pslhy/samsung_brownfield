package com.dxlab.homehub.power;

import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Peak-power admission control. Heavy appliances must obtain a grant before running.
 * Invariant (circuit-breaker safety): totalLoad() <= capWatts at all times.
 */
public final class PowerBudget {
    private final int capWatts;
    private final Map<String, Integer> running = new HashMap<String, Integer>();

    public PowerBudget(int capWatts) {
        if (capWatts <= 0) {
            throw new IllegalArgumentException("capWatts must be positive");
        }
        this.capWatts = capWatts;
    }

    /**
     * Grants power to deviceId if the cap allows it. Idempotent: a device that already holds a
     * grant keeps it (and its original wattage).
     */
    public synchronized boolean tryStart(String deviceId, int watts) {
        if (watts <= 0 || watts > capWatts) return false;
        if (running.containsKey(deviceId)) return true;
        if (totalLoad() + watts > capWatts) return false;
        running.put(deviceId, new Integer(watts));
        return true;
    }

    public synchronized void stop(String deviceId) {
        running.remove(deviceId);
    }

    public synchronized int totalLoad() {
        int sum = 0;
        for (String id : running.keySet()) {
            sum += running.get(id);
        }
        return sum;
    }

    public int headroom() {
        return capWatts - totalLoad();
    }

    public int getCapWatts() {
        return capWatts;
    }

    public synchronized boolean isRunning(String deviceId) {
        return running.containsKey(deviceId);
    }

    public synchronized boolean isIdle() {
        return running.isEmpty();
    }

    public synchronized List<String> runningDevices() {
        List<String> ids = new ArrayList<String>(running.keySet());
        Collections.sort(ids);
        return ids;
    }

    public synchronized void stopAll() {
        running.clear();
    }
}
