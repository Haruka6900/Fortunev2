#!/usr/bin/env python3
"""
Projet Fortune - Bot de Trading Autonome
Point d'entrée principal du système de trading automatique
"""

import asyncio
import logging
import signal
import sys
import os
from datetime import datetime
from pathlib import Path

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    import yaml
except ImportError:
    print("Installing required packages...")
    os.system("pip install pyyaml")
    import yaml

from utils.memory import TradingMemory
from utils.risk_management import RiskManager
from utils.market_data import MarketDataManager
from strategies.strategy_manager import StrategyManager
from utils.portfolio import PortfolioManager
from utils.logger import setup_logger

class FortuneBot:
    def __init__(self):
        self.setup_directories()
        self.load_config()
        self.setup_logging()
        self.initialize_components()
        self.running = False
        
    def setup_directories(self):
        """Créer les répertoires nécessaires"""
        directories = ['data', 'logs', 'backtest_results']
        for directory in directories:
            Path(directory).mkdir(exist_ok=True)
    
    def load_config(self):
        """Charger la configuration depuis settings.yaml"""
        try:
            with open('settings.yaml', 'r') as file:
                self.config = yaml.safe_load(file)
        except FileNotFoundError:
            self.create_default_config()
            with open('settings.yaml', 'r') as file:
                self.config = yaml.safe_load(file)
    
    def create_default_config(self):
        """Créer un fichier de configuration par défaut"""
        default_config = {
            'trading': {
                'mode': 'paper',  # paper ou live
                'base_currency': 'USDT',
                'max_positions': 5,
                'default_risk_per_trade': 0.02,
                'min_trade_amount': 10,
                'max_trade_amount': 1000
            },
            'api': {
                'exchange': 'binance',
                'testnet': True,
                'api_key': '',
                'api_secret': ''
            },
            'strategies': {
                'enabled': ['rsi', 'macd', 'grid', 'dca'],
                'auto_tune': True,
                'backtest_period': 30
            },
            'risk_management': {
                'max_drawdown': 0.15,
                'daily_loss_limit': 0.05,
                'position_sizing': 'kelly',
                'stop_loss_pct': 0.02,
                'take_profit_pct': 0.04
            },
            'dashboard': {
                'port': 8501,
                'auto_refresh': 5
            }
        }
        
        with open('settings.yaml', 'w') as file:
            yaml.dump(default_config, file, default_flow_style=False)
    
    def setup_logging(self):
        """Configurer le système de logging"""
        self.logger = setup_logger('FortuneBot', 'logs/fortune_bot.log')
        self.logger.info("Fortune Bot initialisé")
    
    def initialize_components(self):
        """Initialiser tous les composants du bot"""
        self.memory = TradingMemory()
        self.risk_manager = RiskManager(self.config['risk_management'])
        self.market_data = MarketDataManager(self.config['api'])
        self.portfolio = PortfolioManager(self.config['trading'])
        self.strategy_manager = StrategyManager(
            self.config['strategies'], 
            self.memory, 
            self.risk_manager
        )
    
    async def start(self):
        """Démarrer le bot de trading"""
        self.logger.info("Démarrage du Fortune Bot")
        self.running = True
        
        # Initialiser les connexions
        await self.market_data.connect()
        await self.portfolio.initialize()
        
        # Boucle principale de trading
        while self.running:
            try:
                await self.trading_cycle()
                await asyncio.sleep(1)  # Pause d'1 seconde entre les cycles
            except Exception as e:
                self.logger.error(f"Erreur dans le cycle de trading: {e}")
                await asyncio.sleep(5)
    
    async def trading_cycle(self):
        """Cycle principal de trading"""
        # Récupérer les données de marché
        market_data = await self.market_data.get_latest_data()
        
        # Analyser avec toutes les stratégies
        signals = await self.strategy_manager.analyze_market(market_data)
        
        # Filtrer les signaux selon la gestion des risques
        filtered_signals = self.risk_manager.filter_signals(
            signals, 
            self.portfolio.get_current_positions()
        )
        
        # Exécuter les trades
        for signal in filtered_signals:
            await self.execute_trade(signal)
        
        # Mettre à jour la mémoire
        self.memory.update_market_state(market_data, signals)
        
        # Sauvegarder l'état
        self.memory.save()
    
    async def execute_trade(self, signal):
        """Exécuter un trade basé sur un signal"""
        try:
            # Calculer la taille de position
            position_size = self.risk_manager.calculate_position_size(
                signal, 
                self.portfolio.get_balance()
            )
            
            # Exécuter l'ordre
            result = await self.portfolio.place_order(
                symbol=signal['symbol'],
                side=signal['side'],
                amount=position_size,
                price=signal.get('price'),
                order_type=signal.get('type', 'market')
            )
            
            if result['success']:
                self.logger.info(f"Trade exécuté: {signal['symbol']} {signal['side']} {position_size}")
                self.memory.record_trade(signal, result)
            else:
                self.logger.error(f"Échec du trade: {result['error']}")
                
        except Exception as e:
            self.logger.error(f"Erreur lors de l'exécution du trade: {e}")
    
    def stop(self):
        """Arrêter le bot proprement"""
        self.logger.info("Arrêt du Fortune Bot")
        self.running = False
        self.memory.save()

def signal_handler(signum, frame):
    """Gestionnaire de signaux pour arrêt propre"""
    print("\nArrêt du bot en cours...")
    if 'bot' in globals():
        bot.stop()
    sys.exit(0)

async def main():
    """Fonction principale"""
    global bot
    bot = FortuneBot()
    
    # Configurer les gestionnaires de signaux
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await bot.start()
    except KeyboardInterrupt:
        bot.stop()
    except Exception as e:
        bot.logger.error(f"Erreur fatale: {e}")
        bot.stop()

if __name__ == "__main__":
    asyncio.run(main())
