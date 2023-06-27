import os.path
import os
import discord
from discord.ext import commands
import aiosqlite
import random
import asyncio
from easy_pil import *
import io
import requests
import json
import datetime
from googletrans import Translator
from quotes import Quotes
import time
import schedule



intents = discord.Intents.all()
intents.members = True

config_file_path = os.getcwd() + "/config.json"

try:
    with open(config_file_path) as f:
        configData = json.load(f)
except IOError:
    print(f"Impossible d'ouvrir le fichier {config_file_path}")
    configData = {}

token = configData["Token"]
prefix = configData["Prefix"]
api_key = configData["api_weather"]


bot = commands.Bot(command_prefix='/', case_insensitive=True, intents=intents)
translator = Translator()


def restart_bot():
    python = "/usr/bin/python3"
    script = "/home/vsalk/Bureau/AlkuBot/main.py"
    os.execl(python, python, script)

schedule.every().day.at("04:00").do(restart_bot)
schedule.every().day.at("08:00").do(restart_bot)
schedule.every().day.at("12:00").do(restart_bot)
schedule.every().day.at("16:00").do(restart_bot)
schedule.every().day.at("20:00").do(restart_bot)
schedule.every().day.at("00:00").do(restart_bot)


@bot.event
async def on_ready():
    print("le bot est prêt !")
    await bot.change_presence(activity=discord.Game("être en bêta..."))
    total_members = 0
    bot.db = await aiosqlite.connect("level.db")
    await asyncio.sleep(3)
    async with bot.db.cursor() as cursor:
        await cursor.execute("CREATE TABLE IF NOT EXISTS levels (level INTEGER, xp INTEGER, user INTEGER, guild INTEGER)")
        await cursor.execute("CREATE TABLE IF NOT EXISTS levelSettings (levelsys BOOL, rols INTEGER, levelreq IINTEGER, guild INTEGER)")
    if not os.path.exists(db_folder):
        os.makedirs(db_folder)
    if not os.path.exists(db_jr_folder):
        os.makedirs(db_jr_folder)
    if not os.path.exists(db_r_folder):
        os.makedirs(db_r_folder)
    try:
        await bot.tree.sync()
        print(f"Commandes_Synchro")
    except Exception as e:
        print(e)
    bot.remove_command("help")
    for guild in bot.guilds:
        total_members += guild.member_count
    print('Présent dans {0} serveurs.'.format(len(bot.guilds)))
    print('Nombre total d\'utilisateurs : {0}'.format(total_members))
    while True:
        schedule.run_pending()
        await asyncio.sleep(1)


#début système level

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # Gestion du système de niveaux
    author = message.author
    guild = message.guild
    async with bot.db.cursor() as cursor:
        await cursor.execute("SELECT levelsys FROM levelSettings WHERE guild = ?", (guild.id,))
        levelsys = await cursor.fetchone()
        if levelsys and not levelsys[0]:
            return
        await cursor.execute("SELECT xp FROM levels WHERE user = ? AND guild = ?", (author.id, guild.id))
        xp = await cursor.fetchone()
        await cursor.execute("SELECT level FROM levels WHERE user = ? AND guild = ?", (author.id, guild.id))
        level = await cursor.fetchone()

        if not xp or not level:
            await cursor.execute("INSERT INTO levels (level, xp, user, guild) VALUES (?, ?, ?, ?)", (0, 0, author.id, guild.id,))
            await bot.db.commit()

        try:
            xp = xp[0]
            level = level[0]
        except TypeError:
            xp = 0
            level = 0

        if level < 5:
            xp += random.randint(1, 3)
            await cursor.execute("UPDATE levels SET xp = ? WHERE user = ? AND guild = ?", (xp, author.id, guild.id,))
        else:
            rand = random.randint(1, (level // 4))
            if rand == 1:
                xp += random.randint(1, 3)
                await cursor.execute("UPDATE levels SET xp = ? WHERE user = ? AND guild = ?", (xp, author.id, guild.id,))
        if xp >= (100 * level):
            level += 1
            await cursor.execute("UPDATE levels SET level = ? WHERE user = ? AND guild = ?", (level, author.id, guild.id,))
            await cursor.execute("UPDATE levels SET xp = ? WHERE user = ? AND guild = ?", (0, author.id, guild.id,))
            await message.channel.send(f"{author.mention} est maintenant niveau **{level}**!")
            await bot.db.commit()

    # Gestion des mots bloqués
    if "Modérateurs" not in [role.name for role in message.author.roles]:
        server_id = str(message.guild.id)
        block_words_file = os.path.join(db_folder, f"{server_id}.db")

        if os.path.exists(block_words_file):
            with open(block_words_file, "r") as f:
                block_words = [line.strip() for line in f.readlines()]
        else:
            block_words = []

        for text in block_words:
            if text in message.content.lower():
                await message.delete()
                return


    await bot.process_commands(message)


@bot.tree.command(name="level", description="vous donne votre niveau",)
async def level(interaction: discord.Interaction):
        member = interaction.user
        async with bot.db.cursor() as cursor:
            await cursor.execute("SELECT levelsys FROM levelSettings WHERE guild = ?", (interaction.guild.id,))
            levelsys = await cursor.fetchone()
            if levelsys and not levelsys[0]:
                return
            await cursor.execute("SELECT xp FROM levels WHERE user = ? AND guild = ?", (member.id, interaction.guild.id))
            xp = await cursor.fetchone()
            await cursor.execute("SELECT level FROM levels WHERE user = ? AND guild = ?", (member.id, interaction.guild.id))
            level = await cursor.fetchone()

            if not xp or level:
                await cursor.execute("INSERT INTO levels (level, xp, user, guild) VALUES (?, ?, ?, ?)", (0, 0, member.id, interaction.guild.id,))



            try:
                xp = xp[0]
                level = level[0]
            except TypeError:
                xp = 0
                level = 0



            user_data = {
                "name": f"{member.name}#{member.discriminator}",
                "xp": xp,
                "level": level,
                "next_leve_up": 100,
                "percentage": xp / level,
            }

        background = Editor(Canvas((900, 300), color="#364C63"))
        profile_picture = await load_image_async(str(member.avatar.url))
        profile = Editor(profile_picture).resize((150, 150)).circle_image()

        poppins = Font.poppins(size=40)
        poppins_small = Font.poppins(size=30)

        card_right_shape = [(600, 0), (750, 300), (900, 300), (900, 0)]

        background.polygon(card_right_shape, color="#364C63")
        background.paste(profile, (30, 30))

        background.rectangle((30, 220), width=650, height=40, color="#FFFFFF")
        background.bar((30, 220), max_width=650, height=40, percentage=user_data["percentage"], color="#EC8C07",)
        background.text((200, 40), user_data["name"], font=poppins, color="#FFFFFF")

        background.rectangle((200, 100), width=350, height=2, fill="#FFFFFF")
        background.text(
            (200, 130),
            f"Level - {user_data['level']} | XP - {user_data['xp']} / {100 * level}",
            font=poppins_small,
            color="#FFFFFF",
        )

        file = discord.File(fp=background.image_bytes, filename="levelcard.png")
        await interaction.response.send_message(file=file)




#fin système level



#début système d'ajout de salon de bienvenue

db_jr_folder = "join_remove_channel"

@bot.tree.command(name="add_join", description="cette commande permet d'ajouter les salons de bienvenue")
async def add_join(interaction: discord.Interaction, channel: str):
    if "Administrateurs" in [role.name for role in interaction.user.roles]:
        server_id = str(interaction.guild.id)
        join_remove_file = os.path.join(db_jr_folder, f"{server_id}.db")

        if os.path.exists(join_remove_file):
            with open(join_remove_file, "r") as f:
                join_channel = [line.strip() for line in f.readlines()]

            if channel.lower() not in join_channel:
                join_channel.append(channel.lower())
                with open(join_remove_file, "w") as f:
                    f.write("\n".join(join_channel))
                await interaction.response.send_message(f"{channel} vient d'être ajouté à la liste des salons de bienvenue.")
            else:
                await interaction.response.send_message(f"{channel} est déjà dans la liste des salons de bienvenue.")
        else:
            with open(join_remove_file, "w") as f:
                f.write(channel.lower())
            await interaction.response.send_message(f"{channel} vient d'être ajouté à la liste des salons de bienvenue.")
    else:
        await interaction.response.send_message("Tu ne peux pas utiliser cette commande !")

@bot.tree.command(name="remove_join", description="cette commande permet d'enlever les salons de bienvenue")
async def remove_join(interaction: discord.Interaction, channel: str):
    if "Administrateurs" in [role.name for role in interaction.user.roles]:
        server_id = str(interaction.guild.id)
        join_remove_file = os.path.join(db_jr_folder, f"{server_id}.db")

        if os.path.exists(join_remove_file):
            with open(join_remove_file, "r") as f:
                join_channel = [line.strip() for line in f.readlines()]

            if channel.lower() in join_channel:
                join_channel.remove(channel.lower())
                with open(join_remove_file, "w") as f:
                    f.write("\n".join(join_channel))
                await interaction.response.send_message(f"{channel} vient d'être enlevé de la liste des salons de bienvenue.")
            else:
                await interaction.response.send_message(f"{channel} n'est pas dans la liste des salons de bienvenue.")
        else:
            await interaction.response.send_message("Il n'y a pas de salons de bienvenue pour ce serveur.")
    else:
        await interaction.response.send_message("Tu ne peux pas utiliser cette commande !")

#fin système d'ajout de salon de bienvenue

#début système d'ajout de salon d'au revoir

db_r_folder = "remove_channel"

@bot.tree.command(name="add_remove", description="cette commande permet d'ajouter les salons au revoir")
async def add_remove(interaction: discord.Interaction, channel: str):
    if "Administrateurs" in [role.name for role in interaction.user.roles]:
        server_id = str(interaction.guild.id)
        remove_file = os.path.join(db_r_folder, f"{server_id}.db")

        if os.path.exists(remove_file):
            with open(remove_file, "r") as f:
                remove_channel = [line.strip() for line in f.readlines()]

            if channel.lower() not in remove_channel:
                remove_channel.append(channel.lower())
                with open(remove_file, "w") as f:
                    f.write("\n".join(remove_channel))
                await interaction.response.send_message(f"{channel} vient d'être ajouté à la liste des salons d'au revoir.")
            else:
                await interaction.response.send_message(f"{channel} est déjà dans la liste des salons d'au revoir.")
        else:
            with open(remove_file, "w") as f:
                f.write(channel.lower())
            await interaction.response.send_message(f"{channel} vient d'être ajouté à la liste des salons d'au revoir.")
    else:
        await interaction.response.send_message("Tu ne peux pas utiliser cette commande !")

@bot.tree.command(name="remove_remove", description="cette commande permet d'enlever les salons d'au revoir")
async def remove_remove(interaction: discord.Interaction, channel: str):
    if "Administrateurs" in [role.name for role in interaction.user.roles]:
        server_id = str(interaction.guild.id)
        remove_file = os.path.join(db_r_folder, f"{server_id}.db")

        if os.path.exists(remove_file):
            with open(remove_file, "r") as f:
                remove_channel = [line.strip() for line in f.readlines()]

            if channel.lower() in remove_channel:
                remove_channel.remove(channel.lower())
                with open(remove_file, "w") as f:
                    f.write("\n".join(remove_channel))
                await interaction.response.send_message(f"{channel} vient d'être enlevé de la liste des salons d'au revoir.")
            else:
                await interaction.response.send_message(f"{channel} n'est pas dans la liste des salons d'au revoir.")
        else:
            await interaction.response.send_message("Il n'y a pas de salons d'au revoir pour ce serveur.")
    else:
        await interaction.response.send_message("Tu ne peux pas utiliser cette commande !")

#fin système d'ajout de salon d'au revoir

#début message bienvenue

@bot.tree.command(name="helpjoin", description="vous aide pour les commandes d'arrivants",)
async def helpjoin(interaction: discord.Interaction):
    await interaction.response.send_message("il faut utiliser la commande add_join/remove_join pour ajouter/enlever des salons d'arrivants")

@bot.event
async def on_member_join(member: discord.Member):
    guild = member.guild
    server_id = str(guild.id)
    join_remove_file = os.path.join(db_jr_folder, f"{server_id}.db")

    if os.path.exists(join_remove_file):
        with open(join_remove_file, "r") as f:
            join_channel = [line.strip() for line in f.readlines()]

        for channel_name in join_channel:
            channel = discord.utils.get(guild.channels, name=channel_name)
            if channel is not None:
                await channel.send(f"{member.mention} nous rejoint !")

                user_data = {
                    "name": f"{member.name}#{member.discriminator}",
                }

                background = Editor(Canvas((700, 200), color="#364C63"))
                profile_picture = await load_image_async(str(member.avatar.url))
                profile = Editor(profile_picture).resize((150, 150)).circle_image()

                poppins = Font.poppins(size=40)
                poppins_small = Font.poppins(size=30)

                card_right_shape = [(600, 0), (750, 300), (900, 300), (900, 0)]

                background.polygon(card_right_shape, color="#364C63")
                background.paste(profile, (30, 30))

                background.text((200, 40), user_data["name"], font=poppins, color="#FFFFFF")

                background.rectangle((200, 100), width=350, height=2, fill="#FFFFFF")
                background.text(
                    (200, 130),
                    f"Bienvenue {member.name} #{member.discriminator} !",
                    font=poppins_small,
                    color="#FFFFFF",
                )

                with io.BytesIO() as image_binary:
                    background.save(image_binary, format='PNG')
                    image_binary.seek(0)
                    file = discord.File(fp=image_binary, filename="welcomecard.png")
                    await channel.send(file=file)
            else:
                print(f"{channel_name} not found in server {server_id}")
    else:
        print(f"No join_remove_file found for server {server_id}")


#fin message de bienvenue

#début système de départ


@bot.tree.command(name="helpremove", description="vous aide pour les commandes de départs",)
async def helpremove(interaction: discord.Interaction):
    await interaction.response.send_message("il faut utiliser la commande add_remove pour ajouter des salons d'au revoir.")

@bot.event
async def on_member_remove(member: discord.Member):
    guild = member.guild
    server_id = str(guild.id)
    join_remove_file = os.path.join(db_r_folder, f"{server_id}.db")

    if os.path.exists(join_remove_file):
        with open(join_remove_file, "r") as f:
            join_channel = [line.strip() for line in f.readlines()]

        for channel_name in join_channel:
            channel = discord.utils.get(guild.channels, name=channel_name)
            if channel is not None:
                await channel.send(f"Au revoir {member.mention}...")

                user_data = {
                    "name": f"{member.name}#{member.discriminator}",
                }

                background = Editor(Canvas((700, 200), color="#364C63"))
                profile_picture = await load_image_async(str(member.avatar.url))
                profile = Editor(profile_picture).resize((150, 150)).circle_image()

                poppins = Font.poppins(size=40)
                poppins_small = Font.poppins(size=30)

                card_right_shape = [(600, 0), (750, 300), (900, 300), (900, 0)]

                background.polygon(card_right_shape, color="#364C63")
                background.paste(profile, (30, 30))

                background.text((200, 40), user_data["name"], font=poppins, color="#FFFFFF")

                background.rectangle((200, 100), width=350, height=2, fill="#FFFFFF")
                background.text(
                    (200, 130),
                    f"{member.name} est parti :[",
                    font=poppins_small,
                    color="#FFFFFF",
                )

                with io.BytesIO() as image_binary:
                    background.save(image_binary, format='PNG')
                    image_binary.seek(0)
                    file = discord.File(fp=image_binary, filename="leavecard.png")
                    await channel.send(file=file)

#fin système de départ

# début du code des commandes de réponse


@bot.tree.command(name="hello", description="l'alkubot vous passe le bonjour",)
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message("Hello!")

@bot.tree.command(name="alkudev", description="alkudev c'est quoi ?",)
async def alkudev(interaction: discord.Interaction):
    await interaction.response.send_message("AlkuDev est une équide de développeur, nous travaillons sur beaucoup de projets !")

@bot.tree.command(name="lth", description="los-tortillas-hermanos",)
async def tortillas(interaction: discord.Interaction):
    await interaction.response.send_message("Los Tortillas Hermanos is always watching you")

#fin du code des commandes de réponse

#début react role member

@bot.tree.command(name="helpreact", description="vous aide pour utiliser les commandes de reaction rôles",)
async def helpreact(interaction: discord.Interaction):
    await interaction.response.send_message("il faut que le rôle membre soit écrit ''Membres'' pour que l'attribution de rôle fonctionne")


@bot.tree.command(name="reaction", description="cette commande permet d'obtenir le rôle membres",)
async def reaction(interaction: discord.Interaction):
    message = "Réagis à ce message pour obtenir le rôle."
    react_message = await interaction.channel.send(message)
    emoji = "✅"
    await react_message.add_reaction(emoji)


@bot.event
async def on_raw_reaction_add(payload):
    guild = discord.utils.find(lambda g: g.id == payload.guild_id, bot.guilds)

    if payload.emoji.name == "✅":
        role = discord.utils.get(guild.roles, name="Membres")
        if role is not None:
            member = discord.utils.find(lambda m: m.id == payload.user_id, guild.members)
            if member is not None:
                await member.add_roles(role)



#fin react role member

#début commande météo


base_url = "http://api.openweathermap.org/data/2.5/weather?"
langue = "fr"

@bot.tree.command(name="meteo", description="cette commande vous donne la météo",)
async def meteo(interaction: discord.Interaction, *, city: str):
    city_name = city
    complete_url = base_url + "appid=" + api_key + "&q=" + city_name
    response = requests.get(complete_url)
    x = response.json()
    channel = interaction.channel

    if x["cod"] != "404":
        async with channel.typing():
            y = x["main"]
            current_temperature = y["temp"]
            current_temperature_celsiuis = str(round(current_temperature - 273.15))
            current_humidity = y["humidity"]
            z = x["weather"]

            weather_description = z[0]["description"]
            embed = discord.Embed(title=f"La météo de {city_name}",
                                  color=interaction.guild.me.top_role.color,
                                  timestamp=datetime.datetime.now(), )

            embed.add_field(name="Description", value=f"**{weather_description}**", inline=False)
            embed.add_field(name="Température", value=f"**{current_temperature_celsiuis}°C**", inline=False)
            embed.add_field(name="Humidité", value=f"**{current_humidity}%**", inline=False)
            embed.set_thumbnail(url="https://i.ibb.co/CMrsxdX/weather.png")
            embed.set_footer(text=f"Demandé par {interaction.user.name}")

            await interaction.response.send_message("On parle de la pluie et du beau temps ;]", embed=embed)
    else:
        await interaction.response.send_message("Je ne connais pas cette ville :[")

#fin commande météo

#début modération

db_folder = "block_words"

@bot.tree.command(name="helpbw", description="vous aide à utiliser les commandes pour bannir des mots")
async def helpbw(interaction: discord.Interaction):
    await interaction.response.send_message("En utilisant la commande 'add_bw' il est possible d'ajouter des mots bannis, pour l'instant vous devez avoir le rôle 'Modérateurs' pour executer ces commandes, mais bientôt il y aura des commandes d'ajout de rôle")



@bot.tree.command(name="add_bw", description="cette commande permet d'ajouter des mots interdits")
async def add_bw(interaction: discord.Interaction, word: str):
    if "Modérateurs" in [role.name for role in interaction.user.roles]:
        server_id = str(interaction.guild.id)
        block_words_file = os.path.join(db_folder, f"{server_id}.db")

        if os.path.exists(block_words_file):
            with open(block_words_file, "r") as f:
                block_words = [line.strip() for line in f.readlines()]

            if word.lower() not in block_words:
                block_words.append(word.lower())
                with open(block_words_file, "w") as f:
                    f.write("\n".join(block_words))
                await interaction.response.send_message(f"{word} vient d'être ajouté à la liste des mots interdits.")
            else:
                await interaction.response.send_message(f"{word} est déjà dans la liste des mots interdits.")
        else:
            with open(block_words_file, "w") as f:
                f.write(word.lower())
            await interaction.response.send_message(f"{word} vient d'être ajouté à la liste des mots interdits.")
    else:
        await interaction.response.send_message("Tu ne peux pas utiliser cette commande !")


@bot.tree.command(name="remove_bw", description="cette commande permet d'enlever des mots interdits")
async def remove_bw(interaction: discord.Interaction, word: str):
    if "Modérateurs" in [role.name for role in interaction.user.roles]:
        server_id = str(interaction.guild.id)
        block_words_file = os.path.join(db_folder, f"{server_id}.db")

        if os.path.exists(block_words_file):
            with open(block_words_file, "r") as f:
                block_words = [line.strip() for line in f.readlines()]

            if word.lower() in block_words:
                block_words.remove(word.lower())
                with open(block_words_file, "w") as f:
                    f.write("\n".join(block_words))
                await interaction.response.send_message(f"{word} vient d'être enlevé de la liste des mots interdits.")
            else:
                await interaction.response.send_message(f"{word} n'est pas dans la liste des mots interdits.")
        else:
            await interaction.response.send_message("Il n'y a pas de mots interdits pour ce serveur.")
    else:
        await interaction.response.send_message("Tu ne peux pas utiliser cette commande !")


#fin modération

#début commande help

@bot.tree.command(name="help", description="liste de toutes les commandes",)
async def help(interaction: discord.Interaction):
    names = [command.name for command in bot.tree.get_commands()]
    available_commands = "\n".join(names)
    embed = discord.Embed(title=f"Commandes ({len(names)}):", description=available_commands)
    embed.set_footer(text=f"c'est une belle liste ça")
    await interaction.response.send_message(embed=embed)

#fin commande help

#début commande translation

#début translate fr
@bot.tree.command(name="translate_fr", description="vous permet de traduire n'importe quelle langue en français")
async def translate_fr(interaction: discord.Interaction, text_to_translate: str = None):
    if text_to_translate is None:
        await interaction.response.send_message("Usage: /translate_fr <text_to_translate>")
        return

    translated_text = translator.translate(text_to_translate, dest='fr').text

    embed = discord.Embed(title="Traduction FR", color=0xffa500)
    embed.add_field(name="Texte original", value=f"{interaction.user.mention} a écrit: {text_to_translate}", inline=False)
    embed.add_field(name="Texte traduit", value=translated_text, inline=False)

    await interaction.response.send_message(embed=embed)
#fin translate fr

#début translate en
@bot.tree.command(name="translate_en", description="with this commands you can translate any language to english")
async def translate_en(interaction: discord.Interaction, text_to_translate: str = None):
    if text_to_translate is None:
        await interaction.response.send_message("Usage: /translate_en <text_to_translate>")
        return

    translated_text = translator.translate(text_to_translate, dest='en').text

    embed = discord.Embed(title="Translation EN", color=0xffa500)
    embed.add_field(name="Original text", value=f"{interaction.user.mention} wrote: {text_to_translate}", inline=False)
    embed.add_field(name="Translation", value=translated_text, inline=False)

    await interaction.response.send_message(embed=embed)
#fin translate en

#début translate es
@bot.tree.command(name="translate_es", description="con estos comandos puedes traducir cualquier idioma al ingles")
async def translate_es(interaction: discord.Interaction, text_to_translate: str = None):
    if text_to_translate is None:
        await interaction.response.send_message("Usage: /translate_es <text_to_translate>")
        return

    translated_text = translator.translate(text_to_translate, dest='es').text

    embed = discord.Embed(title="Traducción ES", color=0xffa500)
    embed.add_field(name="Texto original", value=f"{interaction.user.mention} escribió: {text_to_translate}", inline=False)
    embed.add_field(name="Traducción", value=translated_text, inline=False)

    await interaction.response.send_message(embed=embed)
#fin translate es

#début translate ko
@bot.tree.command(name="translate_ko", description="이 명령으로 모든 언어를 영어로 번역할 수 있습니다.")
async def translate_ko(interaction: discord.Interaction, text_to_translate: str = None):
    if text_to_translate is None:
        await interaction.response.send_message("Usage: /translate_ko <text_to_translate>")
        return

    translated_text = translator.translate(text_to_translate, dest='ko').text

    embed = discord.Embed(title="번역 Ko", color=0xffa500)
    embed.add_field(name="원문", value=f"{interaction.user.mention} 썼다: {text_to_translate}", inline=False)
    embed.add_field(name="번역", value=translated_text, inline=False)

    await interaction.response.send_message(embed=embed)
#fin translate ko

#fin commande translation

#début commande quotes

@bot.tree.command(name="citation", description="vous donne une citation au hasard")
async def citation(interaction: discord.Interaction):
    quote = Quotes()
    citation = quote.random()

    embed = discord.Embed(title="Citation", color=0xffa500)
    embed.add_field(name="", value=f"{interaction.user.mention} a demandé: {citation}", inline=False)

    await interaction.response.send_message(embed=embed)

#fin commande quotes

#début commande ping

@bot.tree.command(name="ping", description="vous donne le ping du bot")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f'pong :ping_pong: {round (bot.latency * 1000)} ms')

#fin commande ping

#début commande sondage

@bot.tree.command(name="sondage", description="vous permet de faire un beau sondage")
async def sondage(interaction: discord.Interaction, question: str, timec: int):
    if question is None:
        await interaction.response.send_message("il faut mettre tous les paramètres comme ça /sondage question temps")
        return

    embed = discord.Embed(title="Sondage", color=0xffa500)
    embed.add_field(name="", value=f"{interaction.user.mention} a posé la question: {question}", inline=False)
    embed.set_footer(text=f"Le sondage dure {timec}s")

    emoji_ok = "✅"
    emoji_no = "❎"

    react_embed = await interaction.channel.send(embed=embed)
    await react_embed.add_reaction(emoji_ok)
    await react_embed.add_reaction(emoji_no)

    ok_count = 0
    no_count = 0

    for i in range(timec):
        time.sleep(1)
        timec -= 1
        react_embed = await interaction.channel.fetch_message(react_embed.id)
        for reaction in react_embed.reactions:
            if reaction.emoji == emoji_ok:
                ok_count = reaction.count - 1
            elif reaction.emoji == emoji_no:
                no_count = reaction.count - 1

    if ok_count > no_count:
        await interaction.channel.send(f"Les {timec}s du sondage sont écoulés donc l'emoji '✅' gagne avec {ok_count} votes!")
    elif no_count > ok_count:
        await interaction.channel.send(f"Les {timec}s du sondage sont écoulés donc l'emoji '❎' gagne avec {no_count} votes!")
    else:
        await interaction.channel.send(f"Les {timec}s du sondage sont écoulés mais il n'y a pas de gagnant!")



#fin commande sondage

bot.run(token)