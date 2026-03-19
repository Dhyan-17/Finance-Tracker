"""
DSA Utilities
Only Stack with push and pop - used in actual code
"""

from typing import Any, List, Optional


class Stack:
    """Stack for LIFO operations - only push and pop used in code"""
    
    def __init__(self, max_size: int = 100):
        self._items: List[Any] = []
        self.max_size = max_size
    
    def push(self, item: Any) -> None:
        """Push item onto stack."""
        if len(self._items) >= self.max_size:
            self._items.pop(0)
        self._items.append(item)
    
    def pop(self) -> Optional[Any]:
        """Remove and return top item."""
        return self._items.pop() if self._items else None
