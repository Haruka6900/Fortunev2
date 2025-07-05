"""
Système de mémoire adaptative pour le bot de trading
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import numpy as np

class TradingMemory:
    def __init__(self, memory_file: str = 'data/memory.json'):
        self.memory_file = memory_file
        self.memory = self._load_memory()
        self.session_start = datetime.now()
    
    def _load_memory(self) -> Dict:
        """Charger la mémoire depuis le fichier"""
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        
        return self._create_default_memory()
    
    def _create_default_memory(self) -> Dict:
        """Créer une structure de mémoire par défaut"""
        return {
            'trades': [],
            'market_states': [],
            'strategy_params': {},
            'performance_metrics': {},
            'learned_patterns': {},
            'risk_adjustments': {},
            'session_stats': {},
            'last_updated': datetime.now().isoformat()
        }
    
    def save(self):
        """Sauvegarder la mémoire dans le fichier"""
        self.memory['last_updated'] = datetime.now().isoformat()
        
        # Créer le répertoire si nécessaire
        os.makedirs(os.path.dirname(self.memory_file), exist_ok=True)
        
        try:
            with open(self.memory_file, 'w') as f:
                json.dump(self.memory, f, indent=2, default=str)
        except Exception as e:
            print(f"Erreur lors de la sauvegarde de la mémoire: {e}")
    
    def record_trade(self, signal: Dict, result: Dict):
        """Enregistrer un trade dans la mémoire"""
        trade_record = {
            'timestamp': datetime.now().isoformat(),
            'strategy': signal.get('strategy'),
            'symbol': signal.get('symbol'),
            'side': signal.get('side'),
            'entry_price': result.get('entry_price'),
            'exit_price': result.get('exit_price'),
            'quantity': result.get('quantity'),
            'profit': result.get('profit', 0),
            'profit_pct': result.get('profit_pct', 0),
            'duration': result.get('duration', 0),
            'confidence': signal.get('confidence'),
            'reason': signal.get('reason'),
            'market_conditions': self._capture_market_conditions()
        }
        
        self.memory['trades'].append(trade_record)
        
        # Garder seulement les 10000 derniers trades
        if len(self.memory['trades']) > 10000:
            self.memory['trades'] = self.memory['trades'][-10000:]
        
        # Apprendre du trade
        self._learn_from_trade(trade_record)
    
    def update_market_state(self, market_data: Dict, signals: List[Dict]):
        """Mettre à jour l'état du marché dans la mémoire"""
        market_state = {
            'timestamp': datetime.now().isoformat(),
            'market_data': self._serialize_market_data(market_data),
            'signals_generated': len(signals),
            'signal_confidence_avg': np.mean([s.get('confidence', 0) for s in signals]) if signals else 0
        }
        
        self.memory['market_states'].append(market_state)
        
        # Garder seulement les 1000 derniers états
        if len(self.memory['market_states']) > 1000:
            self.memory['market_states'] = self.memory['market_states'][-1000:]
    
    def _serialize_market_data(self, market_data: Dict) -> Dict:
        """Sérialiser les données de marché pour la sauvegarde"""
        serialized = {}
        for symbol, data in market_data.items():
            if hasattr(data, 'to_dict'):
                # DataFrame pandas
                serialized[symbol] = {
                    'last_price': float(data['close'].iloc[-1]) if 'close' in data.columns else 0,
                    'volume': float(data['volume'].iloc[-1]) if 'volume' in data.columns else 0,
                    'volatility': float(data['close'].pct_change().std()) if 'close' in data.columns else 0
                }
            else:
                serialized[symbol] = data
        return serialized
    
    def _capture_market_conditions(self) -> Dict:
        """Capturer les conditions de marché actuelles"""
        # Analyser les derniers états de marché
        recent_states = self.memory['market_states'][-10:] if self.memory['market_states'] else []
        
        if not recent_states:
            return {'volatility': 'unknown', 'trend': 'unknown'}
        
        # Calculer la volatilité moyenne récente
        volatilities = [state['market_data'].get('volatility', 0) for state in recent_states]
        avg_volatility = np.mean(volatilities) if volatilities else 0
        
        return {
            'volatility': 'high' if avg_volatility > 0.02 else 'low',
            'trend': 'bullish',  # Simplification - à améliorer
            'market_session': self._get_market_session()
        }
    
    def _get_market_session(self) -> str:
        """Déterminer la session de marché actuelle"""
        hour = datetime.now().hour
        if 0 <= hour < 8:
            return 'asian'
        elif 8 <= hour < 16:
            return 'european'
        else:
            return 'american'
    
    def _learn_from_trade(self, trade: Dict):
        """Apprendre des patterns à partir d'un trade"""
        strategy = trade['strategy']
        if not strategy:
            return
        
        # Initialiser les patterns pour cette stratégie si nécessaire
        if strategy not in self.memory['learned_patterns']:
            self.memory['learned_patterns'][strategy] = {
                'successful_conditions': [],
                'failed_conditions': [],
                'optimal_times': [],
                'risk_adjustments': {}
            }
        
        patterns = self.memory['learned_patterns'][strategy]
        
        # Enregistrer les conditions selon le succès du trade
        if trade['profit'] > 0:
            patterns['successful_conditions'].append(trade['market_conditions'])
            patterns['optimal_times'].append(trade['timestamp'])
        else:
            patterns['failed_conditions'].append(trade['market_conditions'])
        
        # Limiter la taille des listes
        for key in ['successful_conditions', 'failed_conditions', 'optimal_times']:
            if len(patterns[key]) > 100:
                patterns[key] = patterns[key][-100:]
    
    def get_strategy_params(self, strategy_name: str) -> Dict:
        """Récupérer les paramètres optimisés d'une stratégie"""
        return self.memory['strategy_params'].get(strategy_name, {})
    
    def save_strategy_params(self, strategy_name: str, params: Dict):
        """Sauvegarder les paramètres optimisés d'une stratégie"""
        self.memory['strategy_params'][strategy_name] = params
    
    def get_performance_insights(self, strategy_name: str = None) -> Dict:
        """Obtenir des insights de performance"""
        trades = self.memory['trades']
        
        if strategy_name:
            trades = [t for t in trades if t.get('strategy') == strategy_name]
        
        if not trades:
            return {}
        
        # Calculer les métriques
        profits = [t['profit'] for t in trades]
        win_rate = len([p for p in profits if p > 0]) / len(profits)
        
        # Analyser les patterns temporels
        hourly_performance = self._analyze_hourly_performance(trades)
        
        # Analyser les conditions de marché favorables
        favorable_conditions = self._analyze_favorable_conditions(trades)
        
        return {
            'total_trades': len(trades),
            'win_rate': win_rate,
            'avg_profit': np.mean(profits),
            'best_hours': hourly_performance,
            'favorable_conditions': favorable_conditions,
            'recent_trend': self._calculate_recent_trend(trades)
        }
    
    def _analyze_hourly_performance(self, trades: List[Dict]) -> Dict:
        """Analyser la performance par heure"""
        hourly_profits = {}
        
        for trade in trades:
            try:
                hour = datetime.fromisoformat(trade['timestamp']).hour
                if hour not in hourly_profits:
                    hourly_profits[hour] = []
                hourly_profits[hour].append(trade['profit'])
            except:
                continue
        
        # Calculer la moyenne par heure
        hourly_avg = {}
        for hour, profits in hourly_profits.items():
            hourly_avg[hour] = np.mean(profits)
        
        # Retourner les 3 meilleures heures
        best_hours = sorted(hourly_avg.items(), key=lambda x: x[1], reverse=True)[:3]
        return dict(best_hours)
    
    def _analyze_favorable_conditions(self, trades: List[Dict]) -> Dict:
        """Analyser les conditions de marché favorables"""
        successful_trades = [t for t in trades if t['profit'] > 0]
        
        if not successful_trades:
            return {}
        
        # Analyser les conditions de marché des trades réussis
        volatility_counts = {}
        trend_counts = {}
        
        for trade in successful_trades:
            conditions = trade.get('market_conditions', {})
            
            vol = conditions.get('volatility', 'unknown')
            trend = conditions.get('trend', 'unknown')
            
            volatility_counts[vol] = volatility_counts.get(vol, 0) + 1
            trend_counts[trend] = trend_counts.get(trend, 0) + 1
        
        return {
            'best_volatility': max(volatility_counts, key=volatility_counts.get) if volatility_counts else 'unknown',
            'best_trend': max(trend_counts, key=trend_counts.get) if trend_counts else 'unknown'
        }
    
    def _calculate_recent_trend(self, trades: List[Dict]) -> str:
        """Calculer la tendance récente des performances"""
        if len(trades) < 10:
            return 'insufficient_data'
        
        recent_trades = trades[-10:]
        recent_profits = [t['profit'] for t in recent_trades]
        
        if np.mean(recent_profits) > 0:
            return 'improving'
        else:
            return 'declining'
    
    def should_adjust_strategy(self, strategy_name: str) -> bool:
        """Déterminer si une stratégie doit être ajustée"""
        insights = self.get_performance_insights(strategy_name)
        
        if not insights:
            return False
        
        # Ajuster si le win rate est trop bas ou la tendance récente est mauvaise
        return (insights.get('win_rate', 0) < 0.4 or 
                insights.get('recent_trend') == 'declining')
    
    def get_memory_summary(self) -> Dict:
        """Obtenir un résumé de la mémoire"""
        return {
            'total_trades': len(self.memory['trades']),
            'strategies_learned': list(self.memory['learned_patterns'].keys()),
            'session_duration': str(datetime.now() - self.session_start),
            'last_updated': self.memory['last_updated'],
            'memory_size_mb': self._calculate_memory_size()
        }
    
    def _calculate_memory_size(self) -> float:
        """Calculer la taille de la mémoire en MB"""
        try:
            if os.path.exists(self.memory_file):
                size_bytes = os.path.getsize(self.memory_file)
                return round(size_bytes / (1024 * 1024), 2)
        except:
            pass
        return 0.0
