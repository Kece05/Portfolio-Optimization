import numpy as np
import pandas as pd
import yfinance as yf
from pathlib import Path

def write_bl_allocation_to_excel(excel_path, weights, holdings_sheet="Sheet1", new_sheet="BL_Allocation"):
    excel_path = Path(excel_path)

    # Read current holdings
    df = pd.read_excel(excel_path, sheet_name=holdings_sheet)
    df["Tickers"] = df["Tickers"].astype(str).str.upper()
    df = df.groupby("Tickers", as_index=False)["Shares"].sum()
    tickers = df["Tickers"].tolist()

    # Latest prices
    px = yf.download(tickers, period="5d", interval="1d", auto_adjust=True)["Close"]
    if isinstance(px, pd.Series):
        px = px.to_frame(name=tickers[0])
    prices = px.ffill().iloc[-1].reindex(tickers).astype(float)

    # Current total value (use market, not user-entered)
    total_value = float((df["Shares"].values * prices.values).sum())

    # Align weights
    w = pd.Series(weights, dtype="float64")
    w.index = w.index.str.upper()
    w = w.reindex(tickers).fillna(0.0)
    if w.sum() == 0:
        raise ValueError("All optimized weights are zero after aligning to held tickers.")
    w = w / w.sum()

    # Dollar targets and initial (floor) shares
    target_dollars = (w * total_value).reindex(tickers).values
    p = prices.values
    floor_shares = np.floor_divide(target_dollars, p).astype(int)

    # Cash leftover after flooring
    spent = (floor_shares * p).sum()
    cash_left = total_value - spent

    # Residuals: who should get the next share?
    residuals = target_dollars - floor_shares * p
    order = np.argsort(-residuals)  # largest residual first

    # Greedy top-up: buy 1 more share while we can afford it
    min_price = np.nanmin(p[np.isfinite(p) & (p > 0)])
    i = 0
    while cash_left >= min_price and i < len(order):
        j = order[i]
        if p[j] > 0 and cash_left >= p[j]:
            floor_shares[j] += 1
            cash_left -= p[j]
        else:
            i += 1  # try next ticker
            # when we reach the end, restart once to try any that became affordable
            if i == len(order) and cash_left >= min_price:
                i = 0

    # Output exactly what Monte Carlo expects
    out = pd.DataFrame({"Tickers": tickers, "Shares": floor_shares.astype(int)})

    with pd.ExcelWriter(excel_path, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
        out.to_excel(writer, sheet_name=new_sheet, index=False)

    # Optional: quick console check
    new_value = float((out["Shares"].values * prices.values).sum())
    print(f"Targeted value: ${total_value:,.2f} | Allocated: ${new_value:,.2f} | Cash left: ${total_value - new_value:,.2f}")
    print(f"✅ Wrote '{new_sheet}' with [Tickers, Shares] to '{excel_path.name}'.")


# compare_values.py
import pandas as pd
import yfinance as yf

def compare_portfolio_values(excel_path, before_sheet="Sheet1", after_sheet="BL_Allocation"):
    # Read
    before = pd.read_excel(excel_path, sheet_name=before_sheet)[["Tickers","Shares"]]
    after  = pd.read_excel(excel_path, sheet_name=after_sheet)[["Tickers","Shares"]]
    before["Tickers"] = before["Tickers"].str.upper()
    after["Tickers"]  = after["Tickers"].str.upper()

    # Universe & prices (same prices used for both)
    tickers = sorted(set(before["Tickers"]).union(after["Tickers"]))
    px = yf.download(tickers, period="5d", interval="1d", auto_adjust=True)["Close"].ffill().iloc[-1]
    px = px.reindex(tickers)

    # Map prices and compute values
    b = before.set_index("Tickers").reindex(tickers).fillna(0)
    a = after.set_index("Tickers").reindex(tickers).fillna(0)
    b["Price"] = px
    a["Price"] = px
    b["Value"] = b["Shares"] * b["Price"]
    a["Value"] = a["Shares"] * a["Price"]

    total_before = float(b["Value"].sum())
    total_after  = float(a["Value"].sum())
    delta = total_after - total_before

    # Per-ticker differences (shares & $)
    diff = pd.DataFrame({
        "Price": px,
        "Before_Shares": b["Shares"].astype(int),
        "After_Shares": a["Shares"].astype(int),
        "Delta_Shares": (a["Shares"] - b["Shares"]).astype(int),
        "Before_$": b["Value"],
        "After_$": a["Value"],
        "Delta_$": a["Value"] - b["Value"],
    })

    print(f"Total (before): ${total_before:,.2f}")
    print(f"Total (after) : ${total_after:,.2f}")
    print(f"Difference    : ${delta:,.2f}")

    return diff.sort_values("Delta_$", ascending=False)
