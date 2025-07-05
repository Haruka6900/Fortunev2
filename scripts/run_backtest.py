"""
Script pour exécuter des backtests complets
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.backtest import run_strategy_backtest
import pandas as pd
import json
from datetime import datetime

async def run_comprehensive_backtest():
    """Exécuter un backtest complet sur toutes les stratégies"""
    print("=== BACKTEST COMPLET FORTUNE BOT ===\n")
    
    strategies = ['rsi', 'macd', 'grid', 'dca']
    symbols = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT']
    periods = [7, 14, 30]
    
    all_results = []
    
    for strategy in strategies:
        print(f"Testing strategy: {strategy.upper()}")
        
        for symbol in symbols:
            print(f"  Symbol: {symbol}")
            
            for period in periods:
                print(f"    Period: {period} days")
                
                result = await run_strategy_backtest(strategy, symbol, period)
                
                if 'error' not in result:
                    result_summary = {
                        'strategy': strategy,
                        'symbol': symbol,
                        'period': period,
                        'total_return': result['total_return'],
                        'win_rate': result['win_rate'],
                        'sharpe_ratio': result['sharpe_ratio'],
                        'max_drawdown': result['max_drawdown'],
                        'total_trades': result['total_trades'],
                        'profit_factor': result['profit_factor']
                    }
                    
                    all_results.append(result_summary)
                    
                    print(f"      Return: {result['total_return']:.2%}")
                    print(f"      Win Rate: {result['win_rate']:.2%}")
                    print(f"      Sharpe: {result['sharpe_ratio']:.2f}")
                    print(f"      Max DD: {result['max_drawdown']:.2%}")
                else:
                    print(f"      Error: {result['error']}")
                
                print()
    
    # Sauvegarder les résultats
    df_results = pd.DataFrame(all_results)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'backtest_results/comprehensive_backtest_{timestamp}.csv'
    df_results.to_csv(filename, index=False)
    
    # Analyser les résultats
    print("=== ANALYSE DES RÉSULTATS ===\n")
    
    # Meilleure stratégie par métrique
    best_return = df_results.loc[df_results['total_return'].idxmax()]
    best_sharpe = df_results.loc[df_results['sharpe_ratio'].idxmax()]
    best_winrate = df_results.loc[df_results['win_rate'].idxmax()]
    
    print(f"Meilleur return: {best_return['strategy']} sur {best_return['symbol']} ({best_return['total_return']:.2%})")
    print(f"Meilleur Sharpe: {best_sharpe['strategy']} sur {best_sharpe['symbol']} ({best_sharpe['sharpe_ratio']:.2f})")
    print(f"Meilleur Win Rate: {best_winrate['strategy']} sur {best_winrate['symbol']} ({best_winrate['win_rate']:.2%})")
    
    # Moyennes par stratégie
    print("\n=== MOYENNES PAR STRATÉGIE ===")
    strategy_avg = df_results.groupby('strategy').agg({
        'total_return': 'mean',
        'win_rate': 'mean',
        'sharpe_ratio': 'mean',
        'max_drawdown': 'mean'
    }).round(4)
    
    print(strategy_avg)
    
    print(f"\nRésultats sauvegardés dans: {filename}")

if __name__ == "__main__":
    # Créer le répertoire de résultats
    os.makedirs('backtest_results', exist_ok=True)
    
    asyncio.run(run_comprehensive_backtest())
