from pymongo import MongoClient
from django.conf import settings

# Setup MongoDB
mongo_client = MongoClient(settings.MONGO_URI)
db = mongo_client[settings.MONGO_DB]
collection = db['user_activities']

def save_to_mongo(user_id, activity_data):
    """Simpan aktivitas user ke MongoDB"""
    collection.insert_one(activity_data)

def get_user_activities(user_id):
    """Ambil aktivitas user dari MongoDB"""
    return collection.find({"user_id": user_id})

def get_default_collection():
    return collection
