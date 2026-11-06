// Shadow model of com.dxlab.homehub.dispatch.Dispatcher (admission and dispatch only).
//
// The proof of this module uses ONLY the contracts of RingQueue (modular verification):
// if a RingQueue method body changes but its contract does not, nothing here is re-verified.
//
// The approved back-pressure policy (SR-2017-11) is written as the contract of Submit:
//   R1  the number of pending events never exceeds Limit (the configured queue capacity)
//   R2  a critical event is never rejected
//   R3  events that stay in the queue keep their relative order; eviction removes the
//       oldest non-critical event
//   R4  a non-critical event is rejected only when the queue is full and autoDrain is off
// Submit's postconditions decide the result and the new state exactly, so two
// implementations that both satisfy them behave identically.
//
// Outside the model: handlers, metrics, audit log, the RuleEngine listener.


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
    ghost const Limit: int
    ghost var Dispatched: seq<Event>    // events handed to the handlers, in order
    var dispatchedCount: int         // Java: long dispatchedCount

    ghost predicate Valid()
      reads this, queue, queue.buf
    {
      queue.Valid() && queue.Capacity() == Limit && dispatchedCount == |Dispatched|
    }

    constructor (q: RingQueue, autoDrain: bool)
      requires q.Valid()
      ensures Valid() && queue == q && autoDrainOnFull == autoDrain
      ensures Limit == q.Capacity() && Dispatched == []
    {
      queue := q;
      autoDrainOnFull := autoDrain;
      Limit := q.Capacity();
      Dispatched := [];
      dispatchedCount := 0;
    }

    method Submit(e: Event) returns (r: SubmitResult)
      requires Valid()
      modifies this, queue, queue.buf
      ensures Valid() && queue.buf == old(queue.buf)
      // R1
      ensures |queue.elems| <= Limit
      // R2
      ensures e.critical ==> r != REJECTED_FULL
      // which result: decided by the old state only
      ensures r == ACCEPTED <==> |old(queue.elems)| < Limit
      ensures r == ACCEPTED_EVICTED <==>
        |old(queue.elems)| == Limit && e.critical && !AllCritical(old(queue.elems))
      ensures r == ACCEPTED_DRAINED <==>
        |old(queue.elems)| == Limit &&
        ((e.critical && AllCritical(old(queue.elems))) || (!e.critical && autoDrainOnFull))
      ensures r == REJECTED_FULL <==>
        |old(queue.elems)| == Limit && !e.critical && !autoDrainOnFull
      // R3 and the exact new state
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
      var res := queue.Offer(e);
      if res == OK {
        return ACCEPTED;
      }
      if e.critical {
        var found, victim := EvictOldestNonCritical();
        if found {
          res := queue.Offer(e);
          return ACCEPTED_EVICTED;
        }
        var ok, d := DispatchOne();
        res := queue.Offer(e);
        return ACCEPTED_DRAINED;
      }
      if autoDrainOnFull {
        var ok, d := DispatchOne();
        res := queue.Offer(e);
        return ACCEPTED_DRAINED;
      }
      return REJECTED_FULL;
    }

    // Java: rotate the whole queue once, dropping the first non-critical event.
    method EvictOldestNonCritical() returns (found: bool, victim: Event)
      requires Valid()
      modifies queue, queue.buf
      ensures Valid() && queue.buf == old(queue.buf)
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
        invariant Valid() && queue.buf == old(queue.buf)
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
      modifies this, queue, queue.buf
      ensures Valid() && queue.buf == old(queue.buf)
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
      modifies this, queue, queue.buf
      ensures Valid() && queue.buf == old(queue.buf)
      ensures queue.elems == [] && Dispatched == old(Dispatched) + old(queue.elems)
      ensures n as int == |old(queue.elems)|
    {
      n := 0;
      var ok := true;
      while ok
        invariant Valid() && queue.buf == old(queue.buf)
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
