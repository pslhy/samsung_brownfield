// Dispatcher (admission only) on top of the example queue model RingEventQueue.dfy, for lab B-2.
// Same contract as formal/Dispatcher.dfy, written with the names of the example queue
// (elems, Event, buf.Length), so it can be read right after RingEventQueue.dfy.
//
// The proof uses ONLY the contracts of RingEventQueue (Offer, Poll), not its code.
//
// The approved back-pressure policy (SR-2017-11) is written as the contract of Submit:
//   R1  the number of pending events never exceeds the queue's capacity (buf.Length)
//   R2  a critical event is never rejected
//   R3  events that stay in the queue keep their relative order; eviction removes the
//       oldest non-critical event
//   R4  a non-critical event is rejected only when the queue is full and autoDrain is off
//
// Outside the model: null events, handlers, metrics, audit log.

include "RingEventQueue.dfy"

module DispatcherModel {
  import opened RingEventQueueModel

  datatype SubmitResult = ACCEPTED | ACCEPTED_EVICTED | ACCEPTED_DRAINED | REJECTED_FULL

  // Index of the oldest non-critical event, or |s| if every event is critical.
  function IndexOfNonCritical(s: seq<Event>): (k: nat)
    ensures k <= |s|
    ensures forall j :: 0 <= j < k ==> s[j].critical
    ensures k < |s| ==> !s[k].critical
  {
    if |s| == 0 then 0
    else if !s[0].critical then 0
    else 1 + IndexOfNonCritical(s[1..])
  }

  predicate AllCritical(s: seq<Event>) {
    forall x <- s :: x.critical
  }

  // s without its k-th element
  function Remove(s: seq<Event>, k: nat): seq<Event>
    requires k < |s|
  {
    s[..k] + s[k + 1..]
  }

  lemma TailOfConcat(a: seq<Event>, b: seq<Event>)
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
    const queue: RingEventQueue
    const autoDrainOnFull: bool
    ghost var Dispatched: seq<Event>    // events handed to the handlers, in order

    ghost predicate Valid()
      reads this, queue, queue.buf
    {
      queue.Valid()
    }

    constructor (q: RingEventQueue, autoDrain: bool)
      requires q.Valid()
      ensures Valid() && queue == q && autoDrainOnFull == autoDrain && Dispatched == []
    {
      queue := q;
      autoDrainOnFull := autoDrain;
      Dispatched := [];
    }

    method Submit(e: Event) returns (r: SubmitResult)
      requires Valid()
      modifies this, queue, queue.buf
      ensures Valid() && queue.buf == old(queue.buf)
      // R1
      ensures |queue.elems| <= queue.buf.Length
      // R2
      ensures e.critical ==> r != REJECTED_FULL
      // which result: decided by the old state only
      ensures r == ACCEPTED <==> |old(queue.elems)| < queue.buf.Length
      ensures r == ACCEPTED_EVICTED <==>
        |old(queue.elems)| == queue.buf.Length && e.critical && !AllCritical(old(queue.elems))
      ensures r == ACCEPTED_DRAINED <==>
        |old(queue.elems)| == queue.buf.Length &&
        ((e.critical && AllCritical(old(queue.elems))) || (!e.critical && autoDrainOnFull))
      ensures r == REJECTED_FULL <==>
        |old(queue.elems)| == queue.buf.Length && !e.critical && !autoDrainOnFull
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
      var n := queue.count;
      var i := 0;
      found := false;
      victim := Event(0, false);
      while i < n
        invariant Valid() && queue.buf == old(queue.buf)
        invariant 0 <= i <= n && n == |orig|
        invariant queue.elems == orig[i..] + kept
        invariant kept == KeptOf(orig, i, k)
        invariant found <==> k < i
        invariant found ==> victim == orig[k]
      {
        var x, ok := queue.Poll();
        TailOfConcat(orig[i..], kept);
        assert orig[i..][1..] == orig[i + 1..];
        assert x == orig[i] && queue.elems == orig[i + 1..] + kept;
        if !found && !x.critical {
          assert k == i;   // all earlier events are critical, this one is not
          KeptSkip(orig, k);
          found := true;
          victim := x;
        } else {
          KeptStep(orig, i, k);
          var r := queue.Offer(x);
          assert queue.elems == orig[i + 1..] + (kept + [x]);
          kept := kept + [x];
        }
        i := i + 1;
      }
      assert orig[n..] == [];
      assert found ==> KeptOf(orig, n, k) == Remove(orig, k);
      assert !found ==> KeptOf(orig, n, k) == orig;
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
      e, ok := queue.Poll();
      if ok {
        Dispatched := Dispatched + [e];
      }
    }
  }
}
