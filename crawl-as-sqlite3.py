import pickle
import os
import time
from pykrx import stock
from datetime import datetime
import sqlite3

def get_tickers_for_year(year):
    ticker_filename = f"cache/tickers_{year}.pkl"
    if os.path.exists(ticker_filename):
        with open(ticker_filename, "rb") as f:
            year_tickers = pickle.load(f)
    else:
        date = f"{year}0101"
        year_tickers = stock.get_market_ticker_list(date)
        os.makedirs(os.path.dirname(ticker_filename), exist_ok=True)
        with open(ticker_filename, "wb") as f:
            pickle.dump(year_tickers, f)
        time.sleep(1)
    return year_tickers

def get_stock_prices(ticker, start_date, end_date):
    price_filename = f"cache/{ticker}_{start_date}_{end_date}.pkl"
    if os.path.exists(price_filename):
        with open(price_filename, "rb") as f:
            df = pickle.load(f)        
        print(f"Fetch from cached stock price of {ticker} is done. Number of rows fetched: {len(df)}")
    else:
        df = stock.get_market_ohlcv_by_date(start_date, end_date, ticker)
        os.makedirs(os.path.dirname(price_filename), exist_ok=True)
        with open(price_filename, "wb") as f:
            pickle.dump(df, f)
        print(f"Fetch from pykrx stock price of {ticker} is done. Number of rows fetched: {len(df)}")
        time.sleep(1)
    return df

# Calculate the start and end dates since 2003
start_date = datetime.strptime('20030101', '%Y%m%d')
# end_date = datetime.now()
end_date = datetime.strptime('20230727', '%Y%m%d')

# Calculate the dates
start_year = start_date.year
end_year = end_date.year

# Create a set to store the tickers
tickers = set()

# Loop over each year and fetch the tickers
for year in range(start_year, end_year + 1):
    year_tickers = get_tickers_for_year(year)
    tickers.update(year_tickers)
    print(f"Fetch ticker of year {year} is done.")

tickers_list = sorted(list(tickers))

# Format the dates in the required format
end_date = end_date.strftime('%Y%m%d')
start_date = start_date.strftime('%Y%m%d')

# ...
# Connect to the SQLite database
conn = sqlite3.connect('stock_prices.db')
conn2023 = sqlite3.connect('stock_prices-2023.db')
conn.execute("DROP TABLE IF EXISTS prices;")
conn2023.execute("DROP TABLE IF EXISTS prices;")

# Loop over all tickers and fetch the stock price data
for ticker in tickers_list:
    df = get_stock_prices(ticker, start_date, end_date).rename(
        columns={'날짜': 'date', '시가': 'open', '고가': 'high', '저가': 'low', '종가': 'close', '거래량': 'volume',
                 '거래대금': 'transaction_amount',
                 '등락률': 'fluctuation_rate'})
    df.index.name = 'date'  # Set the index name
    df['ticker'] = ticker  # Add a column for the ticker
    
    if not df.empty:
        df.to_sql('prices', conn, if_exists='append')

    df2023 = df[df.index.astype(str) >= '20230101']
    if not df2023.empty:
        df2023.to_sql('prices', conn2023, if_exists='append')


# Close the connection
conn.close()
conn2023.close()