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
//   int n = e;  ... for (i = 0; i < n; i++) ...   ~>   ... for (i = 0; i < e; i++) ...
// Condition: the value of e does not change while the variable is used.
//
// The place where it breaks in HomeHub: Dispatcher.evictOldestNonCritical rotates the queue once,
// keeping every event except the oldest non-critical one (the victim):
//   int n = queue.size();
//   for (int i = 0; i < n; i++) { x = queue.poll(); if (no victim yet && !x.critical) victim = x; else queue.offer(x); }
// Inlining n turns the bound into queue.size(), which shrinks when the victim is taken out.
module InlineVariableRule {
  datatype Ev = Ev(id: int, critical: bool)
  datatype State = State(queue: seq<Ev>, victim: int)   // victim: id, or 0 for none

  // one iteration of the loop body (the queue is never empty inside the loop)
  function Step(s: State): State
    requires |s.queue| > 0
  {
    var x := s.queue[0];
    if s.victim == 0 && !x.critical then State(s.queue[1..], x.id)
    else State(s.queue[1..] + [x], s.victim)
  }

  // with the variable: the bound n is fixed when the loop starts
  function Fixed(s: State, i: nat, n: nat): State
    decreases n - i
  {
    if i >= n || |s.queue| == 0 then s else Fixed(Step(s), i + 1, n)
  }

  // inlined: the bound is re-read from the queue every time
  function Inlined(s: State, i: nat, fuel: nat): State
    decreases fuel
  {
    if fuel == 0 || i >= |s.queue| then s else Inlined(Step(s), i + 1, fuel - 1)
  }

  predicate AllCritical(q: seq<Ev>) { forall k :: 0 <= k < |q| ==> q[k].critical }

  lemma StepKeepsSize(s: State)
    requires |s.queue| > 0 && AllCritical(s.queue)
    ensures |Step(s).queue| == |s.queue| && AllCritical(Step(s).queue)
  {
  }

  lemma Loops(s: State, i: nat, n: nat, fuel: nat)
    requires AllCritical(s.queue) && |s.queue| == n && i <= n && fuel >= n - i
    ensures Fixed(s, i, n) == Inlined(s, i, fuel)
    decreases n - i
  {
    if i < n && |s.queue| > 0 {
      StepKeepsSize(s);
      Loops(Step(s), i + 1, n, fuel - 1);
    }
  }

  // Condition met: nothing is taken out of the queue inside the loop (here: every event is
  // critical, so there is no victim), so queue.size() stays n and the two loops are the same.
  lemma InlineVariable_Same(q: seq<Ev>)
    requires AllCritical(q)                    // condition: the loop does not change queue.size()
    ensures Fixed(State(q, 0), 0, |q|) == Inlined(State(q, 0), 0, |q|)
  {
    Loops(State(q, 0), 0, |q|, |q|);
  }

  // Without the condition: three non-critical events 1, 2, 3. With the variable, 1 is taken out and
  // 2, 3 keep their order. Inlined, the loop stops one round early and 3 jumps ahead of 2.
  lemma InlineVariable_Counterexample()
    ensures var q := [Ev(1, false), Ev(2, false), Ev(3, false)];
            Fixed(State(q, 0), 0, 3).queue == [Ev(2, false), Ev(3, false)] &&
            Inlined(State(q, 0), 0, 3).queue == [Ev(3, false), Ev(2, false)]
  {
  }
}
