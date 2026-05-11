import discord
import requests
import pytesseract
from PIL import Image
import io
import os
import datetime

# --- KONFIGURASI TESSERACT (DOCKER) ---
pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'

TOKEN = os.getenv('DISCORD_TOKEN')
WEB_APP_URL = os.getenv('GOOGLE_SCRIPT_URL')
TARGET_CHANNEL_ID = 1502571869189177434

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

def extract_data(text):
    lines = text.split('\n')
    pelanggan, plate, orders = "Tidak ditemukan", "Tidak ditemukan", []
    for i, line in enumerate(lines):
        clean_line = line.strip().upper()
        if "CUSTOMER" in clean_line and i+1 < len(lines): pelanggan = lines[i+1].strip()
        if "PLATE" in clean_line and i+1 < len(lines): plate = lines[i+1].strip()
        if any(x in line.lower() for x in ["(x", "x)", "(1x)"]): orders.append(line.strip())
    return pelanggan, plate, ", ".join(orders)

@client.event
async def on_ready():
    print(f'🟢 BOT MEKANIK ONLINE - LOGGED IN AS {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    # --- LOGIKA COMMAND !RESET ---
    if message.content == "!reset":
        # Cek apakah user memiliki permission Administrator
        if message.author.guild_permissions.administrator:
            confirm_msg = await message.channel.send("🔄 Sedang mereset spreadsheet...")
            try:
                response = requests.post(WEB_APP_URL, json={"action": "reset"})
                if response.status_code == 200:
                    await confirm_msg.edit(content="✅ **Spreadsheet telah dikosongkan oleh Admin.**")
                else:
                    await confirm_msg.edit(content="❌ Gagal mereset spreadsheet.")
            except Exception as e:
                await confirm_msg.edit(content=f"❌ Error: {str(e)}")
        else:
            await message.channel.send("⛔ **Maaf, hanya Admin yang bisa menggunakan perintah ini.**")
        return

    # --- LOGIKA OCR (HANYA DI CHANNEL TARGET) ---
    if message.channel.id == TARGET_CHANNEL_ID and message.attachments:
        for attachment in message.attachments:
            if any(attachment.filename.lower().endswith(ext) for ext in ['png', 'jpg', 'jpeg']):
                status_msg = await message.channel.send("⌛ **Memproses Screenshot...**")
                try:
                    img_data = requests.get(attachment.url).content
                    img = Image.open(io.BytesIO(img_data))
                    raw_text = pytesseract.image_to_string(img, config='--psm 3')
                    cust, plt, ords = extract_data(raw_text)
                    
                    payload = {
                        "mechanicName": message.author.display_name,
                        "pelanggan": cust,
                        "plate": plt,
                        "orders": ords if ords else "Detail tidak terbaca"
                    }
                    
                    requests.post(WEB_APP_URL, json=payload)
                    
                    embed = discord.Embed(title="✅ Data Tercatat", color=0x2ecc71)
                    embed.add_field(name="Mekanik", value=message.author.mention, inline=True)
                    embed.add_field(name="Plat Nomor", value=f"`{plt}`", inline=True)
                    embed.add_field(name="Pelanggan", value=cust, inline=False)
                    await status_msg.edit(content=None, embed=embed)
                except Exception as e:
                    await status_msg.edit(content=f"❌ Error: `{str(e)}`")

client.run(TOKEN)
