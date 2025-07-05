"""
Classe de base pour toutes les stratégies de trading
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
import pandas as pd
import numpy as np

class BaseStrategy(ABC):
    def __init__(self, name: str, params: Dict):
        self.name = name
        self.params = params
        self.performance_history = []
        self.active_positions = {}
        
    @abstractmethod
    async def analyze(self, data: pd.DataFrame) -> List[Dict]:
        """Analyser les données et retourner des signaux de trading"""
        pass
    
    @abstractmethod
    def get_default_params(self) -> Dict:
        """Retourner les paramètres par défaut de la stratégie"""
        pass
    
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculer les indicateurs techniques de base"""
        # Make a copy to avoid modifying original data
        data = data.copy()
        
        # RSI
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        data['rsi'] = 100 - (100 / (1 + rs))
        
        # MACD
        exp1 = data['close'].ewm(span=12).mean()
        exp2 = data['close'].ewm(span=26).mean()
        data['macd'] = exp1 - exp2
        data['macd_signal'] = data['macd'].ewm(span=9).mean()
        data['macd_histogram'] = data['macd'] - data['macd_signal']
        
        # Bollinger Bands
        data['bb_middle'] = data['close'].rolling(window=20).mean()
        bb_std = data['close'].rolling(window=20).std()
        data['bb_upper'] = data['bb_middle'] + (bb_std * 2)
        data['bb_lower'] = data['bb_middle'] - (bb_std * 2)
        
        # Moving Averages
        data['sma_20'] = data['close'].rolling(window=20).mean()
        data['sma_50'] = data['close'].rolling(window=50).mean()
        data['ema_12'] = data['close'].ewm(span=12).mean()
        data['ema_26'] = data['close'].ewm(span=26).mean()
        
        # Volume indicators
        data['volume_sma'] = data['volume'].rolling(window=20).mean()
        
        return data
    
    def update_performance(self, trade_result: Dict):
        """Mettre à jour les performances de la stratégie"""
        self.performance_history.append(trade_result)
    
    def get_performance_metrics(self) -> Dict:
        """Calculer les métriques de performance"""
        if not self.performance_history:
            return {}
        
        profits = [trade['profit'] for trade in self.performance_history]
        win_rate = len([p for p in profits if p > 0]) / len(profits)
        avg_profit = np.mean(profits)
        max_profit = max(profits)
        max_loss = min(profits)
        
        return {
            'total_trades': len(self.performance_history),
            'win_rate': win_rate,
            'avg_profit': avg_profit,
            'max_profit': max_profit,
            'max_loss': max_loss,
            'total_profit': sum(profits)
        }
    
    def optimize_parameters(self, historical_data: pd.DataFrame) -> Dict:
        """Optimiser les paramètres de la stratégie"""
        # Implémentation basique d'optimisation
        # À surcharger dans les stratégies spécifiques
        return self.params
