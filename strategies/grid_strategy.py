"""
Stratégie Grid Trading
"""

from .base_strategy import BaseStrategy
import pandas as pd
from typing import Dict, List
import numpy as np

class GridStrategy(BaseStrategy):
    def __init__(self, params: Dict = None):
        default_params = self.get_default_params()
        if params:
            default_params.update(params)
        super().__init__("Grid", default_params)
        self.grid_levels = []
        self.grid_orders = {}
    
    def get_default_params(self) -> Dict:
        return {
            'grid_size': 0.01,  # 1% entre chaque niveau
            'num_levels': 10,
            'base_amount': 100,
            'volatility_threshold': 0.02
        }
    
    async def analyze(self, data: pd.DataFrame) -> List[Dict]:
        """Analyser avec la stratégie Grid"""
        if len(data) < 20:
            return []
        
        data = self.calculate_indicators(data)
        signals = []
        
        latest = data.iloc[-1]
        current_price = latest['close']
        
        # Calculer la volatilité récente
        volatility = data['close'].pct_change().rolling(20).std().iloc[-1]
        
        # Ne trader que si la volatilité est suffisante
        if volatility < self.params['volatility_threshold']:
            return signals
        
        # Initialiser ou mettre à jour la grille
        if not self.grid_levels:
            self._setup_grid(current_price)
        
        # Vérifier si le prix a atteint un niveau de grille
        for level in self.grid_levels:
            if self._should_place_order(current_price, level):
                signal = self._create_grid_signal(level, current_price)
                if signal:
                    signals.append(signal)
        
        return signals
    
    def _setup_grid(self, center_price: float):
        """Configurer les niveaux de grille"""
        self.grid_levels = []
        grid_size = self.params['grid_size']
        num_levels = self.params['num_levels']
        
        # Créer les niveaux au-dessus et en-dessous du prix actuel
        for i in range(-num_levels//2, num_levels//2 + 1):
            level_price = center_price * (1 + i * grid_size)
            self.grid_levels.append({
                'price': level_price,
                'side': 'buy' if i < 0 else 'sell',
                'active': True,
                'filled': False
            })
    
    def _should_place_order(self, current_price: float, level: Dict) -> bool:
        """Vérifier si un ordre doit être placé à ce niveau"""
        if not level['active'] or level['filled']:
            return False
        
        price_diff = abs(current_price - level['price']) / level['price']
        return price_diff < 0.001  # Très proche du niveau
    
    def _create_grid_signal(self, level: Dict, current_price: float) -> Dict:
        """Créer un signal de trading pour la grille"""
        return {
            'strategy': self.name,
            'symbol': 'UNKNOWN',  # À définir selon le contexte
            'side': level['side'],
            'type': 'limit',
            'price': level['price'],
            'confidence': 0.8,
            'amount': self.params['base_amount'],
            'reason': f"Grid level {level['side']} à {level['price']:.4f}"
        }
