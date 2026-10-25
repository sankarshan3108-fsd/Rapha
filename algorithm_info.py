
"""All explanation text for the "Algorithm Info" panel (one entry per page).

Keeping the text here keeps the GUI code clean.  Each entry has:
  title, summary (used by the "?" popups), algorithm, steps (numbered),
  why, comparison (headers + rows + note), complexity, trace (default text).
The "Live Trace" section is filled at run time by the pages.
"""

ALGORITHM_INFO = {
    "dashboard": {
        "title": "Dashboard - Hash table health & BST shape",
        "summary": "Load factor = records / table size. When it passes 0.75 the "
                   "hash table rehashes to the next prime after doubling. The BST "
                   "height shows how balanced the tree is.",
        "algorithm": "Load factor monitoring + rehashing (hash table) and "
                     "tree-height analysis (BST).",
        "steps": [
            "Load factor = n / table size (records divided by slots).",
            "After every insert, if the load factor is above 0.75 the table "
            "is rehashed.",
            "Rehash: pick the next prime after 2 x size (31 -> 67), create new "
            "slots and re-insert every record with the new h(id) = id % size.",
            "BST height = number of levels. Best case is ceil(log2(n+1)), "
            "worst case is n (a linked list).",
            "At startup records are shuffled (fixed seed) before BST insertion, "
            "because the database returns IDs in ascending order and sorted "
            "input would build a skewed tree.",
        ],
        "why": "Chains stay short while the load factor is low, so lookups stay "
               "O(1) - vital when a doctor needs a record instantly. Prime sizes "
               "spread IDs more evenly over slots because id % size does not "
               "repeat patterns of IDs that are multiples of a common factor. "
               "0.75 is the classic balance between memory waste and long chains.",
        "comparison": {
            "headers": ["Strategy", "Time", "Note"],
            "rows": [
                ["Fixed-size table", "O(n) worst", "chains grow forever"],
                ["Rehash at 0.75", "O(1) avg", "rare O(n) resize"],
                ["Balanced BST (AVL)", "O(log n)", "more complex code"],
            ],
            "note": "Rehash cost O(n) is paid rarely, so inserts stay O(1) amortised.",
        },
        "complexity": "Load factor: O(1). Rehash: O(n) time, O(n) space. "
                      "Height: O(n) to compute.",
        "trace": "Open this page after adding patients to see the load factor move.",
    },
    "patients": {
        "title": "All Patients - BST in-order traversal",
        "summary": "In-order traversal (Left -> Root -> Right) of the BST lists "
                   "patients sorted by ID in O(n) with no sorting. Text search is "
                   "a linear scan. Clicking a column header sorts with merge sort.",
        "algorithm": "BST in-order traversal; linear search; merge sort for columns.",
        "steps": [
            "Visit the left subtree (smaller IDs).",
            "Visit the node itself.",
            "Visit the right subtree (larger IDs).",
            "Result: IDs in ascending order, produced in O(n).",
            "Search box: every record is checked one by one (linear search, "
            "O(n)) because hashing only supports exact-key lookup.",
            "Column header click: records are re-ordered with our own merge sort.",
        ],
        "why": "The ward list is always needed in ID order. A BST keeps data "
               "ordered at all times, so no extra sort is required after each "
               "admission. A hash table could not produce this order.",
        "comparison": {
            "headers": ["Method", "Time", "Note"],
            "rows": [
                ["BST in-order", "O(n)", "already sorted"],
                ["Hash + sort", "O(n log n)", "re-sort every time"],
                ["Linear search", "O(n)", "works on any field"],
            ],
            "note": "Substring search cannot use hashing or the BST (not a key lookup).",
        },
        "complexity": "In-order: O(n) time, O(h) stack. Filter: O(n). "
                      "Column sort: O(n log n) time, O(n) space.",
        "trace": "Sort a column or search to see a trace here.",
    },
    "add": {
        "title": "Add Patient - Hash insert + BST insert",
        "summary": "The ID is hashed with h(id) = id % size to pick a slot; the "
                   "record joins that slot's chain. It is also inserted into the BST "
                   "by comparing with nodes from the root down.",
        "algorithm": "Hash function h(id) = id % size with separate chaining; "
                     "BST insertion; duplicate check by hash lookup.",
        "steps": [
            "Check the ID is unused with an O(1) hash lookup.",
            "Compute slot = id % table size.",
            "If the slot is empty the record becomes its first node; otherwise "
            "it is appended to the chain (a collision).",
            "If load factor > 0.75, rehash to the next prime size.",
            "BST: start at the root, go left if the ID is smaller, right if "
            "larger, and attach the new node at the first empty spot.",
            "The row is also written to SQLite so it survives restarts.",
        ],
        "why": "Chaining never runs out of space and deleting is simple, unlike "
               "open addressing. Hash lookup makes the duplicate-ID check "
               "instant, avoiding two patients sharing one ID.",
        "comparison": {
            "headers": ["Collision method", "Time", "Pros / Cons"],
            "rows": [
                ["Chaining", "O(1) avg", "simple delete; extra pointers"],
                ["Linear probing", "O(1) avg", "clustering; tricky delete"],
                ["Quadratic probing", "O(1) avg", "less clustering; may miss slots"],
            ],
            "note": "We chose chaining: easiest to explain and to visualise.",
        },
        "complexity": "Hash insert O(1) avg / O(n) worst. BST insert O(log n) "
                      "avg / O(n) skewed. Space O(n).",
        "trace": "Add a patient to see the hash slot, BST path and rehash check.",
    },
    "lookup": {
        "title": "Lookup by ID - Hashing with chaining",
        "summary": "The ID is hashed to a slot and only that slot's chain is "
                   "searched, so the average lookup needs about 1-2 comparisons "
                   "instead of scanning all records.",
        "algorithm": "Hash table search with separate chaining.",
        "steps": [
            "Compute slot = id % table size.",
            "Go directly to that slot (array access, O(1)).",
            "Walk the chain from the head, comparing each node's ID.",
            "Stop at the matching node (found) or at the end (not found).",
        ],
        "why": "Emergency staff need a record by ID immediately. Hashing gives "
               "direct access whose cost does not grow with the number of "
               "patients.",
        "comparison": {
            "headers": ["Method", "Time", "Note"],
            "rows": [
                ["Linear search", "O(n)", "checks records one by one"],
                ["Binary search", "O(log n)", "needs a sorted array; slow inserts"],
                ["BST", "O(log n) avg", "O(n) if skewed"],
                ["Hash table", "O(1) avg", "no ordering"],
            ],
            "note": "Hashing wins for exact-ID lookup; the BST is kept for ordered work.",
        },
        "complexity": "Average O(1); worst O(n) if every ID collides. Space O(n).",
        "trace": "Look up an ID to see the hash calculation and chain comparisons.",
    },
    "range": {
        "title": "Range Query - Pruned in-order traversal on the BST",
        "summary": "The BST skips whole subtrees that cannot contain IDs in "
                   "[low, high]: go left only if node.id > low, go right only if "
                   "node.id < high. Results come out sorted.",
        "algorithm": "Pruned in-order traversal of a binary search tree.",
        "steps": [
            "Visit the node and count it as visited.",
            "If node.id > low, the left subtree may hold matches: go left. "
            "Otherwise the left subtree is pruned.",
            "If low <= node.id <= high, add the node to the results.",
            "If node.id < high, go right. Otherwise the right subtree is pruned.",
            "Because the traversal is in-order, results are already ascending.",
        ],
        "why": "Typical hospital questions are 'all patients in ward block "
               "1001-1025'. The BST answers that touching only the relevant part "
               "of the data.",
        "comparison": {
            "headers": ["Method", "Time", "Note"],
            "rows": [
                ["Hash table scan", "O(m + n)", "no order; scan all slots"],
                ["Unsorted list", "O(n) + sort", "filter, then sort results"],
                ["BST (pruned)", "O(h + k)", "h = height, k = results"],
            ],
            "note": "A hash table scatters IDs, so it cannot answer ranges.",
        },
        "complexity": "O(h + k) time, O(h) recursion stack.",
        "trace": "Run a range query to see visited, included and pruned nodes.",
    },
    "report": {
        "title": "Daily Report - Merge sort by admission date",
        "summary": "Merge sort splits the list in halves, sorts each half "
                   "recursively and merges them. It is stable, so patients "
                   "admitted on the same date keep their ID order.",
        "algorithm": "Merge sort (divide and conquer), key = (admission_date, ID).",
        "steps": [
            "Divide: split the list into two halves until each part has 1 item.",
            "A list of 1 item is already sorted.",
            "Merge: compare the front items of two sorted halves and take the "
            "smaller (on ties take the left one - this keeps the sort stable).",
            "Repeat merging upward until one sorted list remains.",
            "Stability example: two patients on 2026-10-21 with IDs 1003 and "
            "1031 stay in the order 1003, 1031.",
        ],
        "why": "A daily report must be deterministic and fast on any input. "
               "Merge sort is always O(n log n), and stability keeps patients "
               "of the same day in ID order.",
        "comparison": {
            "headers": ["Algorithm", "Time", "Stable?"],
            "rows": [
                ["Bubble sort", "O(n^2)", "yes"],
                ["Insertion sort", "O(n^2) worst", "yes"],
                ["Selection sort", "O(n^2)", "no"],
                ["Quick sort", "O(n log n) avg, O(n^2) worst", "no"],
                ["Heap sort", "O(n log n)", "no"],
                ["Merge sort", "O(n log n) always", "yes (O(n) extra space)"],
            ],
            "note": "Merge sort's only cost is O(n) temporary memory.",
        },
        "complexity": "Time O(n log n) in best, average and worst case; "
                      "space O(n).",
        "trace": "Open the report to see comparisons and recursion depth.",
    },
    "hash_view": {
        "title": "Hash Table View - Slots and chains",
        "summary": "Each row is a slot (array index). Boxes to its right are the "
                   "records chained in that slot. Two or more boxes mean a "
                   "collision.",
        "algorithm": "Separate chaining hash table (diagram).",
        "steps": [
            "The teal box on the left is the slot index.",
            "Arrows lead to chain nodes holding patient IDs.",
            "Empty slots are faint; a slot with 1 node is white; 2+ nodes "
            "(a collision) is amber.",
            "Hover a node to see the patient name; click it for details.",
        ],
        "why": "Seeing chains explains why lookup is O(1) on average: most "
               "chains have 0-2 nodes, so only a couple of comparisons occur.",
        "comparison": {
            "headers": ["Chain length", "Meaning", "Cost"],
            "rows": [
                ["0", "empty slot", "instant miss"],
                ["1", "no collision", "1 comparison"],
                ["2+", "collision", "k comparisons"],
            ],
            "note": "The longest chain is the worst-case lookup cost.",
        },
        "complexity": "Lookup O(1) average; O(longest chain) worst. Space O(n + size).",
        "trace": "Statistics update after every insert, delete or rehash.",
    },
    "bst_view": {
        "title": "BST View - Tree shape, search and traversals",
        "summary": "Left child < parent < right child. Search follows one path "
                   "from the root. Traversals visit nodes in In-order "
                   "(sorted), Pre-order or Post-order.",
        "algorithm": "Binary search tree search and depth-first traversals.",
        "steps": [
            "Search: compare the ID with the node; go left if smaller, right "
            "if larger; stop when equal or empty.",
            "In-order (L, Root, R): ascending IDs - used for sorted lists.",
            "Pre-order (Root, L, R): copies/saves a tree.",
            "Post-order (L, R, Root): safe for deleting a tree.",
            "Height = levels in the longest path; it controls search cost.",
        ],
        "why": "The BST keeps patients ordered at all times, enabling range "
               "listings and sorted output that hashing cannot provide.",
        "comparison": {
            "headers": ["Tree", "Search", "Note"],
            "rows": [
                ["Balanced", "O(log n)", "height = ceil(log2(n+1))"],
                ["Skewed", "O(n)", "height = n"],
                ["Our tree", "see stats", "shuffled insertion"],
            ],
            "note": "Compare the actual height with the best and worst values.",
        },
        "complexity": "Search/insert/delete O(h); traversals O(n); space O(n).",
        "trace": "Search an ID or run a traversal to see each step.",
    },
    "about": {
        "title": "About - Why hash table + BST + merge sort",
        "summary": "Each structure answers a different hospital question: hash "
                   "table = instant lookup, BST = ordered/range queries, merge "
                   "sort = daily report.",
        "algorithm": "Hash table, binary search tree and merge sort working together.",
        "steps": [
            "SQLite stores records permanently (storage only).",
            "At startup every record is loaded into the hash table and the BST.",
            "Lookups by ID use the hash table.",
            "Ordered lists and range queries use the BST.",
            "The daily admission report uses merge sort.",
            "Every add/update/delete writes to SQLite and updates both "
            "structures so they never disagree.",
        ],
        "why": "No single structure is best at everything. Combining them gives "
               "O(1) lookup, O(h + k) ranges and O(n log n) reports.",
        "comparison": {
            "headers": ["Need", "Best tool", "Time"],
            "rows": [
                ["Find one patient", "Hash table", "O(1)"],
                ["List IDs in a range", "BST", "O(h + k)"],
                ["Daily report", "Merge sort", "O(n log n)"],
            ],
            "note": "The price is extra memory: records are indexed twice.",
        },
        "complexity": "Memory O(n) per structure; every operation as shown above.",
        "trace": "This page has no live operations.",
    },
}

ALGORITHM_INFO["reports"] = {
    "title": "Generate Report - one data source, five reports",
    "summary": "Every report is built from our own data structures through "
               "PatientManager: hash lookup for one patient, BST traversal or "
               "range query for ID lists, merge sort for date order.",
    "algorithm": "Hash table lookup, BST in-order traversal and range query, "
                 "merge sort - then written as a PDF.",
    "steps": [
        "Pick a report type and its options.",
        "Daily: merge sort orders patients by admission date, then they are "
        "grouped by date.",
        "Department-wise: BST in-order traversal gives each department's "
        "patients in ID order; department names are ordered by merge sort.",
        "ID range: BST pruned in-order traversal returns IDs low..high.",
        "Individual: one hash-table lookup (id % size) finds the record.",
        "Summary: combines all of the above plus the structures' status.",
        "The same content feeds the text preview and the PDF.",
    ],
    "why": "Reports must match what the screens show, so they reuse the same "
           "structures instead of querying the database again. Each structure "
           "is used where it is fastest.",
    "comparison": {
        "headers": ["Report", "Structure", "Time"],
        "rows": [
            ["Daily", "Merge sort", "O(n log n)"],
            ["Department", "BST in-order", "O(n)"],
            ["ID range", "BST range", "O(h + k)"],
            ["Individual", "Hash table", "O(1) avg"],
        ],
        "note": "SQL ORDER BY / BETWEEN is never used; the database only stores.",
    },
    "complexity": "Building a report is O(n log n) at most (daily sort); PDF "
                  "writing is linear in the number of rows.",
    "trace": "Press Preview or Generate PDF to see what was built.",
}

SECTION_ORDER = ["Algorithm Used", "How It Works", "Why This Algorithm?",
                 "Comparison", "Complexity", "Live Trace"]
