package com.dxlab.homehub.app;

import com.dxlab.homehub.device.DeviceRegistry;
import com.dxlab.homehub.dispatch.Dispatcher;
import com.dxlab.homehub.dispatch.HandlerRegistry;
import com.dxlab.homehub.dispatch.SubmitResult;
import com.dxlab.homehub.handlers.CountingHandler;
import com.dxlab.homehub.handlers.DeviceStatusHandler;
import com.dxlab.homehub.handlers.SafetyHandler;
import com.dxlab.homehub.handlers.TemperatureHandler;
import com.dxlab.homehub.io.EventParser;
import com.dxlab.homehub.model.Device;
import com.dxlab.homehub.model.DeviceKind;
import com.dxlab.homehub.model.Event;
import com.dxlab.homehub.model.EventType;
import com.dxlab.homehub.ops.AuditLog;
import com.dxlab.homehub.ops.Metrics;
import com.dxlab.homehub.ops.RecoveryManager;
import com.dxlab.homehub.ops.Watchdog;
import com.dxlab.homehub.power.PowerBudget;
import com.dxlab.homehub.queue.EventQueue;
import com.dxlab.homehub.queue.RingEventQueue;
import com.dxlab.homehub.rules.RuleEngine;

import java.util.Iterator;
import java.util.List;
import java.util.Map;

/** Composition root. One instance per physical hub. */
public final class HomeHub {
    private final HubConfig config;
    private final EventQueue queue;
    private final Metrics metrics = new Metrics();
    private final AuditLog audit = new AuditLog();
    private final DeviceRegistry devices = new DeviceRegistry();
    private final EventParser parser = new EventParser();
    private final PowerBudget power;
    private final Dispatcher dispatcher;
    private final RuleEngine rules;
    private final Watchdog watchdog;
    private final RecoveryManager recovery;

    public HomeHub(HubConfig config) {
        this(config, new RingEventQueue(config.queueCapacity()));
    }

    public HomeHub(HubConfig config, EventQueue queue) {
        this.config = config;
        this.queue = queue;
        this.power = new PowerBudget(config.powerCapWatts());

        Map<String, DeviceKind> declared = config.devices();
        Iterator<Map.Entry<String, DeviceKind>> it = declared.entrySet().iterator();
        while (it.hasNext()) {
            Map.Entry<String, DeviceKind> en = it.next();
            devices.register(en.getKey(), en.getValue());
        }

        HandlerRegistry handlers = new HandlerRegistry();
        DeviceStatusHandler status = new DeviceStatusHandler(devices, power, audit, metrics);
        handlers.register(EventType.POWER_ON, status);
        handlers.register(EventType.POWER_OFF, status);
        handlers.register(EventType.CYCLE_START, status);
        handlers.register(EventType.CYCLE_END, status);
        handlers.register(EventType.DOOR_OPEN, status);
        handlers.register(EventType.DOOR_CLOSE, status);
        handlers.register(EventType.HEARTBEAT, status);
        handlers.register(EventType.TEMP_REPORT,
                new TemperatureHandler(devices, metrics, audit, config.getInt("temp.highCelsius")));
        SafetyHandler safety = new SafetyHandler(devices, power, audit, metrics);
        handlers.register(EventType.LEAK_DETECTED, safety);
        handlers.register(EventType.OVERHEAT, safety);
        handlers.setFallback(new CountingHandler(metrics));

        this.dispatcher = new Dispatcher(queue, handlers, metrics, audit, config.autoDrainOnFull());
        this.rules = new RuleEngine(devices, audit, config.getInt("rules.overheatAfterReports"),
                config.getLong("rules.doorOpenAlertMillis"));
        this.dispatcher.setListener(rules);
        this.watchdog = new Watchdog(queue, audit, config.getInt("watchdog.threshold"));
        this.recovery = new RecoveryManager(queue, metrics, audit);
    }

    /** Parses one wire-format line and submits it. */
    public SubmitResult ingest(String line) {
        Event e = parser.parse(line);
        if (e == null) {
            metrics.increment("ingest.dropped");
            return SubmitResult.INVALID;
        }
        SubmitResult r = dispatcher.submit(e);
        flushDerived();
        return r;
    }

    public SubmitResult submit(Event e) {
        SubmitResult r = dispatcher.submit(e);
        flushDerived();
        return r;
    }

    /** Dispatches one event. Returns false if the queue was empty. */
    public boolean step() {
        Event e = dispatcher.dispatchOne();
        flushDerived();
        return e != null;
    }

    public int drain() {
        int n = 0;
        while (step()) {
            n++;
        }
        return n;
    }

    /** Periodic maintenance (called every second by the scheduler on the real hub). */
    public void tick() {
        if (watchdog.check()) {
            recovery.recover();
        }
    }

    private void flushDerived() {
        List<Event> derived = rules.takeOutbox();
        for (Event d : derived) {
            dispatcher.submit(d);
        }
    }

    /** One-line observable state used for traces and golden-file comparisons. */
    public String observable() {
        StringBuilder sb = new StringBuilder();
        sb.append("q=").append(queue.size()).append('[');
        List<Event> pending = queue.snapshot();
        for (int i = 0; i < pending.size(); i++) {
            if (i > 0) sb.append(',');
            sb.append(pending.get(i).getSeq());
        }
        sb.append("] dev=");
        List<Device> all = devices.all();
        for (int i = 0; i < all.size(); i++) {
            if (i > 0) sb.append(',');
            Device d = all.get(i);
            sb.append(d.getId()).append(':').append(d.getStatus());
        }
        sb.append(" power=").append(power.totalLoad()).append('/').append(power.getCapWatts());
        sb.append(" metrics={").append(metrics.snapshot()).append('}');
        sb.append(" audit=").append(audit.tail(3));
        return sb.toString();
    }

    public EventQueue getQueue() {
        return queue;
    }

    public Metrics getMetrics() {
        return metrics;
    }

    public AuditLog getAudit() {
        return audit;
    }

    public DeviceRegistry getDevices() {
        return devices;
    }

    public PowerBudget getPower() {
        return power;
    }

    public Dispatcher getDispatcher() {
        return dispatcher;
    }

    public EventParser getParser() {
        return parser;
    }

    public RuleEngine getRules() {
        return rules;
    }

    public HubConfig getConfig() {
        return config;
    }
}
