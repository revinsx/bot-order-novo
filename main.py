import discord
import requests
import base64
import os

# Mengambil data rahasia dari Environment Variables Railway
TOKEN = os.getenv('DISCORD_TOKEN')
WEB_APP_URL = os.getenv('GOOGLE_SCRIPT_URL')

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'Bot sudah online sebagai {client.user}')

@client.event
async def on_message(message):
    # Abaikan pesan dari bot itu sendiri
    if message.author == client.user:
        return

    # Cek apakah ada lampiran (attachment)
    if message.attachments:
        for attachment in message.attachments:
            # Pastikan yang dikirim adalah gambar
            if any(attachment.filename.lower().endswith(ext) for ext in ['png', 'jpg', 'jpeg']):
                loading_msg = await message.channel.send("Sedang memproses screenshot... 🔍")
                
                try:
                    # Download gambar dan ubah ke format Base64
                    img_data = requests.get(attachment.url).content
                    encoded_img = base64.b64encode(img_data).decode('utf-8')
                    
                    # Siapkan data untuk dikirim ke Google Sheets
                    payload = {
                        "image": encoded_img,
                        "mechanicName": message.author.display_name
                    }
                    
                    # Tembak data ke Google Apps Script
                    response = requests.post(WEB_APP_URL, json=payload)
                    
                    if response.status_code == 200:
                        await loading_msg.edit(content=f"✅ {response.text}")
                    else:
                        await loading_msg.edit(content="❌ Gagal mengirim data ke Google Sheets.")
                
                except Exception as e:
                    await loading_msg.edit(content=f"❌ Terjadi kesalahan: {str(e)}")

client.run(TOKEN)
