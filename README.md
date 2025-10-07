# 🧠 Black–Litterman Portfolio Optimizer + Monte Carlo Simulation

This project implements a **complete end-to-end portfolio optimization workflow** using the **Black–Litterman model** combined with **Monte Carlo simulation** to visualize and analyze before/after results.

The system:
1. Reads your portfolio (`stocks.xlsx`)  
2. Generates an optimized allocation using the Black–Litterman model  
3. Updates your Excel sheet with whole-share targets  
4. Runs a Monte Carlo simulation to compare **risk & return** before and after optimization  
5. Visualizes the two simulations side by side

## Part 2 of Project:
1. Pulls the top fortune 500 companies through a webscrapper
2. Uses the one hour time frame for the past six months for the prices
3. Calculates the entropy with the Shannon Entropy Model
4. Saves the calculated stocks entropy to a sql database

   ## To-Do's
   Running a diagnositc on a given stock
      Determine whether the stock is moving due to a momentum(trend) or mean-reversion
   Create a strategy and backtest it

---

## 💼 Portfolio Composition (Example)
Below is an example set of tickers and their role in a diversified portfolio:

| Ticker | Company / Sector | Typical Role in Portfolio |
|--------|------------------|----------------------------|
| **AAPL** | Apple Inc. | Large-cap tech growth, strong innovation pipeline |
| **AMZN** | Amazon.com Inc. | E-commerce & cloud (AWS) diversification |
| **JPM** | JPMorgan Chase & Co. | Financial sector exposure (banking stability & dividends) |
| **KO** | Coca-Cola Co. | Consumer defensive stock for stability & yield |
| **META** | Meta Platforms Inc. | Communication services & AI expansion |
| **MSFT** | Microsoft Corp. | Cloud, AI, and productivity software leader |
| **PLTR** | Palantir Technologies | High-growth data analytics & AI sector exposure |
| **SPY** | S&P 500 ETF | Broad U.S. market exposure and diversification anchor |
| **T** | AT&T Inc. | Telecommunications income & dividend stability |
| **UPS** | United Parcel Service | Logistics & transport sector diversification |
| **XOM** | Exxon Mobil Corp. | Energy & commodities exposure for inflation hedge |

This balanced selection provides exposure across **tech, finance, consumer, industrials, energy, and telecom**, which helps control overall volatility.

---

## ⚙️ Required Packages
```
numpy
pandas
matplotlib
yfinance
openpyxl
PyPortfolioOpt
```

## 🧩 How It Works
1. Black–Litterman Optimization (optimization.py)
Uses PyPortfolioOpt to compute a market equilibrium prior.
Instead of handcrafted subjective absolute views, this repo derives absolute views programmatically from 1-year percentage returns scaled by volatility. This yields data-driven, normalized views: View_i = (1-year return_i) / volatility_i
Views are clipped (e.g., between −0.3 and 0.3) for stability.

3. Portfolio Update (updatePortfolio.py)
Converts optimized weights into whole-share allocations using current prices from Yahoo Finance.
Uses a largest-remainder style approach to spend leftover cash fairly and keep total allocated value ≈ original portfolio value.
Writes a new sheet BL_Allocation with exactly:
Tickers | Shares

5. Monte Carlo Simulation (monteCarlo.py)
Simulates thousands of correlated return paths using the covariance structure from historical returns.
Uses actual share counts (from the Excel sheet) to compute starting market-value weights and the initial portfolio value.
Returns expected final return and risk (std) and the simulated paths for visualization.

7. Visualization (main.py)
Orchestrates the workflow and shows a single figure with two side-by-side plots: Monte Carlo paths before and after optimization (normalized to start = 1).

## Real Output
```
python3 main.py
=== Running Black–Litterman Optimization ===
[*********************100%***********************]  11 of 11 completed
[*********************100%***********************]  1 of 1 completed
/Users/kece/Library/Python/3.9/lib/python/site-packages/pypfopt/efficient_frontier/efficient_frontier.py:259: UserWarning: max_sharpe transforms the optimization problem so additional objectives may not work as expected.
  warnings.warn(

Optimized Weights:
 KO      0.1501
T       0.1467
JPM     0.1217
MSFT    0.1187
SPY     0.1175
AAPL    0.1129
XOM     0.0894
PLTR    0.0873
META    0.0556
AMZN    0.0000
UPS     0.0000
dtype: float64
[*********************100%***********************]  11 of 11 completed
Targeted value: $12,913.80 | Allocated: $12,897.50 | Cash left: $16.30
✅ Wrote 'BL_Allocation' with [Tickers, Shares] to 'stocks.xlsx'.

=== Monte Carlo Simulation (Before) ===
[*********************100%***********************]  1 of 1 completed
[*********************100%***********************]  1 of 1 completed
[*********************100%***********************]  1 of 1 completed
[*********************100%***********************]  1 of 1 completed
[*********************100%***********************]  1 of 1 completed
[*********************100%***********************]  1 of 1 completed
[*********************100%***********************]  1 of 1 completed
[*********************100%***********************]  1 of 1 completed
[*********************100%***********************]  1 of 1 completed
[*********************100%***********************]  1 of 1 completed
[*********************100%***********************]  1 of 1 completed
Return: 20.93%, Risk: 31.24%

=== Monte Carlo Simulation (After) ===
[*********************100%***********************]  1 of 1 completed
[*********************100%***********************]  1 of 1 completed
[*********************100%***********************]  1 of 1 completed
[*********************100%***********************]  1 of 1 completed
[*********************100%***********************]  1 of 1 completed
[*********************100%***********************]  1 of 1 completed
[*********************100%***********************]  1 of 1 completed
[*********************100%***********************]  1 of 1 completed
[*********************100%***********************]  1 of 1 completed
[*********************100%***********************]  1 of 1 completed
[*********************100%***********************]  1 of 1 completed
Return: 37.31%, Risk: 27.05%

=== Comparison ===
Return Improvement: 16.37%
Risk Change: -4.19%
```
## Monte Carlo Simulation Results: 
![alt text](https://github.com/Kece05/Portfolio-Optimization/blob/main/Figure_1.png "Monte Carlo Simulation Results")

## 🤝 Acknowledgements
Repository developed by Keller Bice, with structural and algorithmic refinements provided by ChatGPT (OpenAI). 
Contributions from ChatGPT include:
  Refactoring your procedural script into a cleaner module/class layout
  Implementing a stable whole-share allocation (largest-remainder) to use budget efficiently
  Automating absolute-view creation using 1-year returns scaled by volatility (reduces subjectivity)
  Integrating Monte Carlo so actual share counts drive the simulations
  Creating the side-by-side visualization for before/after comparison
