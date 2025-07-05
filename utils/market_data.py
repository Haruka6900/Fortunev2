"""
Gestionnaire de données de marché
"""

import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json

try:
    import aiohttp
except ImportError:
    print("Installing aiohttp...")
    import os
    os.system("pip install aiohttp")
    import aiohttp

class MarketDataManager:
    def __init__(self, config: Dict):
        self.config = config
        self.exchange = config.get('exchange', 'binance')
        self.testnet = config.get('testnet', True)
        self.session = None
        self.symbols = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'DOTUSDT', 'LINKUSDT']
        self.data_cache = {}
        self.last_update = {}
    
    async def connect(self):
        """Établir la connexion aux APIs"""
        self.session = aiohttp.ClientSession()
        print(f"Connexion établie avec {self.exchange}")
    
    async def disconnect(self):
        """Fermer les connexions"""
        if self.session:
            await self.session.close()
    
    async def get_latest_data(self) -> Dict:
        """Récupérer les dernières données de marché"""
        market_data = {}
        
        for symbol in self.symbols:
            try:
                data = await self._fetch_symbol_data(symbol)
                if data is not None:
                    market_data[symbol] = data
            except Exception as e:
                print(f"Erreur lors de la récupération de {symbol}: {e}")
        
        return market_data
    
    async def _fetch_symbol_data(self, symbol: str) -> Optional[pd.DataFrame]:
        """Récupérer les données d'un symbole spécifique"""
        # Vérifier le cache
        if symbol in self.data_cache:
            last_update = self.last_update.get(symbol, datetime.min)
            if datetime.now() - last_update < timedelta(minutes=1):
                return self.data_cache[symbol]
        
        if self.config.get('mode') == 'paper' or not self.session:
            # Mode papier - générer des données simulées
            data = self._generate_mock_data(symbol)
        else:
            # Mode réel - récupérer depuis l'API
            data = await self._fetch_real_data(symbol)
        
        if data is not None:
            self.data_cache[symbol] = data
            self.last_update[symbol] = datetime.now()
        
        return data
    
    def _generate_mock_data(self, symbol: str, periods: int = 100) -> pd.DataFrame:
        """Générer des données de marché simulées"""
        # Prix de base selon le symbole
        base_prices = {
            'BTCUSDT': 45000,
            'ETHUSDT': 3000,
            'ADAUSDT': 0.5,
            'DOTUSDT': 8,
            'LINKUSDT': 15
        }
        
        base_price = base_prices.get(symbol, 100)
        
        # Générer une série temporelle réaliste
        dates = pd.date_range(end=datetime.now(), periods=periods, freq='1min')
        
        # Mouvement brownien géométrique pour simuler les prix
        np.random.seed(42)  # For reproducible results
        returns = np.random.normal(0, 0.002, periods)  # Volatilité de 0.2%
        returns[0] = 0
        
        prices = base_price * np.exp(np.cumsum(returns))
        
        # Générer OHLCV
        data = []
        for i, (date, close) in enumerate(zip(dates, prices)):
            # Simuler open, high, low basés sur close
            volatility = np.random.uniform(0.001, 0.005)
            open_price = close * (1 + np.random.normal(0, volatility/2))
            high = max(open_price, close) * (1 + np.random.uniform(0, volatility))
            low = min(open_price, close) * (1 - np.random.uniform(0, volatility))
            volume = np.random.uniform(1000, 10000)
            
            data.append({
                'timestamp': date,
                'open': open_price,
                'high': high,
                'low': low,
                'close': close,
                'volume': volume
            })
        
        df = pd.DataFrame(data)
        df.set_index('timestamp', inplace=True)
        return df
    
    async def _fetch_real_data(self, symbol: str) -> Optional[pd.DataFrame]:
        """Récupérer des données réelles depuis l'API"""
        if self.exchange == 'binance':
            return await self._fetch_binance_data(symbol)
        else:
            print(f"Exchange {self.exchange} non supporté")
            return None
    
    async def _fetch_binance_data(self, symbol: str) -> Optional[pd.DataFrame]:
        """Récupérer des données depuis Binance"""
        base_url = "https://testnet.binance.vision" if self.testnet else "https://api.binance.com"
        url = f"{base_url}/api/v3/klines"
        
        params = {
            'symbol': symbol,
            'interval': '1m',
            'limit': 100
        }
        
        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_binance_data(data)
                else:
                    print(f"Erreur API Binance: {response.status}")
                    return None
        except Exception as e:
            print(f"Erreur lors de la requête Binance: {e}")
            return None
    
    def _parse_binance_data(self, raw_data: List) -> pd.DataFrame:
        """Parser les données Binance"""
        data = []
        for candle in raw_data:
            data.append({
                'timestamp': pd.to_datetime(candle[0], unit='ms'),
                'open': float(candle[1]),
                'high': float(candle[2]),
                'low': float(candle[3]),
                'close': float(candle[4]),
                'volume': float(candle[5])
            })
        
        df = pd.DataFrame(data)
        df.set_index('timestamp', inplace=True)
        return df
    
    async def get_historical_data(self, symbol: str, days: int = 30) -> Optional[pd.DataFrame]:
        """Récupérer des données historiques"""
        if self.config.get('mode') == 'paper':
            # Générer plus de données historiques pour le backtesting
            return self._generate_mock_data(symbol, periods=days * 1440)  # 1440 minutes par jour
        else:
            # Implémenter la récupération de données historiques réelles
            return await self._fetch_historical_real_data(symbol, days)
    
    async def _fetch_historical_real_data(self, symbol: str, days: int) -> Optional[pd.DataFrame]:
        """Récupérer des données historiques réelles"""
        # Implémentation pour récupérer des données historiques
        # selon l'exchange configuré
        pass
    
    def get_market_summary(self) -> Dict:
        """Obtenir un résumé du marché"""
        summary = {
            'symbols_tracked': len(self.symbols),
            'last_update': max(self.last_update.values()) if self.last_update else None,
            'cache_size': len(self.data_cache),
            'exchange': self.exchange,
            'mode': self.config.get('mode', 'paper')
        }
        
        # Ajouter des statistiques de marché
        if self.data_cache:
            total_volume = 0
            price_changes = []
            
            for symbol, data in self.data_cache.items():
                if len(data) >= 2:
                    latest = data.iloc[-1]
                    previous = data.iloc[-2]
                    
                    total_volume += latest['volume']
                    price_change = (latest['close'] - previous['close']) / previous['close']
                    price_changes.append(price_change)
            
            summary.update({
                'total_volume': total_volume,
                'avg_price_change': np.mean(price_changes) if price_changes else 0,
                'market_volatility': np.std(price_changes) if price_changes else 0
            })
        
        return summary
