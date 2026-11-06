양수 용량은 생성자의 사전조건으로 표현했습니다. 기본 용량은 8이며, `Valid()`는 원형 버퍼의 범위와 저장된 이벤트의 비-null 조건을 보장합니다.

```dafny
class Event {}

datatype OfferResult = REJECTED | FULL | OK

class RingEventQueue {
  static const DEFAULT_CAPACITY: int := 8

  var buf: array<Event?>
  var head: int
  var count: int

  // Equivalent to (h + i) % n within the stated bounds.
  static function Index(n: int, h: int, i: int): int
    requires n > 0
    requires 0 <= h < n
    requires 0 <= i < n
    ensures 0 <= Index(n, h, i) < n
  {
    if h + i < n then h + i else h + i - n
  }

  static lemma IndexDistinct(n: int, h: int, i: int, j: int)
    requires n > 0
    requires 0 <= h < n
    requires 0 <= i < n
    requires 0 <= j < n
    requires i != j
    ensures Index(n, h, i) != Index(n, h, j)
  {
  }

  static lemma IndexShift(n: int, h: int, i: int)
    requires n > 0
    requires 0 <= h < n
    requires 0 <= i < n - 1
    ensures
      Index(n, if h + 1 == n then 0 else h + 1, i)
        == Index(n, h, i + 1)
  {
  }

  ghost predicate Valid()
    reads this, buf
  {
    buf.Length > 0
    && 0 <= head < buf.Length
    && 0 <= count <= buf.Length
    && (forall i: int ::
          0 <= i < count ==>
            buf[Index(buf.Length, head, i)] != null)
  }

  constructor(capacity: int := DEFAULT_CAPACITY)
    requires capacity > 0
    ensures Valid()
    ensures buf.Length == capacity
    ensures head == 0
    ensures count == 0
    ensures fresh(buf)
  {
    buf := new Event?[capacity];
    head := 0;
    count := 0;
  }

  method offer(e: Event?) returns (result: OfferResult)
    requires Valid()
    modifies this, buf
    ensures Valid()
    ensures buf == old(buf)
    ensures head == old(head)
    ensures e == null ==> result == REJECTED
    ensures e != null && old(count) == buf.Length ==> result == FULL
    ensures e != null && old(count) < buf.Length ==> result == OK
    ensures count == old(count) + (if result == OK then 1 else 0)
    ensures result != OK ==> buf[..] == old(buf[..])
    ensures result == OK ==>
      buf[Index(buf.Length, head, old(count))] == e
  {
    if e == null {
      result := REJECTED;
      return;
    }

    if count == buf.Length {
      result := FULL;
      return;
    }

    var n := buf.Length;
    var h := head;
    var c := count;
    var tail := Index(n, h, c);

    assert forall i: int ::
      0 <= i < c ==> buf[Index(n, h, i)] != null;

    forall i: int | 0 <= i < c
      ensures Index(n, h, i) != tail
    {
      IndexDistinct(n, h, i, c);
    }

    buf[tail] := e;
    count := c + 1;

    forall i: int | 0 <= i < count
      ensures buf[Index(n, head, i)] != null
    {
      if i < c {
        assert Index(n, h, i) != tail;
      } else {
        assert i == c;
      }
    }

    result := OK;
  }

  method poll() returns (e: Event?)
    requires Valid()
    modifies this, buf
    ensures Valid()
    ensures buf == old(buf)
    ensures (e == null) <==> old(count) == 0
    ensures count == (if old(count) == 0 then 0 else old(count) - 1)
    ensures old(count) == 0 ==>
      head == old(head) && buf[..] == old(buf[..])
    ensures old(count) > 0 ==>
      e == old(buf[head])
    ensures old(count) > 0 ==>
      head == (if old(head) + 1 == buf.Length
               then 0 else old(head) + 1)
  {
    if count == 0 {
      e := null;
      return;
    }

    var n := buf.Length;
    var h := head;
    var c := count;

    assert Index(n, h, 0) == h;
    e := buf[h];
    assert e != null;

    forall i: int | 0 <= i < c - 1
      ensures Index(n, h, i + 1) != h
      ensures buf[Index(n, h, i + 1)] != null
    {
      IndexDistinct(n, h, i + 1, 0);
      assert Index(n, h, 0) == h;
    }

    buf[h] := null;
    head := if h + 1 == n then 0 else h + 1;
    count := c - 1;

    forall i: int | 0 <= i < count
      ensures buf[Index(n, head, i)] != null
    {
      IndexShift(n, h, i);
      assert Index(n, head, i) == Index(n, h, i + 1);
      assert Index(n, h, i + 1) != h;
    }
  }

  method peek() returns (e: Event?)
    requires Valid()
    ensures (e == null) <==> count == 0
    ensures count > 0 ==> e == buf[head]
  {
    if count == 0 {
      e := null;
    } else {
      assert Index(buf.Length, head, 0) == head;
      e := buf[head];
    }
  }

  method size() returns (n: int)
    requires Valid()
    ensures n == count
  {
    n := count;
  }

  method capacity() returns (n: int)
    requires Valid()
    ensures n == buf.Length
  {
    n := buf.Length;
  }

  method isEmpty() returns (empty: bool)
    requires Valid()
    ensures empty <==> count == 0
  {
    empty := count == 0;
  }

  method clear()
    requires Valid()
    modifies this, buf
    ensures Valid()
    ensures buf == old(buf)
    ensures count == 0
  {
    while count > 0
      invariant Valid()
      invariant buf == old(buf)
      decreases count
    {
      var e := poll();
      assert e != null;
    }
  }

  // A Dafny sequence represents the returned Java List.
  method snapshot() returns (out: seq<Event?>)
    requires Valid()
    ensures |out| == count
    ensures forall i: int ::
      0 <= i < count ==>
        out[i] == buf[Index(buf.Length, head, i)]
    ensures forall i: int ::
      0 <= i < |out| ==> out[i] != null
  {
    out := [];
    var i := 0;

    while i < count
      invariant 0 <= i <= count
      invariant |out| == i
      invariant forall j: int ::
        0 <= j < i ==>
          out[j] == buf[Index(buf.Length, head, j)]
      invariant forall j: int ::
        0 <= j < |out| ==> out[j] != null
      decreases count - i
    {
      var e := buf[Index(buf.Length, head, i)];
      assert e != null;
      out := out + [e];
      i := i + 1;
    }
  }
}
```