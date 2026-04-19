import os
import csv
from datetime import datetime
# เรียกชื่อเดิมได้เลย เพราะเราเตรียมไว้ให้ใน drive_storage.py แล้ว
from utils.drive_storage import upload_or_update_file

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

HISTORY_FILE = os.path.join(DATA_DIR, "prediction_history.csv")

def init_history_file():
    if not os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            # หัวตาราง (จะไปปรากฏใน Google Sheets ด้วยถ้าเป็นการบันทึกครั้งแรก)
            writer.writerow(["message_text", "predicted_label", "confidence_score", "created_at"])

def save_history(message_text: str, predicted_label: str, confidence_score: float):
    init_history_file()

    # 1. บันทึกลงเครื่อง (Local CSV) ก่อน
    with open(HISTORY_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            message_text,
            predicted_label,
            confidence_score,
            datetime.now().strftime("%d/%m/%Y %H:%M")
        ])

    print("SAVE LOCAL OK:", HISTORY_FILE)

    # 2. ส่งข้อมูลแถวที่เพิ่งบันทึกไปที่ Google Sheets
    try:
        # ส่งไฟล์ path ไป เพื่อให้ drive_storage.py ไปดึงแถวล่าสุดออกมา
        upload_or_update_file(HISTORY_FILE, "prediction_history.csv")
    except Exception as e:
        print("SHEETS UPDATE ERROR:", repr(e))

def load_history():
    init_history_file()
    rows = []
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    rows.reverse()
    return rows