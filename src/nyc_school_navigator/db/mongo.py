from pymongo import MongoClient

from nyc_school_navigator.config import settings


client = MongoClient(settings.mongodb_uri)

db = client["nyc_school_navigator"]

SCHOOL_COLLECTION = "school_sections"


def get_school_collection():
    """Return the one collection used for school retrieval documents."""
    return db[SCHOOL_COLLECTION]
