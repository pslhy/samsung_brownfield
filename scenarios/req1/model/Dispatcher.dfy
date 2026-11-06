// REQ-1, patch B: the queue may grow physically, but the Dispatcher enforces the
// approved LOGICAL limit itself (Java: dispatch.maxPending, Watchdog uses the same value).
//
// The behavioral contract R1-R4 is copied unchanged from formal/Dispatcher.dfy.
// Only the frame (Repr instead of queue.buf) and Valid() differ.

module DispatcherModel {
  import opened Types
  import opened RingQueueModel

  datatype SubmitResult = ACCEPTED | ACCEPTED_EVICTED | ACCEPTED_DRAINED | REJECTED_FULL

  lemma TailOfConcat<T>(a: seq<T>, b: seq<T>)
    requires |a| > 0
    ensures (a + b)[1..] == a[1..] + b
  {
  }

  // Events kept after rotating the first i events of s, dropping index k (if k < i).
  ghost function KeptOf(s: seq<Event>, i: nat, k: nat): seq<Event>
    requires i <= |s|
  {
    if k < i then s[..k] + s[k + 1..i] else s[..i]
  }

  lemma KeptStep(s: seq<Event>, i: nat, k: nat)
    requires i < |s| && i != k
    ensures KeptOf(s, i + 1, k) == KeptOf(s, i, k) + [s[i]]
  {
    if k < i {
      assert s[k + 1..i + 1] == s[k + 1..i] + [s[i]];
    } else {
      assert s[..i + 1] == s[..i] + [s[i]];
    }
  }

  lemma KeptSkip(s: seq<Event>, k: nat)
    requires k < |s|
    ensures KeptOf(s, k + 1, k) == KeptOf(s, k, k)
  {
    assert s[k + 1..k + 1] == [];
  }

  class Dispatcher {
    const queue: RingQueue
    const autoDrainOnFull: bool
    const maxPending: i32
    ghost const Limit: int
    ghost var Dispatched: seq<Event>
    var dispatchedCount: int

    ghost predicate Valid()
      reads this, queue, queue.Repr
    {
      && queue.Valid()
      && this !in queue.Repr
      && Limit == maxPending as int
      && 0 < Limit <= queue.MaxCapacity()
      && |queue.elems| <= Limit
      && dispatchedCount == |Dispatched|
    }

    constructor (q: RingQueue, autoDrain: bool, maxPending: i32)
      requires q.Valid() && 0 < maxPending as int <= q.MaxCapacity() && |q.elems| <= maxPending as int
      ensures Valid() && queue == q && autoDrainOnFull == autoDrain
      ensures Limit == maxPending as int && Dispatched == []
    {
      queue := q;
      autoDrainOnFull := autoDrain;
      this.maxPending := maxPending;
      Limit := maxPending as int;
      Dispatched := [];
      dispatchedCount := 0;
    }

    method Submit(e: Event) returns (r: SubmitResult)
      requires Valid()
      modifies this, queue.Repr
      ensures Valid() && fresh(queue.Repr - old(queue.Repr))
      // ---- R1-R4: identical to formal/Dispatcher.dfy ----
      ensures |queue.elems| <= Limit
      ensures e.critical ==> r != REJECTED_FULL
      ensures r == ACCEPTED <==> |old(queue.elems)| < Limit
      ensures r == ACCEPTED_EVICTED <==>
        |old(queue.elems)| == Limit && e.critical && !AllCritical(old(queue.elems))
      ensures r == ACCEPTED_DRAINED <==>
        |old(queue.elems)| == Limit &&
        ((e.critical && AllCritical(old(queue.elems))) || (!e.critical && autoDrainOnFull))
      ensures r == REJECTED_FULL <==>
        |old(queue.elems)| == Limit && !e.critical && !autoDrainOnFull
      ensures r == ACCEPTED ==>
        queue.elems == old(queue.elems) + [e] && Dispatched == old(Dispatched)
      ensures r == ACCEPTED_EVICTED ==>
        queue.elems == Remove(old(queue.elems), IndexOfNonCritical(old(queue.elems))) + [e]
        && Dispatched == old(Dispatched)
      ensures r == ACCEPTED_DRAINED ==>
        queue.elems == old(queue.elems)[1..] + [e]
        && Dispatched == old(Dispatched) + [old(queue.elems)[0]]
      ensures r == REJECTED_FULL ==>
        queue.elems == old(queue.elems) && Dispatched == old(Dispatched)
    {
      var n := queue.Size();
      if n < maxPending {
        var res := queue.Offer(e);
        return ACCEPTED;
      }
      if e.critical {
        var found, victim := EvictOldestNonCritical();
        if found {
          var res := queue.Offer(e);
          return ACCEPTED_EVICTED;
        }
        var ok, d := DispatchOne();
        var res := queue.Offer(e);
        return ACCEPTED_DRAINED;
      }
      if autoDrainOnFull {
        var ok, d := DispatchOne();
        var res := queue.Offer(e);
        return ACCEPTED_DRAINED;
      }
      return REJECTED_FULL;
    }

    method EvictOldestNonCritical() returns (found: bool, victim: Event)
      requires Valid()
      modifies queue.Repr
      ensures Valid() && fresh(queue.Repr - old(queue.Repr))
      ensures found <==> !AllCritical(old(queue.elems))
      ensures found ==>
        var k := IndexOfNonCritical(old(queue.elems));
        k < |old(queue.elems)| && victim == old(queue.elems)[k]
        && queue.elems == Remove(old(queue.elems), k)
      ensures !found ==> queue.elems == old(queue.elems)
    {
      ghost var orig := queue.elems;
      ghost var k := IndexOfNonCritical(orig);
      ghost var kept: seq<Event> := [];
      var n := queue.Size();
      var i: i32 := 0;
      found := false;
      victim := Event(0, false);
      while i < n
        invariant Valid() && fresh(queue.Repr - old(queue.Repr))
        invariant 0 <= i <= n && n as int == |orig|
        invariant queue.elems == orig[i..] + kept
        invariant kept == KeptOf(orig, i as int, k)
        invariant found <==> k < i as int
        invariant found ==> victim == orig[k]
      {
        var ok, x := queue.Poll();
        TailOfConcat(orig[i..], kept);
        assert orig[i..][1..] == orig[i + 1..];
        assert x == orig[i] && queue.elems == orig[i + 1..] + kept;
        if !found && !x.critical {
          assert k == i as int;   // all earlier events are critical, this one is not
          KeptSkip(orig, k);
          found := true;
          victim := x;
        } else {
          KeptStep(orig, i as int, k);
          var r := queue.Offer(x);
          assert queue.elems == orig[i + 1..] + (kept + [x]);
          kept := kept + [x];
        }
        i := i + 1;
      }
      assert orig[n..] == [];
      assert found ==> KeptOf(orig, n as int, k) == Remove(orig, k);
      assert !found ==> KeptOf(orig, n as int, k) == orig;
    }

    method DispatchOne() returns (ok: bool, e: Event)
      requires Valid()
      modifies this, queue.Repr
      ensures Valid() && queue.Repr == old(queue.Repr)
      ensures |old(queue.elems)| == 0 ==>
        !ok && queue.elems == old(queue.elems) && Dispatched == old(Dispatched)
      ensures |old(queue.elems)| > 0 ==>
        ok && e == old(queue.elems)[0] && queue.elems == old(queue.elems)[1..]
        && Dispatched == old(Dispatched) + [e]
    {
      ok, e := queue.Poll();
      if ok {
        Dispatched := Dispatched + [e];
        dispatchedCount := dispatchedCount + 1;
      }
    }

    method Drain() returns (n: i32)
      requires Valid()
      modifies this, queue.Repr
      ensures Valid() && queue.Repr == old(queue.Repr)
      ensures queue.elems == [] && Dispatched == old(Dispatched) + old(queue.elems)
      ensures n as int == |old(queue.elems)|
    {
      n := 0;
      var ok := true;
      while ok
        invariant Valid() && queue.Repr == old(queue.Repr)
        invariant 0 <= n as int <= |old(queue.elems)|
        invariant queue.elems == old(queue.elems)[n..]
        invariant Dispatched == old(Dispatched) + old(queue.elems)[..n]
        invariant !ok ==> n as int == |old(queue.elems)|
        decreases |queue.elems| + (if ok then 1 else 0)
      {
        var e;
        ok, e := DispatchOne();
        if ok {
          n := n + 1;
        }
      }
    }
  }
}
