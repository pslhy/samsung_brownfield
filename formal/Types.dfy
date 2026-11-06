// Shared types for the HomeHub shadow model.
// The model abstracts a Java Event to (id, critical): that is all the queue and the
// dispatcher's admission policy can observe.

module Types {
  newtype i32 = x: int | -0x8000_0000 <= x < 0x8000_0000

  datatype Event = Event(id: i32, critical: bool)

  datatype OfferResult = OK | FULL

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

  // Java's % for an index that is at most one lap past the end of the array.
  lemma ModWrap(k: int, n: int)
    requires 0 < n && 0 <= k < 2 * n
    ensures k % n == if k < n then k else k - n
  {
    if k < n {
      assert k == 0 * n + k;
    } else {
      assert k == 1 * n + (k - n);
    }
  }

  function Remove<T>(s: seq<T>, k: nat): seq<T>
    requires k < |s|
  {
    s[..k] + s[k + 1..]
  }
}
