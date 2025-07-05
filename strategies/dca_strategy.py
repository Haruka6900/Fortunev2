"""
Stratégie DCA (Dollar Cost Averaging)
"""

from .base_strategy import BaseStrategy
import pandas as pd
from typing import Dict, List
from datetime import datetime, timedelta

class DCAStrategy(BaseStrategy):
    def __init__(self, params: Dict = None):
        default_params = self.get_default_params()
        if params:
            default_params.update(params)
        super().__init__("DCA", default_params)
        self.last_purchase = None
        self.purchase_history = []
    
    def get_default_params(self) -> Dict:
        return {
            'interval_hours': 24,  # Acheter toutes les 24h
            'base_amount': 50,
            'volatility_multiplier': 1.5,  # Acheter plus quand c'est volatil
            'trend_filter': True,  # Seulement acheter en tendance haussière
            'max_drawdown_stop': 0.20  # Arrêter si drawdown > 20%
        }
    
    async def analyze(self, data: pd.DataFrame) -> List[Dict]:
        """Analyser avec la stratégie DCA"""
        if len(data) < 50:
            return []
        
        data = self.calculate_indicators(data)
        signals = []
        
        current_time = datetime.now()
        latest = data.iloc[-1]
        
        # Vérifier si c'est le moment d'acheter
        if self._should_purchase(current_time, data):
            amount = self._calculate_purchase_amount(data)
            
            signals.append({
                'strategy': self.name,
                'symbol': latest.name if hasattr(latest, 'name') else 'UNKNOWN',
                'side': 'buy',
                'type': 'market',
                'amount': amount,
                'confidence': 0.7,
                'reason': f"DCA achat programmé: {amount}$"
            })
            
            self.last_purchase = current_time
        
        return signals
    
    def _should_purchase(self, current_time: datetime, data: pd.DataFrame) -> bool:
        """Déterminer s'il faut effectuer un achat DCA"""
        # Vérifier l'intervalle de temps
        if self.last_purchase:
            time_diff = current_time - self.last_purchase
            if time_diff.total_seconds() < self.params['interval_hours'] * 3600:
                return False
        
        # Filtre de tendance si activé
        if self.params['trend_filter']:
            latest = data.iloc[-1]
            if latest['sma_20'] < latest['sma_50']:
                return False
        
        # Vérifier le drawdown maximum
        if self._check_max_drawdown():
            return False
        
        return True
    
    def _calculate_purchase_amount(self, data: pd.DataFrame) -> float:
        """Calculer le montant d'achat basé sur la volatilité"""
        base_amount = self.params['base_amount']
        
        # Calculer la volatilité récente
        volatility = data['close'].pct_change().rolling(20).std().iloc[-1]
        
        # Ajuster le montant selon la volatilité
        volatility_factor = min(2.0, volatility * self.params['volatility_multiplier'] * 100)
        adjusted_amount = base_amount * volatility_factor
        
        return max(base_amount * 0.5, min(base_amount * 2, adjusted_amount))
    
    def _check_max_drawdown(self) -> bool:
        """Vérifier si le drawdown maximum est atteint"""
        if not self.purchase_history:
            return False
        
        total_invested = sum([p['amount'] for p in self.purchase_history])
        current_value = self._calculate_current_portfolio_value()
        
        if current_value > 0:
            drawdown = (total_invested - current_value) / total_invested
            return drawdown > self.params['max_drawdown_stop']
        
        return False
    
    def _calculate_current_portfolio_value(self) -> float:
        """Calculer la valeur actuelle du portefeuille"""
        # Implémentation simplifiée - à adapter selon le contexte
        return 0
