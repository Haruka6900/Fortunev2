"""
Configuration des APIs et gestion des clés
"""

import os
from typing import Dict, Optional
from dotenv import load_dotenv
import yaml

# Charger les variables d'environnement
load_dotenv()

class APIConfig:
    def __init__(self):
        self.load_config()
    
    def load_config(self):
        """Charger la configuration depuis settings.yaml et .env"""
        # Charger settings.yaml
        try:
            with open('settings.yaml', 'r') as file:
                self.config = yaml.safe_load(file)
        except FileNotFoundError:
            self.config = self.get_default_config()
        
        # Override avec les variables d'environnement si disponibles
        self.override_with_env()
    
    def get_default_config(self) -> Dict:
        """Configuration par défaut"""
        return {
            'trading': {'mode': 'paper'},
            'api': {'exchange': 'binance', 'testnet': True}
        }
    
    def override_with_env(self):
        """Override la config avec les variables d'environnement"""
        # API Keys depuis .env
        if os.getenv('BINANCE_API_KEY'):
            self.config['api']['api_key'] = os.getenv('BINANCE_API_KEY')
        if os.getenv('BINANCE_SECRET_KEY'):
            self.config['api']['api_secret'] = os.getenv('BINANCE_SECRET_KEY')
        
        # Mode de trading
        if os.getenv('TRADING_MODE'):
            self.config['trading']['mode'] = os.getenv('TRADING_MODE')
        
        # Environnement
        if os.getenv('ENVIRONMENT'):
            self.config['deployment'] = self.config.get('deployment', {})
            self.config['deployment']['environment'] = os.getenv('ENVIRONMENT')
    
    def get_api_credentials(self, exchange: str = None) -> Dict:
        """Obtenir les credentials API pour un exchange"""
        exchange = exchange or self.config['api']['exchange']
        
        credentials = {}
        
        if exchange == 'binance':
            credentials = {
                'api_key': self.config['api'].get('api_key') or os.getenv('BINANCE_API_KEY'),
                'api_secret': self.config['api'].get('api_secret') or os.getenv('BINANCE_SECRET_KEY'),
                'testnet': self.config['api'].get('testnet', True)
            }
        elif exchange == 'coinbase':
            credentials = {
                'api_key': os.getenv('COINBASE_API_KEY'),
                'api_secret': os.getenv('COINBASE_SECRET_KEY'),
                'sandbox': self.config['api'].get('testnet', True)
            }
        elif exchange == 'kraken':
            credentials = {
                'api_key': os.getenv('KRAKEN_API_KEY'),
                'api_secret': os.getenv('KRAKEN_SECRET_KEY')
            }
        
        return credentials
    
    def validate_credentials(self, exchange: str = None) -> bool:
        """Valider que les credentials sont présents"""
        credentials = self.get_api_credentials(exchange)
        
        required_keys = ['api_key', 'api_secret']
        return all(credentials.get(key) for key in required_keys)
    
    def is_live_mode(self) -> bool:
        """Vérifier si on est en mode live"""
        return self.config['trading']['mode'] == 'live'
    
    def get_trading_config(self) -> Dict:
        """Obtenir la configuration de trading"""
        return self.config.get('trading', {})
    
    def get_risk_config(self) -> Dict:
        """Obtenir la configuration de risque"""
        return self.config.get('risk_management', {})

# Instance globale
api_config = APIConfig()
