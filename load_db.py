import requests
from io import BytesIO
import pandas as pd
import streamlit as st

db_paths = [ 'KOSPI_stock_prices.feather', 'KOSDAQ_stock_prices.feather']

@st.cache_data
def load_data(remote=False):
    all_df = pd.DataFrame()
    for db_path in db_paths:
        if remote:
            # S3의 공개 URL
            url = f'https://stock-ts-bucket.s3.amazonaws.com/{db_path}'

            # 요청을 통해 파일 다운로드
            response = requests.get(url)
            feather_file = BytesIO(response.content)

            # Feather 파일을 pandas DataFrame으로 로드
            df = pd.read_feather(feather_file)
        else:
            df = pd.read_feather(db_path)
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)

        all_df = pd.concat([all_df, df])

    return all_df

if __name__ == '__main__':
    all_df = load_data()
    st.write(all_df.head(10))

