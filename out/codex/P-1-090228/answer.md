```dafny
datatype OfferResult = OK | FULL | REJECTED

class Event {
}

class RingEventQueue {
  const DEFAULT_CAPACITY: int := 8

  var capacityValue: int
  var items: seq<Event>

  constructor(capacity: int)
    requires capacity > 0
    ensures capacityValue == capacity
    ensures items == []
  {
    capacityValue := capacity;
    items := [];
  }

  static method CreateDefault() returns (q: RingEventQueue)
    ensures q.capacity() == 8
    ensures q.size() == 0
  {
    q := new RingEventQueue(8);
  }

  method offer(e: Event?) returns (result: OfferResult)
    ensures e == null ==> result == REJECTED
    ensures e != null && |items| == capacityValue ==> result == FULL
    ensures e != null && |items| < capacityValue ==> result == OK
    ensures e == null ==> items == old(items)
    ensures e != null && |old(items)| == capacityValue ==> items == old(items)
    ensures e != null && |old(items)| < capacityValue ==> items == old(items) + [e]
  {
    if e == null {
      result := REJECTED;
      return;
    }

    if |items| == capacityValue {
      result := FULL;
      return;
    }

    items := items + [e];
    result := OK;
  }

  method poll() returns (e: Event?)
    ensures |old(items)| == 0 ==> e == null
    ensures |old(items)| == 0 ==> items == old(items)
    ensures |old(items)| > 0 ==> e == old(items)[0]
    ensures |old(items)| > 0 ==> items == old(items)[1..]
  {
    if |items| == 0 {
      e := null;
      return;
    }

    e := items[0];
    items := items[1..];
  }

  method peek() returns (e: Event?)
    ensures |items| == 0 ==> e == null
    ensures |items| > 0 ==> e == items[0]
    ensures items == old(items)
  {
    if |items| == 0 {
      e := null;
    } else {
      e := items[0];
    }
  }

  method size() returns (n: int)
    ensures n == |items|
  {
    n := |items|;
  }

  method capacity() returns (n: int)
    ensures n == capacityValue
  {
    n := capacityValue;
  }

  method isEmpty() returns (result: bool)
    ensures result <==> |items| == 0
  {
    result := |items| == 0;
  }

  method clear()
    ensures items == []
  {
    items := [];
  }

  method snapshot() returns (out: seq<Event>)
    ensures out == items
  {
    out := items;
  }
}
```