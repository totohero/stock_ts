from pykrx import stock

df_samsung = stock.get_market_ohlcv_by_date(
        fromdate='2023-07-01', todate='2023-07-16', ticker='003000')

print(df_samsung)
