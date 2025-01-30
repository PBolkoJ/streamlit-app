import streamlit as st
import plotly.express as px
import pandas as pd
import time
from datetime import datetime
import ccxt
import sys
import os

# Získanie cesty k nadradenému priečinku
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(parent_dir)

# Import config
import config

# Pristupovanie k účtom
exchange_a1 = ccxt.binance({
    "apiKey": config.SUB_A1_API_KEY,
    "secret": config.SUB_A1_SECRET_KEY,
    'enableRateLimit': True,
    "timeout": 30000,
})

exchange_a2 = ccxt.binance({
    "apiKey": config.SUB_A2_API_KEY,
    "secret": config.SUB_A2_SECRET_KEY,
    'enableRateLimit': True,
    "timeout": 30000,
})

exchange_a3 = ccxt.binance({
    "apiKey": config.SUB_A3_API_KEY,
    "secret": config.SUB_A3_API_SECRET,
    'enableRateLimit': True,
    "timeout": 30000,
})

exchange_main = ccxt.binance({
    "apiKey": config.MAIN_API_KEY,
    "secret": config.MAIN_API_SECRET,
    'enableRateLimit': True,
    "timeout": 30000,
})

# Inicializácia dát
history = pd.DataFrame(columns=["time", "account", "percent_change"])
initial_values = {}


def get_portfolio_value(exchange, account_name):
    """Získa celkovú hodnotu portfólia v EUR."""
    balance = exchange.fetch_balance()
    eur_balance = balance["total"].get("EUR", 0)

    total_value = eur_balance
    for symbol, asset in balance['total'].items():
        if asset > 0 and symbol != "EUR":
            try:
                ticker = exchange.fetch_ticker(f'{symbol}/EUR')
                current_price = ticker['close']
                total_value += asset * current_price
            except ccxt.BaseError:
                pass

    return round(total_value, 2)


# Nastavenie stránky
st.set_page_config(page_title="📈 Percentuálna zmena portfólia", layout="wide")
st.title("📊 Vývoj portfólia v percentách")

# Kontajner pre graf
graph_container = st.empty()

# Interval aktualizácie
refresh_rate = 60 * 30

while True:
    current_time = datetime.now().strftime("%H:%M:%S")

    # Získanie hodnôt portfólia
    portfolio_values = {
        "Účet 1": get_portfolio_value(exchange_a1, "Účet 1"),
        "Účet 2": get_portfolio_value(exchange_a2, "Účet 2"),
        "Účet 3": get_portfolio_value(exchange_a3, "Účet 3"),
        "Účet Main": get_portfolio_value(exchange_main, "Účet Main"),
    }

    # Uloženie počiatočných hodnôt
    for account, value in portfolio_values.items():
        if account not in initial_values:
            initial_values[account] = value  # Uložíme prvú hodnotu

    # Výpočet percentuálnej zmeny
    percent_changes = [
        {
            "account": account,
            "percent_change": ((value - initial_values[account]) / initial_values[account]) * 100,
            "time": current_time
        }
        for account, value in portfolio_values.items()
    ]

    # Aktualizácia histórie
    new_rows = pd.DataFrame(percent_changes)
    history = pd.concat([history, new_rows], ignore_index=True)

    # Vykreslenie grafu
    fig = px.line(history, x="time", y="percent_change", color="account", markers=True,
                  title="Vývoj hodnoty portfólií v %")
    fig.update_layout(yaxis_title="Percentuálna zmena (%)")

    graph_container.plotly_chart(fig, use_container_width=True)

    time.sleep(refresh_rate)  # Aktualizácia v intervale

