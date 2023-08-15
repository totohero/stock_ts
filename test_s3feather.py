import requests
import pandas as pd
from io import BytesIO
import sqlite3
import pyarrow.feather as feather

def convert_sqlite3_to_feather(market):
    # SQLite 데이터베이스 연결
    sqlite_file_path = f"{market}_stock_prices.db"
    conn = sqlite3.connect(sqlite_file_path)

    # SQL 쿼리로 데이터 읽기 (여기서는 'prices'라는 테이블을 읽는 것으로 가정)
    df = pd.read_sql('SELECT * FROM prices', conn)

    # 연결 닫기
    conn.close()

    # DataFrame을 Feather 형식으로 저장
    feather_file_path = f"{market}_stock_prices.feather"
    df.to_feather(feather_file_path)

    print(f"{feather_file_path}로 저장 완료")

def load_feather():
    # S3의 공개 URL
    url = 'https://stock-ts-bucket.s3.amazonaws.com/KOSDAQ_stock_prices.feather'

    # 요청을 통해 파일 다운로드
    response = requests.get(url)
    feather_file = BytesIO(response.content)

    # Feather 파일을 pandas DataFrame으로 로드
    df = feather.read_feather(feather_file)

    # (선택적) DataFrame 출력
    print(df.head())

if __name__ == '__main__':
    # convert_sqlite3_to_feather('KOSDAQ')
    # convert_sqlite3_to_feather('KOSPI')
    load_feather()
