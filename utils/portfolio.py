"""
Gestionnaire de portefeuille
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional
import json
import os

class PortfolioManager:
    def __init__(self, config: Dict):
        self.config = config
        self.mode = config.get('mode', 'paper')
        self.base_currency = config.get('base_currency', 'USDT')
        self.positions = {}
        self.balance = 10000.0  # Solde initial en mode papier
        self.orders = []
        self.trade_history = []
        self.portfolio_file = 'data/portfolio.json'
        
    async def initialize(self):
        """Initialiser le gestionnaire de portefeuille"""
        self._load_portfolio()
        print(f"Portfolio initialisé en mode {self.mode}")
        print(f"Solde initial: {self.balance} {self.base_currency}")
    
    def _load_portfolio(self):
        """Charger le portefeuille depuis le fichier"""
        if os.path.exists(self.portfolio_file):
            try:
                with open(self.portfolio_file, 'r') as f:
                    data = json.load(f)
                    self.balance = data.get('balance', 10000.0)
                    self.positions = data.get('positions', {})
                    self.trade_history = data.get('trade_history', [])
            except Exception as e:
                print(f"Erreur lors du chargement du portefeuille: {e}")
    
    def _save_portfolio(self):
        """Sauvegarder le portefeuille"""
        os.makedirs(os.path.dirname(self.portfolio_file), exist_ok=True)
        
        data = {
            'balance': self.balance,
            'positions': self.positions,
            'trade_history': self.trade_history,
            'last_updated': datetime.now().isoformat()
        }
        
        try:
            with open(self.portfolio_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            print(f"Erreur lors de la sauvegarde du portefeuille: {e}")
    
    async def place_order(self, symbol: str, side: str, amount: float, 
                         price: Optional[float] = None, order_type: str = 'market') -> Dict:
        """Placer un ordre"""
        try:
            if self.mode == 'paper':
                return await self._place_paper_order(symbol, side, amount, price, order_type)
            else:
                return await self._place_real_order(symbol, side, amount, price, order_type)
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _place_paper_order(self, symbol: str, side: str, amount: float,
                                price: Optional[float], order_type: str) -> Dict:
        """Placer un ordre en mode papier"""
        # Simuler l'exécution d'un ordre
        current_price = price or self._get_current_price(symbol)
        
        if side == 'buy':
            cost = amount
            quantity = cost / current_price
            
            if cost > self.balance:
                return {'success': False, 'error': 'Solde insuffisant'}
            
            # Exécuter l'achat
            self.balance -= cost
            
            if symbol in self.positions:
                # Moyenner la position
                old_qty = self.positions[symbol]['quantity']
                old_price = self.positions[symbol]['avg_price']
                new_qty = old_qty + quantity
                new_avg_price = ((old_qty * old_price) + (quantity * current_price)) / new_qty
                
                self.positions[symbol].update({
                    'quantity': new_qty,
                    'avg_price': new_avg_price
                })
            else:
                self.positions[symbol] = {
                    'quantity': quantity,
                    'avg_price': current_price,
                    'side': 'long',
                    'entry_time': datetime.now().isoformat()
                }
        
        else:  # sell
            if symbol not in self.positions:
                return {'success': False, 'error': 'Aucune position à vendre'}
            
            position = self.positions[symbol]
            sell_quantity = min(amount / current_price, position['quantity'])
            proceeds = sell_quantity * current_price
            
            # Calculer le profit
            profit = (current_price - position['avg_price']) * sell_quantity
            
            # Exécuter la vente
            self.balance += proceeds
            position['quantity'] -= sell_quantity
            
            # Supprimer la position si entièrement vendue
            if position['quantity'] <= 0.001:
                del self.positions[symbol]
        
        # Enregistrer le trade
        trade_record = {
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'side': side,
            'quantity': quantity if side == 'buy' else sell_quantity,
            'price': current_price,
            'amount': amount,
            'profit': profit if side == 'sell' else 0
        }
        
        self.trade_history.append(trade_record)
        self._save_portfolio()
        
        return {
            'success': True,
            'order_id': f"paper_{len(self.trade_history)}",
            'symbol': symbol,
            'side': side,
            'quantity': quantity if side == 'buy' else sell_quantity,
            'price': current_price,
            'entry_price': current_price,
            'profit': profit if side == 'sell' else 0
        }
    
    async def _place_real_order(self, symbol: str, side: str, amount: float,
                               price: Optional[float], order_type: str) -> Dict:
        """Placer un ordre réel (à implémenter selon l'exchange)"""
        # Implémentation pour les ordres réels
        # selon l'exchange configuré (Binance, etc.)
        return {'success': False, 'error': 'Mode réel non implémenté'}
    
    def _get_current_price(self, symbol: str) -> float:
        """Obtenir le prix actuel d'un symbole"""
        # Simulation - dans un vrai système, récupérer depuis market_data
        base_prices = {
            'BTCUSDT': 45000,
            'ETHUSDT': 3000,
            'ADAUSDT': 0.5,
            'DOTUSDT': 8,
            'LINKUSDT': 15
        }
        return base_prices.get(symbol, 100)
    
    def get_balance(self) -> float:
        """Obtenir le solde actuel"""
        return self.balance
    
    def get_current_positions(self) -> Dict:
        """Obtenir les positions actuelles"""
        return self.positions.copy()
    
    def get_portfolio_value(self) -> float:
        """Calculer la valeur totale du portefeuille"""
        total_value = self.balance
        
        for symbol, position in self.positions.items():
            current_price = self._get_current_price(symbol)
            position_value = position['quantity'] * current_price
            total_value += position_value
        
        return total_value
    
    def get_portfolio_summary(self) -> Dict:
        """Obtenir un résumé du portefeuille"""
        total_value = self.get_portfolio_value()
        
        # Calculer les profits/pertes
        total_pnl = 0
        for trade in self.trade_history:
            total_pnl += trade.get('profit', 0)
        
        # Calculer les positions actuelles
        positions_value = 0
        for symbol, position in self.positions.items():
            current_price = self._get_current_price(symbol)
            position_value = position['quantity'] * current_price
            positions_value += position_value
            
            # P&L non réalisé
            unrealized_pnl = (current_price - position['avg_price']) * position['quantity']
            total_pnl += unrealized_pnl
        
        return {
            'total_value': total_value,
            'cash_balance': self.balance,
            'positions_value': positions_value,
            'total_pnl': total_pnl,
            'pnl_percentage': (total_pnl / 10000) * 100,  # Basé sur le capital initial
            'active_positions': len(self.positions),
            'total_trades': len(self.trade_history)
        }
