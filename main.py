import discord
import requests
import pytesseract
from PIL import Image
import io
import os
import datetime

# --- KONFIGURASI TESSERACT (DOCKER/UBUNTU) ---
# Di Docker (python:3.11-slim), tesseract selalu terpasang di sini
pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'

# --- KONFIGURASI BOT & GOOGLE SHEETS ---
TOKEN = os.getenv('DISCORD_TOKEN')
WEB_APP_URL = os.getenv('GOOGLE_SCRIPT_URL')
TARGET_CHANNEL_ID = 1502571869189177434

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

def extract_data(text):
    """Fungsi cerdas untuk mengambil data dari teks hasil scan"""
    lines = text.split('\n')
    pelanggan = "Tidak ditemukan"
    plate = "Tidak ditemukan"
    orders = []
    
    for i, line in enumerate(lines):
        clean_line = line.strip().upper()
        
        # Mencari Nama Pelanggan (biasanya di bawah baris 'Customer')
        if "CUSTOMER" in clean_line:
            if i+1 < len(lines) and lines[i+1].strip():
                pelanggan = lines[i+1].strip()
        
        # Mencari Plat Nomor (biasanya di bawah baris 'Plate')
        if "PLATE" in clean_line:
            if i+1 < len(lines) and lines[i+1].strip():
                plate = lines[i+1].strip()
        
        # Mencari detail pesanan (mencari pola (x) atau (1x))
        lower_line = line.lower()
        if "(x" in lower_line or "x)" in lower_line or "(1x)" in lower_line:
            orders.append(line.strip())
            
    return pelanggan, plate, ", ".join(orders)

@client.event
async def on_ready():
    print(f'======================================')
    print(f'🟢 BOT MEKANIK DOCKER ONLINE')
    print(f'Logged in as: {client.user}')
    print(f'Tesseract Path: {pytesseract.pytesseract.tesseract_cmd}')
    print(f'======================================')

@client.event
async def on_message(message):
    # Validasi: Abaikan bot sendiri & pastikan channel benar
    if message.author == client.user or message.channel.id != TARGET_CHANNEL_ID:
        return

    # Jika ada gambar yang dikirim
    if message.attachments:
        for attachment in message.attachments:
            if any(attachment.filename.lower().endswith(ext) for ext in ['png', 'jpg', 'jpeg']):
                
                status_msg = await message.channel.send("⌛ **Memproses Screenshot...**")
                
                try:
                    # 1. Download Gambar
                    img_data = requests.get(attachment.url).content
                    img = Image.open(io.BytesIO(img_data))
                    
                    # 2. Proses OCR Lokal (Tesseract)
                    # psm 3: Automatic page segmentation (standar)
                    raw_text = pytesseract.image_to_string(img, config='--psm 3')
                    
                    # 3. Ekstraksi Informasi
                    cust, plt, ords = extract_data(raw_text)
                    
                    # 4. Kirim Data ke Google Sheets
                    payload = {
                        "mechanicName": message.author.display_name,
                        "pelanggan": cust,
                        "plate": plt,
                        "orders": ords if ords else "Detail tidak terbaca"
                    }
                    
                    response = requests.post(WEB_APP_URL, json=payload)
                    
                    if response.status_code == 200:
                        # Buat tampilan yang rapi di Discord
                        embed = discord.Embed(
                            title="✅ Laporan Mekanik Berhasil Dicatat",
                            color=0x2ecc71, # Warna Hijau
                            timestamp=datetime.datetime.now()
                        )
                        embed.add_field(name="👤 Mekanik", value=message.author.mention, inline=True)
                        embed.add_field(name="🚘 Plat Nomor", value=f"`{plt}`", inline=True)
                        embed.add_field(name="🤝 Pelanggan", value=cust, inline=False)
                        embed.add_field(name="🛠️ Detail Pekerjaan", value=ords if ords else "-", inline=False)
                        embed.set_footer(text="System OCR Docker-Tesseract")
                        
                        await status_msg.edit(content=None, embed=embed)
                    else:
                        await status_msg.edit(content=f"❌ Gagal mengirim ke Sheets. Error Code: {response.status_code}")
                
                except Exception as e:
                    await status_msg.edit(content=f"❌ **Terjadi Error:**\n`{str(e)}`")

# Jalankan Bot
if TOKEN:
    client.run(TOKEN)
else:
    print("❌ ERROR: DISCORD_TOKEN tidak ditemukan!")
