"""
Stratégie RSI (Relative Strength Index)
"""

from .base_strategy import BaseStrategy
import pandas as pd
from typing import Dict, List

class RSIStrategy(BaseStrategy):
    def __init__(self, params: Dict = None):
        default_params = self.get_default_params()
        if params:
            default_params.update(params)
        super().__init__("RSI", default_params)
    
    def get_default_params(self) -> Dict:
        return {
            'rsi_period': 14,
            'oversold_threshold': 30,
            'overbought_threshold': 70,
            'min_volume_ratio': 1.2
        }
    
    async def analyze(self, data: pd.DataFrame) -> List[Dict]:
        """Analyser avec la stratégie RSI"""
        if len(data) < self.params['rsi_period'] + 1:
            return []
        
        data = self.calculate_indicators(data)
        signals = []
        
        latest = data.iloc[-1]
        previous = data.iloc[-2]
        
        # Signal d'achat: RSI sort de la zone de survente
        if (previous['rsi'] <= self.params['oversold_threshold'] and 
            latest['rsi'] > self.params['oversold_threshold'] and
            latest['volume'] > latest['volume_sma'] * self.params['min_volume_ratio']):
            
            signals.append({
                'strategy': self.name,
                'symbol': latest.name if hasattr(latest, 'name') else 'UNKNOWN',
                'side': 'buy',
                'type': 'market',
                'confidence': self._calculate_confidence(latest, 'buy'),
                'stop_loss': latest['close'] * 0.98,
                'take_profit': latest['close'] * 1.04,
                'reason': f"RSI sortie survente: {latest['rsi']:.2f}"
            })
        
        # Signal de vente: RSI sort de la zone de surachat
        elif (previous['rsi'] >= self.params['overbought_threshold'] and 
              latest['rsi'] < self.params['overbought_threshold'] and
              latest['volume'] > latest['volume_sma'] * self.params['min_volume_ratio']):
            
            signals.append({
                'strategy': self.name,
                'symbol': latest.name if hasattr(latest, 'name') else 'UNKNOWN',
                'side': 'sell',
                'type': 'market',
                'confidence': self._calculate_confidence(latest, 'sell'),
                'stop_loss': latest['close'] * 1.02,
                'take_profit': latest['close'] * 0.96,
                'reason': f"RSI sortie surachat: {latest['rsi']:.2f}"
            })
        
        return signals
    
    def _calculate_confidence(self, data_point, side) -> float:
        """Calculer le niveau de confiance du signal"""
        base_confidence = 0.6
        
        # Ajuster selon l'écart par rapport aux seuils
        if side == 'buy':
            rsi_factor = min(1.0, (40 - data_point['rsi']) / 10)
        else:
            rsi_factor = min(1.0, (data_point['rsi'] - 60) / 10)
        
        # Ajuster selon le volume
        volume_factor = min(1.0, data_point['volume'] / data_point['volume_sma'])
        
        confidence = base_confidence + (rsi_factor * 0.2) + (volume_factor * 0.2)
        return min(1.0, max(0.1, confidence))
