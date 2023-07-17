from pykrx import stock

df_samsung = stock.get_market_ohlcv_by_date(
        fromdate='2020-01-01', todate='2022-01-31', ticker='005930')

print(df_samsung)
