"""
Gestionnaire de stratégies de trading
"""

import asyncio
import sys
import os
from typing import Dict, List

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from .rsi_strategy import RSIStrategy
    from .macd_strategy import MACDStrategy
    from .grid_strategy import GridStrategy
    from .dca_strategy import DCAStrategy
    from .scalping_strategy import ScalpingStrategy
    from .trend_following_strategy import TrendFollowingStrategy
except ImportError:
    # Fallback for direct execution
    from strategies.rsi_strategy import RSIStrategy
    from strategies.macd_strategy import MACDStrategy
    from strategies.grid_strategy import GridStrategy
    from strategies.dca_strategy import DCAStrategy
    from strategies.scalping_strategy import ScalpingStrategy
    from strategies.trend_following_strategy import TrendFollowingStrategy

class StrategyManager:
    def __init__(self, config: Dict, memory, risk_manager):
        self.config = config
        self.memory = memory
        self.risk_manager = risk_manager
        self.strategies = {}
        self.initialize_strategies()
    
    def initialize_strategies(self):
        """Initialiser toutes les stratégies activées"""
        strategy_classes = {
            'rsi': RSIStrategy,
            'macd': MACDStrategy,
            'grid': GridStrategy,
            'dca': DCAStrategy,
            'scalping': ScalpingStrategy,
            'trend_following': TrendFollowingStrategy
        }
        
        for strategy_name in self.config['enabled']:
            if strategy_name in strategy_classes:
                # Récupérer les paramètres personnalisés depuis la mémoire
                params = self.memory.get_strategy_params(strategy_name)
                self.strategies[strategy_name] = strategy_classes[strategy_name](params)
    
    async def analyze_market(self, market_data: Dict) -> List[Dict]:
        """Analyser le marché avec toutes les stratégies"""
        all_signals = []
        
        # Exécuter toutes les stratégies en parallèle
        tasks = []
        for strategy_name, strategy in self.strategies.items():
            if strategy_name in market_data:
                task = strategy.analyze(market_data[strategy_name])
                tasks.append(task)
        
        # Attendre tous les résultats
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Collecter tous les signaux
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"Erreur dans la stratégie: {result}")
                continue
            
            if isinstance(result, list):
                all_signals.extend(result)
        
        # Filtrer et prioriser les signaux
        filtered_signals = self._filter_and_prioritize_signals(all_signals)
        
        return filtered_signals
    
    def _filter_and_prioritize_signals(self, signals: List[Dict]) -> List[Dict]:
        """Filtrer et prioriser les signaux de trading"""
        if not signals:
            return []
        
        # Grouper par symbole
        signals_by_symbol = {}
        for signal in signals:
            symbol = signal['symbol']
            if symbol not in signals_by_symbol:
                signals_by_symbol[symbol] = []
            signals_by_symbol[symbol].append(signal)
        
        # Sélectionner le meilleur signal par symbole
        best_signals = []
        for symbol, symbol_signals in signals_by_symbol.items():
            # Trier par confiance
            symbol_signals.sort(key=lambda x: x['confidence'], reverse=True)
            
            # Vérifier la cohérence des signaux
            if self._signals_are_coherent(symbol_signals):
                best_signals.append(symbol_signals[0])
        
        return best_signals
    
    def _signals_are_coherent(self, signals: List[Dict]) -> bool:
        """Vérifier si les signaux sont cohérents entre eux"""
        if len(signals) <= 1:
            return True
        
        # Vérifier que les signaux vont dans la même direction
        sides = [signal['side'] for signal in signals]
        return len(set(sides)) == 1
    
    def update_strategy_performance(self, strategy_name: str, trade_result: Dict):
        """Mettre à jour les performances d'une stratégie"""
        if strategy_name in self.strategies:
            self.strategies[strategy_name].update_performance(trade_result)
    
    def get_strategy_performance(self) -> Dict:
        """Obtenir les performances de toutes les stratégies"""
        performance = {}
        for name, strategy in self.strategies.items():
            performance[name] = strategy.get_performance_metrics()
        return performance
    
    def optimize_strategies(self, historical_data: Dict):
        """Optimiser les paramètres de toutes les stratégies"""
        if not self.config['auto_tune']:
            return
        
        for name, strategy in self.strategies.items():
            if name in historical_data:
                optimized_params = strategy.optimize_parameters(historical_data[name])
                self.memory.save_strategy_params(name, optimized_params)
