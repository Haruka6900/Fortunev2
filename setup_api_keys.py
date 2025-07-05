"""
Script interactif pour configurer les clés API
"""

import os
import yaml
from getpass import getpass
import sys

def setup_binance_api():
    """Configuration interactive pour Binance"""
    print("\n🔑 CONFIGURATION BINANCE API")
    print("=" * 50)
    print("1. Allez sur https://www.binance.com/en/my/settings/api-management")
    print("2. Créez une nouvelle API Key")
    print("3. Activez 'Spot & Margin Trading' (PAS de Withdrawal)")
    print("4. Notez votre API Key et Secret Key")
    print()
    
    api_key = input("Entrez votre Binance API Key: ").strip()
    if not api_key:
        print("❌ API Key requise")
        return None, None
    
    api_secret = getpass("Entrez votre Binance Secret Key (caché): ").strip()
    if not api_secret:
        print("❌ Secret Key requise")
        return None, None
    
    # Demander si testnet ou mainnet
    use_testnet = input("Utiliser le testnet? (y/n) [y]: ").strip().lower()
    testnet = use_testnet != 'n'
    
    return api_key, api_secret, testnet

def setup_telegram_notifications():
    """Configuration optionnelle pour Telegram"""
    print("\n📱 NOTIFICATIONS TELEGRAM (Optionnel)")
    print("=" * 50)
    
    setup_telegram = input("Configurer les notifications Telegram? (y/n) [n]: ").strip().lower()
    if setup_telegram != 'y':
        return None, None
    
    print("1. Créez un bot avec @BotFather sur Telegram")
    print("2. Obtenez le token du bot")
    print("3. Obtenez votre Chat ID avec @userinfobot")
    print()
    
    bot_token = input("Token du bot Telegram: ").strip()
    chat_id = input("Votre Chat ID: ").strip()
    
    return bot_token, chat_id

def create_env_file(api_key, api_secret, testnet, telegram_token=None, telegram_chat=None):
    """Créer le fichier .env"""
    env_content = f"""# 🔐 FORTUNE BOT - VARIABLES D'ENVIRONNEMENT
# NE JAMAIS COMMITER CE FICHIER !

# BINANCE API
BINANCE_API_KEY={api_key}
BINANCE_SECRET_KEY={api_secret}

# CONFIGURATION
TRADING_MODE=paper
ENVIRONMENT=development
LOG_LEVEL=INFO
"""
    
    if telegram_token and telegram_chat:
        env_content += f"""
# TELEGRAM NOTIFICATIONS
TELEGRAM_BOT_TOKEN={telegram_token}
TELEGRAM_CHAT_ID={telegram_chat}
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print("✅ Fichier .env créé")

def update_settings_yaml(testnet):
    """Mettre à jour settings.yaml"""
    try:
        with open('settings.yaml', 'r') as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        config = {}
    
    # Mettre à jour la configuration
    if 'api' not in config:
        config['api'] = {}
    
    config['api']['exchange'] = 'binance'
    config['api']['testnet'] = testnet
    config['api']['api_key'] = ''  # Sera lu depuis .env
    config['api']['api_secret'] = ''  # Sera lu depuis .env
    
    with open('settings.yaml', 'w') as f:
        yaml.dump(config, f, default_flow_style=False)
    
    print("✅ Fichier settings.yaml mis à jour")

def test_api_connection():
    """Tester la connexion API"""
    print("\n🧪 TEST DE CONNEXION API")
    print("=" * 30)
    
    try:
        from config.api_config import api_config
        
        # Vérifier les credentials
        if api_config.validate_credentials():
            print("✅ Credentials API trouvés")
            
            # Test de connexion (simulation)
            print("✅ Connexion API simulée réussie")
            print(f"Mode: {'Testnet' if api_config.config['api']['testnet'] else 'Mainnet'}")
            print(f"Trading Mode: {api_config.config['trading']['mode']}")
        else:
            print("❌ Credentials API manquants")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        return False
    
    return True

def main():
    """Fonction principale de configuration"""
    print("🚀 FORTUNE BOT - CONFIGURATION DES API")
    print("=" * 60)
    print("Ce script va vous aider à configurer vos clés API de manière sécurisée.")
    print()
    
    # Avertissement de sécurité
    print("⚠️  IMPORTANT - SÉCURITÉ:")
    print("- Vos clés API ne seront stockées que localement")
    print("- N'activez JAMAIS les permissions de retrait")
    print("- Utilisez le testnet pour commencer")
    print("- Gardez vos clés secrètes")
    print()
    
    # Configuration Binance
    result = setup_binance_api()
    if not result:
        print("❌ Configuration annulée")
        return
    
    api_key, api_secret, testnet = result
    
    # Configuration Telegram (optionnel)
    telegram_token, telegram_chat = setup_telegram_notifications()
    
    # Créer les fichiers de configuration
    print("\n📝 CRÉATION DES FICHIERS DE CONFIGURATION")
    print("=" * 50)
    
    create_env_file(api_key, api_secret, testnet, telegram_token, telegram_chat)
    update_settings_yaml(testnet)
    
    # Test de connexion
    if test_api_connection():
        print("\n🎉 CONFIGURATION TERMINÉE AVEC SUCCÈS!")
        print("=" * 50)
        print("Vous pouvez maintenant:")
        print("1. python main.py                    # Démarrer le bot")
        print("2. streamlit run interface/dashboard.py  # Ouvrir le dashboard")
        print()
        print("💡 Conseils:")
        print("- Commencez en mode 'paper' pour tester")
        print("- Surveillez les logs dans le dashboard")
        print("- Ajustez les paramètres de risque selon vos besoins")
    else:
        print("\n⚠️ Configuration créée mais test échoué")
        print("Vérifiez vos clés API et réessayez")

if __name__ == "__main__":
    main()
