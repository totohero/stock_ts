from pymongo.server_api import ServerApi
from pymongo.mongo_client import MongoClient
import os

os.environ["MONGO_URI"] = 'mongodb+srv://totohero:86nggolxqPg2kC8G@cluster0-seoul-1st.coz7epy.mongodb.net/?retryWrites=true&w=majority'


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

    return db, meta, date_collection