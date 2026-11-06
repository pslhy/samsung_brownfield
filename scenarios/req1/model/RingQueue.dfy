// REQ-1, patch B: growable ring buffer (copies in order, head = 0). Same module and class name as the legacy model
// (the Java class keeps its name too), so it can replace formal/RingQueue.dfy.
//
// What changed in the CONTRACT (not only the body):
//   - Offer returns FULL only at MaxCapacity(), not at the initial Capacity()
//   - buf may be replaced by a bigger array: the frame is now Repr, and callers can no longer
//     rely on `queue.buf == old(queue.buf)`
// Every caller of Offer (and every predicate that mentions Valid) must be re-verified.

module RingQueueModel {
  import opened Types

  class RingQueue {
    var buf: array<Event>
    var head: i32
    var count: i32
    const maxCap: i32
    ghost var elems: seq<Event>
    ghost var Repr: set<object>

    // Public invariant: the only facts clients may rely on.
    ghost predicate Valid()
      reads this, Repr
    {
      this in Repr && buf in Repr && Inv() && 0 < MaxCapacity() < 0x4000_0000
      && |elems| <= MaxCapacity()
    }

    // Representation invariant, hidden from clients (revealed only inside this class).
    ghost opaque predicate Inv()
      reads this, Repr
    {
      && buf in Repr
      && 0 < buf.Length <= maxCap as int < 0x4000_0000
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

    // current allocation (Java: capacity())
    function Capacity(): int
      reads this
    {
      buf.Length
    }

    function MaxCapacity(): int {
      maxCap as int
    }

    // Java: RingEventQueue(int capacity) = (capacity, max(capacity, MAX_CAPACITY = 32))
    constructor (capacity: i32)
      requires 0 < capacity < 0x4000_0000
      ensures Valid() && fresh(Repr)
      ensures elems == [] && Capacity() == capacity as int
      ensures MaxCapacity() == if capacity < 32 then 32 else capacity as int
    {
      buf := new Event[capacity](_ => Event(0, false));
      maxCap := if capacity < 32 then 32 else capacity;
      head := 0;
      count := 0;
      elems := [];
      new;
      Repr := {this, buf};
      reveal Inv();
    }

    method Offer(e: Event) returns (r: OfferResult)
      requires Valid()
      modifies Repr
      ensures Valid() && fresh(Repr - old(Repr))
      ensures |old(elems)| < MaxCapacity() ==> r == OK && elems == old(elems) + [e]
      ensures |old(elems)| == MaxCapacity() ==> r == FULL && elems == old(elems)
    {
      reveal Inv();
      if count as int == buf.Length {
        if buf.Length >= maxCap as int {
          return FULL;
        }
        Grow();
      }
      buf[Wrap(head as int + count as int)] := e;     // Java: buf[(head + count) % buf.length] = e
      count := count + 1;
      elems := elems + [e];
      return OK;
    }

    method Grow()
      requires Valid() && count as int == buf.Length < maxCap as int
      modifies Repr
      ensures Valid() && fresh(Repr - old(Repr))
      ensures elems == old(elems) && count as int < buf.Length
    {
      reveal Inv();
      var newLength := if buf.Length * 2 > maxCap as int then maxCap else (buf.Length * 2) as i32;
      var bigger := new Event[newLength](_ => Event(0, false));
      var i: i32 := 0;
      while i < count
        invariant 0 <= i <= count
        invariant forall j :: 0 <= j < i as int ==> bigger[j] == elems[j]
        modifies bigger
      {
        bigger[i] := buf[Wrap(head as int + i as int)];
        i := i + 1;
      }
      buf := bigger;
      head := 0;
      Repr := Repr + {bigger};
    }

    method Poll() returns (ok: bool, e: Event)
      requires Valid()
      modifies Repr
      ensures Valid() && Repr == old(Repr)
      ensures |old(elems)| == 0 ==> !ok && elems == old(elems)
      ensures |old(elems)| > 0 ==> ok && e == old(elems)[0] && elems == old(elems)[1..]
    {
      reveal Inv();
      if count == 0 {
        return false, Event(0, false);
      }
      e := buf[head];
      buf[head] := Event(0, false);
      head := Wrap(head as int + 1) as i32;            // Java: head = (head + 1) % buf.length
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

    method Clear()
      requires Valid()
      modifies Repr
      ensures Valid() && Repr == old(Repr)
      ensures elems == []
    {
      reveal Inv();
      var ok := true;
      while ok
        invariant Valid() && Repr == old(Repr)
        invariant !ok ==> elems == []
        decreases |elems| + (if ok then 1 else 0)
      {
        var e;
        ok, e := Poll();
      }
    }

    method Snapshot() returns (s: seq<Event>)
      requires Valid()
      ensures s == elems
    {
      reveal Inv();
      s := [];
      var i: i32 := 0;
      while i < count
        invariant 0 <= i <= count
        invariant s == elems[..i]
      {
        s := s + [buf[Wrap(head as int + i as int)]];
        i := i + 1;
      }
    }
  }
}
