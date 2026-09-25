# Patterns

Most interview problems are a small number of shapes wearing different costumes.
This document is the recognition table: given the signal in the problem statement,
which shape is it, what does the shape cost, and what does it look like in code.

The implementations live in [TEMPLATES.md](TEMPLATES.md); this document is about
knowing *which* template to reach for.

---

## Recognition table

| Signal in the statement | Pattern | Typical cost |
| :---------------------- | :------ | :----------- |
| Sorted array, find a pair/triplet summing to a target | [Two pointers](#two-pointers) | O(n) after O(n log n) sort |
| "Contiguous subarray/substring" with a constraint | [Sliding window](#sliding-window) | O(n) |
| Linked list, cycle, or "middle node" without extra space | [Fast and slow pointers](#fast-and-slow-pointers) | O(n) time, O(1) space |
| Sorted input, or "minimize the maximum" / "maximum feasible" | [Binary search](#binary-search) | O(log n) or O(n log range) |
| Shortest path in an unweighted graph or grid | [BFS](#breadth-first-search) | O(V + E) |
| Enumerate all subsets, permutations, or valid configurations | [Backtracking](#backtracking) | O(2ⁿ) or O(n!) |
| Dependencies, prerequisites, "valid ordering" | [Topological sort](#topological-sort) | O(V + E) |
| Dynamic connectivity, "are these in the same group" | [Union-find](#union-find) | ~O(α(n)) per operation |
| "k largest", "k closest", a running median | [Heap](#heap) | O(n log k) |
| Overlapping ranges, merging, or scheduling | [Intervals](#intervals) | O(n log n) |
| Range sums queried repeatedly | [Prefix sums](#prefix-sums) | O(n) build, O(1) query |
| "Next greater/smaller element", histogram spans | [Monotonic stack](#monotonic-stack) | O(n) |
| Prefix matching over many strings | [Trie](#trie) | O(L) per operation |
| Count the ways / optimal value with overlapping subproblems | [Dynamic programming](#dynamic-programming) | Usually O(n·k) |
| A locally optimal choice is provably globally optimal | [Greedy](#greedy) | O(n log n) |
| Fixed-width integers, "without extra space", XOR tricks | [Bit manipulation](#bit-manipulation) | O(n) |

---

## Two pointers

**Signal.** The input is sorted (or can be), and you are looking for a pair or
triplet satisfying a numeric relation.

**Mechanism.** Place one index at each end. The sortedness means each comparison
eliminates an entire row or column of the implicit n² search space: if the sum is
too small, no pair using the current left element can work, so advance left.

**Cost.** O(n) after sorting. O(1) extra space.

**Watch for.** Duplicate handling when the problem wants distinct tuples — skip
equal neighbours *after* recording a hit, not before. For 3-sum, the outer loop
fixes one element and the inner loop is a plain two-pointer scan, giving O(n²).

**Representative:** 1 Two Sum (sorted variant) · 15 3Sum · 11 Container With Most Water · 42 Trapping Rain Water

---

## Sliding window

**Signal.** "Longest", "shortest", or "count of" a **contiguous** subarray or
substring subject to a constraint.

**Mechanism.** Expand the right edge unconditionally; shrink the left edge while
the window is invalid. Every index enters and leaves the window at most once, which
is why a doubly nested loop still runs in linear time.

**Cost.** O(n) time. Space is whatever the window state needs — typically O(k) for
an alphabet of size k.

**Watch for.** The distinction between *shrink while invalid* (longest-valid
problems) and *shrink while valid* (shortest-valid problems). Fixed-size windows
are simpler still: add the entering element, remove the leaving one, no inner loop.
Counting problems with an "at most k" structure are usually
`exactly(k) = atMost(k) - atMost(k-1)`.

**Representative:** 3 Longest Substring Without Repeating Characters · 76 Minimum Window Substring · 209 Minimum Size Subarray Sum · 424 Longest Repeating Character Replacement

---

## Fast and slow pointers

**Signal.** A linked list, plus a question about cycles, the middle, or the k-th
node from the end — with an O(1) space requirement.

**Mechanism.** Two pointers moving at different rates. If a cycle exists they must
eventually meet inside it; restarting one pointer at the head and advancing both by
one then meets at the cycle entrance (Floyd's algorithm).

**Cost.** O(n) time, O(1) space.

**Watch for.** Null checks on `fast` *and* `fast.next` before each double advance.
Whether "middle" means the first or second of two middles changes the loop condition.

**Representative:** 141 Linked List Cycle · 142 Linked List Cycle II · 876 Middle of the Linked List · 287 Find the Duplicate Number

---

## Binary search

**Signal.** Two distinct cases, and the second is the one people miss.

1. *Search a sorted array.* Obvious.
2. *Search the answer space.* The statement says "minimize the maximum", "maximum
   value such that…", or gives a huge numeric range with a cheap feasibility check.
   If `feasible(x)` is monotonic — once true, true for everything larger — you can
   binary search over `x` itself, even though nothing in the input is sorted.

**Mechanism.** Maintain a half-open range and an invariant that the answer is inside
it. Prefer `lo < hi` with `mid = lo + (hi - lo) / 2`, moving `hi = mid` or
`lo = mid + 1`, which terminates without a separate equality case.

**Cost.** O(log n), or O(n · log(range)) when each feasibility check is a linear scan.

**Watch for.** Overflow in `(lo + hi) / 2`. Infinite loops from the wrong midpoint
rounding when the update is `lo = mid`. Boundary problems are far easier to get right
as `lowerBound` / `upperBound` helpers than as bespoke loops.

**Representative:** 704 Binary Search · 33 Search in Rotated Sorted Array · 153 Find Minimum in Rotated Sorted Array · 875 Koko Eating Bananas · 410 Split Array Largest Sum

---

## Breadth-first search

**Signal.** Shortest path, minimum number of steps, or level-by-level processing —
in a graph or grid where **every edge costs the same**.

**Mechanism.** A queue processes nodes in non-decreasing distance order, so the first
time a node is dequeued its distance is final. Mark nodes visited *when enqueued*,
not when dequeued, or the queue fills with duplicates.

**Cost.** O(V + E). Space O(V) for the frontier.

**Watch for.** Level-order problems need the size snapshot: capture `queue.size()`
before draining a level. Multi-source BFS — seeding the queue with every source at
distance 0 — solves "nearest X for every cell" in one pass. If edge weights differ,
this is Dijkstra, not BFS; if weights are only 0 and 1, use a deque.

**Representative:** 102 Binary Tree Level Order Traversal · 200 Number of Islands · 994 Rotting Oranges · 127 Word Ladder

---

## Backtracking

**Signal.** "Return all …" — every subset, permutation, combination, or valid board.
The output is exponential, so the algorithm is allowed to be.

**Mechanism.** Choose, recurse, un-choose. The un-choose step is what makes a single
mutable buffer sufficient instead of copying state at every node.

**Cost.** O(2ⁿ) for subsets, O(n!) for permutations, times O(n) to materialize each
result. Space O(n) for the recursion stack.

**Watch for.** Pruning is the whole game on constrained variants — sort first, then
break out of the loop as soon as the remaining budget cannot work. Duplicate inputs
need the `i > start && nums[i] == nums[i-1]` skip to avoid emitting the same
combination twice. Copy the buffer when recording a result; recording the buffer
itself records a reference that later mutations will corrupt.

**Representative:** 78 Subsets · 46 Permutations · 39 Combination Sum · 51 N-Queens

---

## Topological sort

**Signal.** Prerequisites, build order, course scheduling, "is this ordering possible".
The structure is a directed graph and the question is about a linear order consistent
with the edges.

**Mechanism.** Kahn's algorithm: repeatedly emit any node with in-degree zero and
decrement its neighbours. If fewer than V nodes are emitted, a cycle exists — which
makes this a cycle detector as well as a sorter.

**Cost.** O(V + E).

**Watch for.** Getting the edge direction backwards is the most common bug: "a
requires b" means the edge runs `b → a`. Lexicographically smallest orderings need a
priority queue in place of the plain queue.

**Representative:** 207 Course Schedule · 210 Course Schedule II · 269 Alien Dictionary

---

## Union-find

**Signal.** Connectivity questions under incremental merging — "how many groups",
"are these two connected", "does adding this edge create a cycle".

**Mechanism.** A forest where each set is a tree. Path compression flattens trees
during lookup, union by rank or size keeps them shallow; together they give
effectively constant amortized cost.

**Cost.** ~O(α(n)) per operation, α being the inverse Ackermann function — under 5
for any input that fits in memory.

**Watch for.** Both optimizations are needed; either alone leaves a logarithmic
factor. Union-find cannot un-merge, so problems that remove edges are usually solved
by processing the operations in reverse.

**Representative:** 547 Number of Provinces · 684 Redundant Connection · 721 Accounts Merge · 305 Number of Islands II

---

## Heap

**Signal.** "k largest/smallest/closest", a stream where the answer must stay current,
or a running median.

**Mechanism.** For *k largest*, keep a **min**-heap of size k and evict the root when
it overflows — the inverted comparator is the part that trips people up. Running
medians use two heaps: a max-heap of the lower half and a min-heap of the upper half,
rebalanced so their sizes differ by at most one.

**Cost.** O(n log k) for top-k, versus O(n log n) for sorting — the win grows as k
shrinks. Quickselect gives O(n) average if only the k-th element is needed.

**Watch for.** `PriorityQueue` in Java is a min-heap by default. Merging k sorted
lists is a heap over list heads, not a pairwise merge.

**Representative:** 215 Kth Largest Element · 347 Top K Frequent Elements · 23 Merge k Sorted Lists · 295 Find Median from Data Stream

---

## Intervals

**Signal.** Ranges with a start and end — merging, inserting, counting overlaps,
scheduling meetings.

**Mechanism.** Sort by start, then sweep, extending the current interval while the
next one overlaps. Room-count problems are better served by a sweep line: sort start
and end events independently and track the running count of open intervals.

**Cost.** O(n log n), dominated by the sort.

**Watch for.** Whether touching endpoints count as overlapping — `[1,2]` and `[2,3]`
are a merge in some problems and not in others. Read the statement, do not assume.

**Representative:** 56 Merge Intervals · 57 Insert Interval · 253 Meeting Rooms II · 435 Non-overlapping Intervals

---

## Prefix sums

**Signal.** Repeated range-sum queries, or counting subarrays whose sum hits a target.

**Mechanism.** `prefix[i]` is the sum of the first `i` elements, so any range sum is a
single subtraction. The counting variant pairs this with a hash map: a subarray summing
to `k` ending at `i` exists for every earlier prefix equal to `prefix[i] - k`.

**Cost.** O(n) to build, O(1) per query.

**Watch for.** Seed the map with `{0: 1}` — the empty prefix — or every subarray
starting at index 0 is missed. The hash-map variant works with negative numbers, where
sliding window does not. Two dimensions use inclusion–exclusion over four corners.

**Representative:** 303 Range Sum Query · 560 Subarray Sum Equals K · 523 Continuous Subarray Sum · 304 Range Sum Query 2D

---

## Monotonic stack

**Signal.** "Next greater element", "previous smaller element", spans, or the largest
rectangle under a histogram.

**Mechanism.** Keep a stack whose values are monotonic. When the incoming element
breaks the order, pop — and the popped element has just found its answer, because the
incoming element is the first one to violate its condition. Each index is pushed and
popped at most once, hence linear time despite the nested loop.

**Cost.** O(n) time, O(n) space.

**Watch for.** Store indices rather than values when widths matter. A sentinel value
at the end flushes the stack and removes the post-loop cleanup.

**Representative:** 496 Next Greater Element · 739 Daily Temperatures · 84 Largest Rectangle in Histogram · 42 Trapping Rain Water

---

## Trie

**Signal.** Many strings, queried by prefix — autocomplete, word search on a board,
"does any word start with…".

**Mechanism.** A tree where each edge is a character, so a shared prefix is stored
once. A terminal flag marks nodes that complete a word.

**Cost.** O(L) per insert or lookup for a word of length L, independent of how many
words are stored. Space is O(total characters).

**Watch for.** A fixed 26-slot child array beats a `HashMap` for lowercase-only
inputs. Combining a trie with grid DFS turns a per-word search into a single traversal —
the standard solution to Word Search II.

**Representative:** 208 Implement Trie · 211 Design Add and Search Words · 212 Word Search II

---

## Dynamic programming

**Signal.** Count the number of ways, or optimize a value, where the answer is built
from overlapping subproblems and a greedy choice demonstrably fails.

**Mechanism.** Define the state precisely — *what does `dp[i]` mean, in one sentence* —
then write the transition, then the base case. Getting the state definition right is
the entire problem; the code is mechanical afterwards.

Families worth recognizing on sight:

| Family | State | Example |
| :----- | :---- | :------ |
| Linear | `dp[i]` = answer for the prefix ending at `i` | House Robber, Climbing Stairs |
| Knapsack | `dp[i][w]` = best using first `i` items within budget `w` | Partition Equal Subset Sum |
| Two sequences | `dp[i][j]` = answer for prefixes of both | Edit Distance, LCS |
| Interval | `dp[i][j]` = answer for the range `i..j` | Burst Balloons |
| On a grid | `dp[r][c]` = answer for the path reaching `(r, c)` | Unique Paths, Minimum Path Sum |

**Cost.** States × transition cost. Usually O(n·k) time; space often collapses to one
or two rows, since most transitions only look back a bounded distance.

**Watch for.** Iteration order must respect dependencies. The 0/1 knapsack space
optimization requires iterating the budget *downwards*; iterating upwards silently
turns it into the unbounded variant. When stuck, write the recursion with memoization
first and convert to a table afterwards.

**Representative:** 70 Climbing Stairs · 198 House Robber · 322 Coin Change · 72 Edit Distance · 300 Longest Increasing Subsequence

---

## Greedy

**Signal.** An optimization problem where sorting by one key makes the choice obvious.

**Mechanism.** Take the locally best option and never reconsider. This is only valid
with an exchange argument: any optimal solution can be transformed into the greedy one
without getting worse. If you cannot state that argument, the problem is probably DP.

**Cost.** O(n log n) when sorting dominates.

**Watch for.** Greedy failing on a small counterexample is the cheapest test available —
construct one before committing. Interval scheduling sorts by *end* time, not start.

**Representative:** 55 Jump Game · 45 Jump Game II · 435 Non-overlapping Intervals · 621 Task Scheduler

---

## Bit manipulation

**Signal.** Fixed-width integers, "constant extra space", "every element appears twice
except one", or subset enumeration over a small n.

**Mechanism.** XOR cancels equal values and is commutative, which isolates a unique
element in one pass. `x & (x - 1)` clears the lowest set bit; `x & -x` isolates it.
For n ≤ 20, an integer doubles as a subset mask and `for (int m = 0; m < 1 << n; m++)`
enumerates every subset.

**Cost.** O(n), usually with O(1) space.

**Watch for.** Java's `>>` is arithmetic and `>>>` is logical; the difference matters
for negative numbers. Shifting an `int` by 32 or more is undefined behaviour in
practice — the shift distance is taken mod 32.

**Representative:** 136 Single Number · 191 Number of 1 Bits · 338 Counting Bits · 78 Subsets (bitmask form)

---

## How to use this document

When a problem resists for more than a few minutes, the productive move is usually not
to think harder about the problem — it is to work the recognition table. Identify the
constraint that rules out brute force, find the signal that matches, and confirm the
cost against [COMPLEXITY.md](COMPLEXITY.md) before writing a line.
