package com.dxlab.homehub.testkit;

public final class Check {
    private Check() {
    }

    public static void isTrue(boolean cond, String msg) {
        if (!cond) throw new AssertionError(msg);
    }

    public static void isFalse(boolean cond, String msg) {
        if (cond) throw new AssertionError(msg);
    }

    public static void eq(Object expected, Object actual, String msg) {
        if (expected == null ? actual != null : !expected.equals(actual)) {
            throw new AssertionError(msg + ": expected <" + expected + "> but was <" + actual + ">");
        }
    }

    public static void eq(long expected, long actual, String msg) {
        if (expected != actual) {
            throw new AssertionError(msg + ": expected <" + expected + "> but was <" + actual + ">");
        }
    }

    public static void isNull(Object o, String msg) {
        if (o != null) throw new AssertionError(msg + ": expected null but was <" + o + ">");
    }
}
