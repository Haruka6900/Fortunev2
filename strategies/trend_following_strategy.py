"""
Stratégie de suivi de tendance
"""

from .base_strategy import BaseStrategy
import pandas as pd
from typing import Dict, List
import numpy as np

class TrendFollowingStrategy(BaseStrategy):
    def __init__(self, params: Dict = None):
        default_params = self.get_default_params()
        if params:
            default_params.update(params)
        super().__init__("TrendFollowing", default_params)
    
    def get_default_params(self) -> Dict:
        return {
            'fast_ma': 20,
            'slow_ma': 50,
            'trend_strength_period': 14,
            'min_trend_strength': 0.6,
            'trailing_stop_pct': 0.05,
            'breakout_threshold': 0.02
        }
    
    async def analyze(self, data: pd.DataFrame) -> List[Dict]:
        """Analyser avec la stratégie de suivi de tendance"""
        if len(data) < self.params['slow_ma'] + 10:
            return []
        
        data = self.calculate_indicators(data)
        data = self._calculate_trend_indicators(data)
        signals = []
        
        latest = data.iloc[-1]
        previous = data.iloc[-2]
        
        # Détecter le début d'une tendance haussière
        if self._detect_uptrend_start(data):
            signals.append({
                'strategy': self.name,
                'symbol': latest.name if hasattr(latest, 'name') else 'UNKNOWN',
                'side': 'buy',
                'type': 'market',
                'confidence': self._calculate_trend_confidence(data, 'up'),
                'stop_loss': latest['close'] * (1 - self.params['trailing_stop_pct']),
                'trailing_stop': True,
                'reason': f"Début tendance haussière, force: {latest['trend_strength']:.2f}"
            })
        
        # Détecter le début d'une tendance baissière
        elif self._detect_downtrend_start(data):
            signals.append({
                'strategy': self.name,
                'symbol': latest.name if hasattr(latest, 'name') else 'UNKNOWN',
                'side': 'sell',
                'type': 'market',
                'confidence': self._calculate_trend_confidence(data, 'down'),
                'stop_loss': latest['close'] * (1 + self.params['trailing_stop_pct']),
                'trailing_stop': True,
                'reason': f"Début tendance baissière, force: {latest['trend_strength']:.2f}"
            })
        
        return signals
    
    def _calculate_trend_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculer les indicateurs de tendance"""
        # ADX (Average Directional Index)
        high_low = data['high'] - data['low']
        high_close = np.abs(data['high'] - data['close'].shift())
        low_close = np.abs(data['low'] - data['close'].shift())
        
        ranges = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        data['atr'] = ranges.rolling(14).mean()
        
        # Trend strength basé sur la position par rapport aux moyennes mobiles
        ma_fast = data['close'].rolling(self.params['fast_ma']).mean()
        ma_slow = data['close'].rolling(self.params['slow_ma']).mean()
        
        data['trend_strength'] = (ma_fast - ma_slow) / ma_slow
        data['trend_direction'] = np.where(ma_fast > ma_slow, 1, -1)
        
        return data
    
    def _detect_uptrend_start(self, data: pd.DataFrame) -> bool:
        """Détecter le début d'une tendance haussière"""
        latest = data.iloc[-1]
        previous = data.iloc[-2]
        
        # Croisement des moyennes mobiles
        ma_cross = (previous['sma_20'] <= previous['sma_50'] and 
                   latest['sma_20'] > latest['sma_50'])
        
        # Force de tendance suffisante
        strong_trend = latest['trend_strength'] > self.params['min_trend_strength']
        
        # Cassure de résistance
        breakout = (latest['close'] > latest['bb_upper'] and
                   latest['volume'] > latest['volume_sma'] * 1.2)
        
        return ma_cross or (strong_trend and breakout)
    
    def _detect_downtrend_start(self, data: pd.DataFrame) -> bool:
        """Détecter le début d'une tendance baissière"""
        latest = data.iloc[-1]
        previous = data.iloc[-2]
        
        # Croisement des moyennes mobiles
        ma_cross = (previous['sma_20'] >= previous['sma_50'] and 
                   latest['sma_20'] < latest['sma_50'])
        
        # Force de tendance suffisante
        strong_trend = latest['trend_strength'] < -self.params['min_trend_strength']
        
        # Cassure de support
        breakdown = (latest['close'] < latest['bb_lower'] and
                    latest['volume'] > latest['volume_sma'] * 1.2)
        
        return ma_cross or (strong_trend and breakdown)
    
    def _calculate_trend_confidence(self, data: pd.DataFrame, direction: str) -> float:
        """Calculer la confiance dans le signal de tendance"""
        latest = data.iloc[-1]
        base_confidence = 0.7
        
        # Force de la tendance
        trend_factor = min(0.2, abs(latest['trend_strength']) * 2)
        
        # Volume de confirmation
        volume_factor = min(0.1, (latest['volume'] / latest['volume_sma'] - 1) * 0.1)
        
        confidence = base_confidence + trend_factor + volume_factor
        return min(1.0, max(0.1, confidence))
