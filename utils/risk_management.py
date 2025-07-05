"""
Gestionnaire de risques pour le trading
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime, timedelta

class RiskManager:
    def __init__(self, config: Dict):
        self.config = config
        self.daily_pnl = 0
        self.daily_trades = 0
        self.max_daily_loss = config.get('daily_loss_limit', 0.05)
        self.max_drawdown = config.get('max_drawdown', 0.15)
        self.position_sizing_method = config.get('position_sizing', 'kelly')
        self.trade_history = []
    
    def filter_signals(self, signals: List[Dict], current_positions: Dict) -> List[Dict]:
        """Filtrer les signaux selon les règles de gestion des risques"""
        filtered_signals = []
        
        for signal in signals:
            if self._should_execute_signal(signal, current_positions):
                filtered_signals.append(signal)
        
        return filtered_signals
    
    def _should_execute_signal(self, signal: Dict, current_positions: Dict) -> bool:
        """Déterminer si un signal doit être exécuté"""
        # Vérifier la limite de perte journalière
        if self.daily_pnl < -self.max_daily_loss:
            return False
        
        # Vérifier le nombre maximum de positions
        if len(current_positions) >= 5:  # Limite configurable
            return False
        
        # Vérifier si on a déjà une position sur ce symbole
        symbol = signal['symbol']
        if symbol in current_positions:
            # Ne pas ouvrir de position opposée
            if current_positions[symbol]['side'] != signal['side']:
                return False
        
        # Vérifier la confiance minimale
        if signal.get('confidence', 0) < 0.5:
            return False
        
        return True
    
    def calculate_position_size(self, signal: Dict, account_balance: float) -> float:
        """Calculer la taille de position optimale"""
        if self.position_sizing_method == 'fixed':
            return self._fixed_position_size(account_balance)
        elif self.position_sizing_method == 'percentage':
            return self._percentage_position_size(signal, account_balance)
        elif self.position_sizing_method == 'kelly':
            return self._kelly_position_size(signal, account_balance)
        elif self.position_sizing_method == 'volatility':
            return self._volatility_adjusted_size(signal, account_balance)
        else:
            return self._fixed_position_size(account_balance)
    
    def _fixed_position_size(self, account_balance: float) -> float:
        """Taille de position fixe"""
        return min(100, account_balance * 0.1)  # 10% du solde, max 100$
    
    def _percentage_position_size(self, signal: Dict, account_balance: float) -> float:
        """Taille basée sur un pourcentage du solde"""
        risk_per_trade = self.config.get('default_risk_per_trade', 0.02)
        return account_balance * risk_per_trade
    
    def _kelly_position_size(self, signal: Dict, account_balance: float) -> float:
        """Taille basée sur le critère de Kelly"""
        # Calculer les probabilités basées sur l'historique de la stratégie
        strategy_name = signal.get('strategy', 'unknown')
        win_rate, avg_win, avg_loss = self._get_strategy_stats(strategy_name)
        
        if win_rate == 0 or avg_loss == 0:
            return self._percentage_position_size(signal, account_balance)
        
        # Formule de Kelly: f = (bp - q) / b
        # où b = avg_win/avg_loss, p = win_rate, q = 1-win_rate
        b = avg_win / avg_loss
        p = win_rate
        q = 1 - win_rate
        
        kelly_fraction = (b * p - q) / b
        kelly_fraction = max(0, min(0.25, kelly_fraction))  # Limiter à 25%
        
        return account_balance * kelly_fraction
    
    def _volatility_adjusted_size(self, signal: Dict, account_balance: float) -> float:
        """Taille ajustée selon la volatilité"""
        base_size = self._percentage_position_size(signal, account_balance)
        
        # Ajuster selon la confiance du signal
        confidence = signal.get('confidence', 0.5)
        confidence_multiplier = 0.5 + confidence
        
        return base_size * confidence_multiplier
    
    def _get_strategy_stats(self, strategy_name: str) -> tuple:
        """Obtenir les statistiques d'une stratégie"""
        strategy_trades = [t for t in self.trade_history if t.get('strategy') == strategy_name]
        
        if not strategy_trades:
            return 0.5, 1, 1  # Valeurs par défaut
        
        wins = [t for t in strategy_trades if t['profit'] > 0]
        losses = [t for t in strategy_trades if t['profit'] < 0]
        
        win_rate = len(wins) / len(strategy_trades) if strategy_trades else 0.5
        avg_win = np.mean([t['profit'] for t in wins]) if wins else 1
        avg_loss = abs(np.mean([t['profit'] for t in losses])) if losses else 1
        
        return win_rate, avg_win, avg_loss
    
    def update_daily_pnl(self, pnl: float):
        """Mettre à jour le P&L journalier"""
        self.daily_pnl += pnl
        self.daily_trades += 1
    
    def reset_daily_stats(self):
        """Réinitialiser les statistiques journalières"""
        self.daily_pnl = 0
        self.daily_trades = 0
    
    def record_trade(self, trade_result: Dict):
        """Enregistrer un trade dans l'historique"""
        trade_result['timestamp'] = datetime.now()
        self.trade_history.append(trade_result)
        
        # Garder seulement les 1000 derniers trades
        if len(self.trade_history) > 1000:
            self.trade_history = self.trade_history[-1000:]
    
    def get_risk_metrics(self) -> Dict:
        """Calculer les métriques de risque"""
        if not self.trade_history:
            return {}
        
        profits = [t['profit'] for t in self.trade_history]
        
        return {
            'total_trades': len(self.trade_history),
            'win_rate': len([p for p in profits if p > 0]) / len(profits),
            'avg_profit': np.mean(profits),
            'max_profit': max(profits),
            'max_loss': min(profits),
            'sharpe_ratio': self._calculate_sharpe_ratio(profits),
            'max_drawdown': self._calculate_max_drawdown(profits),
            'daily_pnl': self.daily_pnl,
            'daily_trades': self.daily_trades
        }
    
    def _calculate_sharpe_ratio(self, profits: List[float]) -> float:
        """Calculer le ratio de Sharpe"""
        if not profits or np.std(profits) == 0:
            return 0
        return np.mean(profits) / np.std(profits)
    
    def _calculate_max_drawdown(self, profits: List[float]) -> float:
        """Calculer le drawdown maximum"""
        if not profits:
            return 0
        
        cumulative = np.cumsum(profits)
        running_max = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - running_max) / running_max
        
        return abs(np.min(drawdown)) if len(drawdown) > 0 else 0
