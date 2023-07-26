import pickle
import os
import time
import csv
from pykrx import stock
from datetime import datetime, timedelta

def get_tickers_for_year(year):
    ticker_filename = f"tickers_{year}.pkl"
    if os.path.exists(ticker_filename):
        with open(ticker_filename, "rb") as f:
            year_tickers = pickle.load(f)
    else:
        date = f"{year}0101"
        year_tickers = stock.get_market_ticker_list(date)
        with open(ticker_filename, "wb") as f:
            pickle.dump(year_tickers, f)
        time.sleep(1)
    return year_tickers

def get_stock_prices(ticker, start_date, end_date):
    price_filename = f"{ticker}_{start_date}_{end_date}.pkl"
    if os.path.exists(price_filename):
        with open(price_filename, "rb") as f:
            df = pickle.load(f)
    else:
        df = stock.get_market_ohlcv_by_date(start_date, end_date, ticker)
        with open(price_filename, "wb") as f:
            pickle.dump(df, f)
        time.sleep(1)
    return df

# Calculate the start and end dates since 2003
end_date = datetime.now()
start_date = datetime.strptime('20030101', '%Y%m%d')

# Calculate the dates
end_year = end_date.year
start_year = start_date.year

# Create a set to store the tickers
tickers = set()

# Loop over each year and fetch the tickers
for year in range(start_year, end_year + 1):
    year_tickers = get_tickers_for_year(year)
    tickers.update(year_tickers)
    print(f"Fetch ticker of year {year} is done.")

# Save tickers to a CSV file
tickers_list = list(tickers)
with open("tickers.csv", "w") as f:
    writer = csv.writer(f)
    for ticker in tickers_list:
        writer.writerow([ticker])

# Format the dates in the required format
end_date = end_date.strftime('%Y%m%d')
start_date = start_date.strftime('%Y%m%d')

# Loop over all tickers and fetch the stock price data
for ticker in tickers:
    df = get_stock_prices(ticker, start_date, end_date)
    print(f"Fetch stock price of {ticker} is done.")
