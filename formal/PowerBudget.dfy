// Shadow model of com.dxlab.homehub.power.PowerBudget.
//
// Java keeps a HashMap<String,Integer> (device -> watts). The model keeps a sequence of
// grants with distinct ids: a data refinement. Device ids are abstracted to integers.
//
// Safety contract (circuit breaker): Load(running) <= cap at all times.
// Load is a spec-only function: it has no Java counterpart (Java's totalLoad() is a method
// that *computes* it). Changing Load's definition changes the meaning of every contract
// that mentions it - see scenarios/req3.
//
// Modeling finding: Java computes `totalLoad() + watts > capWatts` in 32-bit int.
// The model only verifies with cap < 2^30 (no overflow). Java never checks this.


module PowerBudgetModel {
  import opened Types

  datatype Grant = Grant(id: i32, watts: i32)

  function Sum(s: seq<Grant>): int {
    if |s| == 0 then 0 else s[0].watts as int + Sum(s[1..])
  }

  function Load(s: seq<Grant>): int {
    Sum(s)
  }

  predicate Distinct(s: seq<Grant>) {
    forall i, j :: 0 <= i < j < |s| ==> s[i].id != s[j].id
  }

  predicate Holds(s: seq<Grant>, id: i32) {
    exists g <- s :: g.id == id
  }

  lemma SumAppend(a: seq<Grant>, b: seq<Grant>)
    ensures Sum(a + b) == Sum(a) + Sum(b)
  {
    if |a| == 0 {
      assert a + b == b;
    } else {
      assert (a + b)[1..] == a[1..] + b;
      SumAppend(a[1..], b);
    }
  }

  lemma SumNonNeg(s: seq<Grant>)
    requires forall g <- s :: g.watts > 0
    ensures Sum(s) >= 0
  {
  }

  lemma SumPrefix(s: seq<Grant>, i: nat)
    requires i < |s|
    ensures Sum(s[..i + 1]) == Sum(s[..i]) + s[i].watts as int
  {
    assert s[..i + 1] == s[..i] + [s[i]];
    SumAppend(s[..i], [s[i]]);
  }

  lemma SumPrefixBound(s: seq<Grant>, i: nat)
    requires i <= |s|
    requires forall g <- s :: g.watts > 0
    ensures Sum(s[..i]) <= Sum(s)
  {
    assert s == s[..i] + s[i..];
    SumAppend(s[..i], s[i..]);
    SumNonNeg(s[i..]);
  }

  lemma SumRemove(s: seq<Grant>, k: nat)
    requires k < |s|
    ensures Sum(Remove(s, k)) == Sum(s) - s[k].watts as int
    decreases k
  {
    if k == 0 {
      assert Remove(s, 0) == s[1..];
    } else {
      var r := Remove(s, k);
      assert r[0] == s[0];
      assert r[1..] == Remove(s[1..], k - 1);
      SumRemove(s[1..], k - 1);
    }
  }

  lemma RemoveAt(s: seq<Grant>, k: nat, i: nat)
    requires k < |s| && i < |s| - 1
    ensures Remove(s, k)[i] == s[if i < k then i else i + 1]
  {
  }

  lemma RemoveDistinct(s: seq<Grant>, k: nat)
    requires k < |s| && Distinct(s)
    ensures Distinct(Remove(s, k))
    ensures !Holds(Remove(s, k), s[k].id)
  {
    var r := Remove(s, k);
    forall i, j | 0 <= i < j < |r|
      ensures r[i].id != r[j].id
    {
      RemoveAt(s, k, i);
      RemoveAt(s, k, j);
    }
    forall g | g in r
      ensures g.id != s[k].id
    {
      var i :| 0 <= i < |r| && r[i] == g;
      RemoveAt(s, k, i);
    }
  }

  lemma RemoveSubset(s: seq<Grant>, k: nat)
    requires k < |s|
    ensures forall g <- Remove(s, k) :: g in s
  {
    var r := Remove(s, k);
    forall g | g in r
      ensures g in s
    {
      var i :| 0 <= i < |r| && r[i] == g;
      RemoveAt(s, k, i);
    }
  }

  lemma RemoveKeepsValid(s: seq<Grant>, k: nat, cap: i32)
    requires k < |s| && Distinct(s)
    requires forall g <- s :: 0 < g.watts as int <= cap as int
    requires Sum(s) <= cap as int
    ensures Distinct(Remove(s, k))
    ensures forall g <- Remove(s, k) :: 0 < g.watts as int <= cap as int
    ensures Sum(Remove(s, k)) <= cap as int
    ensures !Holds(Remove(s, k), s[k].id)
  {
    RemoveDistinct(s, k);
    RemoveSubset(s, k);
    SumRemove(s, k);
  }

  class PowerBudget {
    const cap: i32
    var running: seq<Grant>

    ghost predicate Valid()
      reads this
    {
      && 0 < cap as int < 0x4000_0000
      && Distinct(running)
      && (forall g <- running :: 0 < g.watts as int <= cap as int)
      && Load(running) <= cap as int
    }

    constructor (capWatts: i32)
      requires 0 < capWatts as int < 0x4000_0000
      ensures Valid() && cap == capWatts && running == []
    {
      cap := capWatts;
      running := [];
    }

    method TryStart(id: i32, watts: i32) returns (ok: bool)
      requires Valid()
      modifies this
      ensures Valid()
      ensures ok <==> 0 < watts <= cap && (Holds(old(running), id) || Load(old(running)) + watts as int <= cap as int)
      ensures ok && !Holds(old(running), id) ==> running == old(running) + [Grant(id, watts)]
      ensures !ok || Holds(old(running), id) ==> running == old(running)
    {
      if watts <= 0 || watts > cap {
        return false;
      }
      var held := IsRunning(id);
      if held {
        return true;
      }
      var total := TotalLoad();
      if total + watts > cap {
        return false;
      }
      SumAppend(running, [Grant(id, watts)]);
      running := running + [Grant(id, watts)];
      return true;
    }

    method Stop(id: i32)
      requires Valid()
      modifies this
      ensures Valid()
      ensures !Holds(running, id)
      ensures !Holds(old(running), id) ==> running == old(running)
      ensures Holds(old(running), id) ==>
        exists k :: 0 <= k < |old(running)| && old(running)[k].id == id && running == Remove(old(running), k)
    {
      var i := 0;
      while i < |running|
        invariant 0 <= i <= |running|
        invariant forall j :: 0 <= j < i ==> running[j].id != id
      {
        if running[i].id == id {
          RemoveKeepsValid(running, i, cap);
          running := Remove(running, i);
          return;
        }
        i := i + 1;
      }
    }

    method TotalLoad() returns (n: i32)
      requires Valid()
      ensures n as int == Load(running)
    {
      n := 0;
      var i := 0;
      while i < |running|
        invariant 0 <= i <= |running|
        invariant n as int == Sum(running[..i])
      {
        SumPrefix(running, i);
        SumPrefixBound(running, i + 1);
        n := n + running[i].watts;
        i := i + 1;
      }
      assert running[..|running|] == running;
    }

    method Headroom() returns (h: i32)
      requires Valid()
      ensures h as int == cap as int - Load(running)
    {
      var t := TotalLoad();
      SumNonNeg(running);
      h := cap - t;
    }

    method IsRunning(id: i32) returns (b: bool)
      requires Valid()
      ensures b == Holds(running, id)
    {
      var i := 0;
      while i < |running|
        invariant 0 <= i <= |running|
        invariant forall j :: 0 <= j < i ==> running[j].id != id
      {
        if running[i].id == id {
          return true;
        }
        i := i + 1;
      }
      return false;
    }

    method IsIdle() returns (b: bool)
      requires Valid()
      ensures b == (|running| == 0)
    {
      return |running| == 0;
    }

    method StopAll()
      requires Valid()
      modifies this
      ensures Valid() && running == []
    {
      running := [];
    }
  }
}
