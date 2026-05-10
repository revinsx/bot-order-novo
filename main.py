import discord
import requests
import pytesseract
from PIL import Image
import io
import os
import datetime

# Konfigurasi
TOKEN = os.getenv('DISCORD_TOKEN')
# Gunakan URL Google Sheets kamu (yang lama juga bisa, tapi pastikan doPost-nya sederhana)
WEB_APP_URL = os.getenv('GOOGLE_SCRIPT_URL') 
TARGET_CHANNEL_ID = 1502571869189177434

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

def extract_data(text):
    lines = text.split('\n')
    pelanggan = "Tidak ditemukan"
    plate = "Tidak ditemukan"
    orders = []
    
    for i, line in enumerate(lines):
        clean_line = line.strip().upper()
        if "CUSTOMER" in clean_line:
            # Mengambil baris setelah kata Customer
            if i+1 < len(lines): pelanggan = lines[i+1].strip()
        if "PLATE" in clean_line:
            # Mengambil baris setelah kata Plate
            if i+1 < len(lines): plate = lines[i+1].strip()
        if "(1X)" in clean_line or "(X" in clean_line:
            orders.append(line.strip())
            
    return pelanggan, plate, ", ".join(orders)

@client.event
async def on_ready():
    print(f'Bot Tesseract Online: {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user or message.channel.id != TARGET_CHANNEL_ID:
        return

    if message.attachments:
        for attachment in message.attachments:
            if any(attachment.filename.lower().endswith(ext) for ext in ['png', 'jpg', 'jpeg']):
                status_msg = await message.channel.send("Memproses dengan Tesseract... ⚙️")
                
                try:
                    # 1. Download Gambar
                    img_data = requests.get(attachment.url).content
                    img = Image.open(io.BytesIO(img_data))
                    
                    # 2. OCR Lokal (Tanpa Google Drive)
                    text = pytesseract.image_to_string(img)
                    pelanggan, plate, detail_order = extract_data(text)
                    
                    # 3. Kirim ke Google Sheets
                    payload = {
                        "mechanicName": message.author.display_name,
                        "pelanggan": pelanggan,
                        "plate": plate,
                        "orders": detail_order
                    }
                    
                    response = requests.post(WEB_APP_URL, json=payload)
                    
                    if response.status_code == 200:
                        await status_msg.edit(content=f"✅ Berhasil mencatat: **{pelanggan}**")
                    else:
                        await status_msg.edit(content="❌ Gagal mengirim data ke Sheets.")
                
                except Exception as e:
                    await status_msg.edit(content=f"❌ Error: {str(e)}")

client.run(TOKEN)
