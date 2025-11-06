import pymongo.errors
from pymongo import MongoClient


try:
    client = MongoClient("mongodb://localhost:27017/")
    db = client.umay_db
    collection = db.user_collection
except pymongo.errors.ConnectionFailure:
    print("MongoDB sunucusuna bağlanılamadı")

def get_user(username):
    if (user := collection.find_one({"username": username})):
        return user
    return None


def add_user(username, full_name, hashed_password, is_admin=False):
    collection.insert_one({
        "username": username,
        "full_name": full_name,
        "hashed_password": hashed_password,
        "is_admin": is_admin
    })



