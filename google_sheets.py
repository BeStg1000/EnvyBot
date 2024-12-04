import os
import discord
from discord.ext import commands
from google.oauth2 import service_account
from googleapiclient.discovery import build

# ตั้งค่าการใช้งาน Discord
intents = discord.Intents.default()
bot = commands.Bot(command_prefix='!', intents=intents)

# ตั้งค่า Google Sheets API
SERVICE_ACCOUNT_FILE = 'path/to/your/service_account.json'  # เปลี่ยนเป็น path ที่ถูกต้อง
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)

# สร้างตัวเชื่อมต่อกับ Google Sheets API
service = build('sheets', 'v4', credentials=credentials)
spreadsheet_id = 'your_spreadsheet_id'  # เปลี่ยนเป็น ID ของ Google Sheets ของคุณ

@bot.command()
async def update_sheet(ctx, data):
    """Update Google Sheets with data from Discord."""
    values = [
        [data]  # ข้อมูลที่จะเขียนลง Google Sheets
    ]
    body = {
        'values': values
    }
    service.spreadsheets().values().append(
        spreadsheetId=spreadsheet_id,
        range='Sheet1!A1',  # เปลี่ยนเป็นช่วงที่ต้องการเขียน
        valueInputOption='RAW',
        body=body
    ).execute()
    
    await ctx.send('Updated the sheet!')

# เริ่มบอท
bot.run(os.getenv('TOKEN'))
