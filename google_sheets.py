import json
import os
import logging
import gspread
from google.oauth2.service_account import Credentials

# ตั้งค่าระดับของ logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# กำหนดตำแหน่งของ Secret File
GOOGLE_CREDENTIALS_PATH = os.getenv("GOOGLE_SHEETS_CREDENTIALS", "/etc/secrets/GOOGLE_SHEETS_CREDENTIALS")

# ตรวจสอบและโหลด Google Sheets Credentials จาก Secret File
if not os.path.exists(GOOGLE_CREDENTIALS_PATH):
    raise FileNotFoundError(f"Google credentials file not found at {GOOGLE_CREDENTIALS_PATH}")

try:
    with open(GOOGLE_CREDENTIALS_PATH, "r") as file:
        credentials_info = json.load(file)
        logging.info("Loaded Google Sheets credentials from secret file successfully.")
except json.JSONDecodeError as e:
    raise ValueError(f"Invalid JSON format in the credentials file: {e}")

# โหลด Credential
credentials = Credentials.from_service_account_info(
    credentials_info,
    scopes=["https://www.googleapis.com/auth/spreadsheets"]
)

def connect_to_sheets(sheet_name):
    """เชื่อมต่อกับ Google Sheets โดยใช้ Secret File"""
    try:
        client = gspread.authorize(credentials)
        sheet = client.open(sheet_name).sheet1
        logging.info(f"Successfully connected to the Google Sheet: {sheet_name}")
        return sheet
    except Exception as e:
        logging.error(f"Error connecting to Google Sheets: {e}")
        raise

def update_sheet(sheet, discord_id, roblox_id, username, display_name, custom_name):
    """อัปเดตข้อมูลใน Google Sheets พร้อมจัดการข้อผิดพลาด"""
    try:
        data = [discord_id, roblox_id, username, display_name, custom_name]
        sheet.append_row(data)
        logging.info(f"Successfully updated sheet with data: {data}")
    except Exception as e:
        logging.error(f"Error updating Google Sheets: {e}")

def update_display_name(sheet, discord_id, new_display_name):
    """อัปเดต Display Name ใน Google Sheets"""
    try:
        records = sheet.get_all_records()
        if not records:
            logging.warning("Google Sheet is empty. Please add the required columns.")
            return

        for i, record in enumerate(records, start=2):
            if record.get('Discord ID') == discord_id:
                sheet.update_cell(i, 4, new_display_name)
                logging.info(f"Updated display name for Discord ID {discord_id} to {new_display_name}")
                break
        else:
            logging.warning(f"Discord ID {discord_id} not found in the sheet.")
    except Exception as e:
        logging.error(f"Error updating display name: {e}")
