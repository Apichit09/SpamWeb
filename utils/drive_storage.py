import os
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build

# เปลี่ยน SCOPES เป็นของ Spreadsheets
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

def get_sheets_service():
    service_account_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    
    if service_account_json:
        # โหลดจาก Environment (บรรทัดเดียว)
        info = json.loads(service_account_json.strip(), strict=False)
        creds = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
    else:
        # โหลดจากไฟล์ service_account.json ในเครื่อง
        current_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(current_dir, "service_account.json")
        if not os.path.exists(path):
            raise FileNotFoundError(f"ไม่พบไฟล์ Key ที่: {path}")
        creds = service_account.Credentials.from_service_account_file(path, scopes=SCOPES)
        
    return build("sheets", "v4", credentials=creds)

# แก้ไขชื่อฟังก์ชันให้เป็นชื่อเดิม (เพื่อให้ไฟล์ history.py ไม่พัง)
def upload_or_update_file(local_file_path, drive_filename):
    """
    ฟังก์ชันนี้จะถูกเรียกจาก history.py 
    เราจะเปลี่ยนจากการอัปโหลดไฟล์ เป็นการอ่านค่าล่าสุดไปลง Google Sheets แทน
    """
    import pandas as pd
    
    spreadsheet_id = os.getenv("GOOGLE_SHEET_ID")
    if not spreadsheet_id:
        print("กรุณาระบุ GOOGLE_SHEET_ID ใน .env")
        return None

    try:
        # อ่านไฟล์ CSV ที่เพิ่งบันทึกลงเครื่องมาดูแถวล่าสุด
        df = pd.read_csv(local_file_path)
        if df.empty:
            return None
            
        # เอาข้อมูลแถวสุดท้าย (Latest Prediction) แปลงเป็น List
        last_row = df.iloc[-1].tolist()
        
        # ส่งไปบันทึกลง Google Sheets
        service = get_sheets_service()
        range_name = "Sheet1!A1" 
        body = {'values': [last_row]}
        
        result = service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body=body
        ).execute()
        
        print(f"บันทึกลง Google Sheets เรียบร้อย (Row Added)")
        return result
    except Exception as e:
        print(f"Google Sheets Error: {e}")
        raise