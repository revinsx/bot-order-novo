import discord
import requests
import pytesseract
from PIL import Image
import io
import os
import shutil

# --- PENGATURAN TESSERACT ---
# Mencari lokasi instalasi Tesseract secara otomatis di sistem Railway
tesseract_path = shutil.which("tesseract")
if tesseract_path:
    pytesseract.pytesseract.tesseract_cmd = tesseract_path
    print(f"Tesseract ditemukan di: {tesseract_path}")
else:
    print("PERINGATAN: Tesseract tidak ditemukan!")

# --- KONFIGURASI BOT ---
TOKEN = os.getenv('DISCORD_TOKEN')
WEB_APP_URL = os.getenv('GOOGLE_SCRIPT_URL')
TARGET_CHANNEL_ID = 1502571869189177434

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

def extract_data(text):
    """Fungsi untuk mencari nama pelanggan, plat, dan order dari teks OCR"""
    lines = text.split('\n')
    pelanggan = "Tidak ditemukan"
    plate = "Tidak ditemukan"
    orders = []
    
    for i, line in enumerate(lines):
        clean_line = line.strip().upper()
        # Cari Nama Pelanggan
        if "CUSTOMER" in clean_line:
            if i+1 < len(lines):
                pelanggan = lines[i+1].strip()
        # Cari Plat Nomor
        if "PLATE" in clean_line:
            if i+1 < len(lines):
                plate = lines[i+1].strip()
        # Cari Detail Order (biasanya mengandung (1x) atau (x)
        if "(1X)" in clean_line or "(X" in clean_line:
            orders.append(line.strip())
            
    return pelanggan, plate, ", ".join(orders)

@client.event
async def on_ready():
    print(f'Bot Tesseract Aktif: {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user or message.channel.id != TARGET_CHANNEL_ID:
        return

    if message.attachments:
        for attachment in message.attachments:
            if any(attachment.filename.lower().endswith(ext) for ext in ['png', 'jpg', 'jpeg']):
                status_msg = await message.channel.send("Memproses gambar (Tesseract)... ⚙️")
                
                try:
                    # 1. Ambil Gambar
                    response_img = requests.get(attachment.url)
                    img = Image.open(io.BytesIO(response_img.content))
                    
                    # 2. Proses OCR Lokal
                    raw_text = pytesseract.image_to_string(img)
                    cust, plt, ords = extract_data(raw_text)
                    
                    # 3. Kirim data teks ke Google Apps Script
                    payload = {
                        "mechanicName": message.author.display_name,
                        "pelanggan": cust,
                        "plate": plt,
                        "orders": ords if ords else "Tidak ada detail"
                    }
                    
                    post_to_sheet = requests.post(WEB_APP_URL, json=payload)
                    
                    if post_to_sheet.status_code == 200:
                        await status_msg.edit(content=f"✅ Data dicatat! \n**Pelanggan:** {cust} \n**Plat:** {plt}")
                    else:
                        await status_msg.edit(content="❌ Gagal mengirim ke Spreadsheet.")
                
                except Exception as e:
                    await status_msg.edit(content=f"❌ Error: {str(e)}")

client.run(TOKEN)
