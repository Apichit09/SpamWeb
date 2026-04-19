import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SERVICE_ACCOUNT_FILE = os.path.join(BASE_DIR, "service_account.json")
SCOPES = ["https://www.googleapis.com/auth/drive.file"]

# ใส่ Folder ID ของ Google Drive
DRIVE_FOLDER_ID = "PUT_YOUR_FOLDER_ID_HERE"


def get_drive_service():
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=SCOPES
    )
    service = build("drive", "v3", credentials=credentials)
    return service


def find_file_in_folder(service, filename, folder_id):
    query = (
        f"name = '{filename}' and "
        f"'{folder_id}' in parents and "
        f"trashed = false"
    )
    results = service.files().list(
        q=query,
        fields="files(id, name)"
    ).execute()

    files = results.get("files", [])
    return files[0] if files else None


def upload_or_update_file(local_file_path, drive_filename):
    service = get_drive_service()

    existing_file = find_file_in_folder(service, drive_filename, DRIVE_FOLDER_ID)
    media = MediaFileUpload(local_file_path, mimetype="text/csv", resumable=True)

    if existing_file:
        updated = service.files().update(
            fileId=existing_file["id"],
            media_body=media
        ).execute()
        return updated
    else:
        file_metadata = {
            "name": drive_filename,
            "parents": [DRIVE_FOLDER_ID]
        }
        created = service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id, name"
        ).execute()
        return created