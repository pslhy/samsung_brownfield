// Conditions of the three cleanup rules of lab E, stated and proved in Dafny.
//
// A rewrite rule  lhs ~> rhs  keeps the meaning iff the two sides behave the same in every state.
// When that holds only under an extra condition, the rule is CONDITIONAL: it may be applied only
// where the program meets the condition. Each rule below has
//   <Rule>_Same            the two sides behave the same; the condition is the `requires`
//   <Rule>_Counterexample  (conditional rules only) without the condition the two sides differ
//
// The Java behaviour is modeled only as far as each rule needs. A Java List is a seq.

// ---------------------------------------------------------------------------------------------
// Rule 1 (IsEmpty):  list.size() == 0  ~>  list.isEmpty()          no condition
module IsEmptyRule {
  lemma IsEmpty_Same<T>(list: seq<T>)
    ensures (|list| == 0) == (list == [])
  {
  }
}

// ---------------------------------------------------------------------------------------------
// Rule 2 (ForEach):
//   for (int i = 0; i < list.size(); i++) { body(list.get(i)); }   ~>   for (T x : list) { body(x); }
// Condition: the body does not change the list.
//
// The body is modeled as a function from (element, current list) to the list after the body.
// We compare the elements the two loops visit, in order.
module ForEachRule {
  // index loop: re-reads list.size() and list.get(i) on the CURRENT list after each body
  function IndexVisits(list: seq<int>, body: (int, seq<int>) -> seq<int>, i: nat, fuel: nat): seq<int>
    decreases fuel
  {
    if fuel == 0 || i >= |list| then []
    else [list[i]] + IndexVisits(body(list[i], list), body, i + 1, fuel - 1)
  }

  // for-each: visits the elements of the list as it was when the loop started
  function EachVisits(list: seq<int>): seq<int> { list }

  lemma Visits(list: seq<int>, body: (int, seq<int>) -> seq<int>, i: nat, fuel: nat)
    requires forall x, l :: body(x, l) == l                    // condition
    requires i <= |list| && fuel >= |list| - i
    ensures IndexVisits(list, body, i, fuel) == list[i..]
    decreases |list| - i
  {
    if i < |list| {
      Visits(list, body, i + 1, fuel - 1);
    }
  }

  lemma ForEach_Same(list: seq<int>, body: (int, seq<int>) -> seq<int>)
    requires forall x, l :: body(x, l) == l                    // condition: body does not change the list
    ensures IndexVisits(list, body, 0, |list|) == EachVisits(list)
  {
    Visits(list, body, 0, |list|);
  }

  // Without the condition: a body that removes the first element. [1, 2, 3]: the index loop
  // visits 1 and 3 and skips 2.
  lemma ForEach_Counterexample()
    ensures var removeFirst := (x: int, l: seq<int>) => if |l| > 0 then l[1..] else l;
            IndexVisits([1, 2, 3], removeFirst, 0, 3) == [1, 3] && EachVisits([1, 2, 3]) == [1, 2, 3]
  {
  }
}

// ---------------------------------------------------------------------------------------------
// Rule 3 (InlineVariable):
//   int n = e;  for (int i = 0; i < n; i++) { body }   ~>   for (int i = 0; i < e; i++) { body }
// Condition: the body does not change the value of e.
//
// The state can be anything (type S). The expression e is a function `size` of the state, and the
// loop body a function from state to state. We compare the states the two loops end in.
module InlineVariableRule {
  // with the variable: n is computed once, before the loop
  function Fixed<S>(s: S, body: S -> S, i: nat, n: nat): S
    decreases n - i
  {
    if i >= n then s else Fixed(body(s), body, i + 1, n)
  }

  // inlined: e (here size(s)) is computed again before every round, on the current state
  function Inlined<S>(s: S, size: S -> nat, body: S -> S, i: nat, fuel: nat): S
    decreases fuel
  {
    if fuel == 0 || i >= size(s) then s else Inlined(body(s), size, body, i + 1, fuel - 1)
  }

  lemma Loops<S>(s: S, size: S -> nat, body: S -> S, i: nat, n: nat, fuel: nat)
    requires forall t :: size(body(t)) == size(t)
    requires size(s) == n && i <= n && fuel >= n - i
    ensures Fixed(s, body, i, n) == Inlined(s, size, body, i, fuel)
    decreases n - i
  {
    if i < n {
      Loops(body(s), size, body, i + 1, n, fuel - 1);
    }
  }

  lemma InlineVariable_Same<S>(s: S, size: S -> nat, body: S -> S)
    requires forall t :: size(body(t)) == size(t)        // condition: the body does not change e
    ensures Fixed(s, body, 0, size(s)) == Inlined(s, size, body, 0, size(s))
  {
    Loops(s, size, body, 0, size(s), size(s));
  }

  // Without the condition: the state is a list, e is its length, and the body takes out the first
  // element. [1, 2, 3]: with the variable the loop runs 3 times and ends at []; inlined, it stops
  // after 2 rounds at [3] (the loop ends one round early, as in lab E-2).
  lemma InlineVariable_Counterexample()
    ensures var size := (l: seq<int>) => |l|;
            var removeFirst := (l: seq<int>) => if |l| > 0 then l[1..] else l;
            Fixed([1, 2, 3], removeFirst, 0, 3) == [] &&
            Inlined([1, 2, 3], size, removeFirst, 0, 3) == [3]
  {
  }
}
