import pymongo.errors
from pymongo import MongoClient
import logging

logger = logging.getLogger(__name__)

# MongoDB bağlantısı - global değişkenler
client = None
db = None
collection = None

try:
    client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=5000)
    db = client.umay_db
    collection = db.user_collection
    # Bağlantıyı test et
    client.admin.command('ping')
    logger.info("MongoDB bağlantısı başarılı")
except pymongo.errors.ConnectionFailure as e:
    logger.error(f"MongoDB sunucusuna bağlanılamadı: {e}")
except Exception as e:
    logger.error(f"MongoDB bağlantı hatası: {e}")

def get_user(username):
    """Kullanıcıyı veritabanından alır"""
    try:
        if collection is None:
            logger.error("MongoDB collection bağlantısı yok")
            return None
        if (user := collection.find_one({"username": username})):
            return user
        return None
    except Exception as e:
        logger.error(f"get_user hatası: {e}")
        return None


def add_user(username, full_name, hashed_password, is_admin=False):
    """Yeni kullanıcı ekler"""
    try:
        if collection is None:
            logger.error("MongoDB collection bağlantısı yok")
            raise Exception("MongoDB bağlantısı yok")
        collection.insert_one({
            "username": username,
            "full_name": full_name,
            "hashed_password": hashed_password,
            "is_admin": is_admin
        })
        logger.info(f"Kullanıcı eklendi: {username}")
    except Exception as e:
        logger.error(f"add_user hatası: {e}")
        raise



