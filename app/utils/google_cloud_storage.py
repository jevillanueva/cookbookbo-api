import os
import uuid
from google.cloud import storage
from app.core.configuration import APP_GOOGLE_CLOUD_STORAGE, APP_GOOGLE_CLOUD_STORAGE_BUCKET
storage_client = storage.Client.from_service_account_json(APP_GOOGLE_CLOUD_STORAGE)
def upload_file(id, filename, content_type, binary):
    new_filename = f"{id}-{uuid.uuid4()}-{filename}"
    try:
        bucket = storage_client.get_bucket(APP_GOOGLE_CLOUD_STORAGE_BUCKET)
        blob = bucket.blob(new_filename)
        blob.upload_from_file(binary, content_type=content_type)
        return True, new_filename, blob.public_url, blob.content_type
    except Exception as e:
        print(e)
        return False, None, None, None


def delete_file(filename):
    try:
        bucket = storage_client.get_bucket(APP_GOOGLE_CLOUD_STORAGE_BUCKET)
        blob = bucket.blob(filename)
        blob.delete()
        return True
    except Exception as e:
        print(e)
        return False