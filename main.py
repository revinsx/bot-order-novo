import discord
import requests
import pytesseract
from PIL import Image
import io
import os
import shutil

# --- KONFIGURASI SISTEM TESSERACT ---
# Fungsi ini secara otomatis mencari di mana Railway menginstal Tesseract
tesseract_path = shutil.which("tesseract")
if tesseract_path:
    pytesseract.pytesseract.tesseract_cmd = tesseract_path
    print(f"✅ Tesseract ditemukan di: {tesseract_path}")
else:
    # Jika tidak ditemukan secara otomatis, kita coba arahkan ke lokasi standar Linux
    pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"
    print("⚠️ Tesseract tidak ditemukan oleh shutil, mencoba lokasi standar /usr/bin/tesseract")

# --- KONFIGURASI BOT & GOOGLE SHEETS ---
TOKEN = os.getenv('DISCORD_TOKEN')
WEB_APP_URL = os.getenv('GOOGLE_SCRIPT_URL')
TARGET_CHANNEL_ID = 1502571869189177434

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

def extract_data(text):
    """Fungsi ekstraksi data dari teks hasil scan OCR"""
    lines = text.split('\n')
    pelanggan = "Tidak ditemukan"
    plate = "Tidak ditemukan"
    orders = []
    
    for i, line in enumerate(lines):
        clean_line = line.strip().upper()
        
        # Logika mencari Nama Pelanggan (Customer)
        if "CUSTOMER" in clean_line:
            if i+1 < len(lines):
                pelanggan = lines[i+1].strip()
        
        # Logika mencari Plat Nomor (Plate)
        if "PLATE" in clean_line:
            if i+1 < len(lines):
                plate = lines[i+1].strip()
        
        # Logika mencari item pesanan, misal: "Repair (1x)"
        # Tesseract terkadang membaca (1x) sebagai (ix) atau (tx), kita buat lebih fleksibel
        lower_line = line.lower()
        if "(x" in lower_line or "(1x)" in lower_line or "x)" in lower_line:
            orders.append(line.strip())
            
    return pelanggan, plate, ", ".join(orders)

@client.event
async def on_ready():
    print(f'--- Bot Mekanik Online ---')
    print(f'Logged in as: {client.user}')
    print(f'Target Channel ID: {TARGET_CHANNEL_ID}')
    print(f'--------------------------')

@client.event
async def on_message(message):
    # Abaikan pesan dari bot sendiri atau di luar channel target
    if message.author == client.user or message.channel.id != TARGET_CHANNEL_ID:
        return

    # Jika pesan berisi lampiran (gambar)
    if message.attachments:
        for attachment in message.attachments:
            # Cek apakah file tersebut adalah gambar
            if any(attachment.filename.lower().endswith(ext) for ext in ['png', 'jpg', 'jpeg']):
                status_msg = await message.channel.send("🔍 Sedang memproses screenshot (Tesseract)...")
                
                try:
                    # 1. Ambil data gambar dari Discord
                    response_img = requests.get(attachment.url)
                    img = Image.open(io.BytesIO(response_img.content))
                    
                    # 2. Jalankan OCR Lokal (Tesseract)
                    # Kita gunakan config tambahan agar Tesseract lebih fokus baca teks
                    raw_text = pytesseract.image_to_string(img, config='--psm 3')
                    
                    # 3. Ekstrak informasi penting
                    cust, plt, ords = extract_data(raw_text)
                    
                    # 4. Siapkan data untuk dikirim ke Google Sheets
                    payload = {
                        "mechanicName": message.author.display_name,
                        "pelanggan": cust,
                        "plate": plt,
                        "orders": ords if ords else "Detail pesanan tidak terbaca"
                    }
                    
                    # 5. Kirim ke URL Google Apps Script (Web App)
                    post_to_sheet = requests.post(WEB_APP_URL, json=payload)
                    
                    if post_to_sheet.status_code == 200:
                        embed = discord.Embed(title="✅ Data Berhasil Dicatat", color=0x00ff00)
                        embed.add_field(name="Mekanik", value=message.author.display_name, inline=True)
                        embed.add_field(name="Pelanggan", value=cust, inline=True)
                        embed.add_field(name="Plat Nomor", value=plt, inline=True)
                        embed.add_field(name="Pesanan", value=ords if ords else "-", inline=False)
                        embed.set_footer(text="Sistem OCR Tesseract Lokal")
                        
                        await status_msg.edit(content=None, embed=embed)
                    else:
                        await status_msg.edit(content=f"❌ Gagal mengirim ke Sheets (Status: {post_to_sheet.status_code})")
                
                except Exception as e:
                    await status_msg.edit(content=f"❌ Terjadi kesalahan: `{str(e)}`")

# Jalankan Bot
if TOKEN:
    client.run(TOKEN)
else:
    print("ERROR: DISCORD_TOKEN tidak ditemukan di environment variables!")
