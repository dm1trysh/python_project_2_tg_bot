def insert_new_objects(current_collection, new_event):   # insert in current collection new object(as a dictionary)
    current_collection.insert_one(new_event)


def redact_event(current_collection, key_event, new_event):  # changing event in DB (event's type is dictionary)
    current_event_existed = find_event(current_collection, key_event)
    if not current_event_existed:
        return False
    current_collection.update_one({'event': key_event}, {'$set': new_event})
    return True


def find_event(current_collection, key_event):   # checking whether event exists or not
    found_obj = current_collection.find_one({'event': key_event})
    return not(found_obj is None)    # exists - True; doesn't exist - False


def delete_event(current_collection, key_event):  # delete event from DB
    try:
        current_collection.delete_one({'event': key_event})
    except:
        return     # if event doesn't exist, return


def get_all_objects(current_collection):  # return all objects(objects' type - dict) from current collection
    return current_collection.find()


def delete_user(current_collection, key_name):   # delete user from collection
    try:
        current_collection.delete_one({'name': key_name})
    except:
        return