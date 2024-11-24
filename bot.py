import discord
from discord.ext import commands, tasks
from discord import app_commands

from myserver import server_on
from dotenv import load_dotenv
import logging
import os
import json
from google_sheets import connect_to_sheets, update_sheet, update_display_name
from utils import validate_roblox_url, fetch_roblox_data

raw_credentials = os.getenv("GOOGLE_SHEETS_CREDENTIALS")
if raw_credentials is None:
    raise EnvironmentError("GOOGLE_SHEETS_CREDENTIALS environment variable is not set")
try:
    credentials_info = json.loads(raw_credentials)
except json.JSONDecodeError as e:
    raise ValueError(f"Invalid JSON format in GOOGLE_SHEETS_CREDENTIALS: {e}")

credentials = os.getenv("GOOGLE_SHEETS_CREDENTIALS")
if not credentials:
    raise ValueError("Environment variable 'GOOGLE_SHEETS_CREDENTIALS' is not set.")
try:
    credentials_info = json.loads(credentials)
    print("Loaded credentials successfully")
except Exception as e:
    raise ValueError(f"Failed to parse GOOGLE_SHEETS_CREDENTIALS: {e}")


# ตั้งค่าระดับ logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# โหลด Environment Variables
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
YOUR_GUILD_ID = os.getenv("DISCORD_GUILD_ID")  # อาจเป็น None

# โหลด Google Sheets Credentials จาก Secret Files
GOOGLE_SHEETS_CREDENTIALS_PATH = "/etc/secrets/GOOGLE_SHEETS_CREDENTIALS"  # Path ของ Secret File
try:
    with open(GOOGLE_SHEETS_CREDENTIALS_PATH, "r") as file:
        credentials_info = json.load(file)
except Exception as e:
    logging.error(f"ไม่สามารถโหลด Google Sheets Credentials: {e}")
    credentials_info = None


# เชื่อมต่อกับ Google Sheets
sheet = connect_to_sheets("EnvyunfairDatabase", credentials=credentials_info)  # แก้ชื่อ Sheet ให้ตรงกับความจริง

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
bot = commands.Bot(command_prefix='/', intents=intents)

@bot.command()
async def link(ctx, member: discord.Member, roblox_url: str):
    """คำสั่ง /link เชื่อมโยงบัญชี Roblox กับ Discord"""
    if not validate_roblox_url(roblox_url):
        await ctx.send("URL ไม่ถูกต้อง! กรุณาลองใหม่")
        logging.warning(f"Invalid Roblox URL provided: {roblox_url}")
        return

    user_id = roblox_url.split("/")[-2]
    roblox_data = fetch_roblox_data(user_id)

    if roblox_data:
        roblox_username = roblox_data.get("name")
        display_name = roblox_data.get("displayName")

        try:
            await member.edit(nick=f"{roblox_username}[{display_name}]")
            update_sheet(sheet, member.id, user_id, roblox_username, display_name, roblox_username)
            await ctx.send(f"เชื่อมต่อ {member.mention} กับ Roblox สำเร็จ!")
            logging.info(f"Linked {member.name} (Discord ID: {member.id}) to Roblox {roblox_username}.")
        except discord.errors.Forbidden:
            await ctx.send("ฉันไม่มีสิทธิ์เปลี่ยนชื่อผู้ใช้นี้")
            logging.error(f"Permission denied while editing nickname for {member.name} (Discord ID: {member.id}).")
        except Exception as e:
            await ctx.send(f"เกิดข้อผิดพลาด: {e}")
            logging.error(f"Unexpected error: {e}")
    else:
        await ctx.send("ไม่สามารถดึงข้อมูลจาก Roblox ได้")
        logging.warning(f"Failed to fetch Roblox data for user ID: {user_id}")

@tasks.loop(hours=1)
async def update_display_names():
    """อัปเดต Display Name ทุก 1 ชั่วโมง"""
    if not sheet:
        logging.error("Google Sheet ยังไม่ได้เชื่อมต่อ")
        return

    records = sheet.get_all_records()
    if not records:
        logging.warning("Google Sheet is empty. Cannot update display names.")
        return

    for record in records:
        user_id = record.get('Roblox ID')
        discord_id = record.get('Discord ID')
        if not user_id or not discord_id:
            logging.warning("Missing Roblox ID or Discord ID in records.")
            continue

        roblox_data = fetch_roblox_data(user_id)
        if roblox_data and roblox_data['displayName'] != record['Display Name']:
            new_display_name = roblox_data['displayName']
            update_display_name(sheet, discord_id, new_display_name)

            try:
                guild = bot.get_guild(int(YOUR_GUILD_ID)) if YOUR_GUILD_ID else None
                if not guild:
                    logging.error("Guild ID is not set or guild not found.")
                    continue

                member = guild.get_member(int(discord_id))
                if not member:
                    logging.warning(f"Member with Discord ID {discord_id} not found in the guild.")
                    continue

                await member.edit(nick=f"{record['Custom Nickname']}[{new_display_name}]")
                logging.info(f"Updated nickname for {member.name} to {new_display_name}.")
            except discord.errors.Forbidden:
                logging.error(f"Permission error: cannot change nickname for Discord ID {discord_id}.")
            except Exception as e:
                logging.error(f"Error updating nickname: {e}")

@update_display_names.before_loop
async def before_update():
    await bot.wait_until_ready()

if __name__ == "__main__":
    update_display_names.start()
    server_on()
    bot.run(TOKEN)
