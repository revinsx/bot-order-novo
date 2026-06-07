const { Client, GatewayIntentBits, Partials, Events } = require('discord.js');
const axios = require('axios');

// Inisialisasi Client Discord Bot
const client = new Client({
    intents: [
        GatewayIntentBits.Guilds,
        GatewayIntentBits.GuildMessages,
        GatewayIntentBits.MessageContent
    ],
    // Partials digunakan agar bot lancar membaca pesan di dalam Thread lama/baru
    partials: [Partials.Message, Partials.Channel] 
});

// Mengambil konfigurasi dari Environment Variables di Railway
const APPS_SCRIPT_URL = process.env.APPS_SCRIPT_URL;
const TARGET_CHANNEL_ID = process.env.TARGET_CHANNEL_ID; // Isi dengan ID Thread Anda

// Event saat Bot berhasil online (Menggunakan Events.ClientReady agar tidak memicu warning)
client.once(Events.ClientReady, (readyClient) => {
    console.log(`Bot Keuangan Aktif (USD Mode)! Logged in as ${readyClient.user.tag}`);
});

// Event saat ada pesan masuk di Discord
client.on('messageCreate', async (message) => {
    // 1. Abaikan jika pesan berasal dari sesama Bot
    if (message.author.bot) return;
    
    // 2. Hanya proses jika pesan dikirim di dalam Thread yang ID-nya sudah didaftarkan
    if (message.channel.id !== TARGET_CHANNEL_ID) return;
    
    // 3. Cek apakah karakter pertama adalah trigger '+' atau '-'
    const trigger = message.content.charAt(0);
    if (trigger !== '+' && trigger !== '-') return;
    
    // Memisahkan nominal angka dan keterangan teks
    const contentWithoutTrigger = message.content.slice(1).trim();
    const args = contentWithoutTrigger.split(/ +/);
    const jumlahStr = args[0];
    const keterangan = args.slice(1).join(' ') || 'No description';

    // Mengubah teks angka menjadi tipe data Float (Desimal)
    const jumlah = parseFloat(jumlahStr);

    // Validasi jika input setelah tanda baca bukan merupakan angka
    if (isNaN(jumlah)) {
        return message.reply('Format salah! Contoh penggunaan:\n`-50.50 starbucks` atau `+1500 salary` (Gunakan spasi setelah angka).');
    }

    // Memunculkan status "Bot Keuangan is typing..." di Discord
    await message.channel.sendTyping();

    try {
        // Mengirimkan data keuangan ke Google Apps Script (Database)
        const response = await axios.post(APPS_SCRIPT_URL, {
            tipe: trigger,
            jumlah: jumlah,
            keterangan: keterangan,
            username: message.author.username // Mengirim nama Discord pengirim
        });

        // Jika Google Apps Script berhasil memproses dan menyimpan data
        if (response.data.status === 'success') {
            const lastBalance = response.data.lastBalance;
            
            // Format angka menjadi mata uang Dolar AS ($)
            const formatDollar = (angka) => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(angka);

            // Membuat tampilan balasan kotak (Embed) di Discord
            let embedResponse = {
                color: trigger === '+' ? 0x00ff00 : 0xff0000, // Hijau untuk +, Merah untuk -
                title: trigger === '+' ? '📈 Income Recorded' : '📉 Expense Recorded',
                fields: [
                    { name: 'Amount', value: formatDollar(jumlah), inline: true },
                    { name: 'Description', value: keterangan, inline: true },
                    { name: 'By', value: message.author.username, inline: true },
                    { name: 'Last Balance', value: `**${formatDollar(lastBalance)}**`, inline: false }
                ],
                timestamp: new Date()
            };

            // Kirim balasan embed ke dalam Thread
            message.reply({ embeds: [embedResponse] });
        } else {
            message.reply('Gagal mencatat keuangan ke Google Sheets. Silakan periksa konfigurasi Apps Script Anda.');
        }

    } catch (error) {
        console.error(error);
        message.reply('Terjadi kesalahan jaringan/error saat menghubungi Google Sheets.');
    }
});

// Menghubungkan bot menggunakan Token dari Railway
client.login(process.env.DISCORD_TOKEN);
