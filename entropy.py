import os
import numpy as np
import pandas as pd
import yfinance as yf
from scipy.stats import entropy as shannon_entropy
import sqlite3
import requests
from io import StringIO

DB_FILE = "entropy_data.db"
TABLE   = "entropy_results"
TOP_N   = 20
BINS    = 20
FORCE_REFRESH = False

def normalized_entropy(series: pd.Series, bins: int = BINS) -> float:
    if series is None or len(series) == 0:
        return np.nan
    hist, _ = np.histogram(series, bins=bins, density=True)
    hist = hist[hist > 0]
    if len(hist) == 0:
        return np.nan
    H = shannon_entropy(hist, base=2)
    return float(H / np.log2(bins))

def log_returns(close: pd.Series) -> pd.Series:
    return np.log(close / close.shift(1)).dropna()

class StockEntropy:
    def __init__(self, ticker: str, bins: int = BINS):
        self.ticker = ticker
        self.bins = bins
        self.ents = None


    def calc_entropies(self):
        ent_values = []
        try:
            close = yf.download(
                self.ticker,
                period="6mo",
                interval="1h",
                auto_adjust=True,
                progress=False,
            )["Close"]
        except Exception:
            close = pd.Series(dtype=float)

        self.rets = log_returns(close)
        self.H_geo = normalized_entropy(self.rets, bins=self.bins)

    def get_value(self):
        return self.H_geo

def get_stock_list():
    try:
        url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status() 

        html_buffer = StringIO(response.text)
        df = pd.read_html(html_buffer, attrs={'id': 'constituents'})[0]

        tickers = df['Symbol'].tolist()
        tickers = [t.replace('.', '-') for t in tickers]
        print(f"Loaded {len(tickers)} tickers successfully.")
        return tickers
    except Exception as e:
        print(f"yfinance tickers_sp500() failed: {e}")


def save_to_db(df: pd.DataFrame, db_path: str, table: str):
    with sqlite3.connect(db_path) as conn:
        conn.execute(f"""
        CREATE TABLE IF NOT EXISTS {table} (
            Stock TEXT,
            Geometric REAL
        )
        """)
        df.to_sql(table, conn, if_exists="append", index=False)

# ---------- main ----------
if __name__ == "__main__":
    stockList = get_stock_list()
    rows = []
    for ticker in stockList:
        print(f"====> {len(rows)} / {len(stockList)} - Loading Ticker: {ticker}")
        se = StockEntropy(ticker)
        se.calc_entropies()
        rows.append({
            "Stock": ticker,
            "Geometric": se.get_value()
        })

    result_df = pd.DataFrame(rows)
    result_df = result_df.sort_values(by="Geometric", ascending=True).reset_index(drop=True)
    save_to_db(result_df, DB_FILE, TABLE)

    print(f"Computed and saved {len(result_df)} rows to {DB_FILE}. Lowest-entropy (Geometric) {TOP_N}:")
    print(result_df.head(TOP_N))
