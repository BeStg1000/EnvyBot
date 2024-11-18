import gspread
from oauth2client.service_account import ServiceAccountCredentials

def connect_to_sheets(sheet_name):
    """เชื่อมต่อกับ Google Sheets พร้อมการจัดการข้อผิดพลาด"""
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/spreadsheets",
                 "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
        client = gspread.authorize(creds)
        return client.open(sheet_name).sheet1
    except Exception as e:
        print(f"Error connecting to Google Sheets: {e}")
        return None

def update_sheet(sheet, discord_id, roblox_id, username, display_name, custom_name):
    """อัปเดตข้อมูลใน Google Sheets พร้อมจัดการข้อผิดพลาด"""
    try:
        data = [discord_id, roblox_id, username, display_name, custom_name]
        sheet.append_row(data)
    except Exception as e:
        print(f"Error updating Google Sheets: {e}")

def update_display_name(sheet, discord_id, new_display_name):
    """อัปเดต Display Name ใน Google Sheets"""
    try:
        records = sheet.get_all_records()
        for i, record in enumerate(records, start=2):
            if record['Discord ID'] == discord_id:
                sheet.update_cell(i, 4, new_display_name)
                break
    except Exception as e:
        print(f"Error updating display name: {e}")
