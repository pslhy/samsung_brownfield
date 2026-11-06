// REQ-2 version of formal/RingQueue.dfy.
// Rule: when a Java method changes, its Dafny method is rewritten from the new Java code.
// The Java patch changed offer, poll, clear and snapshot, so exactly these four method BODIES
// are rewritten below (marked "REQ-2"). Contracts (requires/ensures) are not touched.
// Shadow model of com.dxlab.homehub.queue.RingEventQueue.
//
// The executable part mirrors the Java fields (buf, head, count) so that the model can be
// compiled to Java and compared with the legacy class (difftest/).
// The ghost field elems is the abstraction: the logical FIFO content, oldest first.
// Every public contract below is stated over elems only.
//
// Outside the model: offer(null) (Java returns REJECTED), object identity, threads.


module RingQueueModel {
  import opened Types

  class RingQueue {
    var buf: array<Event>
    var head: i32
    var count: i32
    ghost var elems: seq<Event>

    // Public invariant: the only facts clients (Dispatcher) may rely on.
    ghost predicate Valid()
      reads this, buf
    {
      Inv() && 0 < Capacity() < 0x4000_0000 && |elems| <= Capacity()
    }

    // Representation invariant. Opaque: hidden from clients, revealed only inside this class.
    // This keeps client proofs small and stable, and a change here only affects the
    // symbols that `reveal Inv()` (see tools/reverify.py).
    ghost opaque predicate Inv()
      reads this, buf
    {
      && 0 < buf.Length < 0x4000_0000
      && 0 <= head as int < buf.Length
      && 0 <= count as int <= buf.Length
      && |elems| == count as int
      && forall i :: 0 <= i < count as int ==> elems[i] == buf[Wrap(head as int + i)]
    }

    // Java: k % buf.length. The postcondition (proved once, by lemma ModWrap) lets the other
    // proofs avoid reasoning about division.
    function Wrap(k: int): (w: int)
      reads this
      requires 0 <= k < 2 * buf.Length
      ensures w == if k < buf.Length then k else k - buf.Length
    {
      ModWrap(k, buf.Length);
      k % buf.Length
    }

    function Capacity(): int
      reads this
    {
      buf.Length
    }

    constructor (capacity: i32)
      requires 0 < capacity < 0x4000_0000
      ensures Valid() && fresh(buf)
      ensures elems == [] && Capacity() == capacity as int
    {
      buf := new Event[capacity](_ => Event(0, false));
      head := 0;
      count := 0;
      elems := [];
      new;
      reveal Inv();
    }

    method Offer(e: Event) returns (r: OfferResult)
      requires Valid()
      modifies this, buf
      ensures Valid() && buf == old(buf)
      ensures |old(elems)| < Capacity() ==> r == OK && elems == old(elems) + [e]
      ensures |old(elems)| == Capacity() ==> r == FULL && elems == old(elems)
    {
      reveal Inv();
      if count as int == buf.Length {
        return FULL;
      }
      // REQ-2. Java: int idx = head + count; if (idx >= buf.length) idx -= buf.length;
      var idx := head + count;
      if idx as int >= buf.Length {
        idx := idx - buf.Length as i32;
      }
      buf[idx] := e;
      count := count + 1;
      elems := elems + [e];
      return OK;
    }

    method Poll() returns (ok: bool, e: Event)
      requires Valid()
      modifies this, buf
      ensures Valid() && buf == old(buf)
      ensures |old(elems)| == 0 ==> !ok && elems == old(elems)
      ensures |old(elems)| > 0 ==> ok && e == old(elems)[0] && elems == old(elems)[1..]
    {
      reveal Inv();
      if count == 0 {
        return false, Event(0, false);
      }
      e := buf[head];
      buf[head] := Event(0, false);   // Java: buf[head] = null
      // REQ-2. Java: head++; if (head == buf.length) head = 0;
      head := head + 1;
      if head as int == buf.Length {
        head := 0;
      }
      count := count - 1;
      elems := elems[1..];
      ok := true;
    }

    method Peek() returns (ok: bool, e: Event)
      requires Valid()
      ensures ok == (|elems| > 0)
      ensures ok ==> e == elems[0]
    {
      reveal Inv();
      if count == 0 {
        return false, Event(0, false);
      }
      return true, buf[head];
    }

    method Size() returns (n: i32)
      requires Valid()
      ensures n as int == |elems|
    {
      reveal Inv();
      return count;
    }

    // Java: capacity()
    method GetCapacity() returns (n: i32)
      requires Valid()
      ensures n as int == Capacity()
    {
      reveal Inv();
      return buf.Length as i32;
    }

    method IsEmpty() returns (b: bool)
      requires Valid()
      ensures b == (|elems| == 0)
    {
      reveal Inv();
      return count == 0;
    }

    // REQ-2. Java: Arrays.fill(buf, null); head = 0; count = 0;
    method Clear()
      requires Valid()
      modifies this, buf
      ensures Valid() && buf == old(buf)
      ensures elems == []
    {
      reveal Inv();
      var i := 0;
      while i < buf.Length
        invariant 0 <= i <= buf.Length
        modifies buf
      {
        buf[i] := Event(0, false);
        i := i + 1;
      }
      head := 0;
      count := 0;
      elems := [];
    }

    // REQ-2. Java: int idx = head; ... idx++; if (idx == buf.length) idx = 0;
    method Snapshot() returns (s: seq<Event>)
      requires Valid()
      ensures s == elems
    {
      reveal Inv();
      s := [];
      var idx := head;
      var i: i32 := 0;
      while i < count
        invariant 0 <= i <= count
        invariant 0 <= idx as int < buf.Length
        invariant idx as int == Wrap(head as int + i as int)
        invariant s == elems[..i]
      {
        s := s + [buf[idx]];
        idx := idx + 1;
        if idx as int == buf.Length {
          idx := 0;
        }
        i := i + 1;
      }
    }
  }
}
