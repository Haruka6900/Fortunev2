"""
Stratégie de Scalping
"""

from .base_strategy import BaseStrategy
import pandas as pd
from typing import Dict, List
import numpy as np

class ScalpingStrategy(BaseStrategy):
    def __init__(self, params: Dict = None):
        default_params = self.get_default_params()
        if params:
            default_params.update(params)
        super().__init__("Scalping", default_params)
    
    def get_default_params(self) -> Dict:
        return {
            'timeframe': '1m',
            'spread_threshold': 0.001,  # 0.1%
            'volume_spike_ratio': 2.0,
            'quick_profit_target': 0.003,  # 0.3%
            'tight_stop_loss': 0.002,  # 0.2%
            'max_hold_time': 300  # 5 minutes max
        }
    
    async def analyze(self, data: pd.DataFrame) -> List[Dict]:
        """Analyser avec la stratégie de scalping"""
        if len(data) < 10:
            return []
        
        data = self.calculate_indicators(data)
        signals = []
        
        latest = data.iloc[-1]
        previous = data.iloc[-2]
        
        # Vérifier les conditions de marché pour le scalping
        if not self._is_good_scalping_conditions(data):
            return signals
        
        # Signal d'achat rapide
        if self._detect_buy_scalp_signal(data):
            signals.append({
                'strategy': self.name,
                'symbol': latest.name if hasattr(latest, 'name') else 'UNKNOWN',
                'side': 'buy',
                'type': 'market',
                'confidence': 0.75,
                'stop_loss': latest['close'] * (1 - self.params['tight_stop_loss']),
                'take_profit': latest['close'] * (1 + self.params['quick_profit_target']),
                'max_hold_time': self.params['max_hold_time'],
                'reason': "Scalping buy signal"
            })
        
        # Signal de vente rapide
        elif self._detect_sell_scalp_signal(data):
            signals.append({
                'strategy': self.name,
                'symbol': latest.name if hasattr(latest, 'name') else 'UNKNOWN',
                'side': 'sell',
                'type': 'market',
                'confidence': 0.75,
                'stop_loss': latest['close'] * (1 + self.params['tight_stop_loss']),
                'take_profit': latest['close'] * (1 - self.params['quick_profit_target']),
                'max_hold_time': self.params['max_hold_time'],
                'reason': "Scalping sell signal"
            })
        
        return signals
    
    def _is_good_scalping_conditions(self, data: pd.DataFrame) -> bool:
        """Vérifier si les conditions sont bonnes pour le scalping"""
        latest = data.iloc[-1]
        
        # Vérifier le volume
        volume_ratio = latest['volume'] / latest['volume_sma']
        if volume_ratio < self.params['volume_spike_ratio']:
            return False
        
        # Vérifier la volatilité (pas trop faible, pas trop élevée)
        volatility = data['close'].pct_change().rolling(5).std().iloc[-1]
        if volatility < 0.001 or volatility > 0.01:
            return False
        
        return True
    
    def _detect_buy_scalp_signal(self, data: pd.DataFrame) -> bool:
        """Détecter un signal d'achat pour scalping"""
        latest = data.iloc[-1]
        previous = data.iloc[-2]
        
        # Prix rebondit sur support (Bollinger Band inférieure)
        if (previous['close'] <= previous['bb_lower'] and 
            latest['close'] > previous['bb_lower'] and
            latest['rsi'] < 40):
            return True
        
        # Momentum haussier rapide
        if (latest['close'] > previous['close'] * 1.002 and
            latest['volume'] > latest['volume_sma'] * 1.5):
            return True
        
        return False
    
    def _detect_sell_scalp_signal(self, data: pd.DataFrame) -> bool:
        """Détecter un signal de vente pour scalping"""
        latest = data.iloc[-1]
        previous = data.iloc[-2]
        
        # Prix rejette résistance (Bollinger Band supérieure)
        if (previous['close'] >= previous['bb_upper'] and 
            latest['close'] < previous['bb_upper'] and
            latest['rsi'] > 60):
            return True
        
        # Momentum baissier rapide
        if (latest['close'] < previous['close'] * 0.998 and
            latest['volume'] > latest['volume_sma'] * 1.5):
            return True
        
        return False
