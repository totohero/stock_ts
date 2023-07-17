from pymongo.server_api import ServerApi
from pymongo.mongo_client import MongoClient
import os

os.environ["MONGO_URI"] = 'mongodb+srv://totohero:86nggolxqPg2kC8G@cluster0-seoul-1st.coz7epy.mongodb.net/?retryWrites=true&w=majority'
os.environ["START_DATE"] = '2019-12-01'
os.environ["END_DATE"] = '2023-07-16'


# 86nggolxqPg2kC8G
uri = os.environ["MONGO_URI"]
# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))
# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

def get_db():
    db = client['stock_db']

    meta = db['meta']
    date_collection = db['date']

    # stock_ts가 없는 경우, 생성
    if 'stock_ts' not in db.list_collection_names():
        db.create_collection('stock_ts', timeseries={'timeField': 'date', 'metaField': 'symbol',
                                                    'granularity': 'hours'})

    stock_ts = db['stock_ts']  # 컬렉션(테이블) 선택

    return db, meta, date_collection, stock_ts