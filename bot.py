import discord
from discord.ext import commands
import asyncio
from config import TOKEN
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

games = {}  # {channel_id: {"players": [], "choices": {user_id: "s/m/k"}}}

@bot.event
async def on_ready():
    print(f'{bot.user} olarak giriş yapıldı.')

@bot.command()
async def oyna(ctx):
    if ctx.channel.id in games:
        await ctx.send("Bu kanalda zaten aktif bir oyun var.")
        return

    await ctx.send("2 oyuncu oyuna katılmak için `!katıl` yazsın.")
    games[ctx.channel.id] = {"players": [], "choices": {}}

@bot.command()
async def katıl(ctx):
    game = games.get(ctx.channel.id)
    if not game:
        await ctx.send("Henüz oyun başlatılmamış. `!oyna` ile başlat.")
        return
    if ctx.author in game["players"]:
        await ctx.send("Zaten katıldın.")
        return
    game["players"].append(ctx.author)

    await ctx.send(f"{ctx.author.mention} oyuna katıldı!")

    if len(game["players"]) == 2:
        await ctx.send("Oyun başlıyor! Oyunculara özel mesaj gönderiliyor.")
        for player in game["players"]:
            await player.send("Hamleni seç: (s)ilah, (k)alkan, (m)ermi. Yanıt olarak sadece harfi yaz.")
        bot.loop.create_task(hamleleri_bekle(ctx.channel.id))

async def hamleleri_bekle(channel_id):
    game = games[channel_id]
    while len(game["choices"]) < 2:
        await asyncio.sleep(1)
    await sonucu_hesapla(channel_id)

@bot.event
async def on_message(message):
    await bot.process_commands(message)

    for channel_id, game in games.items():
        if message.author in game["players"] and message.guild is None:
            choice = message.content.lower()
            if choice in ["s", "k", "m"] and message.author.id not in game["choices"]:
                game["choices"][message.author.id] = choice
                await message.author.send("Hamlen alındı.")
            elif message.guild is None:
                await message.author.send("Geçersiz hamle. Lütfen s/k/m harflerinden birini gir.")

async def sonucu_hesapla(channel_id):
    game = games[channel_id]
    p1, p2 = game["players"]
    c1 = game["choices"][p1.id]
    c2 = game["choices"][p2.id]

    kanal = bot.get_channel(channel_id)
    await kanal.send(f"{p1.mention} seçimi: {c1}\n{p2.mention} seçimi: {c2}")

    sonuc = hesapla_sonuc(c1, c2)

    if sonuc == 0:
        await kanal.send("Beraberlik!")
    elif sonuc == 1:
        await kanal.send(f"{p1.mention} kazandı!")
    elif sonuc == 2:
        await kanal.send(f"{p2.mention} kazandı!")
    else:
        await kanal.send("Kimse kazanmadı. Oyun devam eder.")

    del games[channel_id]

def hesapla_sonuc(c1, c2):
    # 0: Beraberlik, 1: p1 kazanır, 2: p2 kazanır, -1: devam
    if c1 == c2:
        return 0
    elif c1 == "s" and c2 == "m":
        return 1
    elif c1 == "m" and c2 == "s":
        return 2
    elif c1 == "s" and c2 == "k":
        return -1
    elif c1 == "k" and c2 == "s":
        return -1
    elif c1 == "m" and c2 == "k":
        return -1
    elif c1 == "k" and c2 == "m":
        return -1
    return 0


bot.run(TOKEN)
