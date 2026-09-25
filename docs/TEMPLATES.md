# Templates

Reference implementations in Java for the algorithms that keep reappearing. These are
written to be correct at the boundaries — the off-by-one cases are the reason to have
templates at all — and to be adapted rather than copied verbatim.

Pattern selection is covered in [PATTERNS.md](PATTERNS.md); costs are in
[COMPLEXITY.md](COMPLEXITY.md).

---

## Contents

- [Binary search](#binary-search) · [Binary search on the answer](#binary-search-on-the-answer)
- [Sliding window](#sliding-window) · [Two pointers](#two-pointers)
- [Monotonic stack](#monotonic-stack) · [Prefix sums](#prefix-sums)
- [BFS on a grid](#bfs-on-a-grid) · [Backtracking](#backtracking)
- [Union-find](#union-find) · [Topological sort](#topological-sort) · [Dijkstra](#dijkstra)
- [Trie](#trie) · [Top-k with a heap](#top-k-with-a-heap)
- [Linked lists](#linked-lists) · [Iterative tree traversal](#iterative-tree-traversal)
- [Dynamic programming](#dynamic-programming)

---

## Binary search

Write boundaries as `lowerBound` / `upperBound` rather than as a bespoke loop each time.
Both use a half-open range `[lo, hi)` and the invariant *the answer is in `[lo, hi]`*,
which terminates without a separate equality branch.

```java
/** First index with a[i] >= target, or a.length if none. */
static int lowerBound(int[] a, int target) {
    int lo = 0, hi = a.length;
    while (lo < hi) {
        int mid = lo + (hi - lo) / 2;      // never (lo + hi) / 2 — that overflows
        if (a[mid] < target) lo = mid + 1;
        else                 hi = mid;
    }
    return lo;
}

/** First index with a[i] > target, or a.length if none. */
static int upperBound(int[] a, int target) {
    int lo = 0, hi = a.length;
    while (lo < hi) {
        int mid = lo + (hi - lo) / 2;
        if (a[mid] <= target) lo = mid + 1;
        else                  hi = mid;
    }
    return lo;
}
```

With these two, the rest is composition: `target` exists iff
`lowerBound(a, t) < a.length && a[lowerBound(a, t)] == t`, and its occurrence count is
`upperBound(a, t) - lowerBound(a, t)`.

### Binary search on the answer

When `feasible` is monotonic — false, false, …, true, true — the answer space itself is
searchable even though the input is unsorted.

```java
/** Smallest x in [lo, hi] with feasible(x) == true. Assumes feasible(hi) is true. */
static int minFeasible(int lo, int hi) {
    while (lo < hi) {
        int mid = lo + (hi - lo) / 2;
        if (feasible(mid)) hi = mid;
        else               lo = mid + 1;
    }
    return lo;
}
```

The work is entirely in `feasible`. For *Koko Eating Bananas*, `feasible(speed)` is
"can she finish within h hours at this speed"; for *Split Array Largest Sum*, it is
"can the array be cut into at most k parts each summing to no more than this".

---

## Sliding window

Two variants, distinguished by what the inner loop shrinks on.

```java
/** Longest valid window: expand always, shrink WHILE INVALID. */
static int longestWithoutRepeats(String s) {
    int[] count = new int[128];
    int best = 0, left = 0;
    for (int right = 0; right < s.length(); right++) {
        count[s.charAt(right)]++;
        while (count[s.charAt(right)] > 1) {     // window is invalid
            count[s.charAt(left++)]--;
        }
        best = Math.max(best, right - left + 1);
    }
    return best;
}

/** Shortest valid window: expand always, shrink WHILE VALID, recording on the way. */
static int shortestSubarrayAtLeast(int[] nums, int target) {
    int best = Integer.MAX_VALUE, left = 0, sum = 0;
    for (int right = 0; right < nums.length; right++) {
        sum += nums[right];
        while (sum >= target) {                  // window is valid
            best = Math.min(best, right - left + 1);
            sum -= nums[left++];
        }
    }
    return best == Integer.MAX_VALUE ? 0 : best;
}
```

Counting problems phrased as "exactly k" are usually easier as
`atMost(k) - atMost(k - 1)`, where `atMost` is the longest-window form.

---

## Two pointers

```java
/** All distinct triplets summing to zero. O(n^2) after the sort. */
static List<List<Integer>> threeSum(int[] nums) {
    Arrays.sort(nums);
    List<List<Integer>> out = new ArrayList<>();
    for (int i = 0; i < nums.length - 2; i++) {
        if (i > 0 && nums[i] == nums[i - 1]) continue;      // skip duplicate anchors
        if (nums[i] > 0) break;                             // sorted: no way back to zero
        int lo = i + 1, hi = nums.length - 1;
        while (lo < hi) {
            int sum = nums[i] + nums[lo] + nums[hi];
            if (sum < 0) {
                lo++;
            } else if (sum > 0) {
                hi--;
            } else {
                out.add(List.of(nums[i], nums[lo], nums[hi]));
                while (lo < hi && nums[lo] == nums[lo + 1]) lo++;   // skip AFTER recording
                while (lo < hi && nums[hi] == nums[hi - 1]) hi--;
                lo++;
                hi--;
            }
        }
    }
    return out;
}
```

The duplicate skips come *after* recording a hit. Skipping first drops valid triplets
that legitimately contain repeated values.

---

## Monotonic stack

```java
/** For each index, the next strictly greater value to its right; -1 if none. */
static int[] nextGreater(int[] nums) {
    int[] answer = new int[nums.length];
    Arrays.fill(answer, -1);
    Deque<Integer> stack = new ArrayDeque<>();      // indices, values strictly decreasing
    for (int i = 0; i < nums.length; i++) {
        while (!stack.isEmpty() && nums[stack.peek()] < nums[i]) {
            answer[stack.pop()] = nums[i];          // nums[i] is the first to beat it
        }
        stack.push(i);
    }
    return answer;
}
```

Store indices, not values, whenever a distance or width is part of the answer. Appending
a sentinel (`Integer.MIN_VALUE` for a decreasing stack) flushes leftovers and removes the
post-loop cleanup.

---

## Prefix sums

```java
/** Number of contiguous subarrays summing to k. Works with negative values. */
static int subarraysSumming(int[] nums, int k) {
    Map<Long, Integer> seen = new HashMap<>();
    seen.put(0L, 1);                     // the empty prefix — omitting this is the classic bug
    long prefix = 0;
    int count = 0;
    for (int num : nums) {
        prefix += num;                   // long: values reach 1e9, sums reach 1e14
        count += seen.getOrDefault(prefix - k, 0);
        seen.merge(prefix, 1, Integer::sum);
    }
    return count;
}
```

Sliding window cannot replace this when the array contains negative numbers: the running
sum is no longer monotonic in the window size, so shrinking is not well-defined.

---

## BFS on a grid

```java
private static final int[][] DIRS = {{1, 0}, {-1, 0}, {0, 1}, {0, -1}};

/** Minimum steps for every source to reach every reachable cell (multi-source BFS). */
static int spreadTime(int[][] grid) {
    int rows = grid.length, cols = grid[0].length;
    Deque<int[]> queue = new ArrayDeque<>();
    boolean[][] visited = new boolean[rows][cols];

    for (int r = 0; r < rows; r++) {
        for (int c = 0; c < cols; c++) {
            if (grid[r][c] == 2) {                 // every source starts at distance 0
                queue.add(new int[]{r, c});
                visited[r][c] = true;
            }
        }
    }

    int steps = 0;
    while (!queue.isEmpty()) {
        for (int size = queue.size(); size > 0; size--) {   // snapshot: one level at a time
            int[] cell = queue.poll();
            for (int[] dir : DIRS) {
                int r = cell[0] + dir[0], c = cell[1] + dir[1];
                if (r < 0 || r >= rows || c < 0 || c >= cols) continue;
                if (visited[r][c] || grid[r][c] != 1) continue;
                visited[r][c] = true;              // mark on ENQUEUE, not on dequeue
                queue.add(new int[]{r, c});
            }
        }
        steps++;
    }
    return steps == 0 ? 0 : steps - 1;             // the last round enqueued nothing
}
```

Marking visited on dequeue instead of enqueue lets the same cell be queued several times
before it is first processed, which degrades to exponential behaviour on dense grids.

---

## Backtracking

```java
/** All subsets, with duplicate inputs handled. Sort first. */
static void subsets(int[] nums, int start, List<Integer> path, List<List<Integer>> out) {
    out.add(new ArrayList<>(path));                // copy — never add `path` itself
    for (int i = start; i < nums.length; i++) {
        if (i > start && nums[i] == nums[i - 1]) continue;   // same value at same depth
        path.add(nums[i]);
        subsets(nums, i + 1, path, out);
        path.remove(path.size() - 1);              // un-choose
    }
}

/** All permutations, using a membership flag rather than removal. */
static void permute(int[] nums, boolean[] used, List<Integer> path, List<List<Integer>> out) {
    if (path.size() == nums.length) {
        out.add(new ArrayList<>(path));
        return;
    }
    for (int i = 0; i < nums.length; i++) {
        if (used[i]) continue;
        used[i] = true;
        path.add(nums[i]);
        permute(nums, used, path, out);
        path.remove(path.size() - 1);
        used[i] = false;
    }
}
```

`out.add(path)` without the copy stores a reference to a buffer that is about to be
mutated — every result ends up identical and empty. This is the single most common
backtracking bug.

---

## Union-find

```java
/** Disjoint set with path halving and union by rank. ~O(1) amortized per operation. */
final class DisjointSet {
    private final int[] parent;
    private final int[] rank;
    private int components;

    DisjointSet(int n) {
        parent = new int[n];
        rank = new int[n];
        components = n;
        for (int i = 0; i < n; i++) parent[i] = i;
    }

    int find(int x) {
        while (parent[x] != x) {
            parent[x] = parent[parent[x]];    // path halving: flatten while descending
            x = parent[x];
        }
        return x;
    }

    /** Returns false when a and b were already connected — i.e. this edge closes a cycle. */
    boolean union(int a, int b) {
        int rootA = find(a), rootB = find(b);
        if (rootA == rootB) return false;
        if (rank[rootA] < rank[rootB]) {
            int swap = rootA; rootA = rootB; rootB = swap;
        }
        parent[rootB] = rootA;
        if (rank[rootA] == rank[rootB]) rank[rootA]++;
        components--;
        return true;
    }

    int components() { return components; }
}
```

Both optimizations are required. Path compression alone, or union by rank alone, leaves a
logarithmic factor that shows up on large inputs.

---

## Topological sort

```java
/** Kahn's algorithm. Returns an empty array when the graph has a cycle. */
static int[] topologicalOrder(int n, int[][] edges) {
    List<List<Integer>> adjacency = new ArrayList<>();
    for (int i = 0; i < n; i++) adjacency.add(new ArrayList<>());
    int[] indegree = new int[n];

    for (int[] edge : edges) {          // edge = {node, prerequisite}
        adjacency.get(edge[1]).add(edge[0]);    // prerequisite -> node
        indegree[edge[0]]++;
    }

    Deque<Integer> queue = new ArrayDeque<>();
    for (int i = 0; i < n; i++) if (indegree[i] == 0) queue.add(i);

    int[] order = new int[n];
    int emitted = 0;
    while (!queue.isEmpty()) {
        int node = queue.poll();
        order[emitted++] = node;
        for (int next : adjacency.get(node)) {
            if (--indegree[next] == 0) queue.add(next);
        }
    }
    return emitted == n ? order : new int[0];   // short output means a cycle
}
```

Edge direction is the bug to watch: "course a requires b" is an edge `b → a`. Swap a
`PriorityQueue` in for the `ArrayDeque` when the lexicographically smallest order is wanted.

---

## Dijkstra

```java
/** Shortest distances from src over non-negative weights. adjacency: node -> {to, weight}. */
static long[] dijkstra(int n, List<int[]>[] adjacency, int src) {
    long[] dist = new long[n];
    Arrays.fill(dist, Long.MAX_VALUE);
    dist[src] = 0;

    PriorityQueue<long[]> heap = new PriorityQueue<>((a, b) -> Long.compare(a[0], b[0]));
    heap.add(new long[]{0, src});

    while (!heap.isEmpty()) {
        long[] top = heap.poll();
        int node = (int) top[1];
        if (top[0] > dist[node]) continue;          // lazy deletion: a stale entry
        for (int[] edge : adjacency[node]) {
            long candidate = dist[node] + edge[1];
            if (candidate < dist[edge[0]]) {
                dist[edge[0]] = candidate;
                heap.add(new long[]{candidate, edge[0]});
            }
        }
    }
    return dist;
}
```

Java's `PriorityQueue` has no decrease-key, so stale entries are pushed and skipped on
pop. Dijkstra is invalid with negative weights — that is Bellman–Ford.

---

## Trie

```java
/** Prefix tree over lowercase letters. O(L) per operation, independent of word count. */
final class Trie {
    private final Trie[] children = new Trie[26];
    private boolean terminal;

    void insert(String word) {
        Trie node = this;
        for (int i = 0; i < word.length(); i++) {
            int c = word.charAt(i) - 'a';
            if (node.children[c] == null) node.children[c] = new Trie();
            node = node.children[c];
        }
        node.terminal = true;
    }

    boolean contains(String word) {
        Trie node = walk(word);
        return node != null && node.terminal;
    }

    boolean hasPrefix(String prefix) {
        return walk(prefix) != null;
    }

    private Trie walk(String s) {
        Trie node = this;
        for (int i = 0; i < s.length(); i++) {
            node = node.children[s.charAt(i) - 'a'];
            if (node == null) return null;
        }
        return node;
    }
}
```

The fixed 26-slot array beats a `HashMap<Character, Trie>` on both time and memory for
lowercase input, and it is what makes trie-plus-grid-DFS fast enough for Word Search II.

---

## Top-k with a heap

```java
/** The k most frequent values. O(n log k) — a min-heap of size k, not a max-heap. */
static int[] topKFrequent(int[] nums, int k) {
    Map<Integer, Integer> frequency = new HashMap<>();
    for (int num : nums) frequency.merge(num, 1, Integer::sum);

    PriorityQueue<Map.Entry<Integer, Integer>> heap =
            new PriorityQueue<>(Map.Entry.comparingByValue());   // least frequent at the root
    for (Map.Entry<Integer, Integer> entry : frequency.entrySet()) {
        heap.add(entry);
        if (heap.size() > k) heap.poll();        // evict the weakest survivor
    }

    int[] answer = new int[heap.size()];
    for (int i = answer.length - 1; i >= 0; i--) answer[i] = heap.poll().getKey();
    return answer;
}
```

The inversion is the point: to keep the k *largest*, the heap must surrender its
*smallest* cheaply, so the comparator runs opposite to intuition.

---

## Linked lists

```java
/** Reverse in place. O(n) time, O(1) space. */
static ListNode reverse(ListNode head) {
    ListNode prev = null, curr = head;
    while (curr != null) {
        ListNode next = curr.next;      // save before overwriting
        curr.next = prev;
        prev = curr;
        curr = next;
    }
    return prev;
}

/** Entry node of the cycle, or null. Floyd's algorithm. */
static ListNode cycleStart(ListNode head) {
    ListNode slow = head, fast = head;
    while (fast != null && fast.next != null) {
        slow = slow.next;
        fast = fast.next.next;
        if (slow == fast) {                        // meeting point is inside the cycle
            slow = head;
            while (slow != fast) {                 // both now advance one step at a time
                slow = slow.next;
                fast = fast.next;
            }
            return slow;                           // they meet at the entrance
        }
    }
    return null;
}
```

A dummy head node removes the special case for "the deletion or insertion happens at
position 0" in almost every list-manipulation problem — use one by default.

---

## Iterative tree traversal

```java
/** In-order without recursion — required when depth can reach 1e5. */
static List<Integer> inorder(TreeNode root) {
    List<Integer> out = new ArrayList<>();
    Deque<TreeNode> stack = new ArrayDeque<>();
    TreeNode node = root;
    while (node != null || !stack.isEmpty()) {
        while (node != null) {          // descend as far left as possible
            stack.push(node);
            node = node.left;
        }
        node = stack.pop();
        out.add(node.val);              // visit
        node = node.right;              // then the right subtree
    }
    return out;
}
```

In-order on a BST emits sorted values, which is the shortcut behind "validate a BST",
"k-th smallest element", and "minimum absolute difference".

---

## Dynamic programming

```java
/** 0/1 knapsack, space-optimized: can any subset sum to exactly `target`? */
static boolean canPartition(int[] nums, int target) {
    boolean[] reachable = new boolean[target + 1];
    reachable[0] = true;                       // the empty subset
    for (int num : nums) {
        for (int sum = target; sum >= num; sum--) {   // DOWNWARDS — each item used once
            reachable[sum] |= reachable[sum - num];
        }
    }
    return reachable[target];
}

/** Longest strictly increasing subsequence, O(n log n) via patience sorting. */
static int lengthOfLIS(int[] nums) {
    int[] tails = new int[nums.length];        // tails[i] = smallest tail of an LIS of length i+1
    int size = 0;
    for (int num : nums) {
        int i = Arrays.binarySearch(tails, 0, size, num);
        if (i < 0) i = -(i + 1);               // binarySearch returns -(insertion point) - 1
        tails[i] = num;
        if (i == size) size++;
    }
    return size;
}
```

The descending inner loop in the knapsack is load-bearing. Ascending it reuses the value
already updated in this pass, which silently solves the *unbounded* knapsack instead —
a bug that produces plausible-looking wrong answers rather than an obvious failure.

`tails` is not itself a valid subsequence; only its length is meaningful. Reconstructing
the actual sequence needs a parallel predecessor array.
