import os
import csv
from datetime import datetime
from utils.drive_storage import upload_or_update_file

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

HISTORY_FILE = os.path.join(DATA_DIR, "prediction_history.csv")


def init_history_file():
    if not os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["message_text", "predicted_label", "confidence_score", "created_at"])


def save_history(message_text: str, predicted_label: str, confidence_score: float):
    init_history_file()

    with open(HISTORY_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            message_text,
            predicted_label,
            confidence_score,
            datetime.now().strftime("%d/%m/%Y %H:%M")
        ])

    print("SAVE LOCAL OK:", HISTORY_FILE)

    try:
        upload_or_update_file(HISTORY_FILE, "prediction_history.csv")
    except Exception as e:
        print("SHEETS UPDATE ERROR:", repr(e))


def load_history():
    init_history_file()
    rows = []

    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            normalized_row = {
                "message_text": row.get("message_text", row.get("message", "")),
                "predicted_label": row.get("predicted_label", row.get("prediction", "")),
                "confidence_score": row.get("confidence_score", row.get("confidence", "")),
                "created_at": row.get("created_at", "")
            }
            rows.append(normalized_row)

    rows.reverse()
    return rows