"""
Dynamic Online Question Fetcher & Integration Service.
Directly fetches live technical questions from public APIs and dynamic technical repositories,
maps them to the system's 10 core computer science topics, formats answers & explanations,
and ensures deep coverage across Beginner, Intermediate, and Advanced difficulty tiers.
"""
import urllib.request
import urllib.parse
import json
import html
import hashlib
import random
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple

from config.settings import TOPICS, DIFFICULTY_LEVELS, QUESTION_TYPES, JOB_ROLES
from database.collections import get_questions_collection

logger = logging.getLogger(__name__)

# Non-technical trivia keywords to exclude (e.g. company founding years, stock symbols, pop-culture)
NON_TECHNICAL_EXCLUSIONS = [
    "who founded", "which company was established", "when did", "how much storage did it provide",
    "ceo of", "stock symbol", "headquartered in", "who created the character", "mascot", "worth of",
    "stands for what", "stand for what", "what does hp stand for", "what does ibm stand for",
    "what does amd stand for", "what does intel stand for", "founded by", "co-founded", "created in",
    "released in", "invented by", "which year was", "in what year", "who is considered the father",
    "video game", "nintendo", "atari", "sega", "playstation", "xbox", "character", "actor", "actress",
    "movie", "film", "novel", "author of", "headquarters of", "net worth", "acronym for what",
    "who coined", "what year did", "what was the first"
]

TOPIC_KEYWORD_RULES = [
    ("Python Programming", ["python", "pep", "tuple", "dict", "list comprehension", "generator", "decorator", "gil", "pypy", "cpython", "lambda", "asyncio", "dunder", "magic method", "yield", "metaclass"]),
    ("Data Structures and Algorithms", ["algorithm", "sorting", "sort", "search", "binary tree", "bst", "linked list", "stack", "queue", "heap", "graph", "hash table", "hash map", "big-o", "time complexity", "space complexity", "dijkstra", "traversal", "recursion", "dynamic programming", "knapsack", "two pointer", "sliding window", "trie"]),
    ("Object-Oriented Programming", ["object-oriented", "oop", "polymorphism", "inheritance", "encapsulation", "abstraction", "class", "constructor", "destructor", "interface", "solid", "design pattern", "singleton", "factory method", "instantiation", "liskov", "dependency inversion", "coupling", "cohesion"]),
    ("Database Management Systems", ["database", "dbms", "acid", "relational", "normalization", "1nf", "2nf", "3nf", "bcnf", "b-tree", "b+ tree", "transaction", "isolation", "foreign key", "primary key", "concurrency control", "deadlock in dbms", "wal", "write-ahead"]),
    ("SQL and MongoDB", ["sql", "select", "join", "inner join", "outer join", "mongodb", "nosql", "bson", "aggregation", "collection", "document store", "query", "group by", "having", "dense_rank", "window function", "subquery", "crud", "sharding", "replica set"]),
    ("Operating Systems", ["operating system", "os", "linux", "unix", "windows", "kernel", "thread", "process", "deadlock", "coffman", "paging", "virtual memory", "page fault", "thrashing", "semaphore", "mutex", "cpu scheduling", "context switch", "file system", "bios", "boot", "fork", "cfs"]),
    ("Computer Networks", ["network", "tcp", "udp", "ip address", "ipv4", "ipv6", "dns", "http", "https", "tls", "ssl", "osi model", "packet", "router", "switch", "port", "firewall", "handshake", "ethernet", "wifi", "socket", "gateway", "ftp", "smtp", "rest api", "cidr", "bgp"]),
    ("Machine Learning", ["machine learning", "ml", "neural network", "deep learning", "supervised", "unsupervised", "decision tree", "random forest", "svm", "overfitting", "underfitting", "bias-variance", "loss function", "gradient descent", "backpropagation", "clustering", "knn", "nlp", "llm", "confusion matrix", "precision", "recall", "f1-score"]),
    ("Data Analysis", ["data analysis", "data science", "pandas", "numpy", "matplotlib", "seaborn", "outlier", "iqr", "z-score", "imputation", "median", "standard deviation", "variance", "histogram", "pivot table", "correlation", "causation", "hypothesis testing", "dataframe"]),
    ("Problem-Solving Skills", ["problem-solving", "troubleshooting", "debugging", "bug", "architecture", "system design", "scalability", "bottleneck", "load balancer", "caching", "edge case", "optimization", "exception handling", "504 gateway", "rate limiting", "token bucket"]),
]

# Comprehensive Technical Question Bank ensuring rich questions across all 10 topics and all 3 difficulty tiers
DYNAMIC_TECHNICAL_BANK = [
    # ==================== BEGINNER TIER ====================
    {
        "question_id": "TECH-BEG-PY01",
        "topic": "Python Programming",
        "difficulty": "Beginner",
        "question_type": "Conceptual",
        "job_role": "Software Engineer",
        "question": "What is the primary difference between a list and a tuple in Python, and when would you choose a tuple over a list?",
        "answer": "Lists are mutable (elements can be added, removed, or modified in place), while tuples are immutable (cannot be altered once defined). Choose tuples when data should be protected from accidental mutation, when used as dictionary keys (tuples are hashable if elements are immutable), or for slight performance/memory gains.",
        "explanation": "Tuples have fixed memory allocated at creation time and are stored directly in CPython's compact struct. Lists over-allocate capacity to allow O(1) amortized appends.",
        "tags": ["python", "mutability", "lists", "tuples"]
    },
    {
        "question_id": "TECH-BEG-PY02",
        "topic": "Python Programming",
        "difficulty": "Beginner",
        "question_type": "Programming",
        "job_role": "Software Engineer",
        "question": "Why is using a mutable default argument (like `def func(x=[])`) considered an anti-pattern in Python?",
        "answer": "Default arguments are evaluated once when the function is defined, not each time the function is called. If you mutate the default list inside the function, that mutation persists across all subsequent invocations.\n\nIdiomatic fix:\n```python\ndef func(x=None):\n    if x is None:\n        x = []\n    x.append(1)\n    return x\n```",
        "explanation": "Functions in Python are first-class objects, and their default arguments are stored in the function object's `__defaults__` tuple, which is shared across calls.",
        "tags": ["python", "defaults", "anti-pattern", "mutability"]
    },
    {
        "question_id": "TECH-BEG-DSA01",
        "topic": "Data Structures and Algorithms",
        "difficulty": "Beginner",
        "question_type": "Conceptual",
        "job_role": "Software Engineer",
        "question": "Compare the access and insertion characteristics of an Array versus a Singly Linked List.",
        "answer": "Arrays allow O(1) random access by index due to contiguous memory allocation, but inserting in the middle requires O(N) element shifts. Singly Linked Lists have O(N) access time (must traverse sequentially from head), but allow O(1) insertion at the head or when a pointer to the target node is already known.",
        "explanation": "Arrays benefit heavily from CPU cache locality. Linked list nodes are scattered across the heap, incurring cache misses during traversal.",
        "tags": ["dsa", "arrays", "linked-lists", "big-o"]
    },
    {
        "question_id": "TECH-BEG-DSA02",
        "topic": "Data Structures and Algorithms",
        "difficulty": "Beginner",
        "question_type": "Conceptual",
        "job_role": "Software Engineer",
        "question": "What is the difference between a Stack and a Queue in terms of principle and primary operations?",
        "answer": "A Stack operates on LIFO (Last In, First Out) with operations `push` and `pop`. A Queue operates on FIFO (First In, First Out) with operations `enqueue` and `dequeue`. Both achieve O(1) time complexity for boundary additions and removals.",
        "explanation": "Stacks are used in call stacks, expression evaluation, and undo buffers. Queues are used in task scheduling, BFS graph traversal, and printer buffers.",
        "tags": ["dsa", "stack", "queue", "lifo", "fifo"]
    },
    {
        "question_id": "TECH-BEG-OOP01",
        "topic": "Object-Oriented Programming",
        "difficulty": "Beginner",
        "question_type": "Conceptual",
        "job_role": "Software Engineer",
        "question": "What is Encapsulation in OOP, and how is it implemented in modern programming languages?",
        "answer": "Encapsulation is the practice of bundling data (attributes) and methods that operate on that data into a single class while restricting direct access to internal components (data hiding). It is implemented using access modifiers like private, protected, and public, or via getters/setters and property decorators in Python (`@property`).",
        "explanation": "Encapsulation protects class invariants and prevents external code from mutating internal state into an inconsistent or invalid configuration.",
        "tags": ["oop", "encapsulation", "data-hiding"]
    },
    {
        "question_id": "TECH-BEG-OOP02",
        "topic": "Object-Oriented Programming",
        "difficulty": "Beginner",
        "question_type": "Conceptual",
        "job_role": "Software Engineer",
        "question": "Explain compile-time polymorphism versus runtime polymorphism with practical examples.",
        "answer": "Compile-time polymorphism (Static Binding) occurs via Method Overloading or Operator Overloading, resolved at compile/definition time. Runtime polymorphism (Dynamic Binding) occurs via Method Overriding in inheritance hierarchies, resolved dynamically using virtual method tables (vtable).",
        "explanation": "Runtime polymorphism enables writing generic algorithms that operate on abstract base classes or interfaces while invoking specialized child implementations.",
        "tags": ["oop", "polymorphism", "overloading", "overriding"]
    },
    {
        "question_id": "TECH-BEG-DBMS01",
        "topic": "Database Management Systems",
        "difficulty": "Beginner",
        "question_type": "Conceptual",
        "job_role": "Backend Developer",
        "question": "What is a Primary Key and how does it differ from a Unique Key constraint?",
        "answer": "A Primary Key uniquely identifies each row in a database table and strictly forbids NULL values (each table can have only one Primary Key). A Unique Key also ensures distinct values in a column, but permits one or more NULL values depending on the DBMS, and a single table can define multiple Unique Keys.",
        "explanation": "In most relational engines (e.g. MySQL InnoDB), the Primary Key automatically defines the table's clustered index.",
        "tags": ["dbms", "primary-key", "unique-key", "constraints"]
    },
    {
        "question_id": "TECH-BEG-DBMS02",
        "topic": "Database Management Systems",
        "difficulty": "Beginner",
        "question_type": "Conceptual",
        "job_role": "Backend Developer",
        "question": "Explain the difference between First Normal Form (1NF), Second Normal Form (2NF), and Third Normal Form (3NF).",
        "answer": "1NF requires atomic column values (no repeating groups/arrays). 2NF requires 1NF plus all non-key attributes fully functionally dependent on the entire primary key (no partial dependencies). 3NF requires 2NF plus no transitive dependencies (non-key attributes dependent on other non-key attributes).",
        "explanation": "Normalization minimizes data redundancy, prevents insertion/update/deletion anomalies, and ensures data integrity.",
        "tags": ["dbms", "normalization", "1nf", "2nf", "3nf"]
    },
    {
        "question_id": "TECH-BEG-SQL01",
        "topic": "SQL and MongoDB",
        "difficulty": "Beginner",
        "question_type": "Programming",
        "job_role": "Data Analyst",
        "question": "Write a standard SQL query to retrieve the names and salaries of employees earning more than 60,000, ordered from highest to lowest salary.",
        "answer": "```sql\nSELECT name, salary\nFROM employees\nWHERE salary > 60000\nORDER BY salary DESC;\n```",
        "explanation": "The `WHERE` clause filters rows before projection, and `ORDER BY salary DESC` sorts records in descending order.",
        "tags": ["sql", "filtering", "order-by", "queries"]
    },
    {
        "question_id": "TECH-BEG-SQL02",
        "topic": "SQL and MongoDB",
        "difficulty": "Beginner",
        "question_type": "Conceptual",
        "job_role": "Backend Developer",
        "question": "Compare relational database tables with MongoDB document collections. What corresponds to a row and a column?",
        "answer": "In relational databases, data is organized into Tables, Rows (records/tuples), and Columns (attributes). In MongoDB, data is organized into Collections, Documents (BSON objects), and Fields (key-value pairs). MongoDB documents are schema-flexible, allowing embedded nested documents and arrays.",
        "explanation": "MongoDB eliminates relational join overhead for nested hierarchical data by co-locating related entities within a single document.",
        "tags": ["sql", "mongodb", "schema", "nosql"]
    },
    {
        "question_id": "TECH-BEG-OS01",
        "topic": "Operating Systems",
        "difficulty": "Beginner",
        "question_type": "Conceptual",
        "job_role": "Software Engineer",
        "question": "What is the function of the Operating System Kernel, and how does user mode differ from kernel mode?",
        "answer": "The Kernel is the core program of an OS that manages hardware resources (CPU, RAM, disk, I/O devices). User Mode is an unprivileged execution mode for application programs where direct hardware access is blocked. Kernel Mode is a privileged execution mode where code has unrestricted access to hardware and all memory space. Switching occurs via System Calls.",
        "explanation": "Dual-mode operation prevents rogue application code from corrupting system memory or monopolizing hardware.",
        "tags": ["os", "kernel", "user-mode", "system-calls"]
    },
    {
        "question_id": "TECH-BEG-OS02",
        "topic": "Operating Systems",
        "difficulty": "Beginner",
        "question_type": "Conceptual",
        "job_role": "Software Engineer",
        "question": "What is the primary difference between a Process and a Thread in operating systems?",
        "answer": "A Process is an independent executing program with its own dedicated virtual address space, memory, file descriptors, and security context. A Thread is the smallest unit of execution within a process; multiple threads of the same process share the same code, data, and heap memory, but maintain independent stacks and register sets.",
        "explanation": "Context switching between threads is faster than between processes because memory page tables do not need to be flushed.",
        "tags": ["os", "process", "thread", "concurrency"]
    },
    {
        "question_id": "TECH-BEG-NET01",
        "topic": "Computer Networks",
        "difficulty": "Beginner",
        "question_type": "Conceptual",
        "job_role": "Software Engineer",
        "question": "What are common HTTP status code ranges and what do 200, 400, 401, 404, and 500 indicate?",
        "answer": "1xx = Informational, 2xx = Success, 3xx = Redirection, 4xx = Client Errors, 5xx = Server Errors.\n- 200 OK: Request succeeded.\n- 400 Bad Request: Malformed syntax.\n- 401 Unauthorized: Authentication required.\n- 404 Not Found: Resource does not exist.\n- 500 Internal Server Error: Unhandled backend exception.",
        "explanation": "Status codes provide standardized semantic contracts between clients (browsers, apps) and HTTP web servers.",
        "tags": ["networks", "http", "status-codes", "web"]
    },
    {
        "question_id": "TECH-BEG-NET02",
        "topic": "Computer Networks",
        "difficulty": "Beginner",
        "question_type": "Conceptual",
        "job_role": "Software Engineer",
        "question": "Compare TCP and UDP at the transport layer. What trade-offs do they represent?",
        "answer": "TCP is connection-oriented, reliable (acknowledgments, sequence numbers, retransmission), guarantees in-order delivery, and provides congestion control at the cost of higher latency. UDP is connectionless, unreliable (fire-and-forget), has minimal header overhead (8 bytes vs 20 bytes), and delivers packets with lower latency, making it ideal for DNS, VoIP, and gaming.",
        "explanation": "TCP sacrifices raw throughput for data integrity, whereas UDP prioritizes timeliness over packet completeness.",
        "tags": ["networks", "tcp", "udp", "transport-layer"]
    },
    {
        "question_id": "TECH-BEG-ML01",
        "topic": "Machine Learning",
        "difficulty": "Beginner",
        "question_type": "Conceptual",
        "job_role": "Data Scientist",
        "question": "What is the difference between Supervised Learning, Unsupervised Learning, and Reinforcement Learning?",
        "answer": "Supervised Learning trains on labeled data (input-output pairs) to predict known outcomes (e.g. classification, regression). Unsupervised Learning finds intrinsic patterns, groupings, or distributions in unlabeled data (e.g. k-means clustering, PCA). Reinforcement Learning trains an agent to make sequential decisions via actions, states, and trial-and-error reward signals.",
        "explanation": "Supervised requires ground truth labels; Unsupervised discovers hidden structure; Reinforcement learns policy via reward maximization.",
        "tags": ["ml", "supervised", "unsupervised", "reinforcement"]
    },
    {
        "question_id": "TECH-BEG-ML02",
        "topic": "Machine Learning",
        "difficulty": "Beginner",
        "question_type": "Conceptual",
        "job_role": "Machine Learning Engineer",
        "question": "What is Overfitting in machine learning models and how can it be detected and prevented?",
        "answer": "Overfitting occurs when a model learns noise and specific details of the training data rather than generalizing to unseen data (characterized by very low training error but high validation/test error). Prevention: cross-validation, pruning tree depth, L1/L2 regularization, dropout, gathering more training data, or simplifying model complexity.",
        "explanation": "Overfitted models have high variance and low bias, capturing spurious correlations that fail to hold in production.",
        "tags": ["ml", "overfitting", "regularization", "generalization"]
    },
    {
        "question_id": "TECH-BEG-DA01",
        "topic": "Data Analysis",
        "difficulty": "Beginner",
        "question_type": "Programming",
        "job_role": "Data Analyst",
        "question": "In Pandas, how do you inspect missing values in a DataFrame and fill them with the column median?",
        "answer": "```python\n# Inspect missing values count:\nprint(df.isnull().sum())\n\n# Impute missing values with column median:\ndf['column_name'] = df['column_name'].fillna(df['column_name'].median())\n```",
        "explanation": "Median imputation preserves numerical central tendency while resisting distortions caused by extreme outliers.",
        "tags": ["data-analysis", "pandas", "missing-values", "imputation"]
    },
    {
        "question_id": "TECH-BEG-DA02",
        "topic": "Data Analysis",
        "difficulty": "Beginner",
        "question_type": "Conceptual",
        "job_role": "Data Analyst",
        "question": "Explain the difference between Correlation and Causation in data analysis with an example.",
        "answer": "Correlation measures statistical association between two variables (as X increases, Y tends to increase). Causation proves that a change in X directly produces a change in Y. Example: Ice cream sales and drowning incidents correlate strongly, but neither causes the other; hot summer weather is the confounding lurking variable driving both.",
        "explanation": "Establishing causality requires controlled A/B testing, instrumental variables, or randomized clinical trials rather than observational correlation alone.",
        "tags": ["data-analysis", "statistics", "correlation", "causation"]
    },
    {
        "question_id": "TECH-BEG-PS01",
        "topic": "Problem-Solving Skills",
        "difficulty": "Beginner",
        "question_type": "Programming",
        "job_role": "Software Engineer",
        "question": "Write a clean function to determine if an input string is a valid Palindrome, ignoring case and non-alphanumeric characters.",
        "answer": "```python\ndef is_palindrome(s: str) -> bool:\n    clean = [c.lower() for c in s if c.isalnum()]\n    return clean == clean[::-1]\n```\nOr using Two Pointers in O(1) space:\n```python\ndef is_palindrome_opt(s: str) -> bool:\n    left, right = 0, len(s) - 1\n    while left < right:\n        while left < right and not s[left].isalnum(): left += 1\n        while left < right and not s[right].isalnum(): right -= 1\n        if s[left].lower() != s[right].lower(): return False\n        left += 1; right -= 1\n    return True\n```",
        "explanation": "The two-pointer technique achieves O(N) time and O(1) extra memory by comparing matching characters inward.",
        "tags": ["problem-solving", "two-pointers", "palindrome", "strings"]
    },
    {
        "question_id": "TECH-BEG-PS02",
        "topic": "Problem-Solving Skills",
        "difficulty": "Beginner",
        "question_type": "Programming",
        "job_role": "Software Engineer",
        "question": "Given an integer array, write an algorithm to find if the array contains any duplicate values in O(N) time.",
        "answer": "```python\ndef contains_duplicate(nums: list[int]) -> bool:\n    seen = set()\n    for num in nums:\n        if num in seen:\n            return True\n        seen.add(num)\n    return False\n```",
        "explanation": "Using a Hash Set allows O(1) average lookup and insertion, enabling single-pass early termination in O(N) time and O(N) space.",
        "tags": ["problem-solving", "hash-set", "duplicates", "arrays"]
    },

    # ==================== INTERMEDIATE TIER ====================
    {
        "question_id": "TECH-INT-PY01",
        "topic": "Python Programming",
        "difficulty": "Intermediate",
        "question_type": "Programming",
        "job_role": "Backend Developer",
        "question": "Explain Python generators and implement a generator function that yields the cumulative moving average of a streaming sequence.",
        "answer": "```python\ndef cumulative_moving_average():\n    total = 0.0\n    count = 0\n    while True:\n        val = yield (total / count if count > 0 else 0.0)\n        if val is not None:\n            total += val\n            count += 1\n```\nGenerators use `yield` to preserve execution context and produce values lazily on demand.",
        "explanation": "Generators operate in O(1) memory space regardless of stream size by maintaining local state across `next()` and `send()` calls.",
        "tags": ["python", "generators", "yield", "streaming"]
    },
    {
        "question_id": "TECH-INT-PY02",
        "topic": "Python Programming",
        "difficulty": "Intermediate",
        "question_type": "Programming",
        "job_role": "Software Engineer",
        "question": "Write a retry decorator in Python that catches specified exceptions and retries a function up to N times with exponential backoff.",
        "answer": "```python\nimport time\nfrom functools import wraps\n\ndef retry_backoff(max_retries=3, delay=1.0, backoff=2.0, exceptions=(Exception,)):\n    def decorator(func):\n        @wraps(func)\n        def wrapper(*args, **kwargs):\n            current_delay = delay\n            for attempt in range(1, max_retries + 1):\n                try:\n                    return func(*args, **kwargs)\n                except exceptions as e:\n                    if attempt == max_retries:\n                        raise\n                    time.sleep(current_delay)\n                    current_delay *= backoff\n        return wrapper\n    return decorator\n```",
        "explanation": "Decorators with arguments require a 3-tier wrapper closure. `@wraps(func)` preserves original docstrings, signatures, and module metadata.",
        "tags": ["python", "decorators", "backoff", "resilience"]
    },
    {
        "question_id": "TECH-INT-DSA01",
        "topic": "Data Structures and Algorithms",
        "difficulty": "Intermediate",
        "question_type": "Programming",
        "job_role": "Software Engineer",
        "question": "Given the root of a Binary Search Tree (BST), explain how to validate if it is a valid BST (every node in left subtree is strictly less, and right subtree strictly greater).",
        "answer": "Use recursive bounds checking passing allowable (min_val, max_val) range:\n```python\ndef is_valid_bst(root, min_val=float('-inf'), max_val=float('inf')):\n    if not root:\n        return True\n    if not (min_val < root.val < max_val):\n        return False\n    return (is_valid_bst(root.left, min_val, root.val) and\n            is_valid_bst(root.right, root.val, max_val))\n```",
        "explanation": "Checking only immediate children (`node.left < node` and `node.right > node`) is insufficient because descendants must satisfy global bounds. Traversing In-order and verifying strictly increasing values is an alternative O(N) approach.",
        "tags": ["dsa", "bst", "trees", "recursion"]
    },
    {
        "question_id": "TECH-INT-DSA02",
        "topic": "Data Structures and Algorithms",
        "difficulty": "Intermediate",
        "question_type": "Programming",
        "job_role": "Software Engineer",
        "question": "Explain how to detect and remove a cycle in a singly linked list in O(N) time and O(1) space.",
        "answer": "1. Use Floyd's Tortoise and Hare algorithm: move `slow` by 1 step and `fast` by 2 steps until they meet.\n2. Reset `slow` to `head`. Move both `slow` and `fast` 1 step at a time until `slow.next == fast.next`.\n3. The node `fast.next` is the start of the cycle; break it by setting `fast.next = None`.",
        "explanation": "The distance traveled by slow and fast satisfies `2 * (L + k) = L + k + n*C`, where L is distance to cycle start, k is offset inside cycle, and C is cycle circumference.",
        "tags": ["dsa", "linked-list", "floyd-cycle", "pointers"]
    },
    {
        "question_id": "TECH-INT-OOP01",
        "topic": "Object-Oriented Programming",
        "difficulty": "Intermediate",
        "question_type": "Conceptual",
        "job_role": "Software Engineer",
        "question": "Explain the Open/Closed Principle (OCP) and demonstrate how it is achieved using polymorphism or strategy interfaces.",
        "answer": "The Open/Closed Principle states that software entities (classes, modules, functions) should be open for extension, but closed for modification. Instead of modifying an existing class with conditional if/elif statements to support new payment methods, define an abstract `PaymentStrategy` interface with a `pay()` method. New payment types extend the interface without altering existing code.",
        "explanation": "Adhering to OCP prevents regression bugs in tested production code when adding new business requirements.",
        "tags": ["oop", "solid", "open-closed", "design-patterns"]
    },
    {
        "question_id": "TECH-INT-OOP02",
        "topic": "Object-Oriented Programming",
        "difficulty": "Intermediate",
        "question_type": "Conceptual",
        "job_role": "Software Engineer",
        "question": "What is the Dependency Inversion Principle (DIP) in SOLID, and how does Inversion of Control (IoC) relate to it?",
        "answer": "DIP states: 1. High-level modules should not depend on low-level modules; both should depend on abstractions. 2. Abstractions should not depend on details; details should depend on abstractions. Inversion of Control is the architectural practice where the framework or container injects dependencies at runtime rather than classes instantiating them directly.",
        "explanation": "DIP facilitates unit testing with mock implementations and decouples business logic from external database/API implementations.",
        "tags": ["oop", "solid", "dip", "dependency-injection"]
    },
    {
        "question_id": "TECH-INT-DBMS01",
        "topic": "Database Management Systems",
        "difficulty": "Intermediate",
        "question_type": "Conceptual",
        "job_role": "Backend Developer",
        "question": "Explain the difference between Optimistic Concurrency Control and Pessimistic Concurrency Control in relational databases.",
        "answer": "Pessimistic Concurrency Control locks rows (e.g. `SELECT FOR UPDATE`) assuming conflicts will happen, preventing other transactions from modifying data until the lock releases. Optimistic Concurrency Control does not lock records during read; instead, it uses version numbers or timestamps, verifying at commit time that no concurrent transaction modified the row (rolling back if a conflict occurred).",
        "explanation": "Pessimistic locking is best for high-contention write workloads; Optimistic concurrency is best for read-heavy workloads with infrequent collisions.",
        "tags": ["dbms", "concurrency", "locking", "transactions"]
    },
    {
        "question_id": "TECH-INT-DBMS02",
        "topic": "Database Management Systems",
        "difficulty": "Intermediate",
        "question_type": "Conceptual",
        "job_role": "Backend Developer",
        "question": "Why do relational databases use B+ Trees rather than standard Binary Search Trees or Hash Tables for disk storage indexes?",
        "answer": "B+ Trees have high fan-out (hundreds of child pointers per node), which minimizes disk I/O seek operations (tree height is typically 3–4 for millions of rows). Furthermore, all leaf nodes in a B+ Tree are sequentially linked in a doubly linked list, enabling O(log N) point lookups as well as ultra-fast sequential range scans.",
        "explanation": "Disk block reads fetch 4KB–16KB per page. B+ Tree nodes fit perfectly into disk blocks, whereas BSTs cause individual disk seeks for every node traversal.",
        "tags": ["dbms", "b-plus-tree", "indexing", "disk-io"]
    },
    {
        "question_id": "TECH-INT-SQL01",
        "topic": "SQL and MongoDB",
        "difficulty": "Intermediate",
        "question_type": "Programming",
        "job_role": "Backend Developer",
        "question": "Write an SQL query using Window Functions to find the top 3 highest-paid employees in each department.",
        "answer": "```sql\nWITH RankedSalaries AS (\n    SELECT \n        employee_id, \n        name, \n        department_id, \n        salary,\n        DENSE_RANK() OVER (PARTITION BY department_id ORDER BY salary DESC) as rank_num\n    FROM employees\n)\nSELECT employee_id, name, department_id, salary\nFROM RankedSalaries\nWHERE rank_num <= 3;\n```",
        "explanation": "`PARTITION BY department_id` creates independent windows per department; `DENSE_RANK()` assigns ranks without skipping numbers on tied salaries.",
        "tags": ["sql", "window-functions", "dense-rank", "partition-by"]
    },
    {
        "question_id": "TECH-INT-SQL02",
        "topic": "SQL and MongoDB",
        "difficulty": "Intermediate",
        "question_type": "Programming",
        "job_role": "Backend Developer",
        "question": "Write a MongoDB Aggregation Pipeline to compute the average order amount and total revenue grouped by customer tier for completed orders.",
        "answer": "```javascript\ndb.orders.aggregate([\n  { $match: { status: \"completed\" } },\n  {\n    $group: {\n      _id: \"$customer_tier\",\n      total_revenue: { $sum: \"$amount\" },\n      avg_order_amount: { $avg: \"$amount\" },\n      order_count: { $sum: 1 }\n    }\n  },\n  { $sort: { total_revenue: -1 } }\n])\n```",
        "explanation": "Aggregation pipelines process documents sequentially in memory-efficient stages: filtering early with `$match` reduces data volume prior to `$group`.",
        "tags": ["mongodb", "aggregation", "grouping", "pipelines"]
    },
    {
        "question_id": "TECH-INT-OS01",
        "topic": "Operating Systems",
        "difficulty": "Intermediate",
        "question_type": "Conceptual",
        "job_role": "Software Engineer",
        "question": "What is the difference between a Mutex and a Counting Semaphore? Can a thread other than the one that locked a Mutex unlock it?",
        "answer": "A Mutex (Mutual Exclusion) has ownership semantics: only the specific thread that acquired the lock is permitted to unlock it (binary lock). A Counting Semaphore is a signaling mechanism maintaining an integer counter (permitting up to N concurrent threads), and any thread can signal/release it.",
        "explanation": "Using a Mutex prevents priority inversion issues through protocols like priority inheritance, whereas semaphores coordinate producer-consumer buffer capacities.",
        "tags": ["os", "concurrency", "mutex", "semaphore", "synchronization"]
    },
    {
        "question_id": "TECH-INT-OS02",
        "topic": "Operating Systems",
        "difficulty": "Intermediate",
        "question_type": "Conceptual",
        "job_role": "Software Engineer",
        "question": "Explain Demand Paging and what sequence of events occurs when a Page Fault is raised by the CPU Memory Management Unit (MMU).",
        "answer": "1. MMU detects the valid bit in the page table entry is 0 and triggers a page fault hardware trap.\n2. OS kernel traps to page fault handler, saving execution context.\n3. OS checks if the access is valid (if invalid address, SIGSEGV). If valid, locates an empty physical frame (or evicts a page using LRU algorithm).\n4. Issues disk I/O to load the requested page from swap/backing store into RAM frame.\n5. Updates page table entry, sets valid bit = 1, and restarts the faulted instruction.",
        "explanation": "Demand paging allows running applications whose virtual memory size exceeds physical RAM capacity.",
        "tags": ["os", "virtual-memory", "page-fault", "mmu"]
    },
    {
        "question_id": "TECH-INT-NET01",
        "topic": "Computer Networks",
        "difficulty": "Intermediate",
        "question_type": "Scenario-Based",
        "job_role": "Software Engineer",
        "question": "Walk through the TCP 3-way handshake process. What packets are exchanged, and what happens if the final ACK is dropped?",
        "answer": "1. Client sends `SYN` (synchronize seq=x).\n2. Server responds with `SYN-ACK` (seq=y, ack=x+1).\n3. Client sends `ACK` (ack=y+1).\nIf the final ACK is dropped, the server will retransmit the SYN-ACK after a timer timeout. When the client attempts to send initial application data, the server recognizes the ACK and transitions to ESTABLISHED.",
        "explanation": "The 3-way handshake prevents duplicate old connection requests from establishing false states and synchronizes initial sequence numbers.",
        "tags": ["networks", "tcp", "handshake", "transport-layer"]
    },
    {
        "question_id": "TECH-INT-NET02",
        "topic": "Computer Networks",
        "difficulty": "Intermediate",
        "question_type": "Conceptual",
        "job_role": "Software Engineer",
        "question": "Describe the complete DNS resolution lifecycle when a user types a new domain URL into their browser for the first time.",
        "answer": "1. Browser checks local cache -> OS checks resolver cache and `/etc/hosts`.\n2. Queries Recursive Resolver (ISP or 8.8.8.8).\n3. Recursive Resolver queries DNS Root Name Server (`.`), receiving TLD server IP (`.com`).\n4. Queries TLD Name Server (`.com`), receiving Authoritative Name Server IP.\n5. Queries Authoritative Name Server, receiving the A or AAAA record IP address.\n6. Resolver caches answer with TTL and returns IP to browser.",
        "explanation": "Hierarchical DNS resolution delegates authority across decentralized zones, ensuring resilience and scalable namespace management.",
        "tags": ["networks", "dns", "web", "resolution"]
    },
    {
        "question_id": "TECH-INT-ML01",
        "topic": "Machine Learning",
        "difficulty": "Intermediate",
        "question_type": "Conceptual",
        "job_role": "Machine Learning Engineer",
        "question": "Explain the difference between Bagging (e.g. Random Forest) and Boosting (e.g. Gradient Boosting / XGBoost) ensemble methods.",
        "answer": "Bagging (Bootstrap Aggregating) trains multiple base learners in parallel on independent bootstrap samples of the data and averages predictions to reduce Variance. Boosting trains base learners sequentially, where each new model focuses on correcting the errors/residuals of the previous models, primarily reducing Bias.",
        "explanation": "Random Forests reduce overfitting through decorrelated parallel trees. Gradient Boosting builds additive trees minimizing a differentiable loss function.",
        "tags": ["ml", "bagging", "boosting", "random-forest", "gradient-boosting"]
    },
    {
        "question_id": "TECH-INT-ML02",
        "topic": "Machine Learning",
        "difficulty": "Intermediate",
        "question_type": "Conceptual",
        "job_role": "Data Scientist",
        "question": "Why is Accuracy an unreliable metric for imbalanced datasets (e.g., 99% negative, 1% fraud), and what metrics should be used instead?",
        "answer": "A naive model predicting 'no fraud' 100% of the time achieves 99% accuracy while failing completely at its objective. For imbalanced classes, evaluate Precision (positive predictive value), Recall (sensitivity / fraud detection rate), F1-Score (harmonic mean of precision and recall), and PR-AUC (Precision-Recall Area Under Curve).",
        "explanation": "PR-AUC focuses on the minority positive class without being inflated by overwhelming true negatives.",
        "tags": ["ml", "evaluation", "precision", "recall", "imbalance"]
    },
    {
        "question_id": "TECH-INT-DA01",
        "topic": "Data Analysis",
        "difficulty": "Intermediate",
        "question_type": "Conceptual",
        "job_role": "Data Analyst",
        "question": "Explain Simpson's Paradox in statistical data analysis with a practical scenario.",
        "answer": "Simpson's Paradox occurs when a statistical trend appears in several different groups of data, but completely disappears or reverses when the groups are combined together. Example: Hospital A has higher overall mortality than Hospital B, but Hospital A accepts significantly more critical-care emergency patients. When controlling for patient severity, Hospital A has better survival rates in every subgroup.",
        "explanation": "Confounding lurking variables distort aggregate relationships. Always segment data across relevant dimensions to prevent erroneous conclusions.",
        "tags": ["data-analysis", "statistics", "simpsons-paradox", "confounding"]
    },
    {
        "question_id": "TECH-INT-DA02",
        "topic": "Data Analysis",
        "difficulty": "Intermediate",
        "question_type": "Programming",
        "job_role": "Data Analyst",
        "question": "How do you detect and filter statistical outliers in a Pandas Series using the Interquartile Range (IQR) method?",
        "answer": "```python\nQ1 = df['value'].quantile(0.25)\nQ3 = df['value'].quantile(0.75)\nIQR = Q3 - Q1\nlower_bound = Q1 - 1.5 * IQR\nupper_bound = Q3 + 1.5 * IQR\n\n# Filter out outliers:\nclean_df = df[(df['value'] >= lower_bound) & (df['value'] <= upper_bound)]\n```",
        "explanation": "The IQR rule identifies values lying beyond 1.5 times the inner 50% spread, providing non-parametric outlier resistance unaffected by extreme skews.",
        "tags": ["data-analysis", "pandas", "iqr", "outliers"]
    },
    {
        "question_id": "TECH-INT-PS01",
        "topic": "Problem-Solving Skills",
        "difficulty": "Intermediate",
        "question_type": "Programming",
        "job_role": "Software Engineer",
        "question": "Given an array of integers, design an algorithm to find all unique triplets `[nums[i], nums[j], nums[k]]` such that `nums[i] + nums[j] + nums[k] == 0` in O(N^2) time.",
        "answer": "1. Sort the array in O(N log N).\n2. Iterate through with pointer `i`. If `nums[i] > 0`, break (no three positive numbers sum to 0). Skip duplicates `nums[i] == nums[i-1]`.\n3. For each `i`, use Two Pointers: `left = i + 1`, `right = n - 1`.\n4. Check `sum = nums[i] + nums[left] + nums[right]`. If sum == 0, record triplet, advance left and right skipping duplicate elements. If sum < 0, `left += 1`. If sum > 0, `right -= 1`.",
        "explanation": "Sorting transforms the problem into N two-pointer Two-Sum instances, reducing the brute-force O(N^3) complexity down to O(N^2) time with O(1) space.",
        "tags": ["problem-solving", "three-sum", "two-pointers", "sorting"]
    },
    {
        "question_id": "TECH-INT-PS02",
        "topic": "Problem-Solving Skills",
        "difficulty": "Intermediate",
        "question_type": "Programming",
        "job_role": "Software Engineer",
        "question": "Given an array of positive integers and target sum S, find the minimal length of a contiguous subarray whose sum is greater than or equal to S using the Sliding Window technique.",
        "answer": "```python\ndef min_subarray_len(target: int, nums: list[int]) -> int:\n    left = 0\n    current_sum = 0\n    min_len = float('inf')\n    for right in range(len(nums)):\n        current_sum += nums[right]\n        while current_sum >= target:\n            min_len = min(min_len, right - left + 1)\n            current_sum -= nums[left]\n            left += 1\n    return min_len if min_len != float('inf') else 0\n```",
        "explanation": "Both `left` and `right` pointers traverse the array at most once, yielding linear O(N) time complexity and O(1) auxiliary space.",
        "tags": ["problem-solving", "sliding-window", "subarrays", "algorithms"]
    },

    # ==================== ADVANCED TIER ====================
    {
        "question_id": "TECH-ADV-PY01",
        "topic": "Python Programming",
        "difficulty": "Advanced",
        "question_type": "Programming",
        "job_role": "Backend Developer",
        "question": "Explain the difference between `__new__` and `__init__` in Python classes, and write a custom metaclass that enforces all subclass methods have docstrings.",
        "answer": "```python\nclass RequireDocstringsMeta(type):\n    def __new__(cls, name, bases, attrs):\n        for attr_name, attr_val in attrs.items():\n            if callable(attr_val) and not attr_name.startswith('__'):\n                if not getattr(attr_val, '__doc__', None):\n                    raise TypeError(f'Method {attr_name} in {name} must have a docstring.')\n        return super().__new__(cls, name, bases, attrs)\n```\n`__new__` is the static constructor that creates and returns the new instance in memory. `__init__` is the initializer that configures attributes on the already-created instance.",
        "explanation": "Metaclasses intercept class construction at import/definition time, allowing framework authors to enforce architecture contracts.",
        "tags": ["python", "metaclasses", "new-vs-init", "metaprogramming"]
    },
    {
        "question_id": "TECH-ADV-PY02",
        "topic": "Python Programming",
        "difficulty": "Advanced",
        "question_type": "Conceptual",
        "job_role": "Backend Developer",
        "question": "How does CPython's memory management and garbage collection handle circular reference cycles between objects?",
        "answer": "CPython uses reference counting as its primary memory management mechanism (freeing objects immediately when refcount hits 0). For cyclic references (e.g., A references B and B references A), refcounts never hit 0. CPython includes a cyclic garbage collector that tracks container objects across 3 generations (Gen 0, 1, 2) using doubly linked lists, isolating reachable sets and collecting unreferenced cycles via trial decrement.",
        "explanation": "Generational GC exploits the weak generational hypothesis: most allocated objects die very young.",
        "tags": ["python", "garbage-collection", "memory-management", "cpython"]
    },
    {
        "question_id": "TECH-ADV-DSA01",
        "topic": "Data Structures and Algorithms",
        "difficulty": "Advanced",
        "question_type": "Programming",
        "job_role": "Software Engineer",
        "question": "Design an LRU (Least Recently Used) Cache supporting `get(key)` and `put(key, value)` operations in O(1) average time complexity.",
        "answer": "Combine a Hash Map with a Doubly Linked List.\n- The Hash Map maps `key -> ListNode` for O(1) key lookups.\n- The Doubly Linked List maintains access order with dummy `head` (most recent) and `tail` (least recent).\n- `get(key)`: If key in map, move node to head and return value; else return -1.\n- `put(key, val)`: If key exists, update value and move to head. If new key and capacity reached, remove node from tail and delete from map. Insert new node at head.",
        "explanation": "Hash tables provide O(1) access but no ordering; arrays preserve order but have O(N) deletion. A Doubly Linked List allows O(1) node detachment and insertion at boundaries.",
        "tags": ["dsa", "lru-cache", "hash-map", "doubly-linked-list", "system-design"]
    },
    {
        "question_id": "TECH-ADV-DSA02",
        "topic": "Data Structures and Algorithms",
        "difficulty": "Advanced",
        "question_type": "Conceptual",
        "job_role": "Software Engineer",
        "question": "Explain Dijkstra's shortest path algorithm. What are its time complexities with an adjacency matrix versus a min-heap, and why does it fail with negative edge weights?",
        "answer": "Dijkstra's algorithm finds single-source shortest paths in weighted graphs using greedy frontier relaxation. With an adjacency matrix, time complexity is O(V^2). With an adjacency list and binary min-heap / priority queue, it is O((V + E) log V). It fails with negative weights because once a node is marked visited/settled, Dijkstra assumes its optimal distance is finalized, which negative edges can subsequently invalidate.",
        "explanation": "For graphs with negative edge weights, the Bellman-Ford algorithm (O(V * E)) or SPFA must be used instead.",
        "tags": ["dsa", "graphs", "dijkstra", "shortest-path"]
    },
    {
        "question_id": "TECH-ADV-OOP01",
        "topic": "Object-Oriented Programming",
        "difficulty": "Advanced",
        "question_type": "Scenario-Based",
        "job_role": "Software Engineer",
        "question": "Design a distributed Event-Driven Pub/Sub broker using the Observer and Chain of Responsibility design patterns.",
        "answer": "Define a `Topic` observer manager maintaining subscriber callbacks partitioned by message routing keys. Incoming events pass through a Chain of Responsibility for authentication, deduplication, and schema validation before dispatch. Subscribers register handlers conforming to a standard `EventHandler` interface.",
        "explanation": "Decoupling message publishers from consumers via event brokers enables horizontal scaling, independent failure domains, and asynchronous processing.",
        "tags": ["oop", "design-patterns", "observer", "pub-sub", "architecture"]
    },
    {
        "question_id": "TECH-ADV-OOP02",
        "topic": "Object-Oriented Programming",
        "difficulty": "Advanced",
        "question_type": "Programming",
        "job_role": "Software Engineer",
        "question": "Explain the Liskov Substitution Principle (LSP) in depth and describe how the classic Square-Rectangle inheritance problem violates it.",
        "answer": "LSP states that objects of a superclass should be replaceable with objects of a subclass without altering the correctness of the program. A `Square` inheriting from `Rectangle` violates LSP because setting `width` on a Square unexpectedly mutates its `height`, breaking caller invariants that assume modifying width preserves height independently.",
        "explanation": "Subtypes must strengthen preconditions and weaken postconditions, preserving expected behavior contracts.",
        "tags": ["oop", "solid", "lsp", "subtyping"]
    },
    {
        "question_id": "TECH-ADV-DBMS01",
        "topic": "Database Management Systems",
        "difficulty": "Advanced",
        "question_type": "Conceptual",
        "job_role": "Backend Developer",
        "question": "Compare Database Sharding with Read Replicas. What distributed system trade-offs arise when implementing cross-shard transactions?",
        "answer": "Read Replicas distribute read traffic across copies of the database, but all writes must still target the single primary node. Sharding partitions data horizontally across independent database servers by shard key, scaling both reads and writes. Cross-shard transactions require Two-Phase Commit (2PC) or Saga patterns, which incur heavy network latency and risk blocking coordinators during network partitions (CAP theorem).",
        "explanation": "Choosing a high-cardinality, evenly distributed shard key is vital to avoid write hotspots and frequent cross-shard scatter-gather queries.",
        "tags": ["dbms", "sharding", "two-phase-commit", "distributed-systems"]
    },
    {
        "question_id": "TECH-ADV-DBMS02",
        "topic": "Database Management Systems",
        "difficulty": "Advanced",
        "question_type": "Conceptual",
        "job_role": "Backend Developer",
        "question": "How does Write-Ahead Logging (WAL) and the ARIES recovery algorithm guarantee Durability and Atomicity during sudden power failure?",
        "answer": "WAL guarantees that changes are appended sequentially to persistent log files on disk *before* dirty memory pages are flushed to actual table files. The ARIES algorithm executes 3 recovery passes upon reboot: 1. Analysis pass (reconstructs active transactions and dirty pages), 2. Redo pass (repeats history to bring database to failure state), 3. Undo pass (rolls back incomplete active transactions).",
        "explanation": "Sequential disk writes to WAL are orders of magnitude faster than random I/O flushes to disparate table B-tree leaf blocks.",
        "tags": ["dbms", "wal", "aries", "durability", "recovery"]
    },
    {
        "question_id": "TECH-ADV-SQL01",
        "topic": "SQL and MongoDB",
        "difficulty": "Advanced",
        "question_type": "Programming",
        "job_role": "Backend Developer",
        "question": "How does database query planning work? Explain what `EXPLAIN ANALYZE` reveals regarding Index Scans versus Sequential Scans and Hash Joins.",
        "answer": "`EXPLAIN ANALYZE` executes the query and returns the engine's query execution tree with actual runtime metrics: cost estimates, rows returned, and execution time per node. Sequential Scan scans every heap page; Index Scan / Index Only Scan traverses the B-Tree index directly. Nested Loop joins are chosen for small sets with indexed lookups; Hash Join builds an in-memory hash table of the smaller set for large unindexed joins.",
        "explanation": "Inspecting filter predicate selectivity and disk spills helps identify missing compound indexes and prevents unnecessary full-table scans.",
        "tags": ["sql", "explain-plan", "query-optimization", "indexing"]
    },
    {
        "question_id": "TECH-ADV-SQL02",
        "topic": "SQL and MongoDB",
        "difficulty": "Advanced",
        "question_type": "Conceptual",
        "job_role": "Backend Developer",
        "question": "Explain MongoDB Replica Set elections (Raft-like consensus), Write Concerns (`w: 'majority'`), and Read Concerns (`readConcern: 'linearizable'`).",
        "answer": "When a primary heartbeat fails (>10s), secondaries hold an election based on highest oplog optime. Write Concern `w: 'majority'` guarantees the write has been committed to a majority of replica members before returning success, preventing rolled-back writes upon primary failover. `linearizable` read concern checks with a majority of nodes before returning, guaranteeing strict real-time consistency.",
        "explanation": "Configuring write concerns aligns MongoDB with enterprise CP (Consistency/Partition-tolerance) guarantees under network partitions.",
        "tags": ["mongodb", "replica-set", "consensus", "write-concern"]
    },
    {
        "question_id": "TECH-ADV-OS01",
        "topic": "Operating Systems",
        "difficulty": "Advanced",
        "question_type": "Conceptual",
        "job_role": "Software Engineer",
        "question": "State the four Coffman conditions necessary for a Deadlock to occur. How does the Banker's Algorithm ensure deadlock avoidance?",
        "answer": "Coffman Conditions:\n1. Mutual Exclusion (non-shareable resources)\n2. Hold and Wait (processes holding resources request more)\n3. No Preemption (resources cannot be forcibly confiscated)\n4. Circular Wait (closed chain of processes waiting on each other).\nBanker's Algorithm tests for safety before granting resource allocation requests by simulating the maximum possible claims, granting the request only if a safe execution sequence remains.",
        "explanation": "Breaking any one of the four Coffman conditions (e.g. strict global resource acquisition ordering to eliminate circular wait) prevents deadlocks completely.",
        "tags": ["os", "deadlock", "coffman", "bankers-algorithm"]
    },
    {
        "question_id": "TECH-ADV-OS02",
        "topic": "Operating Systems",
        "difficulty": "Advanced",
        "question_type": "Conceptual",
        "job_role": "Software Engineer",
        "question": "How does the Linux Completely Fair Scheduler (CFS) allocate CPU time using Red-Black trees and virtual runtime (`vruntime`)?",
        "answer": "CFS models an 'ideal multi-tasking CPU' where each task receives an equal share of CPU cycles proportional to its nice priority. It tracks `vruntime` (virtual runtime, scaled by task weight). Tasks are stored in a Red-Black tree ordered by `vruntime`. CFS always schedules the leftmost node (task with lowest `vruntime`). When executed, its `vruntime` increases, and it is reinserted into the tree in O(log N) time.",
        "explanation": "CFS eliminates heuristic scheduling ticks in favor of nanosecond-precision virtual runtime tracking.",
        "tags": ["os", "cfs", "linux", "scheduling", "red-black-tree"]
    },
    {
        "question_id": "TECH-ADV-NET01",
        "topic": "Computer Networks",
        "difficulty": "Advanced",
        "question_type": "Conceptual",
        "job_role": "Software Engineer",
        "question": "Walk through the TLS 1.3 cryptographic handshake. How does it achieve 1-RTT connection establishment and Perfect Forward Secrecy (PFS)?",
        "answer": "In TLS 1.3, the client sends `ClientHello` containing supported cipher suites AND speculative Diffie-Hellman key shares in its first message (Client Key Share). The server responds with `ServerHello` (Server Key Share), certificate, and finishes its handshake. Both compute session keys immediately in 1-RTT. Perfect Forward Secrecy is guaranteed via ephemeral Diffie-Hellman (ECDHE): compromising the server's private RSA/ECC identity key later cannot decrypt recorded historical traffic.",
        "explanation": "TLS 1.3 deprecated static RSA key exchange to eliminate man-in-the-middle vulnerability and enforce PFS.",
        "tags": ["networks", "tls", "cryptography", "security", "forward-secrecy"]
    },
    {
        "question_id": "TECH-ADV-NET02",
        "topic": "Computer Networks",
        "difficulty": "Advanced",
        "question_type": "Scenario-Based",
        "job_role": "Software Engineer",
        "question": "Explain Border Gateway Protocol (BGP), Autonomous Systems (AS), and why BGP route hijacking poses major security risks to the Internet.",
        "answer": "BGP is the Path-Vector routing protocol of the global Internet connecting Autonomous Systems (AS networks like ISPs and hyperscalers). BGP peers advertise IP prefix reachability. Because legacy BGP trusts peer route announcements by default without cryptographic verification, a rogue or misconfigured AS can announce more specific prefix routes (e.g. /24 vs /16), hijacking global traffic. RPKI (Resource Public Key Infrastructure) route origin validation mitigates this.",
        "explanation": "Longest prefix match routing rules cause global routers to redirect traffic to the malicious announcer.",
        "tags": ["networks", "bgp", "routing", "security", "internet-architecture"]
    },
    {
        "question_id": "TECH-ADV-ML01",
        "topic": "Machine Learning",
        "difficulty": "Advanced",
        "question_type": "Conceptual",
        "job_role": "Machine Learning Engineer",
        "question": "Explain the vanishing and exploding gradient problem in deep neural networks, and how Batch Normalization and Residual Connections (ResNets) solve it.",
        "answer": "During backpropagation via the chain rule, gradients are multiplied across successive layers. For activation functions with derivatives < 1 (e.g. sigmoid), gradients decay exponentially to 0 (vanishing gradients), halting learning in early layers. For large weights, gradients explode to infinity. Batch Normalization standardizes intermediate activations to zero mean and unit variance. Residual connections add identity shortcut paths ($F(x) + x$), ensuring gradient flow directly back without attenuation ($\\partial(F+x)/\\partial x = \\partial F/\\partial x + 1$).",
        "explanation": "The identity bypass guarantees that deeper networks can always perform at least as well as shallower counterparts.",
        "tags": ["ml", "deep-learning", "resnets", "vanishing-gradient", "optimization"]
    },
    {
        "question_id": "TECH-ADV-ML02",
        "topic": "Machine Learning",
        "difficulty": "Advanced",
        "question_type": "Conceptual",
        "job_role": "Data Scientist",
        "question": "Derive the mathematical intuition behind Cost-Complexity Pruning (minimal alpha pruning) in Decision Trees.",
        "answer": "Unconstrained decision trees grow until every leaf is pure, resulting in high variance and overfitting. Cost-complexity pruning defines a cost function $R_\\alpha(T) = R(T) + \\alpha |T|$, where $R(T)$ is total tree misclassification error, $|T|$ is number of terminal leaves, and $\\alpha \\ge 0$ is the regularization parameter. As $\\alpha$ increases from 0, branches that provide minimal error reduction per leaf penalty are collapsed. The optimal $\\alpha$ is selected via K-fold cross-validation.",
        "explanation": "This formalizes the bias-variance trade-off mathematically, producing robust, generalizable decision trees.",
        "tags": ["ml", "decision-trees", "pruning", "cost-complexity", "scikit-learn"]
    },
    {
        "question_id": "TECH-ADV-DA01",
        "topic": "Data Analysis",
        "difficulty": "Advanced",
        "question_type": "Conceptual",
        "job_role": "Data Analyst",
        "question": "Design an A/B testing framework: define Null Hypothesis, Type I error (alpha), Type II error (beta), Statistical Power, and Sample Size calculation.",
        "answer": "- Null Hypothesis ($H_0$): Treatment variant has no effect compared to control.\n- Type I Error ($\\alpha$, significance level): False Positive (detecting an effect that does not exist; typically 5%).\n- Type II Error ($\\beta$): False Negative (failing to detect a real effect).\n- Statistical Power ($1 - \\beta$): Probability of correctly rejecting false $H_0$ (typically 80%).\n- Sample size is determined before launch based on minimum detectable effect (MDE), baseline conversion rate, and desired power: $N \\propto \\frac{(Z_{\\alpha/2} + Z_\\beta)^2 \\cdot 2\\sigma^2}{\\delta^2}$.",
        "explanation": "Stopping A/B tests early upon seeing statistical significance inflates false positive rates due to peeking bias.",
        "tags": ["data-analysis", "ab-testing", "hypothesis-testing", "sample-size"]
    },
    {
        "question_id": "TECH-ADV-DA02",
        "topic": "Data Analysis",
        "difficulty": "Advanced",
        "question_type": "Conceptual",
        "job_role": "Data Analyst",
        "question": "Compare StandardScaler, MinMaxScaler, and RobustScaler. When is RobustScaler required in preprocessing pipelines?",
        "answer": "StandardScaler centers features to $\\mu=0$ and scales to unit variance $\\sigma=1$; MinMaxScaler bounds values strictly to $[0, 1]$. Both are severely distorted by extreme outliers because mean and min/max ranges are sensitive to extreme points. RobustScaler removes the median and scales the data according to the Interquartile Range (IQR), making it resilient to heavy-tailed distributions and noisy outlier data.",
        "explanation": "Distance-based algorithms (KNN, SVM, K-Means) fail when unscaled outlier features dominate Euclidean space calculations.",
        "tags": ["data-analysis", "preprocessing", "scaling", "robust-scaler"]
    },
    {
        "question_id": "TECH-ADV-PS01",
        "topic": "Problem-Solving Skills",
        "difficulty": "Advanced",
        "question_type": "Scenario-Based",
        "job_role": "Software Engineer",
        "question": "Design a Distributed Rate Limiting system capable of handling 500,000 requests per second across 50 API gateway instances.",
        "answer": "1. Use Redis Cluster with the Sliding Window Counter algorithm or Token Bucket using Lua scripts to ensure atomicity.\n2. Key: `ratelimit:{user_id}:{minute_epoch}`.\n3. Gateway instances maintain a local in-memory token cache (synchronized in batches of 100 every 50ms) to reduce Redis network round-trips from 500k/sec down to 5k/sec.\n4. Return standard HTTP 429 Too Many Requests headers: `Retry-After`, `X-RateLimit-Limit`, `X-RateLimit-Remaining`.",
        "explanation": "Centralized single-node rate limiters fail under 500k RPS due to network I/O saturation. Local token batching combined with atomic Redis counters achieves sub-millisecond enforcement.",
        "tags": ["problem-solving", "system-design", "rate-limiting", "redis", "scalability"]
    },
    {
        "question_id": "TECH-ADV-PS02",
        "topic": "Problem-Solving Skills",
        "difficulty": "Advanced",
        "question_type": "Scenario-Based",
        "job_role": "Software Engineer",
        "question": "Design a highly available distributed URL shortening service (like Bitly) supporting 10 billion URLs with 100:1 read-to-write ratio.",
        "answer": "1. ID Generation: Distributed 64-bit ID generator (Twitter Snowflake) avoiding single-point auto-increment bottlenecks.\n2. Encoding: Convert 64-bit integer into Base62 string (`[0-9a-zA-Z]`), giving 7-character URLs supporting $62^7 \\approx 3.5$ trillion unique links.\n3. Storage: NoSQL key-value store (MongoDB / DynamoDB) partitioned on short_key with secondary index on user_id.\n4. Caching: Redis cluster caching top 20% most accessed URLs (Pareto 80/20 rule) in memory for O(1) redirection with HTTP 302 Found.\n5. Global CDN edge routing for cached redirections.",
        "explanation": "HTTP 302 preserves click analytics tracking on the gateway, whereas HTTP 301 permanently caches in user browsers, bypassing analytics.",
        "tags": ["problem-solving", "system-design", "url-shortener", "base62", "caching"]
    }
]


def classify_question_topic(question_text: str, answer_text: str = "") -> str:
    """Classifies a question into one of the 10 computer science topics using keyword matching."""
    combined = (question_text + " " + answer_text).lower()
    
    for topic, keywords in TOPIC_KEYWORD_RULES:
        for kw in keywords:
            if kw in combined:
                return topic

    if any(k in combined for k in ["code", "syntax", "variable", "string", "int", "boolean"]):
        return "Python Programming"
    elif any(k in combined for k in ["web", "url", "domain", "server", "client"]):
        return "Computer Networks"
    elif any(k in combined for k in ["storage", "disk", "memory", "ram", "hardware"]):
        return "Operating Systems"

    return "Problem-Solving Skills"


def map_api_difficulty(raw_difficulty: str) -> str:
    """Maps API difficulty levels to Beginner, Intermediate, Advanced."""
    diff_lower = str(raw_difficulty).lower()
    if diff_lower == "hard":
        return "Advanced"
    elif diff_lower == "medium":
        return "Intermediate"
    return "Beginner"


def is_valid_technical_question(q_text: str) -> bool:
    """Filters out non-technical general trivia like company founders, years, acquisitions."""
    q_lower = q_text.lower()
    for exc in NON_TECHNICAL_EXCLUSIONS:
        if exc in q_lower:
            return False

    # Question must match genuine computer science technical content
    has_tech_kw = False
    for _, keywords in TOPIC_KEYWORD_RULES:
        if any(kw in q_lower for kw in keywords):
            has_tech_kw = True
            break
            
    if not has_tech_kw:
        generic_tech = [
            "code", "syntax", "variable", "string", "int", "boolean", "loop", "function", 
            "array", "memory", "cpu", "server", "compiler", "runtime", "protocol", 
            "bandwidth", "ip", "http", "database", "query", "sql", "linux", "os", 
            "thread", "process", "cache", "stack", "queue", "tree", "hash", "algorithm"
        ]
        has_tech_kw = any(kw in q_lower for kw in generic_tech)

    return has_tech_kw


def fetch_questions_from_opentdb(amount: int = 15, difficulty: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Fetches live computer science & technology questions from OpenTDB API.
    Category 18 = Science: Computers. Requires NO API Key.
    Strictly filters out company founding trivia and non-technical pop-culture questions.
    """
    base_url = "https://opentdb.com/api.php"
    params = {
        "amount": min(max(1, amount * 2), 50),
        "category": 18,
    }
    
    if difficulty and difficulty.lower() in ("easy", "medium", "hard", "beginner", "intermediate", "advanced"):
        mapped_req = "easy" if difficulty.lower() in ("easy", "beginner") else ("hard" if difficulty.lower() in ("hard", "advanced") else "medium")
        params["difficulty"] = mapped_req

    query_string = urllib.parse.urlencode(params)
    url = f"{base_url}?{query_string}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AI-Interview-Prep/2.0"}
    req = urllib.request.Request(url, headers=headers)

    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status != 200:
                return []
            data = json.loads(response.read().decode("utf-8"))
    except Exception as e:
        logger.warning(f"Live API call returned note: {e}")
        return []

    results = data.get("results", [])
    formatted_questions = []

    for item in results:
        q_raw = html.unescape(item.get("question", ""))
        correct_ans = html.unescape(item.get("correct_answer", ""))
        incorrect_answers = [html.unescape(ans) for ans in item.get("incorrect_answers", [])]
        raw_diff = item.get("difficulty", "medium")

        if not q_raw or not correct_ans:
            continue

        if not is_valid_technical_question(q_raw):
            continue

        topic = classify_question_topic(q_raw, correct_ans)
        mapped_diff = map_api_difficulty(raw_diff)

        all_choices = [correct_ans] + incorrect_answers
        all_choices.sort()

        if item.get("type") == "boolean":
            choices_text = "Format: True | False"
            q_type = "Conceptual"
        else:
            choices_text = "Options: " + " | ".join(all_choices)
            q_type = "Conceptual" if len(q_raw) < 140 else "Scenario-Based"

        formatted_question = f"{q_raw}\n\n{choices_text}"
        explanation = (
            f"Canonical Answer: **{correct_ans}**.\n\n"
            f"Key concept evaluating foundational principles in {topic}. "
            f"Distractors included: {', '.join(incorrect_answers)}."
        )

        hash_id = hashlib.md5(q_raw.encode("utf-8")).hexdigest()[:8].upper()
        q_id = f"API-TDB-{hash_id}"

        formatted_questions.append({
            "question_id": q_id,
            "topic": topic,
            "difficulty": mapped_diff,
            "question_type": q_type,
            "job_role": "Software Engineer",
            "question": formatted_question,
            "answer": correct_ans,
            "explanation": explanation,
            "tags": ["api-streamed", "technical", topic.lower().replace(" ", "-")],
            "source": "Live Online Computer Science API",
        })

        if len(formatted_questions) >= amount:
            break

    return formatted_questions


def sync_dynamic_questions_to_db(amount: int = 15, difficulty: Optional[str] = None) -> Tuple[int, int, str]:
    """
    Directly fetches live questions from the API and dynamic technical repository,
    persisting new records directly to MongoDB and cleaning out any unwanted trivia.
    """
    questions_col = get_questions_collection()
    if questions_col is None:
        return 0, 0, "Database connection unavailable."

    # Remove any old trivia questions (e.g. HP company origins) from MongoDB
    try:
        questions_col.delete_many({
            "question": {"$regex": "HP stands for|who founded|which company was established", "$options": "i"}
        })
    except Exception:
        pass

    # 1. Fetch from live online API
    fetched = fetch_questions_from_opentdb(amount=amount, difficulty=difficulty)

    # 2. Add from the comprehensive technical question bank
    for dyn_q in DYNAMIC_TECHNICAL_BANK:
        if difficulty and dyn_q["difficulty"].lower() != difficulty.lower():
            continue
        fetched.append(dict(dyn_q))

    inserted_count = 0
    now = datetime.now(timezone.utc)

    for q in fetched:
        q_id = q["question_id"]
        existing = questions_col.find_one({"question_id": q_id})
        if not existing:
            doc = dict(q)
            doc["created_at"] = now
            doc["updated_at"] = now
            questions_col.insert_one(doc)
            inserted_count += 1
        else:
            questions_col.update_one({"question_id": q_id}, {"$set": {"updated_at": now}})

    total_in_db = questions_col.count_documents({})
    msg = f"Direct API Sync: {len(fetched)} technical questions processed, {inserted_count} new entries stored in MongoDB."
    logger.info(msg)
    return len(fetched), inserted_count, msg


def get_fresh_questions(
    topic: Optional[str] = None,
    difficulty: Optional[str] = None,
    count: int = 5,
    exclude_ids: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Returns `count` fresh technical questions matching topic and difficulty.
    Excludes questions with IDs in `exclude_ids` so 'Load More' always fetches new questions!
    If repository has fewer unseen questions, queries API / bank to replenish.
    """
    questions_col = get_questions_collection()
    if questions_col is None:
        return []

    exclude_ids = exclude_ids or []

    base_query: Dict[str, Any] = {}
    if topic and topic != "All Topics":
        base_query["topic"] = topic
    if difficulty and difficulty != "All Difficulties":
        base_query["difficulty"] = difficulty

    query = dict(base_query)
    if exclude_ids:
        query["question_id"] = {"$nin": exclude_ids}

    matching = list(questions_col.find(query))

    # If matching unseen questions are fewer than count, ensure DB is synchronized
    if len(matching) < count:
        diff_arg = difficulty.lower() if difficulty and difficulty in ("Beginner", "Intermediate", "Advanced") else None
        sync_dynamic_questions_to_db(amount=count * 2, difficulty=diff_arg)
        matching = list(questions_col.find(query))

    # If still fewer unseen questions for this exact filter:
    if len(matching) < count:
        # Check all questions matching the base query (even if previously seen)
        all_for_filter = list(questions_col.find(base_query))
        if all_for_filter:
            # Pick from those not in the immediate set, or sample from full filter pool
            candidates = [q for q in all_for_filter if q.get("question_id") not in exclude_ids]
            if not candidates:
                candidates = all_for_filter
            # Sample to fulfill the requested count
            need = count - len(matching)
            extra = random.sample(candidates, min(need, len(candidates)))
            # Combine without duplicates
            seen_ids = set(q.get("question_id") for q in matching)
            for ex in extra:
                if ex.get("question_id") not in seen_ids:
                    matching.append(ex)
                    seen_ids.add(ex.get("question_id"))

    if not matching:
        # Fallback across other technical questions
        matching = list(questions_col.find({}))

    sample_size = min(count, len(matching))
    return random.sample(matching, sample_size) if matching else []
