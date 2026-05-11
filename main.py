import discord
import requests
import pytesseract
from PIL import Image
import io
import os
import re

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
    pelanggan = "Tidak ditemukan"
    plate = "Tidak ditemukan"
    wo_number = "Tidak ditemukan"
    orders = []
    
    for i, line in enumerate(lines):
        clean_line = line.strip().upper()
        
        # Cari Work Order # (Mencari angka setelah tanda # atau kata Order)
        if "WORK ORDER" in clean_line or "ORDER #" in clean_line:
            # Menggunakan regex untuk mengambil angka saja
            match = re.search(r'#\s*(\d+)', clean_line)
            if match:
                wo_number = match.group(1)
            elif i+1 < len(lines): # Jika angka ada di baris bawahnya
                match_below = re.search(r'(\d+)', lines[i+1])
                if match_below: wo_number = match_below.group(1)

        # Cari Pelanggan & Plat (Logika lama tetap dipertahankan)
        if "CUSTOMER" in clean_line and i+1 < len(lines): pelanggan = lines[i+1].strip()
        if "PLATE" in clean_line and i+1 < len(lines): plate = lines[i+1].strip()
        if any(x in line.lower() for x in ["(x", "x)", "(1x)"]): orders.append(line.strip())
            
    return pelanggan, plate, wo_number, ", ".join(orders)

@client.event
async def on_ready():
    print(f'🟢 BOT ANTI-DUPLIKASI ONLINE')

@client.event
async def on_message(message):
    if message.author == client.user: return

    # Logika !reset tetap sama
    if message.content == "!reset":
        if message.author.guild_permissions.administrator:
            response = requests.post(WEB_APP_URL, json={"action": "reset"})
            await message.channel.send("✅ **Spreadsheet telah direset.**")
        return

    if message.channel.id == TARGET_CHANNEL_ID and message.attachments:
        for attachment in message.attachments:
            if any(attachment.filename.lower().endswith(ext) for ext in ['png', 'jpg', 'jpeg']):
                status_msg = await message.channel.send("⌛ **Mengecek validasi data...**")
                try:
                    img_data = requests.get(attachment.url).content
                    img = Image.open(io.BytesIO(img_data))
                    raw_text = pytesseract.image_to_string(img, config='--psm 3')
                    
                    cust, plt, wo, ords = extract_data(raw_text)
                    
                    # Kirim data ke Sheets untuk pengecekan duplikasi
                    payload = {
                        "mechanicName": message.author.display_name,
                        "pelanggan": cust,
                        "plate": plt,
                        "wo": wo,
                        "orders": ords if ords else "Detail tidak terbaca"
                    }
                    
                    response = requests.post(WEB_APP_URL, json=payload)
                    result = response.text
                    
                    if result == "DUPLICATE":
                        await status_msg.edit(content=f"❌ **KECURANGAN TERDETEKSI!**\nWork Order `#{wo}` dengan Plat `{plt}` sudah pernah didaftarkan sebelumnya.")
                    elif response.status_code == 200:
                        embed = discord.Embed(title="✅ Data Berhasil Dicatat", color=0x2ecc71)
                        embed.add_field(name="WO #", value=f"`{wo}`", inline=True)
                        embed.add_field(name="Plat", value=f"`{plt}`", inline=True)
                        embed.add_field(name="Mekanik", value=message.author.mention, inline=False)
                        await status_msg.edit(content=None, embed=embed)
                    
                except Exception as e:
                    await status_msg.edit(content=f"❌ Error: `{str(e)}`")

client.run(TOKEN)
