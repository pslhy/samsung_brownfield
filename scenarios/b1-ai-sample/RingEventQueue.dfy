// Example answer to docs/PROMPTS.md P-1 ("translate this Java class to Dafny"), kept so the
// lab works without an AI tool. A different AI will write a different model: names, types and
// proof style vary. What matters is checked by people (contracts) and by tools (dafny verify,
// make difftest-mine).

module RingEventQueueModel {

  // Java's Event is reduced to what the queue can observe.
  datatype Event = Event(id: int, critical: bool)

  datatype OfferResult = OK | FULL | REJECTED

  class RingEventQueue {
    var buf: array<Event>
    var head: int
    var count: int
    ghost var elems: seq<Event>     // logical content, oldest first

    ghost predicate Valid()
      reads this, buf
    {
      && buf.Length > 0
      && 0 <= head < buf.Length
      && 0 <= count <= buf.Length
      && |elems| == count
      && forall i :: 0 <= i < count ==> elems[i] == buf[(head + i) % buf.Length]
    }

    constructor (capacity: int)
      requires capacity > 0
      ensures Valid() && fresh(buf)
      ensures elems == [] && buf.Length == capacity
    {
      buf := new Event[capacity](_ => Event(0, false));
      head := 0;
      count := 0;
      elems := [];
    }

    method Offer(e: Event) returns (r: OfferResult)
      requires Valid()
      modifies this, buf
      ensures Valid() && buf == old(buf)
      ensures old(count) < buf.Length ==> r == OK && elems == old(elems) + [e]
      ensures old(count) == buf.Length ==> r == FULL && elems == old(elems)
    {
      if count == buf.Length {
        return FULL;
      }
      buf[(head + count) % buf.Length] := e;
      count := count + 1;
      elems := elems + [e];
      forall i | 0 <= i < count
        ensures elems[i] == buf[(head + i) % buf.Length]
      {
        ModLemma(head, i, buf.Length);
        ModLemma(head, count - 1, buf.Length);
      }
      return OK;
    }

    method Poll() returns (e: Event, ok: bool)
      requires Valid()
      modifies this, buf
      ensures Valid() && buf == old(buf)
      ensures old(count) == 0 ==> !ok && elems == old(elems)
      ensures old(count) > 0 ==> ok && e == old(elems)[0] && elems == old(elems)[1..]
    {
      if count == 0 {
        return Event(0, false), false;
      }
      assert head % buf.Length == head;
      e := buf[head];
      buf[head] := Event(0, false);
      var oldHead := head;
      head := (head + 1) % buf.Length;
      count := count - 1;
      elems := elems[1..];
      forall i | 0 <= i < count
        ensures elems[i] == buf[(head + i) % buf.Length]
      {
        ModLemma(oldHead, i + 1, buf.Length);
        ModLemma(oldHead, 0, buf.Length);
        ShiftLemma(oldHead, i, buf.Length);
      }
      ok := true;
    }

    method Peek() returns (e: Event, ok: bool)
      requires Valid()
      ensures ok == (|elems| > 0)
      ensures ok ==> e == elems[0]
    {
      if count == 0 {
        return Event(0, false), false;
      }
      assert head % buf.Length == head;
      return buf[head], true;
    }

    function Size(): int
      reads this
    {
      count
    }

    function Capacity(): int
      reads this
    {
      buf.Length
    }

    function IsEmpty(): bool
      reads this
    {
      count == 0
    }

    method Clear()
      requires Valid()
      modifies this, buf
      ensures Valid() && buf == old(buf)
      ensures elems == []
    {
      var e, ok := Poll();
      while ok
        invariant Valid() && buf == old(buf)
        invariant !ok ==> elems == []
        decreases |elems| + (if ok then 1 else 0)
      {
        e, ok := Poll();
      }
    }

    method Snapshot() returns (out: seq<Event>)
      requires Valid()
      ensures out == elems
    {
      out := [];
      var i := 0;
      while i < count
        invariant 0 <= i <= count
        invariant out == elems[..i]
      {
        out := out + [buf[(head + i) % buf.Length]];
        i := i + 1;
      }
    }
  }

  // (h + i) % n stays a valid slot, and the slot at position i differs from the slot at
  // position count-1 unless i == count-1 (positions are distinct within one lap).
  lemma ModLemma(h: int, i: int, n: int)
    requires 0 <= h < n && 0 <= i < n
    ensures 0 <= (h + i) % n < n
    ensures (h + i) % n == if h + i < n then h + i else h + i - n
  {
    if h + i < n {
      assert h + i == 0 * n + (h + i);
    } else {
      assert h + i == 1 * n + (h + i - n);
    }
  }

  lemma ShiftLemma(h: int, i: int, n: int)
    requires 0 <= h < n && 0 <= i < n - 1
    ensures ((h + 1) % n + i) % n == (h + (i + 1)) % n
  {
    ModLemma(h, 1, n);
    ModLemma(h, i + 1, n);
    var h1 := (h + 1) % n;
    ModLemma(h1, i, n);
  }
}
