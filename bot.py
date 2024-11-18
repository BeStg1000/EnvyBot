import discord
from discord.ext import commands, tasks
from discord import app_commands

from myserver import server_on
from dotenv import load_dotenv

import os
from google_sheets import connect_to_sheets, update_sheet, update_display_name
from utils import validate_roblox_url, fetch_roblox_data

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
bot = commands.Bot(command_prefix='/', intents=intents)

sheet = connect_to_sheets("YourGoogleSheetName")

@bot.command()
async def link(ctx, member: discord.Member, roblox_url: str):
    """คำสั่ง /link เชื่อมโยงบัญชี Roblox กับ Discord"""
    if not validate_roblox_url(roblox_url):
        await ctx.send("URL ไม่ถูกต้อง! กรุณาลองใหม่")
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
        except discord.errors.Forbidden:
            await ctx.send("ฉันไม่มีสิทธิ์เปลี่ยนชื่อผู้ใช้นี้")
        except Exception as e:
            await ctx.send(f"เกิดข้อผิดพลาด: {e}")
    else:
        await ctx.send("ไม่สามารถดึงข้อมูลจาก Roblox ได้")

@tasks.loop(hours=24)
async def update_display_names():
    """อัปเดต Display Name ทุก 24 ชั่วโมง"""
    records = sheet.get_all_records()
    for record in records:
        user_id = record['Roblox ID']
        discord_id = record['Discord ID']
        roblox_data = fetch_roblox_data(user_id)

        if roblox_data and roblox_data['displayName'] != record['Display Name']:
            new_display_name = roblox_data['displayName']
            update_display_name(sheet, discord_id, new_display_name)
            try:
                guild = bot.get_guild(YOUR_GUILD_ID)
                member = guild.get_member(int(discord_id))
                if member:
                    await member.edit(nick=f"{record['Custom Nickname']}[{new_display_name}]")
            except discord.errors.Forbidden:
                print("Permission error: cannot change nickname")
            except Exception as e:
                print(f"Error updating nickname: {e}")

@update_display_names.before_loop
async def before_update():
    await bot.wait_until_ready()


update_display_names.start()
server_on()
bot.run(TOKEN)