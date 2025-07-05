"""
Module de backtesting pour les stratégies de trading
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import asyncio
from strategies.strategy_manager import StrategyManager
from utils.risk_management import RiskManager
from utils.memory import TradingMemory

class BacktestEngine:
    def __init__(self, initial_capital: float = 10000):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.positions = {}
        self.trades = []
        self.equity_curve = []
        
    async def run_backtest(self, strategy_name: str, data: pd.DataFrame, 
                          start_date: str, end_date: str) -> Dict:
        """Exécuter un backtest pour une stratégie donnée"""
        
        # Filtrer les données par période
        mask = (data.index >= start_date) & (data.index <= end_date)
        test_data = data.loc[mask].copy()
        
        if len(test_data) == 0:
            return {'error': 'Aucune donnée pour la période spécifiée'}
        
        # Initialiser les composants
        memory = TradingMemory()
        risk_manager = RiskManager({'daily_loss_limit': 0.05, 'max_drawdown': 0.15})
        
        config = {'enabled': [strategy_name], 'auto_tune': False}
        strategy_manager = StrategyManager(config, memory, risk_manager)
        
        # Simuler le trading jour par jour
        for i in range(len(test_data)):
            current_data = test_data.iloc[:i+1]
            
            if len(current_data) < 50:  # Besoin de données suffisantes
                continue
            
            # Analyser avec la stratégie
            market_data = {strategy_name: current_data}
            signals = await strategy_manager.analyze_market(market_data)
            
            # Exécuter les signaux
            for signal in signals:
                await self._execute_backtest_trade(signal, current_data.iloc[-1])
            
            # Enregistrer l'équité
            current_equity = self._calculate_current_equity(current_data.iloc[-1])
            self.equity_curve.append({
                'timestamp': current_data.index[-1],
                'equity': current_equity,
                'capital': self.capital
            })
        
        # Calculer les métriques de performance
        return self._calculate_performance_metrics()
    
    async def _execute_backtest_trade(self, signal: Dict, current_bar: pd.Series):
        """Exécuter un trade en mode backtest"""
        symbol = signal['symbol']
        side = signal['side']
        current_price = current_bar['close']
        
        # Calculer la taille de position (2% du capital)
        position_size = self.capital * 0.02 / current_price
        
        if side == 'buy':
            cost = position_size * current_price
            if cost <= self.capital:
                self.capital -= cost
                
                if symbol in self.positions:
                    # Moyenner la position
                    old_qty = self.positions[symbol]['quantity']
                    old_price = self.positions[symbol]['avg_price']
                    new_qty = old_qty + position_size
                    new_avg_price = ((old_qty * old_price) + (position_size * current_price)) / new_qty
                    
                    self.positions[symbol].update({
                        'quantity': new_qty,
                        'avg_price': new_avg_price
                    })
                else:
                    self.positions[symbol] = {
                        'quantity': position_size,
                        'avg_price': current_price,
                        'entry_time': current_bar.name
                    }
        
        elif side == 'sell' and symbol in self.positions:
            position = self.positions[symbol]
            sell_quantity = min(position_size, position['quantity'])
            proceeds = sell_quantity * current_price
            
            # Calculer le profit
            profit = (current_price - position['avg_price']) * sell_quantity
            
            self.capital += proceeds
            position['quantity'] -= sell_quantity
            
            # Enregistrer le trade
            self.trades.append({
                'timestamp': current_bar.name,
                'symbol': symbol,
                'side': side,
                'quantity': sell_quantity,
                'price': current_price,
                'profit': profit,
                'strategy': signal['strategy']
            })
            
            # Supprimer la position si entièrement vendue
            if position['quantity'] <= 0.001:
                del self.positions[symbol]
    
    def _calculate_current_equity(self, current_bar: pd.Series) -> float:
        """Calculer l'équité actuelle"""
        equity = self.capital
        
        # Ajouter la valeur des positions ouvertes
        for symbol, position in self.positions.items():
            current_price = current_bar['close']  # Simplification
            position_value = position['quantity'] * current_price
            equity += position_value
        
        return equity
    
    def _calculate_performance_metrics(self) -> Dict:
        """Calculer les métriques de performance du backtest"""
        if not self.trades:
            return {'error': 'Aucun trade exécuté'}
        
        # Métriques de base
        profits = [trade['profit'] for trade in self.trades]
        total_return = (self.equity_curve[-1]['equity'] - self.initial_capital) / self.initial_capital
        
        # Win rate
        winning_trades = [p for p in profits if p > 0]
        win_rate = len(winning_trades) / len(profits)
        
        # Profit factor
        gross_profit = sum(winning_trades)
        gross_loss = abs(sum([p for p in profits if p < 0]))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        # Sharpe ratio
        returns = []
        for i in range(1, len(self.equity_curve)):
            ret = (self.equity_curve[i]['equity'] - self.equity_curve[i-1]['equity']) / self.equity_curve[i-1]['equity']
            returns.append(ret)
        
        sharpe_ratio = np.mean(returns) / np.std(returns) if np.std(returns) > 0 else 0
        
        # Maximum drawdown
        equity_values = [point['equity'] for point in self.equity_curve]
        peak = equity_values[0]
        max_drawdown = 0
        
        for value in equity_values:
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        return {
            'total_trades': len(self.trades),
            'winning_trades': len(winning_trades),
            'losing_trades': len(profits) - len(winning_trades),
            'win_rate': win_rate,
            'total_return': total_return,
            'profit_factor': profit_factor,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'avg_profit': np.mean(profits),
            'max_profit': max(profits),
            'max_loss': min(profits),
            'initial_capital': self.initial_capital,
            'final_equity': self.equity_curve[-1]['equity'],
            'equity_curve': self.equity_curve,
            'trades': self.trades
        }

async def run_strategy_backtest(strategy_name: str, symbol: str, days: int = 30) -> Dict:
    """Fonction utilitaire pour lancer un backtest"""
    from utils.market_data import MarketDataManager
    
    # Configuration pour les données de test
    config = {'mode': 'paper', 'exchange': 'binance', 'testnet': True}
    market_data_manager = MarketDataManager(config)
    
    # Récupérer les données historiques
    await market_data_manager.connect()
    historical_data = await market_data_manager.get_historical_data(symbol, days)
    await market_data_manager.disconnect()
    
    if historical_data is None:
        return {'error': 'Impossible de récupérer les données historiques'}
    
    # Exécuter le backtest
    backtest_engine = BacktestEngine()
    
    start_date = historical_data.index[0]
    end_date = historical_data.index[-1]
    
    results = await backtest_engine.run_backtest(
        strategy_name, 
        historical_data, 
        start_date.strftime('%Y-%m-%d'), 
        end_date.strftime('%Y-%m-%d')
    )
    
    return results
