"""
DSA Utilities
Stack, Queue, and other data structure implementations
Used for transaction management, undo operations, and caching
"""

from collections import deque
from datetime import datetime
from typing import Any, Dict, List, Optional
import heapq


class Stack:
    """
    Stack implementation for LIFO operations.
    Used for: Undo operations, recent transactions, navigation history
    """
    
    def __init__(self, max_size: int = 100):
        self._items: List[Any] = []
        self.max_size = max_size
    
    def push(self, item: Any) -> None:
        """Push item onto stack. Removes oldest if at max capacity."""
        if len(self._items) >= self.max_size:
            self._items.pop(0)  # Remove from bottom
        self._items.append(item)
    
    def pop(self) -> Optional[Any]:
        """Remove and return top item."""
        return self._items.pop() if self._items else None
    
    def peek(self) -> Optional[Any]:
        """Return top item without removing."""
        return self._items[-1] if self._items else None
    
    def is_empty(self) -> bool:
        return len(self._items) == 0
    
    def size(self) -> int:
        return len(self._items)
    
    def clear(self) -> None:
        self._items = []
    
    def get_all(self) -> List[Any]:
        """Return all items (bottom to top)."""
        return self._items.copy()
    
    def get_recent(self, n: int) -> List[Any]:
        """Return n most recent items (top to bottom)."""
        return self._items[-n:][::-1] if self._items else []


class Queue:
    """
    Queue implementation for FIFO operations.
    Used for: Scheduled transactions, notification queue, task processing
    """
    
    def __init__(self, max_size: int = 100):
        self._items: deque = deque(maxlen=max_size)
    
    def enqueue(self, item: Any) -> None:
        """Add item to back of queue."""
        self._items.append(item)
    
    def dequeue(self) -> Optional[Any]:
        """Remove and return front item."""
        return self._items.popleft() if self._items else None
    
    def peek(self) -> Optional[Any]:
        """Return front item without removing."""
        return self._items[0] if self._items else None
    
    def is_empty(self) -> bool:
        return len(self._items) == 0
    
    def size(self) -> int:
        return len(self._items)
    
    def clear(self) -> None:
        self._items.clear()
    
    def get_all(self) -> List[Any]:
        """Return all items (front to back)."""
        return list(self._items)


class PriorityQueue:
    """
    Priority Queue implementation using heap.
    Used for: Goal prioritization, alert severity ordering
    """
    
    def __init__(self):
        self._heap: List[tuple] = []
        self._counter = 0  # For stable sorting
    
    def push(self, item: Any, priority: int) -> None:
        """Add item with priority (lower = higher priority)."""
        heapq.heappush(self._heap, (priority, self._counter, item))
        self._counter += 1
    
    def pop(self) -> Optional[Any]:
        """Remove and return highest priority item."""
        if self._heap:
            priority, _, item = heapq.heappop(self._heap)
            return item
        return None
    
    def peek(self) -> Optional[Any]:
        """Return highest priority item without removing."""
        if self._heap:
            return self._heap[0][2]
        return None
    
    def is_empty(self) -> bool:
        return len(self._heap) == 0
    
    def size(self) -> int:
        return len(self._heap)


class LRUCache:
    """
    Least Recently Used Cache.
    Used for: Caching user data, analytics results
    """
    
    def __init__(self, capacity: int = 100):
        self.capacity = capacity
        self._cache: Dict[str, Any] = {}
        self._order: deque = deque()
    
    def get(self, key: str) -> Optional[Any]:
        """Get item from cache. Returns None if not found."""
        if key in self._cache:
            # Move to end (most recently used)
            self._order.remove(key)
            self._order.append(key)
            return self._cache[key]
        return None
    
    def put(self, key: str, value: Any) -> None:
        """Add/update item in cache."""
        if key in self._cache:
            self._order.remove(key)
        elif len(self._cache) >= self.capacity:
            # Remove least recently used
            oldest = self._order.popleft()
            del self._cache[oldest]
        
        self._cache[key] = value
        self._order.append(key)
    
    def remove(self, key: str) -> bool:
        """Remove item from cache."""
        if key in self._cache:
            del self._cache[key]
            self._order.remove(key)
            return True
        return False
    
    def clear(self) -> None:
        self._cache.clear()
        self._order.clear()
    
    def size(self) -> int:
        return len(self._cache)


class TransactionManager:
    """
    Transaction management using DSA concepts.
    Manages undo stack, recent transactions, and category totals.
    """
    
    def __init__(self):
        self.undo_stack = Stack(max_size=50)
        self.recent_transactions = Stack(max_size=100)
        self.notification_queue = Queue(max_size=200)
        self.category_totals: Dict[str, float] = {}
        self.monthly_cache = LRUCache(capacity=24)  # 24 months
    
    def add_transaction(self, transaction: Dict) -> None:
        """Add transaction to recent stack and update totals."""
        # Add to recent
        self.recent_transactions.push({
            **transaction,
            'timestamp': datetime.now().isoformat()
        })
        
        # Add to undo stack if expense/income
        if transaction.get('type') in ['EXPENSE', 'INCOME']:
            self.undo_stack.push(transaction)
        
        # Update category total
        category = transaction.get('category')
        amount = transaction.get('amount', 0)
        if category and transaction.get('type') == 'EXPENSE':
            self.category_totals[category] = self.category_totals.get(category, 0) + amount
    
    def undo_last(self) -> Optional[Dict]:
        """Pop and return last undoable transaction."""
        return self.undo_stack.pop()
    
    def get_recent(self, n: int = 10) -> List[Dict]:
        """Get n most recent transactions."""
        return self.recent_transactions.get_recent(n)
    
    def add_notification(self, notification: Dict) -> None:
        """Queue a notification."""
        self.notification_queue.enqueue({
            **notification,
            'timestamp': datetime.now().isoformat()
        })
    
    def get_pending_notifications(self) -> List[Dict]:
        """Get all pending notifications."""
        notifications = []
        while not self.notification_queue.is_empty():
            notifications.append(self.notification_queue.dequeue())
        return notifications
    
    def get_category_totals(self) -> Dict[str, float]:
        """Get current category totals."""
        return self.category_totals.copy()
    
    def reset_category_totals(self) -> None:
        """Reset category totals (monthly reset)."""
        self.category_totals = {}
    
    def cache_monthly_summary(self, month_key: str, summary: Dict) -> None:
        """Cache a monthly summary."""
        self.monthly_cache.put(month_key, summary)
    
    def get_cached_summary(self, month_key: str) -> Optional[Dict]:
        """Get cached monthly summary."""
        return self.monthly_cache.get(month_key)


class BinarySearchTree:
    """
    Binary Search Tree for sorted data operations.
    Used for: Expense amount searching, date-based lookups
    """
    
    class Node:
        def __init__(self, key: Any, value: Any):
            self.key = key
            self.value = value
            self.left = None
            self.right = None
    
    def __init__(self):
        self.root = None
        self._size = 0
    
    def insert(self, key: Any, value: Any) -> None:
        """Insert key-value pair."""
        if not self.root:
            self.root = self.Node(key, value)
        else:
            self._insert_recursive(self.root, key, value)
        self._size += 1
    
    def _insert_recursive(self, node, key, value):
        if key < node.key:
            if node.left:
                self._insert_recursive(node.left, key, value)
            else:
                node.left = self.Node(key, value)
        else:
            if node.right:
                self._insert_recursive(node.right, key, value)
            else:
                node.right = self.Node(key, value)
    
    def search(self, key: Any) -> Optional[Any]:
        """Search for value by key."""
        return self._search_recursive(self.root, key)
    
    def _search_recursive(self, node, key) -> Optional[Any]:
        if not node:
            return None
        if key == node.key:
            return node.value
        elif key < node.key:
            return self._search_recursive(node.left, key)
        else:
            return self._search_recursive(node.right, key)
    
    def range_search(self, low: Any, high: Any) -> List[Any]:
        """Find all values with keys in range [low, high]."""
        result = []
        self._range_recursive(self.root, low, high, result)
        return result
    
    def _range_recursive(self, node, low, high, result):
        if not node:
            return
        if low < node.key:
            self._range_recursive(node.left, low, high, result)
        if low <= node.key <= high:
            result.append(node.value)
        if high > node.key:
            self._range_recursive(node.right, low, high, result)
    
    def size(self) -> int:
        return self._size
    
    def inorder(self) -> List[Any]:
        """Return all values in sorted order."""
        result = []
        self._inorder_recursive(self.root, result)
        return result
    
    def _inorder_recursive(self, node, result):
        if node:
            self._inorder_recursive(node.left, result)
            result.append(node.value)
            self._inorder_recursive(node.right, result)


class Graph:
    """
    Graph implementation for relationship mapping.
    Used for: User transfer network, category relationships
    """
    
    def __init__(self, directed: bool = True):
        self._adj: Dict[Any, List[tuple]] = {}
        self.directed = directed
    
    def add_vertex(self, vertex: Any) -> None:
        """Add vertex to graph."""
        if vertex not in self._adj:
            self._adj[vertex] = []
    
    def add_edge(self, u: Any, v: Any, weight: float = 1.0) -> None:
        """Add edge from u to v with optional weight."""
        self.add_vertex(u)
        self.add_vertex(v)
        self._adj[u].append((v, weight))
        if not self.directed:
            self._adj[v].append((u, weight))
    
    def get_neighbors(self, vertex: Any) -> List[tuple]:
        """Get all neighbors of a vertex."""
        return self._adj.get(vertex, [])
    
    def bfs(self, start: Any) -> List[Any]:
        """Breadth-first search from start vertex."""
        if start not in self._adj:
            return []
        
        visited = set()
        result = []
        queue = deque([start])
        
        while queue:
            vertex = queue.popleft()
            if vertex not in visited:
                visited.add(vertex)
                result.append(vertex)
                for neighbor, _ in self._adj[vertex]:
                    if neighbor not in visited:
                        queue.append(neighbor)
        
        return result
    
    def dfs(self, start: Any) -> List[Any]:
        """Depth-first search from start vertex."""
        if start not in self._adj:
            return []
        
        visited = set()
        result = []
        
        def dfs_recursive(vertex):
            if vertex in visited:
                return
            visited.add(vertex)
            result.append(vertex)
            for neighbor, _ in self._adj[vertex]:
                dfs_recursive(neighbor)
        
        dfs_recursive(start)
        return result
    
    def total_weight(self, vertex: Any) -> float:
        """Get total weight of all edges from a vertex."""
        return sum(weight for _, weight in self._adj.get(vertex, []))


# Create singleton instances
transaction_manager = TransactionManager()
