const { Client, GatewayIntentBits, Partials } = require('discord.js');
const axios = require('axios');

const client = new Client({
    intents: [
        GatewayIntentBits.Guilds,
        GatewayIntentBits.GuildMessages,
        GatewayIntentBits.MessageContent
    ],
    partials: [Partials.Message, Partials.Channel] 
});

const APPS_SCRIPT_URL = process.env.APPS_SCRIPT_URL;
const TARGET_CHANNEL_ID = process.env.TARGET_CHANNEL_ID;

client.once('ready', () => {
    console.log(`Bot Keuangan Aktif (Nama Terbaca)! Logged in as ${client.user.tag}`);
});

client.on('messageCreate', async (message) => {
    if (message.author.bot) return;
    if (message.channel.id !== TARGET_CHANNEL_ID) return;
    
    const trigger = message.content.charAt(0);
    if (trigger !== '+' && trigger !== '-') return;
    
    const contentWithoutTrigger = message.content.slice(1).trim();
    const args = contentWithoutTrigger.split(/ +/);
    const jumlahStr = args[0];
    const keterangan = args.slice(1).join(' ') || 'Tanpa keterangan';

    const jumlah = parseFloat(jumlahStr);

    if (isNaN(jumlah)) {
        return message.reply('Format salah. Contoh: `-50000 makan siang` atau `+1000000 gajian` (Gunakan spasi setelah angka).');
    }

    await message.channel.sendTyping();

    try {
        // Mengirim data tambahan berupa username discord pengirim pesan
        const response = await axios.post(APPS_SCRIPT_URL, {
            tipe: trigger,
            jumlah: jumlah,
            keterangan: keterangan,
            username: message.author.username // <--- Mengirim nama global username Discord
        });

        if (response.data.status === 'success') {
            const lastBalance = response.data.lastBalance;
            const formatRupiah = (angka) => new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR' }).format(angka);

            let embedResponse = {
                color: trigger === '+' ? 0x00ff00 : 0xff0000,
                title: trigger === '+' ? '📈 Pemasukan Tercatat' : '📉 Pengeluaran Tercatat',
                fields: [
                    { name: 'Nominal', value: formatRupiah(jumlah), inline: true },
                    { name: 'Keterangan', value: keterangan, inline: true },
                    { name: 'Oleh', value: message.author.username, inline: true }, // Ditampilkan juga di embed Discord
                    { name: 'Saldo Terakhir', value: `**${formatRupiah(lastBalance)}**`, inline: false }
                ],
                timestamp: new Date()
            };

            message.reply({ embeds: [embedResponse] });
        } else {
            message.reply('Gagal mencatat keuangan ke Google Sheets.');
        }

    } catch (error) {
        console.error(error);
        message.reply('Terjadi error saat menghubungi Google Sheets.');
    }
});

client.login(process.env.DISCORD_TOKEN);
