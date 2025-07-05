"""
Script de test pour le Fortune Bot
"""

import asyncio
import sys
import os
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_components():
    """Tester tous les composants du bot"""
    print("=== TEST DU FORTUNE BOT ===\n")
    
    try:
        # Test 1: Memory
        print("1. Test du système de mémoire...")
        from utils.memory import TradingMemory
        memory = TradingMemory()
        print("   ✓ Mémoire initialisée")
        
        # Test 2: Portfolio
        print("2. Test du gestionnaire de portfolio...")
        from utils.portfolio import PortfolioManager
        config = {'mode': 'paper', 'base_currency': 'USDT'}
        portfolio = PortfolioManager(config)
        await portfolio.initialize()
        print("   ✓ Portfolio initialisé")
        
        # Test 3: Risk Management
        print("3. Test de la gestion des risques...")
        from utils.risk_management import RiskManager
        risk_config = {'daily_loss_limit': 0.05, 'max_drawdown': 0.15}
        risk_manager = RiskManager(risk_config)
        print("   ✓ Gestionnaire de risques initialisé")
        
        # Test 4: Market Data
        print("4. Test des données de marché...")
        from utils.market_data import MarketDataManager
        api_config = {'mode': 'paper', 'exchange': 'binance', 'testnet': True}
        market_data = MarketDataManager(api_config)
        await market_data.connect()
        data = await market_data.get_latest_data()
        print(f"   ✓ Données récupérées pour {len(data)} symboles")
        await market_data.disconnect()
        
        # Test 5: Strategies
        print("5. Test des stratégies...")
        from strategies.strategy_manager import StrategyManager
        strategy_config = {'enabled': ['rsi', 'macd'], 'auto_tune': False}
        strategy_manager = StrategyManager(strategy_config, memory, risk_manager)
        
        # Test avec des données simulées
        if data:
            signals = await strategy_manager.analyze_market(data)
            print(f"   ✓ {len(signals)} signaux générés")
        
        # Test 6: Trade execution
        print("6. Test d'exécution de trade...")
        if signals:
            signal = signals[0]
            result = await portfolio.place_order(
                symbol=signal['symbol'],
                side=signal['side'],
                amount=100,
                order_type='market'
            )
            if result['success']:
                print("   ✓ Trade exécuté avec succès")
            else:
                print(f"   ⚠ Erreur de trade: {result['error']}")
        
        print("\n=== TOUS LES TESTS RÉUSSIS ===")
        return True
        
    except Exception as e:
        print(f"\n❌ ERREUR LORS DU TEST: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_dashboard():
    """Tester le dashboard Streamlit"""
    print("\n=== TEST DU DASHBOARD ===")
    
    try:
        # Vérifier que Streamlit est installé
        import streamlit as st
        print("✓ Streamlit disponible")
        
        # Tester l'import du dashboard
        from interface.dashboard import FortuneDashboard
        print("✓ Dashboard importé")
        
        # Créer une instance
        dashboard = FortuneDashboard()
        print("✓ Dashboard initialisé")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur dashboard: {e}")
        return False

def test_file_structure():
    """Vérifier la structure des fichiers"""
    print("=== VÉRIFICATION DE LA STRUCTURE ===\n")
    
    required_files = [
        'main.py',
        'settings.yaml',
        'requirements.txt',
        'Procfile',
        'render.yaml',
        'strategies/base_strategy.py',
        'strategies/rsi_strategy.py',
        'strategies/macd_strategy.py',
        'strategies/strategy_manager.py',
        'utils/memory.py',
        'utils/risk_management.py',
        'utils/portfolio.py',
        'utils/market_data.py',
        'utils/logger.py',
        'interface/dashboard.py',
        'data/memory.json'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
        else:
            print(f"✓ {file_path}")
    
    if missing_files:
        print(f"\n❌ Fichiers manquants: {missing_files}")
        return False
    else:
        print("\n✓ Tous les fichiers requis sont présents")
        return True

async def main():
    """Fonction principale de test"""
    print("FORTUNE BOT - TESTS COMPLETS")
    print("=" * 50)
    
    # Test 1: Structure des fichiers
    structure_ok = test_file_structure()
    
    if not structure_ok:
        print("❌ Structure de fichiers incorrecte")
        return
    
    # Test 2: Composants du bot
    components_ok = await test_components()
    
    # Test 3: Dashboard
    dashboard_ok = test_dashboard()
    
    # Résumé
    print("\n" + "=" * 50)
    print("RÉSUMÉ DES TESTS:")
    print(f"Structure des fichiers: {'✓' if structure_ok else '❌'}")
    print(f"Composants du bot: {'✓' if components_ok else '❌'}")
    print(f"Dashboard: {'✓' if dashboard_ok else '❌'}")
    
    if structure_ok and components_ok and dashboard_ok:
        print("\n🎉 TOUS LES TESTS SONT RÉUSSIS!")
        print("\nPour démarrer le bot:")
        print("1. python main.py (pour le bot)")
        print("2. streamlit run interface/dashboard.py (pour le dashboard)")
    else:
        print("\n⚠ Certains tests ont échoué. Vérifiez les erreurs ci-dessus.")

if __name__ == "__main__":
    asyncio.run(main())
