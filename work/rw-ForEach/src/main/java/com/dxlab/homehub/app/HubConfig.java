package com.dxlab.homehub.app;

import com.dxlab.homehub.model.DeviceKind;

import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Properties;

/** Hub configuration (hub.properties). Unknown keys are ignored. */
public final class HubConfig {
    private final Properties props = new Properties();

    public HubConfig() {
        props.setProperty("queue.capacity", "8");
        props.setProperty("dispatch.autoDrainOnFull", "false");
        props.setProperty("power.capWatts", "4000");
        props.setProperty("watchdog.threshold", "3");
        props.setProperty("temp.highCelsius", "10");
        props.setProperty("rules.overheatAfterReports", "3");
        props.setProperty("rules.doorOpenAlertMillis", "300000");
        props.setProperty("devices",
                "washer-1:WASHER,dryer-1:DRYER,fridge-1:FRIDGE,fridge-2:FRIDGE,aircon-1:AIRCON,"
                        + "oven-1:OVEN,leak-1:LEAK_SENSOR,tv-1:TV");
    }

    public static HubConfig load(String path) throws IOException {
        HubConfig c = new HubConfig();
        InputStream in = new FileInputStream(path);
        try {
            c.props.load(in);
        } finally {
            in.close();
        }
        return c;
    }

    public HubConfig set(String key, String value) {
        props.setProperty(key, value);
        return this;
    }

    public int getInt(String key) {
        return Integer.parseInt(props.getProperty(key).trim());
    }

    public long getLong(String key) {
        return Long.parseLong(props.getProperty(key).trim());
    }

    public boolean getBoolean(String key) {
        return Boolean.valueOf(props.getProperty(key).trim()).booleanValue() == true;
    }

    public int queueCapacity() {
        return getInt("queue.capacity");
    }

    public boolean autoDrainOnFull() {
        return getBoolean("dispatch.autoDrainOnFull");
    }

    public int powerCapWatts() {
        return getInt("power.capWatts");
    }

    /** device id -> kind, in declaration order. */
    public Map<String, DeviceKind> devices() {
        Map<String, DeviceKind> out = new LinkedHashMap<String, DeviceKind>();
        String raw = props.getProperty("devices", "");
        String[] items = raw.split(",");
        for (int i = 0; i < items.length; i++) {
            String item = items[i].trim();
            if (item.length() == 0) continue;
            String[] kv = item.split(":");
            out.put(kv[0].trim(), DeviceKind.valueOf(kv[1].trim()));
        }
        return out;
    }
}
