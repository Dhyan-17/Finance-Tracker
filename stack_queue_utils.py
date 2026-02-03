from collections import deque
from datetime import datetime

class Stack:
    """Stack implementation for undo operations and recent transactions"""
    def __init__(self, max_size=100):
        self.stack = []
        self.max_size = max_size

    def push(self, item):
        """Push item to stack"""
        if len(self.stack) >= self.max_size:
            self.stack.pop(0)  # Remove oldest item if full
        self.stack.append(item)

    def pop(self):
        """Pop item from stack"""
        if not self.is_empty():
            return self.stack.pop()
        return None

    def peek(self):
        """Peek top item without removing"""
        if not self.is_empty():
            return self.stack[-1]
        return None

    def is_empty(self):
        """Check if stack is empty"""
        return len(self.stack) == 0

    def size(self):
        """Get stack size"""
        return len(self.stack)

    def clear(self):
        """Clear the stack"""
        self.stack = []

class Queue:
    """Queue implementation for scheduled operations"""
    def __init__(self, max_size=100):
        self.queue = deque(maxlen=max_size)

    def enqueue(self, item):
        """Add item to queue"""
        self.queue.append(item)

    def dequeue(self):
        """Remove and return item from queue"""
        if not self.is_empty():
            return self.queue.popleft()
        return None

    def peek(self):
        """Peek front item without removing"""
        if not self.is_empty():
            return self.queue[0]
        return None

    def is_empty(self):
        """Check if queue is empty"""
        return len(self.queue) == 0

    def size(self):
        """Get queue size"""
        return len(self.queue)

    def clear(self):
        """Clear the queue"""
        self.queue.clear()

class StackQueueManager:
    """Manager class for DSA operations in the wallet system"""
    def __init__(self):
        # Stack for undo operations
        self.undo_stack = Stack()

        # Stack for recent transactions
        self.recent_transactions = Stack(max_size=10)

        # Queue for scheduled recurring expenses
        self.recurring_expenses_queue = Queue()

        # Queue for scheduled income
        self.recurring_income_queue = Queue()

        # Dictionary for category totals
        self.category_totals = {}

        # Dictionary for monthly summaries
        self.monthly_summaries = {}

        # Dictionary for budget vs spent
        self.budget_tracking = {}

    def add_transaction_to_recent(self, transaction):
        """Add transaction to recent transactions stack"""
        self.recent_transactions.push(transaction)

    def add_to_undo_stack(self, transaction):
        """Add transaction to undo stack"""
        self.undo_stack.push(transaction)

    def get_recent_transactions(self, limit=5):
        """Get recent transactions from stack"""
        transactions = []
        temp_stack = Stack()

        # Get transactions without modifying original stack
        count = 0
        while not self.recent_transactions.is_empty() and count < limit:
            transaction = self.recent_transactions.pop()
            transactions.append(transaction)
            temp_stack.push(transaction)
            count += 1

        # Restore original stack
        while not temp_stack.is_empty():
            self.recent_transactions.push(temp_stack.pop())

        return transactions[::-1]  # Reverse to get chronological order

    def schedule_recurring_expense(self, expense_data):
        """Schedule recurring expense"""
        self.recurring_expenses_queue.enqueue(expense_data)

    def schedule_recurring_income(self, income_data):
        """Schedule recurring income"""
        self.recurring_income_queue.enqueue(income_data)

    def process_scheduled_expenses(self):
        """Process scheduled recurring expenses"""
        processed = []
        while not self.recurring_expenses_queue.is_empty():
            expense = self.recurring_expenses_queue.dequeue()
            # Here you would typically process the expense
            processed.append(expense)
        return processed

    def process_scheduled_income(self):
        """Process scheduled recurring income"""
        processed = []
        while not self.recurring_income_queue.is_empty():
            income = self.recurring_income_queue.dequeue()
            # Here you would typically process the income
            processed.append(income)
        return processed

    def update_category_total(self, category, amount):
        """Update category total in dictionary"""
        if category not in self.category_totals:
            self.category_totals[category] = 0.0
        self.category_totals[category] += amount

    def get_category_totals(self):
        """Get all category totals"""
        return self.category_totals.copy()

    def reset_category_totals(self):
        """Reset category totals (monthly reset)"""
        self.category_totals = {}

    def update_monthly_summary(self, month_key, income=0, expense=0):
        """Update monthly summary"""
        if month_key not in self.monthly_summaries:
            self.monthly_summaries[month_key] = {'income': 0, 'expense': 0, 'net': 0}

        self.monthly_summaries[month_key]['income'] += income
        self.monthly_summaries[month_key]['expense'] += expense
        self.monthly_summaries[month_key]['net'] = (
            self.monthly_summaries[month_key]['income'] -
            self.monthly_summaries[month_key]['expense']
        )

    def get_monthly_summaries(self):
        """Get monthly summaries"""
        return self.monthly_summaries.copy()

    def set_budget(self, user_id, category, limit_amount, month):
        """Set budget for category"""
        key = f"{user_id}_{category}_{month}"
        self.budget_tracking[key] = {
            'limit': limit_amount,
            'spent': 0.0,
            'remaining': limit_amount
        }

    def update_budget_spent(self, user_id, category, month, amount):
        """Update spent amount in budget"""
        key = f"{user_id}_{category}_{month}"
        if key in self.budget_tracking:
            self.budget_tracking[key]['spent'] += amount
            self.budget_tracking[key]['remaining'] = (
                self.budget_tracking[key]['limit'] - self.budget_tracking[key]['spent']
            )

    def get_budget_status(self, user_id, category, month):
        """Get budget status for category"""
        key = f"{user_id}_{category}_{month}"
        return self.budget_tracking.get(key, {'limit': 0, 'spent': 0, 'remaining': 0})

    def get_all_budgets(self, user_id, month_key):
        """Get all budgets for user in a month"""
        budgets = {}

        for key, data in self.budget_tracking.items():
            try:
                uid, category, month = key.split("_")
                if uid == str(user_id) and month == month_key:
                    budgets[category] = data
            except ValueError:
                continue

        return budgets


    def get_top_expenses(self, month_key, top_n=3):
        """
        Return top N highest expenses for a given month
        (Uses recent transactions stack)
        """
        expenses = []

        for txn in self.recent_transactions.stack:
            if (
                txn.get("type") == "EXPENSE"
                and txn.get("date").strftime("%Y-%m") == month_key
            ):
                expenses.append(txn)

        expenses.sort(key=lambda x: x["amount"], reverse=True)
        return expenses[:top_n]

    def undo_last_transaction(self):
        """Pop and return last transaction from undo stack"""
        # NOTE: Database rows are not deleted (audit preserved)
        if self.undo_stack.is_empty():
            return None
        return self.undo_stack.pop()

    def remove_budget(self, user_id, category, month):
        """Remove budget for category"""
        key = f"{user_id}_{category}_{month}"
        if key in self.budget_tracking:
            del self.budget_tracking[key]
            return True
        return False

    def clear_user_data(self, user_id):
        """Clear all data for a user (logout cleanup)"""
        # Clear user-specific data from dictionaries
        keys_to_remove = []
        for key in self.budget_tracking:
            if key.startswith(f"{user_id}_"):
                keys_to_remove.append(key)

        for key in keys_to_remove:
            del self.budget_tracking[key]

        # Note: In a real implementation, you'd also clear from database
        # But for session management, this is sufficient
