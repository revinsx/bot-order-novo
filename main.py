import discord
import requests
import pytesseract
from PIL import Image
import io
import os
import re
import datetime

# --- KONFIGURASI TESSERACT (DOCKER) ---
pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'

# --- AMBIL ENV VARIABLES DARI RAILWAY ---
TOKEN = os.getenv('DISCORD_TOKEN')
WEB_APP_URL = os.getenv('GOOGLE_SCRIPT_URL')
TARGET_CHANNEL_ID = 1502571869189177434 # Sesuaikan ID Channel Anda

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

def extract_data(text):
    """Mengekstrak Pelanggan, Plat, WO#, dan Orders dari hasil OCR"""
    lines = text.split('\n')
    pelanggan, plate, wo_number, orders = "Tidak ditemukan", "Tidak ditemukan", "0", []
    
    for i, line in enumerate(lines):
        clean_line = line.strip().upper()
        
        # Ekstrak Work Order #
        if "WORK ORDER" in clean_line or "ORDER #" in clean_line:
            match = re.search(r'#\s*(\d+)', clean_line)
            if match:
                wo_number = match.group(1)
            elif i+1 < len(lines):
                match_below = re.search(r'(\d+)', lines[i+1])
                if match_below: wo_number = match_below.group(1)

        # Ekstrak Customer & Plate
        if "CUSTOMER" in clean_line and i+1 < len(lines): pelanggan = lines[i+1].strip()
        if "PLATE" in clean_line and i+1 < len(lines): plate = lines[i+1].strip()
        
        # Ekstrak Detail Order (mencari tanda x atau 1x)
        if any(x in line.lower() for x in ["(x", "x)", "(1x)"]):
            orders.append(line.strip())
            
    return pelanggan, plate, wo_number, ", ".join(orders)

@client.event
async def on_ready():
    print(f'======================================')
    print(f'🟢 BOT MEKANIK ANTI-DUPLIKASI AKTIF')
    print(f'Logged in as: {client.user}')
    print(f'======================================')

@client.event
async def on_message(message):
    if message.author == client.user: return

    # --- COMMAND RESET (ADMIN ONLY) ---
    if message.content == "!reset":
        if message.author.guild_permissions.administrator:
            confirm = await message.channel.send("🔄 Sedang mereset spreadsheet...")
            res = requests.post(WEB_APP_URL, json={"action": "reset"})
            if res.text == "RESET_SUCCESS":
                await confirm.edit(content="✅ **Spreadsheet telah berhasil dikosongkan.**")
            else:
                await confirm.edit(content="❌ Gagal mereset data.")
        else:
            await message.channel.send("⛔ Anda tidak memiliki izin Admin.")
        return

    # --- PROSES SCAN GAMBAR ---
    if message.channel.id == TARGET_CHANNEL_ID and message.attachments:
        for attachment in message.attachments:
            if any(attachment.filename.lower().endswith(ext) for ext in ['png', 'jpg', 'jpeg']):
                status_msg = await message.channel.send("⌛ **Memverifikasi data...**")
                
                try:
                    # Download & OCR
                    img_data = requests.get(attachment.url).content
                    img = Image.open(io.BytesIO(img_data))
                    # Gunakan psm 3 dan oem 1 untuk akurasi/kecepatan seimbang
                    raw_text = pytesseract.image_to_string(img, config='--psm 3 --oem 1')
                    
                    cust, plt, wo, ords = extract_data(raw_text)
                    
                    payload = {
                        "mechanicName": message.author.display_name,
                        "pelanggan": cust,
                        "plate": plt,
                        "wo": wo,
                        "orders": ords if ords else "Detail tidak terbaca"
                    }
                    
                    # Kirim ke Sheets
                    response = requests.post(WEB_APP_URL, json=payload)
                    result = response.text

                    if result == "REJECTED_DUPLICATE":
                        await status_msg.edit(content=f"❌ **PENGAJUAN DITOLAK!**\nData dengan Plat `{plt}` dan Work Order `#{wo}` sudah pernah didaftarkan.")
                    elif result == "SUCCESS":
                        embed = discord.Embed(title="✅ Laporan Mekanik Diterima", color=0x2ecc71, timestamp=datetime.datetime.now())
                        embed.add_field(name="Mekanik", value=message.author.mention, inline=True)
                        embed.add_field(name="Work Order", value=f"`#{wo}`", inline=True)
                        embed.add_field(name="Plat Nomor", value=f"`{plt}`", inline=True)
                        embed.set_footer(text="Anti-Cheat System Active")
                        await status_msg.edit(content=None, embed=embed)
                    else:
                        await status_msg.edit(content=f"⚠️ Sistem Sheets merespon: `{result}`")
                
                except Exception as e:
                    await status_msg.edit(content=f"❌ Error Teknis: `{str(e)}`")

if TOKEN:
    client.run(TOKEN)
else:
    print("TOKEN KOSONG!")
