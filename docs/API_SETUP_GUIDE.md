# 🔑 Guide de Configuration des API

## 📋 Étapes de Configuration

### 1. Configuration Automatique (Recommandé)
\`\`\`bash
python setup_api_keys.py
\`\`\`

### 2. Configuration Manuelle

#### A. Créer le fichier .env
\`\`\`bash
cp .env.example .env
# Puis éditez .env avec vos clés
\`\`\`

#### B. Modifier settings.yaml
\`\`\`yaml
api:
  exchange: binance
  testnet: true  # false pour production
  api_key: ""    # Laissez vide, sera lu depuis .env
  api_secret: "" # Laissez vide, sera lu depuis .env
\`\`\`

## 🏦 Configuration par Exchange

### Binance
1. Allez sur [Binance API Management](https://www.binance.com/en/my/settings/api-management)
2. Créez une nouvelle API Key
3. **IMPORTANT**: Activez seulement "Spot & Margin Trading"
4. **NE JAMAIS** activer "Enable Withdrawals"
5. Ajoutez votre IP si nécessaire

**Permissions requises:**
- ✅ Read Info
- ✅ Spot & Margin Trading
- ❌ Futures Trading (optionnel)
- ❌ Enable Withdrawals (JAMAIS!)

### Coinbase Pro
1. Allez sur [Coinbase Pro API](https://pro.coinbase.com/profile/api)
2. Créez une nouvelle API Key
3. Permissions: View, Trade (PAS Transfer)

### Kraken
1. Allez sur [Kraken API](https://www.kraken.com/u/security/api)
2. Créez une nouvelle API Key
3. Permissions: Query Funds, Query Open Orders, Create & Modify Orders

## 🔒 Sécurité

### Variables d'Environnement Requises
\`\`\`env
# OBLIGATOIRE
BINANCE_API_KEY=votre_cle_api
BINANCE_SECRET_KEY=votre_cle_secrete

# OPTIONNEL
TRADING_MODE=paper  # ou "live"
ENVIRONMENT=development
TELEGRAM_BOT_TOKEN=votre_token_telegram
TELEGRAM_CHAT_ID=votre_chat_id
\`\`\`

### Bonnes Pratiques
- ✅ Utilisez le testnet pour commencer
- ✅ Stockez les clés dans .env (jamais dans le code)
- ✅ Ajoutez .env au .gitignore
- ✅ Utilisez des IP whitelisting
- ✅ Surveillez les logs d'API
- ❌ Ne jamais activer les retraits
- ❌ Ne jamais commiter les clés
- ❌ Ne jamais partager vos clés

## 🧪 Test de Configuration

\`\`\`bash
# Tester la configuration
python test_api_config.py

# Tester le bot complet
python test_bot.py
\`\`\`

## 🚀 Déploiement

### Variables Render/Heroku
\`\`\`
BINANCE_API_KEY=your_key
BINANCE_SECRET_KEY=your_secret
TRADING_MODE=live
ENVIRONMENT=production
\`\`\`

### Variables Locales vs Production
- **Local**: Utilisez .env
- **Production**: Variables d'environnement du serveur
- **Testnet**: Toujours pour les tests
- **Mainnet**: Seulement en production avec surveillance

## ❓ Dépannage

### Erreur "Invalid API Key"
- Vérifiez que la clé est correcte
- Vérifiez les permissions
- Vérifiez l'IP whitelisting

### Erreur "Insufficient Permissions"
- Activez "Spot Trading" sur Binance
- Vérifiez que les retraits sont DÉSACTIVÉS

### Erreur de Connexion
- Vérifiez votre connexion internet
- Vérifiez si l'exchange est en maintenance
- Utilisez le testnet pour tester
\`\`\`

```python file="test_api_config.py"
"""
Script de test pour la configuration API
"""

import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.api_config import api_config
from utils.market_data import MarketDataManager

async def test_api_configuration():
    """Tester la configuration API complète"""
    print("🧪 TEST DE CONFIGURATION API")
    print("=" * 50)
    
    # Test 1: Chargement de la configuration
    print("1. Test du chargement de configuration...")
    try:
        trading_config = api_config.get_trading_config()
        print(f"   ✅ Mode de trading: {trading_config.get('mode', 'non défini')}")
        print(f"   ✅ Devise de base: {trading_config.get('base_currency', 'non définie')}")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False
    
    # Test 2: Validation des credentials
    print("\n2. Test des credentials API...")
    try:
        exchange = api_config.config['api']['exchange']
        if api_config.validate_credentials(exchange):
            print(f"   ✅ Credentials {exchange} valides")
            
            # Masquer les clés pour la sécurité
            credentials = api_config.get_api_credentials(exchange)
            masked_key = credentials['api_key'][:8] + "..." if credentials['api_key'] else "NON DÉFINIE"
            print(f"   ✅ API Key: {masked_key}")
            print(f"   ✅ Testnet: {credentials.get('testnet', 'non défini')}")
        else:
            print(f"   ❌ Credentials {exchange} manquants ou invalides")
            print("   💡 Exécutez: python setup_api_keys.py")
            return False
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False
    
    # Test 3: Connexion à l'API
    print("\n3. Test de connexion à l'API...")
    try:
        market_data = MarketDataManager(api_config.config['api'])
        await market_data.connect()
        
        # Test de récupération de données
        data = await market_data.get_latest_data()
        if data:
            print(f"   ✅ Données récupérées pour {len(data)} symboles")
            
            # Afficher un échantillon
            for symbol, df in list(data.items())[:2]:
                latest_price = df['close'].iloc[-1]
                print(f"   📊 {symbol}: ${latest_price:,.2f}")
        else:
            print("   ⚠️ Aucune donnée récupérée")
        
        await market_data.disconnect()
        
    except Exception as e:
        print(f"   ❌ Erreur de connexion: {e}")
        return False
    
    # Test 4: Configuration de sécurité
    print("\n4. Test de sécurité...")
    try:
        if api_config.is_live_mode():
            print("   ⚠️ MODE LIVE ACTIVÉ - Soyez prudent!")
        else:
            print("   ✅ Mode paper trading (sécurisé)")
        
        # Vérifier que les retraits ne sont pas activés
        print("   ✅ Vérification: retraits désactivés (recommandé)")
        
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    print("\n🎉 CONFIGURATION API VALIDÉE!")
    print("\nPrêt à démarrer le trading:")
    print("- python main.py (démarrer le bot)")
    print("- streamlit run interface/dashboard.py (dashboard)")
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_api_configuration())
    if not success:
        print("\n❌ Configuration incomplète. Consultez le guide:")
        print("- docs/API_SETUP_GUIDE.md")
        print("- python setup_api_keys.py")
        sys.exit(1)
