# Complexity

A practical cost model. The goal here is not formal analysis but the two judgements
that actually decide an interview: *what complexity does this constraint demand*, and
*what does this line of Java really cost*.

---

## Reading the constraints

The constraint block at the bottom of a problem statement is a hint about the intended
solution, not decoration. Judges accept roughly 10⁸ simple operations per second, which
gives this mapping:

| Constraint on n | Affordable complexity | What that usually means |
| :-------------- | :-------------------- | :---------------------- |
| n ≤ 10 | O(n!) | Permutations, brute-force search over all orderings |
| n ≤ 20 | O(2ⁿ) | Subset enumeration, bitmask DP |
| n ≤ 100 | O(n⁴) | Four nested loops, interval DP on small ranges |
| n ≤ 500 | O(n³) | Floyd–Warshall, interval DP |
| n ≤ 5 000 | O(n²) | Two-sequence DP, pairwise comparison |
| n ≤ 10⁵ | O(n log n) | Sorting, heap, binary search per element |
| n ≤ 10⁶ | O(n) | Single pass, sliding window, prefix sums |
| n ≤ 10⁹ | O(log n) | Binary search on the answer, closed-form math |
| n up to 10¹⁸ | O(1) or O(log n) | Math, fast exponentiation — n cannot even be iterated |

Read it in reverse to derive the approach: `n ≤ 10⁵` rules out O(n²) and points at
sorting, a heap, or a linear pass with auxiliary structure. A suspiciously small bound
like `n ≤ 20` is an invitation to enumerate subsets.

Also read the *value* bounds, not just the size bounds. `1 ≤ nums[i] ≤ 10⁹` with
`n ≤ 10⁵` means sums reach 10¹⁴ and must be held in a `long`.

---

## Growth at a glance

| n | log n | n log n | n² | 2ⁿ |
| ---: | ---: | ---: | ---: | ---: |
| 10 | 3 | 33 | 100 | 1 024 |
| 100 | 7 | 664 | 10 000 | 10³⁰ |
| 1 000 | 10 | 9 966 | 10⁶ | — |
| 10⁵ | 17 | 1.7 × 10⁶ | 10¹⁰ | — |
| 10⁶ | 20 | 2.0 × 10⁷ | 10¹² | — |

The practical lesson is the n² column: at n = 10⁵ a quadratic solution needs 10¹⁰
operations, which is minutes, not milliseconds. The gap between n log n and n² is where
most "time limit exceeded" verdicts live.

---

## Java data structures

Costs for the implementations you actually get from `java.util`.

| Structure | Access | Search | Insert | Delete | Notes |
| :-------- | :----- | :----- | :----- | :----- | :---- |
| `int[]` | O(1) | O(n) | — | — | Fixed size; cheapest thing available |
| `ArrayList` | O(1) | O(n) | O(1)* | O(n) | *Amortized at the tail; `add(0, x)` is O(n) |
| `LinkedList` | O(n) | O(n) | O(1) | O(1) | Only worth it as a `Deque` |
| `ArrayDeque` | — | — | O(1)* | O(1)* | Preferred stack **and** queue in Java |
| `HashMap` / `HashSet` | — | O(1)* | O(1)* | O(1)* | *Average; O(log n) worst case since Java 8 |
| `TreeMap` / `TreeSet` | — | O(log n) | O(log n) | O(log n) | Sorted; gives `floorKey`, `ceilingKey`, `subMap` |
| `PriorityQueue` | O(1) peek | O(n) | O(log n) | O(log n) | Min-heap by default; `remove(Object)` is O(n) |
| `StringBuilder` | O(1) | — | O(1)* | — | Always use instead of `+=` in a loop |

Two specific traps:

- **`Stack` and `Vector` are synchronized legacy classes.** Use `ArrayDeque` for both
  stack and queue duties. `LinkedList` as a queue works but allocates a node per element.
- **`PriorityQueue.remove(Object)` is a linear scan.** A heap supports cheap removal of
  the *root* only. Arbitrary removal usually calls for lazy deletion — pop stale entries
  when they surface — or a `TreeSet`.

---

## Sorting

| Input | Algorithm Java uses | Cost | Stable |
| :---- | :------------------ | :--- | :----- |
| `int[]`, `long[]`, … | Dual-pivot quicksort | O(n log n) average, O(n²) adversarial | No |
| `Integer[]`, `List<T>` | TimSort | O(n log n) worst case | Yes |

Sorting a primitive array with a hand-crafted adversarial input can hit the quadratic
case. It is not a realistic risk on LeetCode, but boxing to `Integer[]` — which routes
to the guaranteed-O(n log n) merge sort — is the standard mitigation where it matters.

Boxing is not free: `Integer[]` costs roughly 4× the memory of `int[]` and adds an
indirection to every comparison. Sort primitives as primitives unless a custom
comparator forces otherwise.

---

## Amortized versus worst case

Three results worth being able to state precisely, because interviewers ask:

**Dynamic array growth.** `ArrayList` doubles its capacity when full. A single `add`
can cost O(n) for the copy, but n appends cost O(n) in total, because the copies form a
geometric series: n + n/2 + n/4 + … < 2n. Hence O(1) amortized.

**Union-find.** Path compression plus union by rank gives O(α(n)) amortized per
operation, where α is the inverse Ackermann function — below 5 for any n that fits in
memory. Treat it as constant but do not call it constant in an interview.

**Monotonic stack and sliding window.** Both contain a loop nested inside a loop and
both are O(n). The argument is the same in each case: every element is pushed at most
once and popped at most once, so the total work across all iterations of the inner loop
is bounded by n — not by n per outer iteration.

This last argument is the one candidates most often fail to make, and it is the
difference between correctly calling a solution linear and wrongly calling it quadratic.

---

## Space

Count everything that scales with the input:

- **The output does not count**, by convention, when the problem requires it. Returning
  all subsets is O(2ⁿ) output but may still be described as O(n) auxiliary space.
- **Recursion costs stack frames.** Depth-n recursion is O(n) space, which is why an
  "O(1) space" requirement rules out the recursive form. Java has no tail-call
  elimination, so a deep recursion on n = 10⁵ will overflow the stack — convert to an
  explicit `ArrayDeque`.
- **Sorting is not free.** TimSort on objects uses O(n) auxiliary space; the primitive
  quicksort uses O(log n) for its own recursion.
- **Row-rolling.** Most 2D DP tables only read the previous row, so O(n·m) collapses to
  O(min(n, m)). Doing this is often the difference between passing and exceeding the
  memory limit on large grids.

---

## Java-specific costs that surprise people

| Expression | Real cost | Use instead |
| :--------- | :-------- | :---------- |
| `s += c` inside a loop | O(n²) — strings are immutable, each concat copies | `StringBuilder.append` |
| `s.substring(i, j)` | O(j − i); copies since Java 7 | Index arithmetic, or compare in place |
| `list.remove(0)` | O(n) shift | `ArrayDeque.poll()` |
| `map.get(k)` then `map.put(k, …)` | Two hashes of the same key | `merge`, `compute`, or `getOrDefault` once |
| `new int[n][m]` | Zero-filled, O(n·m) | Fine — but do not allocate it inside a loop |
| Autoboxing in a hot loop | Allocation per operation | Primitive arrays where the key range is small |

A `HashMap<Character, Integer>` over lowercase letters is almost always better written
as `int[26]`: no hashing, no boxing, no allocation, and the indexing is `c - 'a'`.

---

## Stating complexity well

When reporting complexity in a note or an interview, say three things:

1. **What n is.** "n is the number of nodes" or "n is the string length, k the alphabet
   size". Ambiguous variables make the rest meaningless.
2. **Time and space, separately.** An O(n) time solution that uses O(n) space loses to
   an O(n) time, O(1) space one, and the distinction is the follow-up question.
3. **Why, in one clause.** "O(n) because each index enters and leaves the window once."
   The justification is what is actually being assessed.
