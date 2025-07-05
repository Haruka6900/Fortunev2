"""
Stratégie MACD (Moving Average Convergence Divergence)
"""

from .base_strategy import BaseStrategy
import pandas as pd
from typing import Dict, List

class MACDStrategy(BaseStrategy):
    def __init__(self, params: Dict = None):
        default_params = self.get_default_params()
        if params:
            default_params.update(params)
        super().__init__("MACD", default_params)
    
    def get_default_params(self) -> Dict:
        return {
            'fast_period': 12,
            'slow_period': 26,
            'signal_period': 9,
            'min_histogram_change': 0.001
        }
    
    async def analyze(self, data: pd.DataFrame) -> List[Dict]:
        """Analyser avec la stratégie MACD"""
        if len(data) < self.params['slow_period'] + self.params['signal_period']:
            return []
        
        data = self.calculate_indicators(data)
        signals = []
        
        latest = data.iloc[-1]
        previous = data.iloc[-2]
        
        # Signal d'achat: MACD croise au-dessus de la ligne de signal
        if (previous['macd'] <= previous['macd_signal'] and 
            latest['macd'] > latest['macd_signal'] and
            latest['macd_histogram'] > self.params['min_histogram_change']):
            
            signals.append({
                'strategy': self.name,
                'symbol': latest.name if hasattr(latest, 'name') else 'UNKNOWN',
                'side': 'buy',
                'type': 'market',
                'confidence': self._calculate_confidence(latest, 'buy'),
                'stop_loss': latest['close'] * 0.97,
                'take_profit': latest['close'] * 1.05,
                'reason': f"MACD croisement haussier: {latest['macd']:.4f}"
            })
        
        # Signal de vente: MACD croise en-dessous de la ligne de signal
        elif (previous['macd'] >= previous['macd_signal'] and 
              latest['macd'] < latest['macd_signal'] and
              latest['macd_histogram'] < -self.params['min_histogram_change']):
            
            signals.append({
                'strategy': self.name,
                'symbol': latest.name if hasattr(latest, 'name') else 'UNKNOWN',
                'side': 'sell',
                'type': 'market',
                'confidence': self._calculate_confidence(latest, 'sell'),
                'stop_loss': latest['close'] * 1.03,
                'take_profit': latest['close'] * 0.95,
                'reason': f"MACD croisement baissier: {latest['macd']:.4f}"
            })
        
        return signals
    
    def _calculate_confidence(self, data_point, side) -> float:
        """Calculer le niveau de confiance du signal"""
        base_confidence = 0.65
        
        # Force du signal MACD
        macd_strength = abs(data_point['macd_histogram'])
        macd_factor = min(0.3, macd_strength * 100)
        
        # Tendance générale
        trend_factor = 0
        if side == 'buy' and data_point['sma_20'] > data_point['sma_50']:
            trend_factor = 0.1
        elif side == 'sell' and data_point['sma_20'] < data_point['sma_50']:
            trend_factor = 0.1
        
        confidence = base_confidence + macd_factor + trend_factor
        return min(1.0, max(0.1, confidence))
