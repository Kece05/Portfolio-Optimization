import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import datetime as dt
import yfinance as yf

class initialization:
    def __init__(self, stockList, sheet):
        self.df = pd.read_excel(stockList, sheet_name=sheet)
        self.stockList = self.df["Tickers"].dropna().to_list()

        if "Shares" in self.df.columns:
            self.shares = (self.df.set_index("Tickers")
                               .reindex(self.stockList)["Shares"]
                               .fillna(1.0)
                               .astype(float))
        else:
            self.shares = pd.Series(1.0, index=self.stockList)

        self.end_date = dt.datetime.today()
        self.start_date = self.end_date - dt.timedelta(days=252)
    
    def get_data(self):
        self.data = pd.DataFrame()
        for ticker in self.stockList:
            self.data[ticker] = yf.download(
                ticker, start=self.start_date, end=self.end_date, auto_adjust=True
            )["Close"]

        self.returns = self.data.pct_change().dropna()
        self.meanR = self.returns.mean()
        self.cov_matrix = self.returns.cov()

        latest_prices = self.data.iloc[-1]
        market_values = latest_prices.reindex(self.stockList) * self.shares.reindex(self.stockList)
        self.weights = (market_values / market_values.sum()).values 
        self.initial_value = float(market_values.sum())

    def getValues(self):
        return self.meanR, self.cov_matrix, self.weights, self.initial_value


class monte_carlo:
    def __init__(self, mean, cov, weights, initial_value):
        self.meanReturn = mean.values       # ensure numpy
        self.covMatrix = cov.values
        self.weights = np.asarray(weights, dtype=float)
        self.initial_port = float(initial_value)

    def initializeEnv(self, num_sim, num_days): 
        self.mc_sims = num_sim
        self.days = num_days

    def createSim(self):
        n = len(self.weights)
        L = np.linalg.cholesky(self.covMatrix)
        self.sim_matrix = np.empty((self.days, self.mc_sims))

        mu = self.meanReturn.reshape(-1, 1)

        for sim in range(self.mc_sims):
            Z = np.random.normal(size=(n, self.days))
            dailyR = mu + L @ Z
            port_daily = self.weights @ dailyR
            self.sim_matrix[:, sim] = np.cumprod(1.0 + port_daily) * self.initial_port
    
    def graphResult(self):
        plt.plot(self.sim_matrix)
        plt.ylabel("Portfolio Value $")
        plt.xlabel("Number of Days")
        plt.title("Monte Carlo Simulation of Stock Portfolio")
        plt.show()


if __name__ == "__main__":
    initilizing = initialization("stocks.xlsx", "Sheet1")
    initilizing.get_data()
    mean, cov, weights, initial_value = initilizing.getValues()

    simulation = monte_carlo(mean, cov, weights, initial_value)
    simulation.initializeEnv(100, 100)
    simulation.createSim()
    simulation.graphResult()