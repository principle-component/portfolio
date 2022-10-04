import pandas as pd
import datetime
import yfinance as yf
import numpy as np

#%%

tickers = pd.read_csv('./sp500_tickers.csv')
unique_tickers = tickers['Symbol'].unique().tolist()

#%%
start = pd.to_datetime('01-01-2022').date()
end = datetime.datetime.today().date()
data = yf.download(unique_tickers, start=start, end=end, interval = "1d")

#%%

closes = data['Adj Close'].reset_index().melt(id_vars='Date').reset_index()
closes.columns = ['Index','Ticker_Date','Symbol','Adj Close']
closes['return'] = closes.groupby('Symbol').apply(lambda g: (g['Adj Close']/g['Adj Close'].shift(1)) - 1).values
closes['log_return'] = np.log(closes['return'] + 1)
#test = closes.groupby('Symbol').apply(lambda g: (g['Adj Close']/g['Adj Close'].shift(1)) - 1)
#closes.merge(tickers,how='inner',on='Symbol').reset_index()

closes.to_csv('./sp500_prices.csv')

#%%