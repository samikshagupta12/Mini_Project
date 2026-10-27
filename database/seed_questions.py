"""Seed script to populate MongoDB with high-quality technical interview questions."""
import uuid
from datetime import datetime, timezone
import logging
from config.settings import TOPICS, DIFFICULTY_LEVELS, QUESTION_TYPES, JOB_ROLES
from database.connection import get_database, check_connection
from database.collections import get_questions_collection, init_db_indexes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SEED_QUESTIONS = [
    # 1. Python Programming
    {
        "question_id": "PY-001",
        "topic": "Python Programming",
        "question": "Explain the difference between mutable and immutable data types in Python with examples.",
        "difficulty": "Beginner",
        "question_type": "Conceptual",
        "job_role": "Software Engineer",
        "answer": "Mutable objects can be modified in place after creation (e.g., lists, dictionaries, sets), while immutable objects cannot be altered once created (e.g., integers, floats, strings, tuples). Modifying an immutable object creates a new object in memory.",
        "explanation": "In Python, identity (`id()`) remains constant for mutable objects when modified (e.g. `list.append()`). For immutable types like strings or ints, operations like concatenation return a new reference with a different memory address. This distinction is critical for function arguments and default parameter values.",
        "tags": ["python", "mutability", "core", "memory"]
    },
    {
        "question_id": "PY-002",
        "topic": "Python Programming",
        "question": "Write a Python generator function to produce the Fibonacci sequence indefinitely.",
        "difficulty": "Intermediate",
        "question_type": "Programming",
        "job_role": "Backend Developer",
        "answer": "```python\ndef fibonacci():\n    a, b = 0, 1\n    while True:\n        yield a\n        a, b = b, a + b\n```",
        "explanation": "Generators use the `yield` statement to produce items lazily on demand without loading the entire infinite series into memory. This provides O(1) space complexity and allows iteration with `next()` or in a `for` loop.",
        "tags": ["python", "generators", "fibonacci", "memory-efficiency"]
    },
    {
        "question_id": "PY-003",
        "topic": "Python Programming",
        "question": "What is the Global Interpreter Lock (GIL) in CPython, and how does it impact multi-threaded CPU-bound versus I/O-bound tasks?",
        "difficulty": "Advanced",
        "question_type": "Conceptual",
        "job_role": "Software Engineer",
        "answer": "The GIL is a mutex that protects access to Python objects, preventing multiple native threads from executing Python bytecodes simultaneously in CPython. It does not hinder I/O-bound tasks (which release the GIL while waiting for network/disk), but prevents true parallelism for CPU-bound tasks, requiring `multiprocessing` instead.",
        "explanation": "CPython's memory management is not thread-safe without the GIL. For CPU-bound parallel execution across multiple CPU cores, developers use the `multiprocessing` module, Celery, or native C extensions that explicitly release the GIL.",
        "tags": ["python", "gil", "concurrency", "multithreading"]
    },
    {
        "question_id": "PY-004",
        "topic": "Python Programming",
        "question": "How would you design a custom decorator in Python that measures and logs the execution time of any function?",
        "difficulty": "Intermediate",
        "question_type": "Programming",
        "job_role": "Backend Developer",
        "answer": "```python\nimport time\nfrom functools import wraps\n\ndef timing_decorator(func):\n    @wraps(func)\n    def wrapper(*args, **kwargs):\n        start = time.perf_counter()\n        result = func(*args, **kwargs)\n        duration = time.perf_counter() - start\n        print(f'{func.__name__} took {duration:.4f}s')\n        return result\n    return wrapper\n```",
        "explanation": "The `@wraps(func)` decorator from `functools` preserves original function metadata such as docstrings and `__name__`. `time.perf_counter()` provides the highest available resolution for benchmarking.",
        "tags": ["python", "decorators", "metaprogramming", "performance"]
    },

    # 2. Data Structures and Algorithms
    {
        "question_id": "DSA-001",
        "topic": "Data Structures and Algorithms",
        "question": "What is the time and space complexity of searching, inserting, and deleting in a balanced Binary Search Tree (AVL / Red-Black Tree)?",
        "difficulty": "Beginner",
        "question_type": "Conceptual",
        "job_role": "Software Engineer",
        "answer": "Time Complexity: O(log N) for Search, Insert, and Delete in the worst and average cases. Space Complexity: O(N) to store N nodes.",
        "explanation": "Self-balancing binary search trees maintain a maximum height of O(log N) through tree rotations. Unlike an unbalanced BST which can degenerate into a linked list with O(N) worst-case time, balanced trees guarantee logarithmic operations.",
        "tags": ["dsa", "trees", "avl", "big-o", "time-complexity"]
    },
    {
        "question_id": "DSA-002",
        "topic": "Data Structures and Algorithms",
        "question": "Describe how to detect a cycle in a singly linked list and return the node where the cycle begins.",
        "difficulty": "Intermediate",
        "question_type": "Programming",
        "job_role": "Software Engineer",
        "answer": "Use Floyd's Cycle-Finding Algorithm (Tortoise and Hare). Advance slow by 1 step and fast by 2 steps. If they meet, reset slow to head while keeping fast at meeting point, then advance both by 1 step; the node where they meet again is the cycle start.",
        "explanation": "Mathematical proof: Let distance from head to cycle start be L, cycle length be C, and distance from cycle start to meeting point be k. When they meet, fast traveled twice the distance of slow: 2(L + k) = L + k + nC, hence L = nC - k. Moving slow from head and fast from meeting point at equal speed guarantees meeting at the start node in O(N) time and O(1) space.",
        "tags": ["dsa", "linked-list", "floyd-cycle", "two-pointers"]
    },
    {
        "question_id": "DSA-003",
        "topic": "Data Structures and Algorithms",
        "question": "Solve the 0/1 Knapsack Problem: given weights, values, and capacity W, formulate the dynamic programming state transition.",
        "difficulty": "Advanced",
        "question_type": "Conceptual",
        "job_role": "Software Engineer",
        "answer": "Let DP[i][w] be the maximum value considering the first i items with remaining capacity w. DP[i][w] = DP[i-1][w] if wt[i-1] > w, else max(DP[i-1][w], val[i-1] + DP[i-1][w - wt[i-1]]). Space can be optimized to O(W) using a 1D array traversed backwards.",
        "explanation": "Backward traversal in the 1D space-optimized array ensures each item is included at most once, preventing reuse of the same item within the same capacity state.",
        "tags": ["dsa", "dynamic-programming", "knapsack", "optimization"]
    },
    {
        "question_id": "DSA-004",
        "topic": "Data Structures and Algorithms",
        "question": "You are given a stream of numbers arriving in real time. Design a data structure to find the median in O(1) time.",
        "difficulty": "Advanced",
        "question_type": "Scenario-Based",
        "job_role": "Software Engineer",
        "answer": "Use two heaps: a max-heap for the lower half of numbers and a min-heap for the upper half. Maintain size balance such that the heaps differ in size by at most 1. The median is either the root of the larger heap or the average of both roots.",
        "explanation": "Insertion of each stream element takes O(log N) as it pushes and balances between the two heaps. Extracting or querying the median takes O(1) by inspecting `max_heap[0]` and `min_heap[0]`.",
        "tags": ["dsa", "heaps", "median", "streaming", "data-structures"]
    },

    # 3. Object-Oriented Programming
    {
        "question_id": "OOP-001",
        "topic": "Object-Oriented Programming",
        "question": "Explain the four pillars of Object-Oriented Programming with brief real-world analogies.",
        "difficulty": "Beginner",
        "question_type": "Conceptual",
        "job_role": "Software Engineer",
        "answer": "1. Encapsulation: Bundling data and methods into a single unit (e.g., a capsule hiding medication). 2. Abstraction: Hiding internal complexity and showing only essential features (e.g., driving a car with pedals without knowing engine thermodynamics). 3. Inheritance: Reusing attributes and behaviors from a parent class (e.g., ElectricCar inherits from Vehicle). 4. Polymorphism: Same interface behaving differently for different types (e.g., Shape.draw() works on Circle or Square).",
        "explanation": "The four pillars enable modularity, code reuse, maintainability, and clean decoupling across software systems.",
        "tags": ["oop", "encapsulation", "abstraction", "inheritance", "polymorphism"]
    },
    {
        "question_id": "OOP-002",
        "topic": "Object-Oriented Programming",
        "question": "What are the SOLID principles? Explain the Single Responsibility Principle and Open/Closed Principle.",
        "difficulty": "Intermediate",
        "question_type": "Conceptual",
        "job_role": "Software Engineer",
        "answer": "SOLID stands for Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, and Dependency Inversion. SRP states a class should have one and only one reason to change. OCP states software entities should be open for extension, but closed for modification.",
        "explanation": "By adhering to SRP, classes remain focused and cohesive. By adhering to OCP via polymorphism or abstraction interfaces, new features can be added without modifying existing tested code.",
        "tags": ["oop", "solid", "design-principles", "architecture"]
    },
    {
        "question_id": "OOP-003",
        "topic": "Object-Oriented Programming",
        "question": "Design a thread-safe Singleton pattern in Python or explain the Factory Method pattern.",
        "difficulty": "Advanced",
        "question_type": "Programming",
        "job_role": "Backend Developer",
        "answer": "```python\nimport threading\n\nclass Singleton:\n    _instance = None\n    _lock = threading.Lock()\n\n    def __new__(cls, *args, **kwargs):\n        if not cls._instance:\n            with cls._lock:\n                if not cls._instance:\n                    cls._instance = super().__new__(cls)\n        return cls._instance\n```",
        "explanation": "Double-checked locking ensures synchronization overhead is only incurred upon first creation. Once initialized, subsequent calls skip the lock acquisition.",
        "tags": ["oop", "design-patterns", "singleton", "concurrency"]
    },

    # 4. Database Management Systems
    {
        "question_id": "DBMS-001",
        "topic": "Database Management Systems",
        "question": "Explain the ACID properties in database transaction management.",
        "difficulty": "Beginner",
        "question_type": "Conceptual",
        "job_role": "Backend Developer",
        "answer": "Atomicity (all operations succeed or all rollback), Consistency (database transitions from one valid state to another, preserving constraints), Isolation (concurrent transactions execute independently without interfering), Durability (committed changes persist permanently even after hardware failures).",
        "explanation": "ACID properties ensure reliable processing of database transactions, especially in financial and mission-critical applications where partial writes would corrupt business logic.",
        "tags": ["dbms", "acid", "transactions", "reliability"]
    },
    {
        "question_id": "DBMS-002",
        "topic": "Database Management Systems",
        "question": "What is Database Normalization? Compare 1NF, 2NF, 3NF, and BCNF.",
        "difficulty": "Intermediate",
        "question_type": "Conceptual",
        "job_role": "Backend Developer",
        "answer": "Normalization organizes database columns and tables to eliminate data redundancy and insertion/update/deletion anomalies. 1NF requires atomic values; 2NF removes partial functional dependencies on a composite primary key; 3NF removes transitive dependencies; BCNF requires that for every functional dependency X -> Y, X must be a super key.",
        "explanation": "Higher normal forms reduce redundancy and ensure referential integrity, though denormalization is sometimes used in OLAP/read-heavy systems to reduce expensive joins.",
        "tags": ["dbms", "normalization", "relational", "database-design"]
    },
    {
        "question_id": "DBMS-003",
        "topic": "Database Management Systems",
        "question": "How do B-Tree and B+ Tree indexes work internally, and why do relational databases prefer B+ Trees over standard Binary Search Trees?",
        "difficulty": "Advanced",
        "question_type": "Scenario-Based",
        "job_role": "Backend Developer",
        "answer": "B+ Trees have high fanout, dramatically reducing tree height and disk I/O operations (one disk read loads an entire page of keys). Furthermore, in a B+ Tree, all data records are stored exclusively in leaf nodes linked sequentially, making range queries (`BETWEEN`, `< >`) highly efficient.",
        "explanation": "Binary trees have height O(log2 N), which would require dozens of disk seeks. B+ Trees have height O(logB N) where B is 100-1000, reducing tree depth to 3-4 levels for millions of rows.",
        "tags": ["dbms", "indexing", "b-plus-tree", "disk-io", "performance"]
    },

    # 5. SQL and MongoDB
    {
        "question_id": "SQL-001",
        "topic": "SQL and MongoDB",
        "question": "Write an SQL query to find the second highest salary from an Employee table.",
        "difficulty": "Beginner",
        "question_type": "Programming",
        "job_role": "Data Analyst",
        "answer": "```sql\nSELECT MAX(salary) AS SecondHighestSalary\nFROM Employee\nWHERE salary < (SELECT MAX(salary) FROM Employee);\n```\nOr using `DENSE_RANK()`:\n```sql\nWITH Ranked AS (\n    SELECT salary, DENSE_RANK() OVER (ORDER BY salary DESC) as rnk\n    FROM Employee\n)\nSELECT salary FROM Ranked WHERE rnk = 2 LIMIT 1;\n```",
        "explanation": "The subquery approach handles ties gracefully and returns `NULL` if no second highest salary exists. Window functions like `DENSE_RANK()` allow finding the N-th highest rank.",
        "tags": ["sql", "queries", "window-functions", "subquery"]
    },
    {
        "question_id": "SQL-002",
        "topic": "SQL and MongoDB",
        "question": "Compare relational SQL databases with MongoDB (Document NoSQL). When should you choose MongoDB over SQL?",
        "difficulty": "Intermediate",
        "question_type": "Conceptual",
        "job_role": "Full Stack Developer",
        "answer": "SQL databases are tabular, schema-enforced, and excel at complex relational queries and ACID transactions. MongoDB is a document database storing JSON-like BSON documents, offering dynamic schemas, horizontal scaling via sharding, and faster reads when related data is embedded.",
        "explanation": "Choose MongoDB when data structure evolves rapidly, data is hierarchical/polymorphic, high write throughput is needed, or sharding across a distributed cluster is required natively.",
        "tags": ["sql", "mongodb", "nosql", "database-selection"]
    },
    {
        "question_id": "SQL-003",
        "topic": "SQL and MongoDB",
        "question": "Write a MongoDB aggregation pipeline to calculate the average order total and total sales grouped by customer_id for orders with status 'completed'.",
        "difficulty": "Advanced",
        "question_type": "Programming",
        "job_role": "Backend Developer",
        "answer": "```javascript\ndb.orders.aggregate([\n  { $match: { status: 'completed' } },\n  {\n    $group: {\n      _id: '$customer_id',\n      totalSales: { $sum: '$total_amount' },\n      avgOrderValue: { $avg: '$total_amount' },\n      orderCount: { $sum: 1 }\n    }\n  },\n  { $sort: { totalSales: -1 } }\n]);\n```",
        "explanation": "The pipeline processes documents through stages: `$match` filters first to leverage index scans, `$group` aggregates per customer, and `$sort` orders the results.",
        "tags": ["mongodb", "aggregation-pipeline", "nosql", "grouping"]
    },

    # 6. Operating Systems
    {
        "question_id": "OS-001",
        "topic": "Operating Systems",
        "question": "What is the difference between a Process and a Thread?",
        "difficulty": "Beginner",
        "question_type": "Conceptual",
        "job_role": "Software Engineer",
        "answer": "A process is an executing instance of a program with its own independent memory space, file handles, and PCB. A thread is a lightweight execution unit within a process that shares the process's code, data, and heap, but has its own stack and registers.",
        "explanation": "Creating or context-switching processes is expensive due to virtual memory page table swaps. Threads share memory, making context switching faster but requiring synchronization mechanisms to avoid race conditions.",
        "tags": ["os", "process", "thread", "concurrency", "memory"]
    },
    {
        "question_id": "OS-002",
        "topic": "Operating Systems",
        "question": "What are the four Coffman conditions necessary for a Deadlock to occur, and how can one condition be prevented?",
        "difficulty": "Intermediate",
        "question_type": "Conceptual",
        "job_role": "Software Engineer",
        "answer": "Conditions: 1. Mutual Exclusion. 2. Hold and Wait. 3. No Preemption. 4. Circular Wait. Prevention: Break Circular Wait by imposing a strict global ordering on all resources such that processes must acquire resources in strictly increasing numerical order.",
        "explanation": "If any one of the four conditions is invalidated, a deadlock is mathematically impossible. Resource ordering eliminates cycles in the Resource Allocation Graph.",
        "tags": ["os", "deadlock", "coffman-conditions", "concurrency"]
    },
    {
        "question_id": "OS-003",
        "topic": "Operating Systems",
        "question": "Explain Virtual Memory, Paging, and what causes a Page Fault and Thrashing.",
        "difficulty": "Advanced",
        "question_type": "Scenario-Based",
        "job_role": "Software Engineer",
        "answer": "Virtual memory maps virtual addresses to physical RAM frames via page tables. A page fault occurs when a referenced page is not currently in physical memory, requiring the OS to fetch it from disk swap. Thrashing occurs when the system spends more time paging data between disk and RAM than executing instructions, caused by insufficient RAM for active working sets.",
        "explanation": "When thrashing occurs, CPU utilization plummets while disk I/O saturates. The OS scheduler must decrease the degree of multiprogramming to allow active processes to retain their working sets.",
        "tags": ["os", "virtual-memory", "paging", "thrashing", "page-fault"]
    },

    # 7. Computer Networks
    {
        "question_id": "CN-001",
        "topic": "Computer Networks",
        "question": "Compare TCP and UDP protocols. When would you use UDP over TCP?",
        "difficulty": "Beginner",
        "question_type": "Conceptual",
        "job_role": "Software Engineer",
        "answer": "TCP is connection-oriented, reliable, guarantees packet ordering, and features flow/congestion control. UDP is connectionless, unreliable, lightweight, and unordered. Use UDP for real-time video streaming, DNS lookups, VoIP, and online multiplayer gaming where speed and low latency are prioritized over 100% packet delivery.",
        "explanation": "TCP establishes state via a 3-way handshake (SYN, SYN-ACK, ACK) and retransmits dropped packets. UDP avoids handshake and retransmission latency.",
        "tags": ["networks", "tcp", "udp", "transport-layer", "protocols"]
    },
    {
        "question_id": "CN-002",
        "topic": "Computer Networks",
        "question": "Walk through what happens step-by-step when you type 'https://www.google.com' into your browser and press Enter.",
        "difficulty": "Intermediate",
        "question_type": "Scenario-Based",
        "job_role": "Full Stack Developer",
        "answer": "1. Browser checks DNS cache (browser, OS, router, ISP resolver) to resolve domain to IP. 2. TCP 3-way handshake established with server IP on port 443. 3. TLS handshake completes (certificate verification, key exchange, encryption negotiation). 4. Browser sends HTTP GET request. 5. Server processes request and returns HTTP 200 response with HTML payload. 6. Browser parses HTML, fetches CSS/JS, and renders DOM.",
        "explanation": "This classic question tests holistic understanding of DNS, transport layer (TCP), transport security (TLS), HTTP protocol semantics, and browser rendering engines.",
        "tags": ["networks", "dns", "http", "tls", "web-architecture"]
    },
    {
        "question_id": "CN-003",
        "topic": "Computer Networks",
        "question": "Explain how HTTPS achieves both confidentiality and authenticity using asymmetric and symmetric encryption.",
        "difficulty": "Advanced",
        "question_type": "Conceptual",
        "job_role": "Software Engineer",
        "answer": "HTTPS uses TLS. During the initial TLS handshake, asymmetric encryption (e.g. RSA or Elliptic Curve Diffie-Hellman) and digital certificates signed by Certificate Authorities (CAs) are used to authenticate the server and securely exchange a shared session key. Once agreed, fast symmetric encryption (e.g., AES-GCM) is used to encrypt all actual data transfer.",
        "explanation": "Asymmetric encryption is computationally expensive for large payloads. By using asymmetric keys only for authentication and session key derivation, HTTPS combines high cryptographic security with wire-speed performance.",
        "tags": ["networks", "security", "https", "tls", "cryptography"]
    },

    # 8. Machine Learning
    {
        "question_id": "ML-001",
        "topic": "Machine Learning",
        "question": "What is the Bias-Variance tradeoff in supervised machine learning?",
        "difficulty": "Beginner",
        "question_type": "Conceptual",
        "job_role": "Machine Learning Engineer",
        "answer": "Bias is error caused by overly simplistic model assumptions (underfitting). Variance is error caused by excessive model sensitivity to training data noise (overfitting). The tradeoff states that decreasing bias increases variance and vice versa; optimal generalization requires balancing both.",
        "explanation": "High bias models (e.g., simple linear regression on non-linear data) have high training and testing error. High variance models (e.g., deep unpruned decision trees) have near-zero training error but poor test set accuracy.",
        "tags": ["ml", "bias-variance", "overfitting", "underfitting"]
    },
    {
        "question_id": "ML-002",
        "topic": "Machine Learning",
        "question": "How does a Decision Tree split nodes? Explain Gini Impurity and Information Gain (Entropy).",
        "difficulty": "Intermediate",
        "question_type": "Conceptual",
        "job_role": "Data Scientist",
        "answer": "Decision trees recursively split features to maximize purity in child nodes. Gini Impurity measures the probability of incorrectly classifying a randomly chosen element: Gini = 1 - sum(p_i^2). Entropy measures disorder/information content: Entropy = -sum(p_i * log2(p_i)). Information Gain is the reduction in entropy after a split.",
        "explanation": "Algorithms like CART use Gini Impurity (computationally faster as it avoids logarithms), while ID3/C4.5 use Information Gain and Gain Ratio.",
        "tags": ["ml", "decision-trees", "entropy", "gini-impurity", "algorithms"]
    },
    {
        "question_id": "ML-003",
        "topic": "Machine Learning",
        "question": "You have a dataset with severe class imbalance (99% negative, 1% positive). Why is Accuracy misleading, and what metrics and techniques should you use?",
        "difficulty": "Advanced",
        "question_type": "Scenario-Based",
        "job_role": "Data Scientist",
        "answer": "A naive model predicting 'negative' for every sample achieves 99% accuracy while detecting zero true positives. Instead, evaluate using Precision, Recall, F1-Score, and PR-AUC. Mitigation techniques include SMOTE (synthetic oversampling), random undersampling, focal loss, or adjusting class weights (`class_weight='balanced'`).",
        "explanation": "In medical diagnosis or fraud detection, false negatives are catastrophic. Recall measures the fraction of actual positives captured, and Precision-Recall curves are more informative than ROC-AUC when positive instances are rare.",
        "tags": ["ml", "class-imbalance", "evaluation-metrics", "f1-score", "smote"]
    },

    # 9. Data Analysis
    {
        "question_id": "DA-001",
        "topic": "Data Analysis",
        "question": "How do you detect and handle missing data and outliers in a Pandas DataFrame?",
        "difficulty": "Beginner",
        "question_type": "Programming",
        "job_role": "Data Analyst",
        "answer": "Missing values: detect with `df.isnull().sum()`, handle by dropping (`df.dropna()`) or imputation (`df.fillna(df.median())`). Outliers: detect using IQR method (Q1 - 1.5*IQR to Q3 + 1.5*IQR) or Z-score (> 3 standard deviations); handle by capping (winsorization), filtering, or transforming (log scale).",
        "explanation": "Mean imputation can be distorted by outliers, so median is often preferred for skewed numerical data. Categorical missing values are commonly imputed with mode or an explicit 'Unknown' category.",
        "tags": ["data-analysis", "pandas", "data-cleaning", "outliers", "imputation"]
    },
    {
        "question_id": "DA-002",
        "topic": "Data Analysis",
        "question": "Explain the difference between Correlation and Causation. Provide an example where correlation does not imply causation.",
        "difficulty": "Intermediate",
        "question_type": "Conceptual",
        "job_role": "Data Analyst",
        "answer": "Correlation measures statistical association between two variables. Causation implies that a change in one variable directly produces a change in the other. Example: Ice cream sales and drowning incidents correlate strongly, but both are caused by a confounding variable (hot summer weather), not by each other.",
        "explanation": "Confounding variables and reverse causality often create spurious correlations. Establishing causation requires controlled experiments (A/B testing) or causal inference techniques like Instrumental Variables.",
        "tags": ["data-analysis", "statistics", "correlation", "causation", "hypothesis-testing"]
    },
    {
        "question_id": "DA-003",
        "topic": "Data Analysis",
        "question": "Demonstrate how to perform group aggregations and create a pivot table in Pandas to analyze monthly revenue by product category.",
        "difficulty": "Advanced",
        "question_type": "Programming",
        "job_role": "Data Analyst",
        "answer": "```python\n# Using groupby:\nmonthly_rev = df.groupby(['month', 'category'])['revenue'].sum().reset_index()\n\n# Using pivot_table:\npivot_df = df.pivot_table(index='month', columns='category', values='revenue', aggfunc='sum', fill_value=0)\n```",
        "explanation": "`pivot_table` reshapes the data into wide format, making it directly suitable for time series plotting and heatmap visualization with Matplotlib/Seaborn.",
        "tags": ["data-analysis", "pandas", "pivot-table", "aggregation"]
    },

    # 10. Problem-Solving Skills
    {
        "question_id": "PS-001",
        "topic": "Problem-Solving Skills",
        "question": "Describe your systematic approach to solving a complex coding problem when you don't immediately know the solution.",
        "difficulty": "Beginner",
        "question_type": "Conceptual",
        "job_role": "Software Engineer",
        "answer": "1. Clarify inputs, outputs, constraints, and edge cases (nulls, empty lists, duplicates). 2. Walk through a small manual example. 3. Formulate a brute-force approach and analyze its Big-O. 4. Identify bottlenecks and optimize using appropriate data structures (hash maps, two pointers). 5. Write clean, modular code. 6. Test edge cases manually before execution.",
        "explanation": "Interviewers evaluate structured thought processes and communication just as much as final syntax. Breaking problems into small verifiable steps prevents getting stuck.",
        "tags": ["problem-solving", "interview-strategy", "methodology"]
    },
    {
        "question_id": "PS-002",
        "topic": "Problem-Solving Skills",
        "question": "Given an array of integers and a target sum, describe how to find all unique pairs that add up to the target in O(N) time.",
        "difficulty": "Intermediate",
        "question_type": "Programming",
        "job_role": "Software Engineer",
        "answer": "Use a Hash Set to track seen numbers. For each number x in the array, check if target - x is in the seen set. If yes, record the pair (min(x, target-x), max(x, target-x)). Add x to the seen set. Store unique pairs in a result set to avoid duplicate pairs.",
        "explanation": "Lookup and insertion in a Hash Set take O(1) average time, reducing the naive O(N^2) nested loop search to a single O(N) linear scan.",
        "tags": ["problem-solving", "two-sum", "hash-table", "optimization"]
    },
    {
        "question_id": "PS-003",
        "topic": "Problem-Solving Skills",
        "question": "A production service is suddenly experiencing intermittent 504 Gateway Timeouts. How do you isolate the root cause?",
        "difficulty": "Advanced",
        "question_type": "Scenario-Based",
        "job_role": "Backend Developer",
        "answer": "1. Check monitoring dashboards (CPU, RAM, network, connection pool metrics). 2. Inspect reverse proxy / load balancer logs to isolate affected endpoints and upstream servers. 3. Examine database query latency and slow query logs for locking or unindexed queries. 4. Check downstream microservice dependency response times. 5. Check garbage collection pauses or thread pool exhaustion in application runtimes.",
        "explanation": "504 indicates an upstream gateway timed out waiting for a backend response. Systematic isolation starting from the edge balancer down to database and third-party APIs rapidly pinpoints whether the bottleneck is database locks, server saturation, or network congestion.",
        "tags": ["problem-solving", "troubleshooting", "system-design", "production-incident"]
    }
]


def seed_database(force: bool = False):
    """Inserts seed questions into MongoDB without creating duplicates."""
    db = get_database()
    if db is None:
        logger.error("Database connection unavailable. Cannot seed questions.")
        return 0, "Database unavailable"
    
    init_db_indexes(db)
    questions_col = get_questions_collection(db)
    if questions_col is None:
        return 0, "Questions collection unavailable"

    inserted_count = 0
    updated_count = 0
    now = datetime.now(timezone.utc)

    for item in SEED_QUESTIONS:
        q_id = item["question_id"]
        doc = dict(item)
        doc["updated_at"] = now
        
        # Check if already exists
        existing = questions_col.find_one({"question_id": q_id})
        if existing:
            if force:
                questions_col.update_one({"question_id": q_id}, {"$set": doc})
                updated_count += 1
        else:
            doc["created_at"] = now
            questions_col.insert_one(doc)
            inserted_count += 1

    total_in_db = questions_col.count_documents({})
    msg = f"Seeding complete: {inserted_count} inserted, {updated_count} updated. Total questions in database: {total_in_db}"
    logger.info(msg)
    return total_in_db, msg


if __name__ == "__main__":
    count, message = seed_database(force=True)
    print(f"[Seed Result] {message}")

