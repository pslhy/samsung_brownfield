package com.dxlab.homehub.dispatch;

public enum SubmitResult {
    /** Queued normally. */
    ACCEPTED,
    /** Queue was full; the oldest non-critical event was evicted to make room (critical events only). */
    ACCEPTED_EVICTED,
    /** Queue was full; one queued event was dispatched synchronously to make room. */
    ACCEPTED_DRAINED,
    /** Queue was full; non-critical event rejected (back-pressure to the device). */
    REJECTED_FULL,
    /** Null or unparsable input. */
    INVALID
}
