"""
Script de démarrage rapide pour le Fortune Bot
"""

import os
import sys
import subprocess
import asyncio
from pathlib import Path

def install_requirements():
    """Installer les dépendances"""
    print("Installation des dépendances...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✓ Dépendances installées")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors de l'installation: {e}")
        return False

def create_directories():
    """Créer les répertoires nécessaires"""
    directories = ['data', 'logs', 'backtest_results']
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✓ Répertoire {directory} créé")

def check_python_version():
    """Vérifier la version de Python"""
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print(f"✓ Python {version.major}.{version.minor} compatible")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor} non compatible. Requis: Python 3.8+")
        return False

async def run_initial_test():
    """Exécuter un test initial"""
    print("\nTest initial du système...")
    try:
        from test_bot import test_components
        success = await test_components()
        if success:
            print("✓ Test initial réussi")
        return success
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        return False

def main():
    """Fonction principale de démarrage"""
    print("🚀 FORTUNE BOT - DÉMARRAGE RAPIDE")
    print("=" * 50)
    
    # Vérifications préliminaires
    if not check_python_version():
        return
    
    # Créer les répertoires
    create_directories()
    
    # Installer les dépendances
    if not install_requirements():
        return
    
    # Test initial
    print("\nExécution du test initial...")
    try:
        success = asyncio.run(run_initial_test())
        if not success:
            print("⚠ Le test initial a échoué, mais vous pouvez continuer")
    except Exception as e:
        print(f"⚠ Impossible d'exécuter le test: {e}")
    
    print("\n🎉 CONFIGURATION TERMINÉE!")
    print("\nCommandes disponibles:")
    print("1. python main.py                    # Démarrer le bot de trading")
    print("2. streamlit run interface/dashboard.py  # Ouvrir le dashboard")
    print("3. python test_bot.py                # Exécuter les tests")
    print("4. python scripts/run_backtest.py   # Lancer un backtest")
    
    print("\n📊 Le dashboard sera disponible sur: http://localhost:8501")
    print("💰 Mode par défaut: Paper Trading (simulation)")
    
    # Proposer de lancer le dashboard
    try:
        choice = input("\nVoulez-vous lancer le dashboard maintenant? (y/n): ")
        if choice.lower() in ['y', 'yes', 'o', 'oui']:
            print("Lancement du dashboard...")
            subprocess.run([sys.executable, "-m", "streamlit", "run", "interface/dashboard.py"])
    except KeyboardInterrupt:
        print("\nAu revoir!")

if __name__ == "__main__":
    main()
