"""
Investment Service
Market operations with realistic price simulation
"""

import random
from typing import Tuple, Dict, Optional, List
from datetime import datetime, timedelta
from database.db import db


class InvestmentService:
    """Investment and market operations"""
    
    # ============================================================
    # MARKET PRICE SIMULATION
    # ============================================================
    
    def update_market_prices(self) -> List[Dict]:
        """
        Update all market asset prices with realistic simulation.
        Returns list of updated assets.
        """
        assets = db.get_market_assets()
        updated = []
        
        for asset in assets:
            old_price = asset['current_price']
            volatility = asset['volatility_percent']
            
            # Simulate price movement
            new_price = self._simulate_price_movement(old_price, volatility)
            
            if new_price != old_price:
                change_percent = ((new_price - old_price) / old_price) * 100
                
                # Update asset
                db.update_asset_price(asset['asset_id'], new_price, change_percent)
                
                # Record price history
                db.execute_insert(
                    "INSERT INTO market_price_history (asset_id, price) VALUES (?, ?)",
                    (asset['asset_id'], new_price)
                )
                
                updated.append({
                    'asset_id': asset['asset_id'],
                    'name': asset['asset_name'],
                    'symbol': asset['asset_symbol'],
                    'old_price': db.to_rupees(old_price),
                    'new_price': db.to_rupees(new_price),
                    'change_percent': change_percent
                })
        
        return updated
    
    def _simulate_price_movement(self, current_price: int, volatility: float) -> int:
        """
        Simulate realistic price movement based on volatility.
        Uses random walk with slight upward bias.
        """
        # Random direction with slight upward bias (60% up, 40% down)
        direction = random.choices([1, -1], weights=[0.6, 0.4])[0]
        
        # Movement percentage based on volatility
        max_change = volatility / 100
        change = random.uniform(0, max_change) * direction
        
        # Apply change
        new_price = int(current_price * (1 + change))
        
        # Ensure minimum price (1 paise)
        return max(new_price, 1)
    
    # ============================================================
    # BUY OPERATIONS
    # ============================================================
    
    def buy_asset(
        self,
        user_id: int,
        asset_id: int,
        amount: float,
        source_account_type: str = 'WALLET',
        source_account_id: int = None
    ) -> Tuple[bool, str, Optional[Dict]]:
        """
        Buy an asset at current market price.
        Amount is in rupees.
        """
        if amount <= 0:
            return False, "Amount must be positive", None
        
        amount_paise = db.to_paise(amount)
        
        # Get asset
        asset = db.get_asset_by_id(asset_id)
        if not asset or not asset['is_active']:
            return False, "Asset not found or inactive", None
        
        current_price = asset['current_price']
        if current_price <= 0:
            return False, "Invalid asset price", None
        
        # Calculate units
        units = amount_paise / current_price
        
        try:
            with db.transaction() as conn:
                cursor = conn.cursor()
                
                # Deduct from source account
                if source_account_type == 'WALLET':
                    cursor.execute(
                        "SELECT wallet_balance FROM users WHERE user_id = ?",
                        (user_id,)
                    )
                    result = cursor.fetchone()
                    if not result:
                        return False, "User not found", None
                    
                    balance = result[0]
                    if balance < amount_paise:
                        return False, f"Insufficient balance. Available: ₹{db.to_rupees(balance):.2f}", None
                    
                    new_balance = balance - amount_paise
                    cursor.execute(
                        "UPDATE users SET wallet_balance = ? WHERE user_id = ?",
                        (new_balance, user_id)
                    )
                    
                    # Add wallet transaction
                    cursor.execute(
                        """INSERT INTO wallet_transactions 
                           (user_id, txn_type, amount, balance_after, reference_type, description)
                           VALUES (?, 'INVESTMENT', ?, ?, 'investment', ?)""",
                        (user_id, amount_paise, new_balance, f"Buy {asset['asset_symbol']}")
                    )
                    
                elif source_account_type == 'BANK':
                    if not source_account_id:
                        return False, "Bank account ID required", None
                    
                    cursor.execute(
                        "SELECT balance FROM bank_accounts WHERE account_id = ? AND user_id = ?",
                        (source_account_id, user_id)
                    )
                    result = cursor.fetchone()
                    if not result:
                        return False, "Bank account not found", None
                    
                    balance = result[0]
                    if balance < amount_paise:
                        return False, f"Insufficient balance. Available: ₹{db.to_rupees(balance):.2f}", None
                    
                    new_balance = balance - amount_paise
                    cursor.execute(
                        "UPDATE bank_accounts SET balance = ? WHERE account_id = ?",
                        (new_balance, source_account_id)
                    )
                else:
                    return False, "Invalid account type", None
                
                # Check existing investment
                cursor.execute(
                    "SELECT * FROM user_investments WHERE user_id = ? AND asset_id = ?",
                    (user_id, asset_id)
                )
                existing = cursor.fetchone()
                
                if existing:
                    # Average the buy price
                    existing_dict = dict(zip(
                        ['investment_id', 'user_id', 'asset_id', 'units_owned', 'buy_price', 'invested_amount', 'purchase_date'],
                        existing
                    ))
                    total_units = existing_dict['units_owned'] + units
                    total_invested = existing_dict['invested_amount'] + amount_paise
                    avg_price = int(total_invested / total_units)
                    
                    cursor.execute(
                        """UPDATE user_investments 
                           SET units_owned = ?, invested_amount = ?, buy_price = ?
                           WHERE investment_id = ?""",
                        (total_units, total_invested, avg_price, existing_dict['investment_id'])
                    )
                    investment_id = existing_dict['investment_id']
                else:
                    # New investment
                    cursor.execute(
                        """INSERT INTO user_investments 
                           (user_id, asset_id, units_owned, buy_price, invested_amount)
                           VALUES (?, ?, ?, ?, ?)""",
                        (user_id, asset_id, units, current_price, amount_paise)
                    )
                    investment_id = cursor.lastrowid
                
                # Log investment transaction
                cursor.execute(
                    """INSERT INTO investment_transactions 
                       (user_id, asset_id, txn_type, units, price_per_unit, total_amount, 
                        source_account_type, source_account_id)
                       VALUES (?, ?, 'BUY', ?, ?, ?, ?, ?)""",
                    (user_id, asset_id, units, current_price, amount_paise,
                     source_account_type, source_account_id)
                )
            
            db.log_action(
                'USER', user_id,
                f"Bought {units:.4f} units of {asset['asset_symbol']} for ₹{amount:.2f}",
                'user_investments', investment_id
            )
            
            return True, "Investment successful", {
                'investment_id': investment_id,
                'asset': asset['asset_name'],
                'symbol': asset['asset_symbol'],
                'units': units,
                'price_per_unit': db.to_rupees(current_price),
                'total_amount': amount
            }
            
        except Exception as e:
            return False, f"Investment failed: {str(e)}", None
    
    # ============================================================
    # SELL OPERATIONS
    # ============================================================
    
    def sell_asset(
        self,
        user_id: int,
        asset_id: int,
        units_to_sell: float,
        target_account_type: str = 'WALLET',
        target_account_id: int = None
    ) -> Tuple[bool, str, Optional[Dict]]:
        """
        Sell an asset at current market price.
        """
        if units_to_sell <= 0:
            return False, "Units must be positive", None
        
        # Get holding
        holdings = db.execute(
            """SELECT ui.*, ma.current_price, ma.asset_name, ma.asset_symbol
               FROM user_investments ui
               JOIN market_assets ma ON ui.asset_id = ma.asset_id
               WHERE ui.user_id = ? AND ui.asset_id = ?""",
            (user_id, asset_id),
            fetch=True
        )
        
        if not holdings:
            return False, "You don't own this asset", None
        
        holding = holdings[0]
        owned_units = holding['units_owned']
        
        if units_to_sell > owned_units:
            return False, f"Insufficient units. You own: {owned_units:.4f}", None
        
        current_price = holding['current_price']
        sale_amount = int(units_to_sell * current_price)
        buy_price = holding['buy_price']
        
        # Calculate profit/loss
        cost_basis = int(units_to_sell * buy_price)
        profit_loss = sale_amount - cost_basis
        
        try:
            with db.transaction() as conn:
                cursor = conn.cursor()
                
                # Credit to target account
                if target_account_type == 'WALLET':
                    cursor.execute(
                        "SELECT wallet_balance FROM users WHERE user_id = ?",
                        (user_id,)
                    )
                    result = cursor.fetchone()
                    balance = result[0]
                    new_balance = balance + sale_amount
                    
                    cursor.execute(
                        "UPDATE users SET wallet_balance = ? WHERE user_id = ?",
                        (new_balance, user_id)
                    )
                    
                    cursor.execute(
                        """INSERT INTO wallet_transactions 
                           (user_id, txn_type, amount, balance_after, reference_type, description)
                           VALUES (?, 'INCOME', ?, ?, 'investment_sale', ?)""",
                        (user_id, sale_amount, new_balance, f"Sell {holding['asset_symbol']}")
                    )
                    
                elif target_account_type == 'BANK':
                    if not target_account_id:
                        return False, "Bank account ID required", None
                    
                    cursor.execute(
                        "SELECT balance FROM bank_accounts WHERE account_id = ? AND user_id = ?",
                        (target_account_id, user_id)
                    )
                    result = cursor.fetchone()
                    if not result:
                        return False, "Bank account not found", None
                    
                    balance = result[0]
                    new_balance = balance + sale_amount
                    
                    cursor.execute(
                        "UPDATE bank_accounts SET balance = ? WHERE account_id = ?",
                        (new_balance, target_account_id)
                    )
                else:
                    return False, "Invalid account type", None
                
                # Update or remove holding
                remaining_units = owned_units - units_to_sell
                
                if remaining_units < 0.000001:  # Essentially zero
                    cursor.execute(
                        "DELETE FROM user_investments WHERE investment_id = ?",
                        (holding['investment_id'],)
                    )
                else:
                    remaining_invested = int(remaining_units * buy_price)
                    cursor.execute(
                        """UPDATE user_investments 
                           SET units_owned = ?, invested_amount = ?
                           WHERE investment_id = ?""",
                        (remaining_units, remaining_invested, holding['investment_id'])
                    )
                
                # Log investment transaction
                cursor.execute(
                    """INSERT INTO investment_transactions 
                       (user_id, asset_id, txn_type, units, price_per_unit, total_amount,
                        source_account_type, source_account_id)
                       VALUES (?, ?, 'SELL', ?, ?, ?, ?, ?)""",
                    (user_id, asset_id, units_to_sell, current_price, sale_amount,
                     target_account_type, target_account_id)
                )
            
            db.log_action(
                'USER', user_id,
                f"Sold {units_to_sell:.4f} units of {holding['asset_symbol']} for ₹{db.to_rupees(sale_amount):.2f}",
                'investment_transactions', None
            )
            
            return True, "Sale successful", {
                'asset': holding['asset_name'],
                'symbol': holding['asset_symbol'],
                'units_sold': units_to_sell,
                'price_per_unit': db.to_rupees(current_price),
                'total_amount': db.to_rupees(sale_amount),
                'profit_loss': db.to_rupees(profit_loss),
                'new_balance': db.to_rupees(new_balance)
            }
            
        except Exception as e:
            return False, f"Sale failed: {str(e)}", None
    
    # ============================================================
    # PORTFOLIO OPERATIONS
    # ============================================================
    
    def get_portfolio(self, user_id: int) -> Dict:
        """Get complete investment portfolio"""
        holdings = db.get_user_investments(user_id)
        
        if not holdings:
            return {
                'holdings': [],
                'total_invested': 0,
                'current_value': 0,
                'total_profit_loss': 0,
                'profit_loss_percent': 0,
                'by_type': {}
            }
        
        # Convert to rupees and organize by type
        formatted_holdings = []
        by_type = {}
        
        for h in holdings:
            holding = {
                'investment_id': h['investment_id'],
                'asset_id': h['asset_id'],
                'asset_name': h['asset_name'],
                'asset_symbol': h['asset_symbol'],
                'asset_type': h['asset_type'],
                'units_owned': h['units_owned'],
                'buy_price': db.to_rupees(h['buy_price']),
                'current_price': db.to_rupees(h['current_price']),
                'invested_amount': db.to_rupees(h['invested_amount']),
                'current_value': db.to_rupees(h['current_value']),
                'profit_loss': db.to_rupees(h['profit_loss']),
                'profit_loss_percent': (h['profit_loss'] / h['invested_amount'] * 100) if h['invested_amount'] > 0 else 0,
                'day_change': h['day_change_percent']
            }
            formatted_holdings.append(holding)
            
            # Group by type
            asset_type = h['asset_type']
            if asset_type not in by_type:
                by_type[asset_type] = {'invested': 0, 'current': 0, 'count': 0}
            by_type[asset_type]['invested'] += holding['invested_amount']
            by_type[asset_type]['current'] += holding['current_value']
            by_type[asset_type]['count'] += 1
        
        total_invested = sum(h['invested_amount'] for h in formatted_holdings)
        current_value = sum(h['current_value'] for h in formatted_holdings)
        total_pl = current_value - total_invested
        pl_percent = (total_pl / total_invested * 100) if total_invested > 0 else 0
        
        return {
            'holdings': formatted_holdings,
            'total_invested': total_invested,
            'current_value': current_value,
            'total_profit_loss': total_pl,
            'profit_loss_percent': pl_percent,
            'by_type': by_type
        }
    
    def get_market_overview(self) -> Dict:
        """Get market overview with all assets"""
        assets = db.get_market_assets()
        
        # Group by type
        by_type = {}
        for asset in assets:
            asset_type = asset['asset_type']
            if asset_type not in by_type:
                by_type[asset_type] = []
            
            by_type[asset_type].append({
                'asset_id': asset['asset_id'],
                'name': asset['asset_name'],
                'symbol': asset['asset_symbol'],
                'price': db.to_rupees(asset['current_price']),
                'change': asset['day_change_percent'],
                'volatility': asset['volatility_percent']
            })
        
        # Top gainers and losers
        sorted_assets = sorted(assets, key=lambda x: x['day_change_percent'] or 0, reverse=True)
        
        return {
            'by_type': by_type,
            'top_gainers': sorted_assets[:5],
            'top_losers': sorted_assets[-5:][::-1],
            'total_assets': len(assets)
        }
    
    def get_investment_history(self, user_id: int, limit: int = 50) -> List[Dict]:
        """Get investment transaction history"""
        transactions = db.execute(
            """SELECT it.*, ma.asset_name, ma.asset_symbol
               FROM investment_transactions it
               JOIN market_assets ma ON it.asset_id = ma.asset_id
               WHERE it.user_id = ?
               ORDER BY it.txn_date DESC
               LIMIT ?""",
            (user_id, limit),
            fetch=True
        )
        
        return [{
            'txn_id': t['txn_id'],
            'asset_name': t['asset_name'],
            'symbol': t['asset_symbol'],
            'type': t['txn_type'],
            'units': t['units'],
            'price_per_unit': db.to_rupees(t['price_per_unit']),
            'total_amount': db.to_rupees(t['total_amount']),
            'date': t['txn_date']
        } for t in transactions]
    
    def get_price_history(self, asset_id: int, days: int = 30) -> List[Dict]:
        """Get price history for an asset"""
        history = db.execute(
            """SELECT price, recorded_at
               FROM market_price_history
               WHERE asset_id = ? AND recorded_at >= date('now', ? || ' days')
               ORDER BY recorded_at""",
            (asset_id, f"-{days}"),
            fetch=True
        )
        
        return [{
            'price': db.to_rupees(h['price']),
            'date': h['recorded_at']
        } for h in history]


# Singleton instance
investment_service = InvestmentService()
