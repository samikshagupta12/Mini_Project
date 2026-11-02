"""
Technical Preparation Hub & Interactive Study Materials.
Provides high-yield cheat sheets, interactive flashcards, algorithmic complexity charts,
and interview preparation summaries across all 10 computer science disciplines.
"""
from typing import Dict, Any, List

# High-Yield Topic Revision Guides
PREP_CHEAT_SHEETS: Dict[str, Dict[str, Any]] = {
    "Data Structures and Algorithms": {
        "title": "Data Structures & Big-O Complexity Matrix",
        "summary": "Master fundamental time and space complexities and recurring algorithmic patterns.",
        "tables": [
            {
                "caption": "Common Data Structure Operations",
                "headers": ["Data Structure", "Access", "Search", "Insertion", "Deletion", "Space"],
                "rows": [
                    ["Array", "O(1)", "O(N)", "O(N)", "O(N)", "O(N)"],
                    ["Singly Linked List", "O(N)", "O(N)", "O(1) at head", "O(1) at head", "O(N)"],
                    ["Hash Table (Average)", "N/A", "O(1)", "O(1)", "O(1)", "O(N)"],
                    ["Binary Search Tree (Balanced)", "O(log N)", "O(log N)", "O(log N)", "O(log N)", "O(N)"],
                    ["Binary Search Tree (Worst)", "O(N)", "O(N)", "O(N)", "O(N)", "O(N)"],
                    ["Binary Heap (Min/Max)", "O(1) peek", "O(N)", "O(log N)", "O(log N)", "O(N)"],
                ]
            },
            {
                "caption": "Sorting Algorithms Benchmark",
                "headers": ["Algorithm", "Best Time", "Average Time", "Worst Time", "Space", "Stable?"],
                "rows": [
                    ["Merge Sort", "O(N log N)", "O(N log N)", "O(N log N)", "O(N)", "Yes"],
                    ["Quick Sort", "O(N log N)", "O(N log N)", "O(N^2)", "O(log N)", "No"],
                    ["Heap Sort", "O(N log N)", "O(N log N)", "O(N log N)", "O(1)", "No"],
                    ["Insertion Sort", "O(N)", "O(N^2)", "O(N^2)", "O(1)", "Yes"],
                ]
            }
        ],
        "key_takeaways": [
            "**Two Pointers:** Optimal for sorted arrays, palindrome checks, and cycle detection.",
            "**Sliding Window:** Optimal for subarray/substring contiguous constraints (e.g. max sum of size k).",
            "**Fast & Slow Pointers (Floyd's):** Detects linked list cycles in O(N) time and O(1) space.",
            "**Monotonic Stack:** Next greater / next smaller element queries in linear O(N) time."
        ]
    },
    "Python Programming": {
        "title": "Python Core Architecture & Performance Guide",
        "summary": "Essential CPython runtime mechanics, memory management, and idioms.",
        "key_takeaways": [
            "**CPython GIL:** Global Interpreter Lock allows only one native thread to execute Python bytecodes simultaneously. Use `multiprocessing` for CPU-bound parallelism; use `threading` or `asyncio` for I/O-bound tasks.",
            "**Mutability Rules:** Lists, Dicts, Sets are *mutable*. Ints, Floats, Strings, Tuples, Frozensets are *immutable*. Never use mutable default arguments (`def func(x=[])`).",
            "**Generators vs Lists:** Generators compute values lazily using `yield` with O(1) memory footprint vs O(N) for list comprehensions.",
            "**Decorators:** Functions that take another function as input and extend its behavior using `@functools.wraps`."
        ]
    },
    "Database Management Systems": {
        "title": "DBMS Architecture, ACID & Normalization",
        "summary": "Core relational theory, indexing mechanics, and transaction guarantees.",
        "key_takeaways": [
            "**ACID Properties:** Atomicity (All or nothing), Consistency (Preserves constraints), Isolation (Serial execution view), Durability (Persisted to disk).",
            "**B+ Tree Indexing:** Leaf nodes store actual data or row pointers linked sequentially for O(log N) lookups and ultra-fast range queries (`BETWEEN`).",
            "**Normalization Levels:**\n- **1NF:** Atomic values, no repeating groups.\n- **2NF:** 1NF + no partial dependencies on composite PK.\n- **3NF:** 2NF + no transitive functional dependencies (A -> B -> C).\n- **BCNF:** For every dependency X -> Y, X must be a super key."
        ]
    },
    "SQL and MongoDB": {
        "title": "SQL Query Optimization & MongoDB Aggregations",
        "summary": "Relational query formulations versus NoSQL document modeling.",
        "key_takeaways": [
            "**Window Functions:** `ROW_NUMBER()` assigns sequential integer; `RANK()` leaves gaps on ties (1, 2, 2, 4); `DENSE_RANK()` does not leave gaps (1, 2, 2, 3).",
            "**MongoDB Aggregation Pipeline:** Processes documents sequentially via stages: `$match` (filter first for index usage) -> `$project` -> `$group` -> `$sort` -> `$limit`.",
            "**SQL vs NoSQL:** Choose SQL for relational integrity and strict ACID transactions; choose MongoDB for hierarchical, dynamic document schemas and high write throughput."
        ]
    },
    "Operating Systems": {
        "title": "OS Concurrency, Memory & Deadlocks",
        "summary": "Process management, virtual memory paging, and concurrency coordination.",
        "key_takeaways": [
            "**Process vs Thread:** A process possesses isolated address space and PCB; threads share code, data, and heap but maintain separate execution stacks and registers.",
            "**Coffman Deadlock Conditions:** 1. Mutual Exclusion, 2. Hold and Wait, 3. No Preemption, 4. Circular Wait. Breaking Circular Wait via global resource ordering prevents deadlocks.",
            "**Thrashing:** System spends more time paging between RAM and disk swap than executing code, caused by working sets exceeding physical RAM."
        ]
    },
    "Computer Networks": {
        "title": "Computer Networks & Protocol Stack Lifecycle",
        "summary": "Transport protocols, web requests lifecycle, and encryption handshakes.",
        "key_takeaways": [
            "**TCP vs UDP:** TCP is connection-oriented, ordered, reliable, and features flow/congestion control; UDP is connectionless, unordered, and low-latency.",
            "**TCP 3-Way Handshake:** `SYN` -> `SYN-ACK` -> `ACK`.",
            "**URL Navigation Lifecycle:** Browser DNS lookup -> TCP handshake -> TLS handshake -> HTTP GET -> Server processing -> HTTP 200 -> DOM parsing & render.",
            "**HTTPS / TLS 1.3:** Asymmetric cryptography (RSA / ECDHE) securely authenticates server and exchanges session keys; fast symmetric AES-GCM encrypts application data."
        ]
    },
    "Machine Learning": {
        "title": "Machine Learning Foundations & Model Diagnostics",
        "summary": "Bias-variance tradeoff, decision tree mechanics, and metric selection.",
        "key_takeaways": [
            "**Bias-Variance Tradeoff:** High Bias = Underfitting (model too simple); High Variance = Overfitting (model memorizes noise).",
            "**Decision Tree Splitting:** CART uses **Gini Impurity** ($1 - \\sum p_i^2$); ID3/C4.5 uses **Entropy / Information Gain** ($-\\sum p_i \\log_2 p_i$).",
            "**Metric Selection for Imbalanced Data:** Accuracy is misleading on skewed data (e.g. 99% negative). Evaluate with Precision (Quality of positive claims), Recall (Coverage of actual positives), and F1-Score."
        ]
    },
    "Object-Oriented Programming": {
        "title": "SOLID Principles & Architectural Patterns",
        "summary": "Clean code structure, modular design, and object relationships.",
        "key_takeaways": [
            "**Single Responsibility (SRP):** A class should have one, and only one, reason to change.",
            "**Open/Closed (OCP):** Open for extension, closed for modification.",
            "**Liskov Substitution (LSP):** Subtypes must be substitutable for their base types without altering correctness.",
            "**Interface Segregation (ISP):** Clients should not be forced to depend upon interfaces they do not use.",
            "**Dependency Inversion (DIP):** Depend on abstractions, not on concrete implementations."
        ]
    }
}

# Rapid-Fire Interactive Flashcards
FLASHCARDS: List[Dict[str, str]] = [
    {
        "topic": "Python Programming",
        "question": "Why shouldn't you use a mutable object like a list as a default argument in Python functions?",
        "answer": "Default arguments are evaluated once when the function is defined, not each time it is called. A mutable default is shared across all function calls, leading to unexpected shared state bugs."
    },
    {
        "topic": "Data Structures and Algorithms",
        "question": "What is the worst-case time complexity of QuickSort, and how can it be mitigated?",
        "answer": "Worst-case is O(N^2) when the pivot selected is consistently the minimum or maximum element. Mitigate using randomized pivot selection, median-of-three, or IntroSort."
    },
    {
        "topic": "Operating Systems",
        "question": "What is the difference between a Mutex and a Semaphore?",
        "answer": "A Mutex (Mutual Exclusion) has ownership: only the thread that locked it can unlock it (binary lock). A Semaphore is a signaling mechanism with an integer counter permitting up to N concurrent threads."
    },
    {
        "topic": "Database Management Systems",
        "question": "What is the difference between Clustered and Non-Clustered Indexes?",
        "answer": "A Clustered Index determines the physical order of data rows in the table (only 1 per table). A Non-Clustered Index contains keys and row pointers to physical records without rearranging table rows (multiple allowed)."
    },
    {
        "topic": "Computer Networks",
        "question": "What is the purpose of the TTL (Time to Live) field in an IPv4 packet header?",
        "answer": "TTL prevents packets from endlessly looping in routing loops. Every router decrements TTL by 1; when TTL hits 0, the packet is discarded and an ICMP Time Exceeded message is returned."
    },
    {
        "topic": "Machine Learning",
        "question": "Why do Decision Trees tend to suffer from high variance, and how do Random Forests fix this?",
        "answer": "Unpruned trees fit deeply to training data noise (high variance). Random Forests train an ensemble of decorrelated trees over bootstrap samples and random feature subsets, reducing variance via averaging."
    },
    {
        "topic": "SQL and MongoDB",
        "question": "What is the difference between WHERE and HAVING in SQL?",
        "answer": "`WHERE` filters individual rows before grouping operations occur. `HAVING` filters aggregated groups after the `GROUP BY` clause is evaluated."
    },
    {
        "topic": "Object-Oriented Programming",
        "question": "Explain the difference between Composition and Inheritance. Which is generally preferred?",
        "answer": "Inheritance is an 'is-a' relationship (tight coupling); Composition is a 'has-a' relationship (loose coupling via holding references). Modern design prefers Composition over Inheritance for flexibility."
    }
]

