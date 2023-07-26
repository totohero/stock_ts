from pykrx import stock
from datetime import datetime, timedelta
import time

# Calculate the start and end dates for the last 3 years
end_date = datetime.now()
start_date = datetime.strptime('20030101', '%Y%m%d')

# Calculate the dates for the last 3 years
end_year = end_date.year
start_year = start_date.year

# Create a set to store the tickers
tickers = set()

# Loop over each year and fetch the tickers
for year in range(start_year, end_year + 1):
    date = f"{year}0101"
    year_tickers = stock.get_market_ticker_list(date)
    tickers.update(year_tickers)
    print(f"fetch ticker of year {year} is done.")
    time.sleep(1)

from pykrx import stock
from datetime import datetime, timedelta

# Format the dates in the required format
end_date = end_date.strftime('%Y%m%d')
start_date = start_date.strftime('%Y%m%d')

# Create a dictionary to store the stock prices
stock_prices = {}

# Loop over all tickers and fetch the stock price data
for ticker in tickers:
    df = stock.get_market_ohlcv_by_date(start_date, end_date, ticker)
    # Save the DataFrame to a CSV file
    df.to_csv(f"{ticker}.csv")
    stock_prices[ticker] = df
    print(f"fetch stock price of {ticker} is done.")
    time.sleep(1)

