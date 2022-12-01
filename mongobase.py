from imports import *

db_client = pymongo.MongoClient("mongodb://localhost:27017")
current_db = db_client["calendar_bot_db"]
collection = current_db["calendar_events"]
collection_current_user = current_db["current_users"]


def insert_new_objects(current_collection, new_event):
    current_collection.insert_one(new_event)


def redact_event(current_collection, key_event, new_event):
    current_event_existed = find_event(current_collection, key_event)
    if not current_event_existed:
        return False
    current_collection.update_one({'event': key_event}, {'$set': new_event})
    return True


def find_event(current_collection, key_event):
    found_obj = current_collection.find_one({'event': key_event})
    return not(found_obj is None)


def delete_event(current_collection, key_event):
    try:
        current_collection.delete_one({'event': key_event})
    except:
        return


def get_all_objects(current_collection):
    return current_collection.find()

def delete_user(current_collection, key_name):
    try:
        current_collection.delete_one({'name': key_name})
    except:
        return