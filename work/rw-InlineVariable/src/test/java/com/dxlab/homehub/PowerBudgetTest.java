package com.dxlab.homehub;

import com.dxlab.homehub.power.PowerBudget;
import com.dxlab.homehub.testkit.Check;

public class PowerBudgetTest {

    public void testGrantWithinCap() {
        PowerBudget p = new PowerBudget(4000);
        Check.isTrue(p.tryStart("washer-1", 2000), "washer");
        Check.isTrue(p.tryStart("oven-1", 1800), "oven");
        Check.eq(3800, p.totalLoad(), "load");
    }

    public void testDenyOverCap() {
        PowerBudget p = new PowerBudget(4000);
        p.tryStart("washer-1", 2000);
        Check.isFalse(p.tryStart("dryer-1", 2500), "dryer denied");
        Check.eq(2000, p.totalLoad(), "load unchanged");
    }

    public void testIdempotentStart() {
        PowerBudget p = new PowerBudget(4000);
        p.tryStart("washer-1", 2000);
        Check.isTrue(p.tryStart("washer-1", 2000), "again");
        Check.eq(2000, p.totalLoad(), "counted once");
    }

    public void testStopReleases() {
        PowerBudget p = new PowerBudget(4000);
        p.tryStart("washer-1", 2000);
        p.stop("washer-1");
        Check.isTrue(p.isIdle(), "idle");
        Check.eq(4000, p.headroom(), "headroom");
    }

    public void testRejectInvalidWatts() {
        PowerBudget p = new PowerBudget(4000);
        Check.isFalse(p.tryStart("x", 0), "zero");
        Check.isFalse(p.tryStart("x", 5000), "over cap");
    }
}
