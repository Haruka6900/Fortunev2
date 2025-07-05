"""
Script d'optimisation des paramètres de stratégies
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.backtest import run_strategy_backtest
from strategies.rsi_strategy import RSIStrategy
from strategies.macd_strategy import MACDStrategy
import itertools
import pandas as pd

async def optimize_rsi_strategy():
    """Optimiser les paramètres de la stratégie RSI"""
    print("Optimisation de la stratégie RSI...")
    
    # Paramètres à tester
    rsi_periods = [10, 14, 18, 21]
    oversold_levels = [25, 30, 35]
    overbought_levels = [65, 70, 75]
    
    best_params = None
    best_return = -float('inf')
    results = []
    
    # Tester toutes les combinaisons
    for rsi_period, oversold, overbought in itertools.product(rsi_periods, oversold_levels, overbought_levels):
        params = {
            'rsi_period': rsi_period,
            'oversold_threshold': oversold,
            'overbought_threshold': overbought
        }
        
        print(f"Test: RSI={rsi_period}, Oversold={oversold}, Overbought={overbought}")
        
        # Exécuter le backtest
        result = await run_strategy_backtest('rsi', 'BTCUSDT', days=30)
        
        if 'error' not in result:
            total_return = result['total_return']
            sharpe_ratio = result['sharpe_ratio']
            max_drawdown = result['max_drawdown']
            
            # Score composite (return ajusté par le risque)
            score = total_return * sharpe_ratio * (1 - max_drawdown)
            
            results.append({
                'params': params,
                'return': total_return,
                'sharpe': sharpe_ratio,
                'drawdown': max_drawdown,
                'score': score
            })
            
            if score > best_return:
                best_return = score
                best_params = params
                
            print(f"  Return: {total_return:.2%}, Sharpe: {sharpe_ratio:.2f}, Score: {score:.4f}")
        else:
            print(f"  Erreur: {result['error']}")
    
    # Sauvegarder les résultats
    df_results = pd.DataFrame(results)
    df_results.to_csv('backtest_results/rsi_optimization.csv', index=False)
    
    print(f"\nMeilleurs paramètres RSI: {best_params}")
    print(f"Score: {best_return:.4f}")
    
    return best_params

async def optimize_macd_strategy():
    """Optimiser les paramètres de la stratégie MACD"""
    print("Optimisation de la stratégie MACD...")
    
    # Paramètres à tester
    fast_periods = [8, 12, 16]
    slow_periods = [21, 26, 30]
    signal_periods = [6, 9, 12]
    
    best_params = None
    best_return = -float('inf')
    results = []
    
    # Tester toutes les combinaisons
    for fast, slow, signal in itertools.product(fast_periods, slow_periods, signal_periods):
        if fast >= slow:  # Fast doit être < slow
            continue
            
        params = {
            'fast_period': fast,
            'slow_period': slow,
            'signal_period': signal
        }
        
        print(f"Test: Fast={fast}, Slow={slow}, Signal={signal}")
        
        # Exécuter le backtest
        result = await run_strategy_backtest('macd', 'BTCUSDT', days=30)
        
        if 'error' not in result:
            total_return = result['total_return']
            sharpe_ratio = result['sharpe_ratio']
            max_drawdown = result['max_drawdown']
            
            # Score composite
            score = total_return * sharpe_ratio * (1 - max_drawdown)
            
            results.append({
                'params': params,
                'return': total_return,
                'sharpe': sharpe_ratio,
                'drawdown': max_drawdown,
                'score': score
            })
            
            if score > best_return:
                best_return = score
                best_params = params
                
            print(f"  Return: {total_return:.2%}, Sharpe: {sharpe_ratio:.2f}, Score: {score:.4f}")
        else:
            print(f"  Erreur: {result['error']}")
    
    # Sauvegarder les résultats
    df_results = pd.DataFrame(results)
    df_results.to_csv('backtest_results/macd_optimization.csv', index=False)
    
    print(f"\nMeilleurs paramètres MACD: {best_params}")
    print(f"Score: {best_return:.4f}")
    
    return best_params

async def main():
    """Fonction principale d'optimisation"""
    print("=== OPTIMISATION DES STRATÉGIES FORTUNE BOT ===\n")
    
    # Créer le répertoire de résultats
    os.makedirs('backtest_results', exist_ok=True)
    
    # Optimiser RSI
    rsi_params = await optimize_rsi_strategy()
    print("\n" + "="*50 + "\n")
    
    # Optimiser MACD
    macd_params = await optimize_macd_strategy()
    
    print("\n=== RÉSUMÉ DE L'OPTIMISATION ===")
    print(f"RSI optimisé: {rsi_params}")
    print(f"MACD optimisé: {macd_params}")
    
    # Sauvegarder les paramètres optimaux
    optimal_params = {
        'rsi': rsi_params,
        'macd': macd_params
    }
    
    import json
    with open('data/optimized_params.json', 'w') as f:
        json.dump(optimal_params, f, indent=2)
    
    print("\nParamètres optimaux sauvegardés dans data/optimized_params.json")

if __name__ == "__main__":
    asyncio.run(main())
