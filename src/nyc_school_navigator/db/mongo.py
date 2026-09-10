from pymongo import MongoClient

from nyc_school_navigator.config import settings


client = MongoClient(settings.mongodb_uri)

db = client["nyc_school_navigator"]