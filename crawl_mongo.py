from datetime import timedelta
from datetime import datetime
import pandas as pd
import time
from pykrx import stock
import os

import mydb


# db 및 collection 모음
db, meta, date_collection, stock_ts = mydb.get_db()

# 자료 수집 시작일
global_begin_date = datetime.strptime(os.environ['START_DATE'], '%Y-%m-%d')

# 자료 수집 종료일
try:
    global_end_date = datetime.strptime(os.environ['END_DATE'], '%Y-%m-%d')
except (TypeError, KeyError):
    global_end_date = datetime.today()

# 일자별 자료 수집 여부 확인
try:
    ticker_synced_dates = meta.find_one(
        {'name': 'ticker_synced_dates'})['dates']
except (TypeError, KeyError):
    ticker_synced_dates = []

# 자료 수집 안된 날에 한해 해당일의 모든 ticker list 수집
dt = pd.date_range(start=global_begin_date, end=global_end_date, freq='B')
for d in dt:
    curr_date = d.date()
    curr_datetime = datetime(
        year=curr_date.year, month=curr_date.month, day=curr_date.day)

    if curr_datetime in ticker_synced_dates:
        print("Skipping " + curr_date.strftime('%Y-%m-%d'))
    else:
        print("Fetching tickers on " + curr_date.strftime('%Y-%m-%d'))
        tickers = stock.get_market_ticker_list(date=curr_date, market="ALL")
        date_collection.update_one({'date': curr_datetime}, {
                                   '$set': {'tickers': tickers}}, upsert=True)
        meta.update_one({'name': 'ticker_synced_dates'}, {
                        '$push': {'dates': curr_datetime}}, upsert=True)

        # meta ticker_set은 날짜와 무관하게 존재했던 모든 ticker들의 집합
        meta.update_one({'name': 'ticker_set'}, {'$addToSet': {
                        'tickers': {'$each': tickers}}}, upsert=True)
        time.sleep(0.1)
print("Done")


def missing_dates(prev_begin: datetime, prev_end: datetime, curr_begin: datetime, curr_end: datetime) -> list[datetime]:
    '''
    This is test:
    >>> from datetime import datetime
    >>> prev_begin = datetime(2020, 1, 1)
    >>> prev_end = datetime(2020, 1, 10)
    >>> curr_begin = datetime(2020, 1, 5)
    >>> curr_end = datetime(2020, 1, 15)
    >>> missing_dates(prev_begin, prev_end, curr_begin, curr_end)
    [(datetime.datetime(2020, 1, 11, 0, 0), datetime.datetime(2020, 1, 15, 0, 0))]
    >>> prev_begin = datetime(2020, 1, 10)
    >>> prev_end = datetime(2020, 1, 15)
    >>> curr_begin = datetime(2020, 1, 1)
    >>> curr_end = datetime(2020, 1, 20)
    >>> missing_dates(prev_begin, prev_end, curr_begin, curr_end)
    [(datetime.datetime(2020, 1, 5, 0, 0), datetime.datetime(2020, 1, 10, 0, 0)), (datetime.datetime(2020, 1, 16, 0, 0), datetime.datetime(2020, 1, 20, 0, 0))]
    >>> prev_begin = datetime(2020, 1, 1)
    >>> prev_end = datetime(2020, 1, 10)
    >>> curr_begin = datetime(2020, 1, 1)
    >>> curr_end = datetime(2020, 1, 10)
    >>> missing_dates(prev_begin, prev_end, curr_begin, curr_end)
    []
    '''
    if prev_end < curr_begin or curr_end < prev_begin:
        return [(curr_begin, curr_end)]
    missing = []
    if curr_begin < prev_begin:
        missing.append((curr_begin, prev_begin-timedelta(days=1)))
    if prev_end < curr_end:
        missing.append((prev_end+timedelta(days=1), curr_end))
    return missing


# 역사상 존재했던 모든 ticker들의 집합
tickers = meta.find_one({'name': 'ticker_set'})['tickers']

# sort tickers
tickers = sorted(tickers)

# ticker별로 sync된 날짜들의 map
try:
    symbol_dates = meta.find_one({'name': 'ohlcv_synced_dates'})[
        'symbol_dates']
except (TypeError, KeyError):
    symbol_dates = []

def crawl_stock_by_date(ticker, begin_date, end_date):
    df = stock.get_market_ohlcv_by_date(
        fromdate=begin_date, todate=end_date, ticker=ticker)
    df = df.reset_index()
    df = df.rename(
        columns={'날짜': 'date', '시가': 'open', '고가': 'high', '저가': 'low', '종가': 'close', '거래량': 'volume',
                 '거래대금': 'amount',
                 '등락률': 'change'})
    df['symbol'] = ticker

    cap = stock.get_market_cap_by_date(
        fromdate=begin_date, todate=end_date, ticker=ticker)
    cap = cap.reset_index()
    cap = cap.rename(columns={'날짜': 'date', '거래량': 'volume',
                              '거래대금': 'amount',
                              '시가총액': 'cap',
                              '상장주식수': 'shares'})

    df = pd.merge(df, cap)
    records = df.to_dict(orient='records')
    if records:
        stock_ts.insert_many(records)
    time.sleep(0.1)


tickers_len = len(tickers)


def crawl_stock(begin_date: datetime, end_date: datetime):
    print("Crawl from " + begin_date.strftime('%Y-%m-%d') +
          " to " + end_date.strftime('%Y-%m-%d'))
    for ind, ticker in enumerate(tickers):
        # if ticker != '005930':
        #    continue
        print(" (" + str(ind) + "/" + str(tickers_len) + ") " + ticker)
        try:
            prev_sync = [
                sd for sd in symbol_dates if sd['ticker'] == ticker][0]
            prev_sync_msg = "previously synced from " + \
                prev_sync['begin'].strftime(
                    '%Y-%m-%d') + " to " + prev_sync['end'].strftime('%Y-%m-%d')
            missing = missing_dates(
                prev_sync['begin'], prev_sync['end'], begin_date, end_date)
            print(missing)
        except:
            prev_sync_msg = "no previous sync"
            missing = [(begin_date, end_date)]
        for (b, e) in missing:
            print(" Fetching OHLCV " +
                  b.strftime('%Y-%m-%d') + " ~ " + e.strftime('%Y-%m-%d'))
            crawl_stock_by_date(ticker, b, e)

        update_sync_status(begin_date, end_date, ticker)
    print("Done")

def update_sync_status(begin_date, end_date, ticker):
    exist = meta.count_documents(
            {'name': 'ohlcv_synced_dates', 'symbol_dates.ticker': ticker})
    if exist:
        meta.update_one({'name': 'ohlcv_synced_dates', 'symbol_dates.ticker': ticker},
                            {'$set': {
                                'symbol_dates.$.begin': begin_date,
                                'symbol_dates.$.end': end_date
                            }}, upsert=True)
    else:
        meta.update_one({'name': 'ohlcv_synced_dates'}, {
                            '$push': {'symbol_dates': {
                                'ticker': ticker,
                                'begin': begin_date,
                                'end': end_date
                            }}}, upsert=True)


# 일단 시작일, 종료일 기준 모두 수집
crawl_stock(global_begin_date, global_end_date)

# draw bar chart for each symbol which represents if OHLCV data for each date has been collected
