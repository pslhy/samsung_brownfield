package com.dxlab.homehub;

import com.dxlab.homehub.io.EventParser;
import com.dxlab.homehub.model.Event;
import com.dxlab.homehub.model.EventType;
import com.dxlab.homehub.testkit.Check;

public class EventParserTest {

    public void testBasicLine() {
        EventParser p = new EventParser();
        Event e = p.parse("12|washer-1|CYC_S|0|1000");
        Check.eq(12L, e.getSeq(), "seq");
        Check.eq("washer-1", e.getDeviceId(), "device");
        Check.eq(EventType.CYCLE_START, e.getType(), "type");
    }

    public void testAttributes() {
        EventParser p = new EventParser();
        Event e = p.parse("3|tv-1|PWR_ON|0|5|fw=2.1; region=KR");
        Check.eq("2.1", e.attr("fw"), "fw");
        Check.eq("KR", e.attr("region"), "region");
    }

    public void testCelsiusTemperature() {
        EventParser p = new EventParser();
        Event e = p.parse("5|fridge-1|TEMP|4|100|unit=C");
        Check.eq(4, e.getValue(), "celsius kept");
    }

    public void testFahrenheitIsNormalized() {
        EventParser p = new EventParser();
        Event e = p.parse("6|fridge-1|TEMP|50|100|unit=F");
        Check.eq(10, e.getValue(), "50F = 10C");
    }

    public void testMalformedLines() {
        EventParser p = new EventParser();
        Check.isNull(p.parse("garbage"), "too few fields");
        Check.isNull(p.parse("x|tv-1|HB|0|1"), "bad seq");
        Check.isNull(p.parse(null), "null");
        Check.eq(3, p.getStats().malformed, "malformed count");
    }

    public void testCommentsAreSkipped() {
        EventParser p = new EventParser();
        Check.isNull(p.parse("# comment"), "comment");
        Check.isNull(p.parse("   "), "blank");
        Check.eq(2, p.getStats().skipped, "skipped");
    }

    public void testUnknownCode() {
        Event e = new EventParser().parse("1|tv-1|ZZZ|0|1");
        Check.eq(EventType.UNKNOWN, e.getType(), "unknown");
    }
}
