package com.dxlab.homehub;

import com.dxlab.homehub.app.HomeHub;
import com.dxlab.homehub.app.HubConfig;
import com.dxlab.homehub.dispatch.SubmitResult;
import com.dxlab.homehub.model.DeviceStatus;
import com.dxlab.homehub.testkit.Check;

public class HomeHubTest {

    public void testWasherCycleEndToEnd() {
        HomeHub hub = new HomeHub(new HubConfig());
        hub.ingest("1|washer-1|PWR_ON|0|1000");
        hub.ingest("2|washer-1|CYC_S|0|2000");
        hub.drain();
        Check.eq(DeviceStatus.RUNNING, hub.getDevices().get("washer-1").getStatus(), "running");
        hub.ingest("3|washer-1|CYC_E|0|3000");
        hub.drain();
        Check.eq(DeviceStatus.IDLE, hub.getDevices().get("washer-1").getStatus(), "idle");
        Check.isTrue(hub.getPower().isIdle(), "power released");
    }

    public void testFridgeOverheatRaisesAlarm() {
        HomeHub hub = new HomeHub(new HubConfig());
        hub.ingest("1|fridge-1|PWR_ON|0|0");
        hub.ingest("2|fridge-1|TEMP|11|1000|unit=C");
        hub.ingest("3|fridge-1|TEMP|12|2000|unit=C");
        hub.ingest("4|fridge-1|TEMP|13|3000|unit=C");
        hub.drain();
        Check.eq(DeviceStatus.ERROR, hub.getDevices().get("fridge-1").getStatus(), "alarm");
        Check.isTrue(hub.getAudit().contains("OVERHEAT_ALARM"), "audited");
    }

    public void testInvalidLineIsDropped() {
        HomeHub hub = new HomeHub(new HubConfig());
        Check.eq(SubmitResult.INVALID, hub.ingest("not|an|event"), "invalid");
        Check.eq(1, hub.getMetrics().get("ingest.dropped"), "counted");
    }

    public void testWatchdogRecoversStuckQueue() {
        HomeHub hub = new HomeHub(new HubConfig().set("queue.capacity", "4").set("dispatch.maxPending", "4"));
        hub.ingest("1|tv-1|HB|0|1");
        hub.ingest("2|tv-1|HB|0|2");
        hub.ingest("3|tv-1|HB|0|3");
        hub.ingest("4|leak-1|LEAK|1|4");
        hub.tick();
        hub.tick();
        hub.tick();
        Check.eq(1, hub.getQueue().size(), "only the critical event is kept");
        Check.eq(1, hub.getMetrics().get("recovery.count"), "recovered once");
    }

    public void testBurstOf32IsAccepted() {
        HomeHub hub = new HomeHub(new HubConfig());
        for (int i = 1; i <= 32; i++) {
            Check.eq(SubmitResult.ACCEPTED, hub.ingest(i + "|tv-1|HB|0|" + i), "event " + i);
        }
        Check.eq(SubmitResult.REJECTED_FULL, hub.ingest("33|tv-1|HB|0|33"), "33rd rejected");
    }

    public void testLeakDuringWashCycle() {
        HomeHub hub = new HomeHub(new HubConfig());
        hub.ingest("1|washer-1|PWR_ON|0|1000");
        hub.ingest("2|washer-1|CYC_S|0|2000");
        hub.ingest("3|leak-1|LEAK|1|3000");
        hub.drain();
        Check.eq(DeviceStatus.ERROR, hub.getDevices().get("washer-1").getStatus(), "safety stop");
    }
}
