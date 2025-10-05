import datetime as dt
import numpy as np
import pandas as pd
import yfinance as yf

from pypfopt import risk_models, black_litterman, objective_functions
from pypfopt.black_litterman import BlackLittermanModel
from pypfopt import EfficientFrontier

class initialization:
    def __init__(self, stockList, sheet):
        self.df = pd.read_excel(stockList, sheet_name=sheet)
        self.stockList = self.df["Tickers"].dropna().astype(str).str.upper().to_list()

        self.end_date = dt.datetime.today()
        self.start_date = self.end_date - dt.timedelta(days=252)
        self.portfolio = None
        self.mcaps = None

    @staticmethod
    def _get_market_cap(ticker: str) -> float:
        try:
            tk = yf.Ticker(ticker)
            fi = getattr(tk, "fast_info", None)
            if isinstance(fi, dict):
                mc = fi.get("market_cap", None)
            else:
                mc = None
            if mc is None:
                mc = (tk.info or {}).get("marketCap", None)
            return float(mc) if mc else 0.0
        except Exception:
            return 0.0

    def get_data(self):
        self.portfolio = yf.download(
            self.stockList, start=self.start_date, end=self.end_date, auto_adjust=True
        )["Close"].dropna(how="all")

        self.mcaps = {t: self._get_market_cap(t) for t in self.portfolio.columns}
        self.mcaps = {k: v for k, v in self.mcaps.items() if v and v > 0}

    def getValues(self):
        return self.portfolio, self.mcaps


class Priors:
    def __init__(self, portfolio: pd.DataFrame, mcaps: dict, benchmark: str = "SPY"):
        self.portfolio = portfolio
        self.mcaps = mcaps
        self.benchmark = benchmark
        self.S = None
        self.delta = None
        self.market_prior = None

    def compute(self):
        self.S = risk_models.CovarianceShrinkage(self.portfolio).ledoit_wolf()
        end_date = dt.datetime.today()
        start_date = end_date - dt.timedelta(days=252)
        market_benchmark = yf.download(
            self.benchmark, start=start_date, end=end_date, auto_adjust=True
        )["Close"].dropna()
        self.delta = black_litterman.market_implied_risk_aversion(market_prices=market_benchmark)
        self.market_prior = black_litterman.market_implied_prior_returns(self.mcaps, self.delta, self.S)
        return self.S, self.delta, self.market_prior


class ViewsAndConfidence:
    def __init__(self, portfolio: pd.DataFrame, S: pd.DataFrame):
        self.portfolio = portfolio
        self.S = S
        self.h = None
        self.absolute_views = None
        self.omega_df = None

    def compute(self):
        self.h = int(min(252, len(self.portfolio) - 1))
        returns_1y = (
            self.portfolio.iloc[-1] / self.portfolio.iloc[-1 - self.h] - 1
        ).clip(lower=-0.5, upper=0.5)
        vols = self.portfolio.pct_change().std() * np.sqrt(252)
        vols = vols.replace(0, np.nan)
        views = (returns_1y / vols).replace([np.inf, -np.inf], np.nan).dropna()
        views = views.clip(lower=-0.3, upper=0.3)
        self.absolute_views = views.to_dict()

        view_names = list(self.absolute_views.keys())
        vol_views = vols[view_names]
        stderr = vol_views / np.sqrt(self.h)
        omega = np.diag((stderr ** 2).values)
        self.omega_df = pd.DataFrame(omega, index=view_names, columns=view_names)
        return self.absolute_views, self.omega_df


class BLOptimizer:
    def __init__(self, S, market_prior, mcaps, delta, absolute_views, omega_df):
        self.S = S
        self.market_prior = market_prior
        self.mcaps = mcaps
        self.delta = delta
        self.absolute_views = absolute_views
        self.omega_df = omega_df
        self.weights_series = None
        self.bl = None

    def run(self, rf: float = 0.02):
        self.bl = BlackLittermanModel(
            cov_matrix=self.S,
            pi=self.market_prior,
            market_caps=self.mcaps,
            risk_aversion=self.delta,
            omega=self.omega_df,
            absolute_views=self.absolute_views
        )
        ef = EfficientFrontier(self.bl.bl_returns(), self.bl.bl_cov())
        ef.add_objective(objective_functions.L2_reg)
        ef.max_sharpe(risk_free_rate=rf)
        weights = ef.clean_weights()
        self.weights_series = pd.Series(weights).sort_values(ascending=False)
        return self.weights_series

class BLWorkflow:
    def __init__(self, excel_path: str, sheet: str = "Sheet1"):
        self.excel_path = excel_path
        self.sheet = sheet
        self.portfolio = None
        self.mcaps = None
        self.S = None
        self.delta = None
        self.market_prior = None
        self.absolute_views = None
        self.omega_df = None
        self.weights_series = None
        self.bl_model = None

    def run(self):
        init = initialization(self.excel_path, self.sheet)
        init.get_data()
        self.portfolio, self.mcaps = init.getValues()

        pri = Priors(self.portfolio, self.mcaps)
        self.S, self.delta, self.market_prior = pri.compute()

        vc = ViewsAndConfidence(self.portfolio, self.S)
        self.absolute_views, self.omega_df = vc.compute()

        opt = BLOptimizer(
            S=self.S,
            market_prior=self.market_prior,
            mcaps=self.mcaps,
            delta=self.delta,
            absolute_views=self.absolute_views,
            omega_df=self.omega_df
        )
        self.weights_series = opt.run(rf=0.02)
        self.bl_model = opt.bl

        return {
            "portfolio": self.portfolio,
            "mcaps": self.mcaps,
            "S": self.S,
            "delta": self.delta,
            "market_prior": self.market_prior,
            "absolute_views": self.absolute_views,
            "omega_df": self.omega_df,
            "weights_series": self.weights_series,
            "bl_model": self.bl_model
        }


if __name__ == "__main__":
    wf = BLWorkflow("stocks.xlsx", sheet="Sheet1")
    outputs = wf.run()
    print("\nOptimized Weights:\n", outputs["weights_series"].round(4))
