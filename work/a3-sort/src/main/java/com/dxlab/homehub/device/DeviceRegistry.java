package com.dxlab.homehub.device;

import com.dxlab.homehub.model.Device;
import com.dxlab.homehub.model.DeviceKind;

import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public final class DeviceRegistry {
    private final Map<String, Device> devices = new HashMap<String, Device>();

    public Device register(String id, DeviceKind kind) {
        Device d = devices.get(id);
        if (d == null) {
            d = new Device(id, kind);
            devices.put(id, d);
        }
        return d;
    }

    public Device get(String id) {
        return devices.get(id);
    }

    public boolean isKnown(String id) {
        return devices.containsKey(id);
    }

    public List<Device> byKind(DeviceKind kind) {
        List<Device> out = new ArrayList<Device>();
        for (Device d : devices.values()) {
            if (d.getKind() == kind) out.add(d);
        }
        sortById(out);
        return out;
    }

    public List<Device> all() {
        List<Device> out = new ArrayList<Device>(devices.values());
        sortById(out);
        return out;
    }

    public int size() {
        return devices.size();
    }

    private static void sortById(List<Device> list) {
        Collections.sort(list, new Comparator<Device>() {
            public int compare(Device a, Device b) {
                // group by kind first, then by id
                int k = a.getKind().compareTo(b.getKind());
                return k != 0 ? k : a.getId().compareTo(b.getId());
            }
        });
    }
}
