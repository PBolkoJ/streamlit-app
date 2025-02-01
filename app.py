import streamlit as st
import plotly.express as px
import pandas as pd
import time
from datetime import datetime
import ccxt
import csv
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


def get_portfolio_value(exchange):
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


def save_values_to_csv():
    with open("Data/data_a1.csv", mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([data_a1])  # Zapisujeme ako zoznam

    with open("Data/data_a2.csv", mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([data_a2])  # Zapisujeme ako zoznam

    with open("Data/data_a3.csv", mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([data_a3])  # Zapisujeme ako zoznam

    with open("Data/data_main.csv", mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([data_main])  # Zapisujeme ako zoznam


def read_values_from_csv():
    def read_single_value(file_path):
        with open(file_path, mode="r", newline="", encoding="utf-8") as file:
            reader = csv.reader(file)
            return float(next(reader)[0])  # Prečítame prvú hodnotu a skonvertujeme na float

    return (
        read_single_value("Data/data_a1.csv"),
        read_single_value("Data/data_a2.csv"),
        read_single_value("Data/data_a3.csv"),
        read_single_value("Data/data_main.csv"),
    )


# Nastavenie stránky
st.set_page_config(page_title="📈 Percentuálna zmena portfólia", layout="wide")
st.title("📊 Vývoj portfólia v percentách")

# Kontajner pre graf
graph_container = st.empty()

# Interval aktualizácie
refresh_rate = 5

portfolio_values = {}

while True:
    current_time = datetime.now().strftime("%H:%M:%S")

    data_a1 = get_portfolio_value(exchange_a1)
    data_a2 = get_portfolio_value(exchange_a2)
    data_a3 = get_portfolio_value(exchange_a3)
    data_main = get_portfolio_value(exchange_main)

    save_values_to_csv()

    a1_values, a2_values, a3_values, main_values = read_values_from_csv()

    portfolio_values["Account_a1"] = a1_values
    portfolio_values["Account_a2"] = a2_values
    portfolio_values["Account_a3"] = a3_values
    portfolio_values["Account_main"] = main_values

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
        for account, value in portfolio_values.items() if account in initial_values
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

