"""
Market Engine - Global Investment System
Handles realistic market price movements affecting ALL users equally
"""

import random
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
import requests


class MarketEngine:
    """
    Global market engine that simulates realistic price movements.
    When prices change, ALL users holding that asset are affected equally.
    """

    def __init__(self, db):
        self.db = db
        self.api_enabled = False  # Set True to use real APIs
        
    # ==================================================
    # MARKET PRICE UPDATES (GLOBAL)
    # ==================================================
    
    def update_all_market_prices(self):
        """
        Update prices for ALL assets in the market.
        This affects every user's portfolio value globally.
        """
        assets = self.db.execute_query(
            "SELECT * FROM market_assets WHERE is_active = TRUE",
            fetch=True
        )
        
        if not assets:
            return []
        
        updated_assets = []
        
        for asset in assets:
            old_price = float(asset['current_price'])
            volatility = float(asset['volatility_percent'])
            
            # Get new price (API or simulation)
            if self.api_enabled and asset['asset_type'] == 'CRYPTO':
                new_price = self._fetch_crypto_price(asset['asset_symbol'])
            else:
                new_price = self._simulate_price_movement(old_price, volatility)
            
            if new_price and new_price != old_price:
                change_percent = ((new_price - old_price) / old_price) * 100
                
                # Update asset price
                self.db.execute_query(
                    """UPDATE market_assets 
                       SET previous_price = current_price,
                           current_price = %s,
                           day_change_percent = %s,
                           last_updated = NOW()
                       WHERE asset_id = %s""",
                    (new_price, change_percent, asset['asset_id'])
                )
                
                # Record price history
                self.db.execute_query(
                    "INSERT INTO market_price_history (asset_id, price) VALUES (%s, %s)",
                    (asset['asset_id'], new_price)
                )
                
                updated_assets.append({
                    'name': asset['asset_name'],
                    'symbol': asset['asset_symbol'],
                    'old_price': old_price,
                    'new_price': new_price,
                    'change_percent': change_percent
                })
        
        # Update all users' portfolio values
        self._recalculate_all_portfolios()
        
        return updated_assets
    
    def _simulate_price_movement(self, current_price, volatility):
        """
        Simulate realistic price movement based on volatility.
        Uses random walk with mean reversion tendency.
        """
        # Random direction with slight upward bias (markets tend to grow)
        direction = random.choice([1, 1, 1, -1, -1])  # 60% up, 40% down
        
        # Movement percentage based on volatility
        max_change = volatility / 100
        change = random.uniform(0, max_change) * direction
        
        # Apply change
        new_price = current_price * (1 + change)
        
        # Ensure minimum price
        new_price = max(new_price, 0.01)
        
        # Round to 4 decimal places
        return round(new_price, 4)
    
    def _fetch_crypto_price(self, symbol):
        """Fetch real crypto price from API (optional)"""
        try:
            # Using CoinGecko free API
            symbol_map = {
                'BTC': 'bitcoin',
                'ETH': 'ethereum',
                'SOL': 'solana',
                'ADA': 'cardano'
            }
            
            coin_id = symbol_map.get(symbol)
            if not coin_id:
                return None
            
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=inr"
            response = requests.get(url, timeout=5)
            data = response.json()
            
            if coin_id in data:
                return float(data[coin_id]['inr'])
            
        except Exception as e:
            print(f"API Error: {e}")
        
        return None
    
    def _recalculate_all_portfolios(self):
        """Recalculate portfolio values for ALL users after market update"""
        self.db.execute_query("""
            UPDATE user_analytics_cache uac
            SET investment_current_value = (
                SELECT COALESCE(SUM(ui.units_owned * ma.current_price), 0)
                FROM user_investments ui
                JOIN market_assets ma ON ui.asset_id = ma.asset_id
                WHERE ui.user_id = uac.user_id
            ),
            last_calculated = NOW()
        """)
    
    # ==================================================
    # USER INVESTMENT OPERATIONS
    # ==================================================
    
    def buy_asset(self, user_id, asset_id, amount, source_account_type='WALLET', source_account_id=None):
        """
        User buys an asset at current market price.
        Returns: (success, message, transaction_details)
        """
        # Get asset details
        asset = self.db.execute_query(
            "SELECT * FROM market_assets WHERE asset_id = %s AND is_active = TRUE",
            (asset_id,), fetch=True
        )
        
        if not asset:
            return False, "Asset not found or inactive", None
        
        asset = asset[0]
        current_price = float(asset['current_price'])
        
        # Check user balance
        if source_account_type == 'WALLET':
            balance = self.db.get_user_balance(user_id)
        elif source_account_type == 'BANK':
            balance = self.db.get_bank_account_balance(source_account_id)
        else:
            return False, "Invalid account type", None
        
        if balance < amount:
            return False, f"Insufficient balance. Available: ₹{balance:.2f}", None
        
        # Calculate units
        units = amount / current_price
        
        # Deduct from account
        if source_account_type == 'WALLET':
            new_balance = balance - amount
            self.db.update_user_balance(user_id, new_balance)
            self.db.add_transaction(user_id, 'INVESTMENT', amount, new_balance)
        else:
            new_balance = balance - amount
            self.db.update_bank_account_balance(source_account_id, new_balance)
        
        # Check if user already owns this asset
        existing = self.db.execute_query(
            "SELECT * FROM user_investments WHERE user_id = %s AND asset_id = %s",
            (user_id, asset_id), fetch=True
        )
        
        if existing:
            # Average the buy price
            existing = existing[0]
            total_units = float(existing['units_owned']) + units
            total_invested = float(existing['invested_amount']) + amount
            avg_price = total_invested / total_units
            
            self.db.execute_query(
                """UPDATE user_investments 
                   SET units_owned = %s, invested_amount = %s, buy_price = %s
                   WHERE investment_id = %s""",
                (total_units, total_invested, avg_price, existing['investment_id'])
            )
        else:
            # New investment
            self.db.execute_query(
                """INSERT INTO user_investments 
                   (user_id, asset_id, units_owned, buy_price, invested_amount)
                   VALUES (%s, %s, %s, %s, %s)""",
                (user_id, asset_id, units, current_price, amount)
            )
        
        # Log transaction
        self.db.execute_query(
            """INSERT INTO investment_transactions 
               (user_id, asset_id, txn_type, units, price_per_unit, total_amount)
               VALUES (%s, %s, 'BUY', %s, %s, %s)""",
            (user_id, asset_id, units, current_price, amount)
        )
        
        return True, "Investment successful", {
            'asset': asset['asset_name'],
            'units': units,
            'price': current_price,
            'total': amount
        }
    
    def sell_asset(self, user_id, asset_id, units_to_sell, target_account_type='WALLET', target_account_id=None):
        """
        User sells an asset at current market price.
        """
        # Get user's holding
        holding = self.db.execute_query(
            """SELECT ui.*, ma.current_price, ma.asset_name
               FROM user_investments ui
               JOIN market_assets ma ON ui.asset_id = ma.asset_id
               WHERE ui.user_id = %s AND ui.asset_id = %s""",
            (user_id, asset_id), fetch=True
        )
        
        if not holding:
            return False, "You don't own this asset", None
        
        holding = holding[0]
        owned_units = float(holding['units_owned'])
        
        if units_to_sell > owned_units:
            return False, f"Insufficient units. You own: {owned_units:.4f}", None
        
        current_price = float(holding['current_price'])
        sale_amount = units_to_sell * current_price
        buy_price = float(holding['buy_price'])
        
        # Calculate profit/loss
        cost_basis = units_to_sell * buy_price
        profit_loss = sale_amount - cost_basis
        
        # Credit to account
        if target_account_type == 'WALLET':
            balance = self.db.get_user_balance(user_id)
            new_balance = balance + sale_amount
            self.db.update_user_balance(user_id, new_balance)
            self.db.add_transaction(user_id, 'INCOME', sale_amount, new_balance)
        else:
            balance = self.db.get_bank_account_balance(target_account_id)
            new_balance = balance + sale_amount
            self.db.update_bank_account_balance(target_account_id, new_balance)
        
        # Update or remove holding
        remaining_units = owned_units - units_to_sell
        
        if remaining_units <= 0.000001:  # Essentially zero
            self.db.execute_query(
                "DELETE FROM user_investments WHERE investment_id = %s",
                (holding['investment_id'],)
            )
        else:
            remaining_invested = remaining_units * buy_price
            self.db.execute_query(
                """UPDATE user_investments 
                   SET units_owned = %s, invested_amount = %s
                   WHERE investment_id = %s""",
                (remaining_units, remaining_invested, holding['investment_id'])
            )
        
        # Log transaction
        self.db.execute_query(
            """INSERT INTO investment_transactions 
               (user_id, asset_id, txn_type, units, price_per_unit, total_amount)
               VALUES (%s, %s, 'SELL', %s, %s, %s)""",
            (user_id, asset_id, units_to_sell, current_price, sale_amount)
        )
        
        return True, "Sale successful", {
            'asset': holding['asset_name'],
            'units_sold': units_to_sell,
            'price': current_price,
            'total': sale_amount,
            'profit_loss': profit_loss
        }
    
    # ==================================================
    # PORTFOLIO & ANALYTICS
    # ==================================================
    
    def get_user_portfolio(self, user_id):
        """Get user's complete investment portfolio with current values"""
        holdings = self.db.execute_query(
            """SELECT ui.*, ma.asset_name, ma.asset_symbol, ma.asset_type,
                      ma.current_price, ma.day_change_percent,
                      (ui.units_owned * ma.current_price) as current_value,
                      ((ui.units_owned * ma.current_price) - ui.invested_amount) as profit_loss
               FROM user_investments ui
               JOIN market_assets ma ON ui.asset_id = ma.asset_id
               WHERE ui.user_id = %s
               ORDER BY current_value DESC""",
            (user_id,), fetch=True
        )
        
        if not holdings:
            return {
                'holdings': [],
                'total_invested': 0,
                'current_value': 0,
                'total_profit_loss': 0,
                'profit_loss_percent': 0
            }
        
        total_invested = sum(float(h['invested_amount']) for h in holdings)
        current_value = sum(float(h['current_value']) for h in holdings)
        total_pl = current_value - total_invested
        pl_percent = (total_pl / total_invested * 100) if total_invested > 0 else 0
        
        return {
            'holdings': holdings,
            'total_invested': total_invested,
            'current_value': current_value,
            'total_profit_loss': total_pl,
            'profit_loss_percent': pl_percent
        }
    
    def get_market_overview(self):
        """Get overview of all market assets"""
        return self.db.execute_query(
            """SELECT asset_id, asset_name, asset_symbol, asset_type,
                      current_price, previous_price, day_change_percent,
                      volatility_percent, last_updated
               FROM market_assets
               WHERE is_active = TRUE
               ORDER BY asset_type, asset_name""",
            fetch=True
        )
    
    def get_top_gainers_losers(self, limit=5):
        """Get top gaining and losing assets"""
        gainers = self.db.execute_query(
            """SELECT asset_name, asset_symbol, current_price, day_change_percent
               FROM market_assets WHERE is_active = TRUE
               ORDER BY day_change_percent DESC LIMIT %s""",
            (limit,), fetch=True
        )
        
        losers = self.db.execute_query(
            """SELECT asset_name, asset_symbol, current_price, day_change_percent
               FROM market_assets WHERE is_active = TRUE
               ORDER BY day_change_percent ASC LIMIT %s""",
            (limit,), fetch=True
        )
        
        return {'gainers': gainers, 'losers': losers}
    
    # ==================================================
    # NET WORTH CALCULATION
    # ==================================================
    
    def calculate_user_net_worth(self, user_id):
        """
        Calculate complete net worth for a user.
        Net Worth = Wallet + Bank Balances + Manual Accounts + Investment Value
        """
        # Wallet balance
        wallet = self.db.get_user_balance(user_id) or 0
        
        # Bank balances
        bank_result = self.db.execute_query(
            "SELECT COALESCE(SUM(balance), 0) as total FROM bank_accounts WHERE user_id = %s",
            (user_id,), fetch=True
        )
        bank_total = float(bank_result[0]['total']) if bank_result else 0
        
        # Manual accounts
        manual_result = self.db.execute_query(
            "SELECT COALESCE(SUM(balance), 0) as total FROM manual_accounts WHERE user_id = %s",
            (user_id,), fetch=True
        )
        manual_total = float(manual_result[0]['total']) if manual_result else 0
        
        # Investment current value
        investment_result = self.db.execute_query(
            """SELECT COALESCE(SUM(ui.units_owned * ma.current_price), 0) as total
               FROM user_investments ui
               JOIN market_assets ma ON ui.asset_id = ma.asset_id
               WHERE ui.user_id = %s""",
            (user_id,), fetch=True
        )
        investment_total = float(investment_result[0]['total']) if investment_result else 0
        
        net_worth = float(wallet) + bank_total + manual_total + investment_total
        
        # Update cache
        self.db.execute_query(
            """INSERT INTO user_analytics_cache 
               (user_id, investment_current_value, net_worth, last_calculated)
               VALUES (%s, %s, %s, NOW())
               ON DUPLICATE KEY UPDATE 
               investment_current_value = VALUES(investment_current_value),
               net_worth = VALUES(net_worth),
               last_calculated = NOW()""",
            (user_id, investment_total, net_worth)
        )
        
        return {
            'wallet': float(wallet),
            'bank_accounts': bank_total,
            'manual_accounts': manual_total,
            'investments': investment_total,
            'net_worth': net_worth
        }
    
    def get_net_worth_leaderboard(self, limit=10):
        """Get top users by net worth"""
        # First update all net worth values
        users = self.db.execute_query("SELECT user_id FROM users WHERE status = 'ACTIVE'", fetch=True)
        
        for user in users:
            self.calculate_user_net_worth(user['user_id'])
        
        # Get leaderboard
        return self.db.execute_query(
            """SELECT u.user_id, u.username, u.email, 
                      COALESCE(uac.net_worth, 0) as net_worth,
                      COALESCE(uac.investment_current_value, 0) as investment_value
               FROM users u
               LEFT JOIN user_analytics_cache uac ON u.user_id = uac.user_id
               WHERE u.status = 'ACTIVE'
               ORDER BY net_worth DESC
               LIMIT %s""",
            (limit,), fetch=True
        )
