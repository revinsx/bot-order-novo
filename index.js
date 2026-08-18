const { Client, GatewayIntentBits, Partials, Events } = require('discord.js');
const axios = require('axios');

// Inisialisasi Client Discord Bot
const client = new Client({
    intents: [
        GatewayIntentBits.Guilds,
        GatewayIntentBits.GuildMessages,
        GatewayIntentBits.MessageContent,
        GatewayIntentBits.GuildMembers
    ],
    partials: [Partials.Message, Partials.Channel] 
});

// Mengambil konfigurasi dari Environment Variables di Railway
const APPS_SCRIPT_URL = process.env.APPS_SCRIPT_URL;
const TARGET_CHANNEL_ID = process.env.TARGET_CHANNEL_ID; // Channel untuk pencatatan keuangan

// Channel khusus untuk interaksi/sapaan otomatis
const INTERACTION_CHANNEL_ID = process.env.INTERACTION_CHANNEL_ID || '1463961470344757336';

// List pesan interaksi acak yang genit, centil, dan penuh gombalan
const INTERACTION_MESSAGES = [
    "Aduh {user}, kamu tau gak bedanya kamu sama shift duty? Kalo duty ada selesainya, kalo cintaku ke kamu gak ada selesainya~ 🙈💖",
    "Udah berapa lama duty-nya hari ini {user}? Jangan kecapekan dong, nanti siapa yang nemenin aku di masa depan? 🥹✨",
    "Semangat ya kerjanya {user}! Jangan lupa minum air putih, biar tetep manis kaya senyuman kamu ke aku 🥤😉",
    "Ehem... {user} kamu punya peta gak? Aku tersesat nih di dalam indahnya mata kamu~ 😚🌸",
    "Halo ganteng/cantik {user}, duty mulu deh... Kapan dong waktu untuk mencintai aku sepenuhnya? 🥹👉👈",
    "{user} kamu tau gak kenapa bintang malam ini redup? Soalnya kalah terang sama pesona kamu! 💅✨",
    "Kerja yang rajin ya {user}! Nanti kalo udah sukses, langsung lamar aku ya! 🧋💕",
    "Capek ya {user}? Sini-sini aku peluk biar rasa capeknya pindah jadi rasa sayang~ 🥰✨",
    "{user} kamu itu kaya Wi-Fi deh, soalnya aku langsung merasa 'connected' tiap liat kamu~ 🤭💖",
    "Fokus banget sih {user} dari tadi, lirih-lirih aku dikit napa... Aku kan juga butuh perhatian kamu 🥺👉👈",
    "Beli baju warna merah, {user} emang yang paling bikin hatiku merona deh hari ini! 🔥✨",
    "Lagi mikirin apa sih {user}? Mending mikirin gimana cara menata masa depan kita berdua! 🫣💗",
    "Semangat terus {user}! Kalo butuh sandaran, bahu dan hatiku selalu terbuka buat kamu~ 😉💅",
    "Hari ini kamu keliatan makin manis deh {user}, pantesan semut pada ngumpul! 😍✨",
    "Jangan lupa makan ya {user}, aku ga mau kamu sakit... Nanti hatiku juga ikut sakit tau! 🥺💔",
    "Ssstt... {user}, kerjaannya jangan terlalu diseriusin, mending seriusin hubungan kita aja~ 🤭✨",
    "Lagi keliling duty ya {user}? Awas jatuh, tapi kalau jatuhnya ke hatiku sih gak apa-apa~ 🥹💕",
    "Duh, mataku langsung adem banget begitu liat {user} muncul di sini! 🌸✨",
    "{user} kamu punya pemadam kebakaran gak? Soalnya kamu berhasil membakar api cinta di hatiku! 😋💅",
    "Semangat ya {user}! Inget, ada aku yang selalu merindukanmu dari jauh~ 🥰✨",
    "Kalo duty-nya udah kelar, bales chat aku ya {user}! Nanti aku kangennya makin berabe! 🥺👉👈",
    "Ihh {user} kamu itu kaya kopi deh, bikin aku ga bisa tidur karena ketagihan mikirin kamu! ☕💕",
    "Kerja mulu {user}, ga ada niatan buat ngebahagiain aku gitu? 🫣✨",
    "Semangat terus ya darling {user}! Kamu tuh alasan aku tersenyum hari ini! 💖🔥",
    "Duh {user}, pesona kamu meluap-luap deh hari ini, tolong dikondisikan ya bikin hatiku deg-degan mulu! 🙈✨",
    "{user} tau gak bedanya kamu sama AC? AC pendingin ruangan, kalau kamu pendingin hatiku yang lagi gundah~ 🍦😉",
    "Lagi kerja ya {user}? Ya udah deh aku pandangin aja foto kamu biar tambah semangat~ 🥰✨",
    "{user} kamu cape gak sih? Dari tadi malam kamu lari-lari terus di pikiran aku tau! 🏃‍♂️💨",
    "Kamu tau gak {user}, rumah apa yang paling indah? RUMAH tangga kita nanti~ 🏠💖",
    "Satu tambah satu sama dengan dua, aku tambah kamu sama dengan bahagia selamanya! {user} 😘✨"
];

// Fungsi untuk memilih member acak & mengirim pesan interaksi
async function sendRandomInteraction(channel) {
    try {
        if (!channel || !channel.guild) return;

        // Fetch seluruh member di server
        const members = await channel.guild.members.fetch();
        // Filter agar tidak ngetag bot
        const nonBotMembers = members.filter(member => !member.user.bot);

        if (nonBotMembers.size === 0) return;

        // Pilih 1 member acak
        const randomMember = nonBotMembers.random();

        // Pilih 1 template pesan acak
        const randomTemplate = INTERACTION_MESSAGES[Math.floor(Math.random() * INTERACTION_MESSAGES.length)];
        const messageToSend = randomTemplate.replace('{user}', `<@${randomMember.id}>`);

        await channel.send(messageToSend);
    } catch (error) {
        console.error("Gagal mengirim interaksi acak:", error);
    }
}

// Event saat Bot berhasil online
client.once(Events.ClientReady, (readyClient) => {
    console.log(`Bot Keuangan & Interaksi Aktif! Logged in as ${readyClient.user.tag}`);

    // Set interval pengecekan setiap 3 jam (3 * 60 * 60 * 1000 ms)
    const THREE_HOURS = 3 * 60 * 60 * 1000;

    setInterval(async () => {
        try {
            // Ambil jam saat ini dalam zona waktu WIB (Asia/Jakarta)
            const now = new Date();
            const options = { timeZone: 'Asia/Jakarta', hour: '2-digit', hour12: false };
            const currentHour = parseInt(new Intl.DateTimeFormat('en-US', options).format(now), 10);

            // Cek apakah jam saat ini antara 06:00 sampai 23:59 WIB
            if (currentHour >= 6 && currentHour <= 23) {
                // Kirim ke channel interaksi khusus
                const channel = await client.channels.fetch(INTERACTION_CHANNEL_ID);
                if (channel) {
                    await sendRandomInteraction(channel);
                }
            }
        } catch (err) {
            console.error("Error pada penjadwalan otomatis:", err);
        }
    }, THREE_HOURS);
});

// Event saat ada pesan masuk di Discord
client.on('messageCreate', async (message) => {
    if (message.author.bot) return;

    // ----------------------------------------------------
    // FITUR MANUAL COMMAND: !novo
    // Bekerja jika diketik di INTERACTION_CHANNEL_ID atau TARGET_CHANNEL_ID
    // ----------------------------------------------------
    if (message.content.trim().toLowerCase() === '!novo') {
        const targetChannel = await client.channels.fetch(INTERACTION_CHANNEL_ID).catch(() => message.channel);
        await sendRandomInteraction(targetChannel);
        return;
    }

    // ----------------------------------------------------
    // FITUR CATATAN KEUANGAN (+ / -)
    // Hanya berjalan di TARGET_CHANNEL_ID
    // ----------------------------------------------------
    if (message.channel.id !== TARGET_CHANNEL_ID) return;

    const trigger = message.content.charAt(0);
    if (trigger !== '+' && trigger !== '-') return;

    const contentWithoutTrigger = message.content.slice(1).trim();
    const args = contentWithoutTrigger.split(/ +/);
    const jumlahStr = args[0];
    const keterangan = args.slice(1).join(' ') || 'No description';

    const jumlah = parseFloat(jumlahStr);

    if (isNaN(jumlah)) {
        return message.reply('Format salah! Contoh penggunaan:\n`-50.50 starbucks` atau `+1500 salary` (Gunakan spasi setelah angka).');
    }

    await message.channel.sendTyping();

    try {
        const response = await axios.post(APPS_SCRIPT_URL, {
            tipe: trigger,
            jumlah: jumlah,
            keterangan: keterangan,
            username: message.author.username
        });

        if (response.data.status === 'success') {
            const lastBalance = response.data.lastBalance;
            const formatDollar = (angka) => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(angka);

            let embedResponse = {
                color: trigger === '+' ? 0x00ff00 : 0xff0000,
                title: trigger === '+' ? '📈 Income Recorded' : '📉 Expense Recorded',
                fields: [
                    { name: 'Amount', value: formatDollar(jumlah), inline: true },
                    { name: 'Description', value: keterangan, inline: true },
                    { name: 'By', value: message.author.username, inline: true },
                    { name: 'Last Balance', value: `**${formatDollar(lastBalance)}**`, inline: false }
                ],
                timestamp: new Date()
            };

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
