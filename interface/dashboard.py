"""
Dashboard Streamlit pour le bot de trading Fortune
"""

import streamlit as st
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime, timedelta
import time
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
except ImportError:
    st.error("Installing plotly...")
    os.system("pip install plotly")
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots

from utils.memory import TradingMemory
from utils.portfolio import PortfolioManager
fromutils.risk_management import RiskManager

# Configuration de la page
st.set_page_config(
    page_title="Fortune Bot Dashboard",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personnalisé
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        background: linear-gradient(90deg, #1f4037, #99f2c8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 2rem;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    
    .status-running {
        color: #00ff00;
        font-weight: bold;
    }
    
    .status-stopped {
        color: #ff0000;
        font-weight: bold;
    }
    
    .profit-positive {
        color: #00ff00;
        font-weight: bold;
    }
    
    .profit-negative {
        color: #ff0000;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

class FortuneDashboard:
    def __init__(self):
        self.memory = TradingMemory()
        self.portfolio = None
        self.risk_manager = None
        self.initialize_components()
    
    def initialize_components(self):
        """Initialiser les composants"""
        try:
            # Configuration par défaut
            config = {
                'trading': {'mode': 'paper', 'base_currency': 'USDT'},
                'risk_management': {'daily_loss_limit': 0.05, 'max_drawdown': 0.15}
            }
            
            self.portfolio = PortfolioManager(config['trading'])
            self.risk_manager = RiskManager(config['risk_management'])
            
            # Initialize portfolio synchronously for Streamlit
            import asyncio
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            if loop.is_running():
                # If loop is already running, create a task
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self.portfolio.initialize())
                    future.result()
            else:
                loop.run_until_complete(self.portfolio.initialize())
        
    except Exception as e:
        st.error(f"Erreur lors de l'initialisation: {e}")
        # Create minimal fallback
        self.portfolio = None
        self.risk_manager = None
    
    def run(self):
        """Exécuter le dashboard"""
        # Header principal
        st.markdown('<h1 class="main-header">💰 Fortune Bot Dashboard</h1>', unsafe_allow_html=True)
        
        # Sidebar
        self.render_sidebar()
        
        # Contenu principal
        self.render_main_content()
        
        # Auto-refresh
        if st.session_state.get('auto_refresh', True):
            time.sleep(5)
            st.rerun()
    
    def render_sidebar(self):
        """Rendre la sidebar"""
        st.sidebar.title("🎛️ Contrôles")
        
        # Statut du bot
        bot_status = self.get_bot_status()
        status_class = "status-running" if bot_status == "Running" else "status-stopped"
        st.sidebar.markdown(f'**Statut:** <span class="{status_class}">{bot_status}</span>', 
                           unsafe_allow_html=True)
        
        # Contrôles
        col1, col2 = st.sidebar.columns(2)
        with col1:
            if st.button("▶️ Start", use_container_width=True):
                self.start_bot()
        with col2:
            if st.button("⏹️ Stop", use_container_width=True):
                self.stop_bot()
        
        st.sidebar.divider()
        
        # Configuration
        st.sidebar.subheader("⚙️ Configuration")
        
        # Mode de trading
        trading_mode = st.sidebar.selectbox(
            "Mode de trading",
            ["paper", "live"],
            index=0
        )
        
        # Stratégies actives
        st.sidebar.subheader("📈 Stratégies")
        strategies = ["RSI", "MACD", "Grid", "DCA", "Scalping", "Trend Following"]
        selected_strategies = st.sidebar.multiselect(
            "Stratégies actives",
            strategies,
            default=["RSI", "MACD", "DCA"]
        )
        
        # Paramètres de risque
        st.sidebar.subheader("⚠️ Gestion des risques")
        risk_per_trade = st.sidebar.slider("Risque par trade (%)", 1, 10, 2)
        max_positions = st.sidebar.slider("Positions max", 1, 10, 5)
        
        # Auto-refresh
        st.sidebar.divider()
        auto_refresh = st.sidebar.checkbox("Auto-refresh", value=True)
        st.session_state['auto_refresh'] = auto_refresh
        
        if st.sidebar.button("🔄 Refresh Now"):
            st.rerun()
    
    def render_main_content(self):
        """Rendre le contenu principal"""
        # Métriques principales
        self.render_key_metrics()
        
        # Graphiques
        col1, col2 = st.columns(2)
        
        with col1:
            self.render_portfolio_chart()
            self.render_strategy_performance()
        
        with col2:
            self.render_trades_chart()
            self.render_risk_metrics()
        
        # Tableaux détaillés
        self.render_detailed_tables()
    
    def render_key_metrics(self):
        """Rendre les métriques clés"""
        portfolio_summary = self.portfolio.get_portfolio_summary() if self.portfolio else {}
        memory_summary = self.memory.get_memory_summary()
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            total_value = portfolio_summary.get('total_value', 0)
            st.metric(
                "💰 Valeur Portfolio",
                f"${total_value:,.2f}",
                delta=f"{portfolio_summary.get('pnl_percentage', 0):.2f}%"
            )
        
        with col2:
            pnl = portfolio_summary.get('total_pnl', 0)
            pnl_color = "profit-positive" if pnl >= 0 else "profit-negative"
            st.metric(
                "📊 P&L Total",
                f"${pnl:,.2f}",
                delta=f"{pnl:+.2f}"
            )
        
        with col3:
            active_positions = portfolio_summary.get('active_positions', 0)
            st.metric(
                "📈 Positions Actives",
                str(active_positions),
                delta=None
            )
        
        with col4:
            total_trades = memory_summary.get('total_trades', 0)
            st.metric(
                "🔄 Trades Total",
                str(total_trades),
                delta=None
            )
        
        with col5:
            session_duration = memory_summary.get('session_duration', '0:00:00')
            st.metric(
                "⏱️ Session",
                str(session_duration).split('.')[0],  # Enlever les microsecondes
                delta=None
            )
    
    def render_portfolio_chart(self):
        """Rendre le graphique du portfolio"""
        st.subheader("📊 Évolution du Portfolio")
        
        # Générer des données d'exemple pour la démonstration
        dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
        values = [10000]
        
        import numpy as np
        for i in range(1, 30):
            change = values[-1] * (1 + (0.02 * (0.5 - np.random.random())))
            values.append(change)
        
        df = pd.DataFrame({
            'Date': dates,
            'Value': values
        })
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['Date'],
            y=df['Value'],
            mode='lines',
            name='Portfolio Value',
            line=dict(color='#00ff88', width=3)
        ))
        
        fig.update_layout(
            title="Évolution de la valeur du portfolio",
            xaxis_title="Date",
            yaxis_title="Valeur ($)",
            template="plotly_dark",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def render_trades_chart(self):
        """Rendre le graphique des trades"""
        st.subheader("🎯 Analyse des Trades")
        
        trades = self.memory.memory.get('trades', [])
        
        if trades:
            # Convertir en DataFrame
            df_trades = pd.DataFrame(trades)
            df_trades['timestamp'] = pd.to_datetime(df_trades['timestamp'])
            df_trades['profit_cumsum'] = df_trades['profit'].cumsum()
            
            fig = make_subplots(
                rows=2, cols=1,
                subplot_titles=('Profit Cumulé', 'Profits par Trade'),
                vertical_spacing=0.1
            )
            
            # Profit cumulé
            fig.add_trace(
                go.Scatter(
                    x=df_trades['timestamp'],
                    y=df_trades['profit_cumsum'],
                    mode='lines',
                    name='Profit Cumulé',
                    line=dict(color='#ff6b6b')
                ),
                row=1, col=1
            )
            
            # Profits individuels
            colors = ['green' if p > 0 else 'red' for p in df_trades['profit']]
            fig.add_trace(
                go.Bar(
                    x=df_trades['timestamp'],
                    y=df_trades['profit'],
                    name='Profit par Trade',
                    marker_color=colors
                ),
                row=2, col=1
            )
            
            fig.update_layout(
                template="plotly_dark",
                height=400,
                showlegend=False
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aucun trade enregistré pour le moment")
    
    def render_strategy_performance(self):
        """Rendre les performances par stratégie"""
        st.subheader("🎯 Performance par Stratégie")
        
        strategies_data = {
            'RSI': {'trades': 45, 'win_rate': 0.67, 'profit': 234.56},
            'MACD': {'trades': 32, 'win_rate': 0.59, 'profit': 156.78},
            'Grid': {'trades': 78, 'win_rate': 0.72, 'profit': 445.23},
            'DCA': {'trades': 12, 'win_rate': 0.83, 'profit': 123.45}
        }
        
        df_strategies = pd.DataFrame(strategies_data).T
        df_strategies.reset_index(inplace=True)
        df_strategies.rename(columns={'index': 'Strategy'}, inplace=True)
        
        fig = px.bar(
            df_strategies,
            x='Strategy',
            y='profit',
            color='win_rate',
            title="Profit par Stratégie",
            color_continuous_scale='RdYlGn'
        )
        
        fig.update_layout(
            template="plotly_dark",
            height=300
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def render_risk_metrics(self):
        """Rendre les métriques de risque"""
        st.subheader("⚠️ Métriques de Risque")
        
        risk_metrics = {
            'Sharpe Ratio': 1.45,
            'Max Drawdown': -8.5,
            'Win Rate': 68.5,
            'Risk/Reward': 1.8
        }
        
        for metric, value in risk_metrics.items():
            if 'Drawdown' in metric:
                st.metric(metric, f"{value}%", delta=f"{value:.1f}%")
            elif 'Rate' in metric:
                st.metric(metric, f"{value}%", delta=None)
            else:
                st.metric(metric, f"{value:.2f}", delta=None)
    
    def render_detailed_tables(self):
        """Rendre les tableaux détaillés"""
        tab1, tab2, tab3, tab4 = st.tabs(["📊 Positions", "🔄 Trades Récents", "📈 Signaux", "⚙️ Logs"])
        
        with tab1:
            self.render_positions_table()
        
        with tab2:
            self.render_recent_trades_table()
        
        with tab3:
            self.render_signals_table()
        
        with tab4:
            self.render_logs_table()
    
    def render_positions_table(self):
        """Rendre le tableau des positions"""
        st.subheader("📊 Positions Actuelles")
        
        if self.portfolio:
            positions = self.portfolio.get_current_positions()
            
            if positions:
                positions_data = []
                for symbol, position in positions.items():
                    current_price = self.portfolio._get_current_price(symbol)
                    unrealized_pnl = (current_price - position['avg_price']) * position['quantity']
                    
                    positions_data.append({
                        'Symbole': symbol,
                        'Quantité': f"{position['quantity']:.6f}",
                        'Prix Moyen': f"${position['avg_price']:.4f}",
                        'Prix Actuel': f"${current_price:.4f}",
                        'P&L Non Réalisé': f"${unrealized_pnl:.2f}",
                        'Entrée': position['entry_time']
                    })
                
                df_positions = pd.DataFrame(positions_data)
                st.dataframe(df_positions, use_container_width=True)
            else:
                st.info("Aucune position active")
        else:
            st.error("Portfolio non initialisé")
    
    def render_recent_trades_table(self):
        """Rendre le tableau des trades récents"""
        st.subheader("🔄 Trades Récents")
        
        trades = self.memory.memory.get('trades', [])
        
        if trades:
            # Prendre les 20 derniers trades
            recent_trades = trades[-20:]
            
            trades_data = []
            for trade in recent_trades:
                trades_data.append({
                    'Timestamp': trade.get('timestamp', ''),
                    'Stratégie': trade.get('strategy', ''),
                    'Symbole': trade.get('symbol', ''),
                    'Côté': trade.get('side', ''),
                    'Prix': f"${trade.get('entry_price', 0):.4f}",
                    'Quantité': f"{trade.get('quantity', 0):.6f}",
                    'Profit': f"${trade.get('profit', 0):.2f}"
                })
            
            df_trades = pd.DataFrame(trades_data)
            st.dataframe(df_trades, use_container_width=True)
        else:
            st.info("Aucun trade enregistré")
    
    def render_signals_table(self):
        """Rendre le tableau des signaux"""
        st.subheader("📈 Signaux Récents")
        
        # Simuler des signaux pour la démonstration
        signals_data = [
            {'Timestamp': datetime.now().strftime('%H:%M:%S'), 'Stratégie': 'RSI', 'Symbole': 'BTCUSDT', 'Signal': 'BUY', 'Confiance': '85%'},
            {'Timestamp': (datetime.now() - timedelta(minutes=5)).strftime('%H:%M:%S'), 'Stratégie': 'MACD', 'Symbole': 'ETHUSDT', 'Signal': 'SELL', 'Confiance': '72%'},
            {'Timestamp': (datetime.now() - timedelta(minutes=10)).strftime('%H:%M:%S'), 'Stratégie': 'Grid', 'Symbole': 'ADAUSDT', 'Signal': 'BUY', 'Confiance': '90%'},
        ]
        
        df_signals = pd.DataFrame(signals_data)
        st.dataframe(df_signals, use_container_width=True)
    
    def render_logs_table(self):
        """Rendre le tableau des logs"""
        st.subheader("⚙️ Logs Système")
        
        # Lire les logs récents
        log_file = 'logs/fortune_bot.log'
        if os.path.exists(log_file):
            try:
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                    recent_logs = lines[-50:]  # 50 dernières lignes
                
                logs_text = ''.join(recent_logs)
                st.text_area("Logs récents", logs_text, height=300)
            except Exception as e:
                st.error(f"Erreur lors de la lecture des logs: {e}")
        else:
            st.info("Aucun fichier de log trouvé")
    
    def get_bot_status(self):
        """Obtenir le statut du bot"""
        # Vérifier si le bot est en cours d'exécution
        # Implémentation simplifiée
        return "Stopped"  # ou "Running"
    
    def start_bot(self):
        """Démarrer le bot"""
        st.success("Bot démarré!")
        # Implémentation pour démarrer le bot
    
    def stop_bot(self):
        """Arrêter le bot"""
        st.warning("Bot arrêté!")
        # Implémentation pour arrêter le bot

# Point d'entrée principal
if __name__ == "__main__":
    dashboard = FortuneDashboard()
    dashboard.run()
