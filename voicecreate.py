import discord
from discord.ext import commands
import json
import traceback
import sys
import psycopg2

client = discord.Client()

config = json.load(open("config.json"))

bot = commands.Bot(command_prefix=json.load(open('config.json'))['bot_prefix'])

initial_extensions = ['cogs.voice']

def getBotMessageChannel(guildID):
    rtrn = 0
    try:
        conn = None
        conn = psycopg2.connect(host=json.load(open("config.json"))["db-addr"], user="postgres", password=json.load(open("config.json"))["db-pass"])
        c = conn.cursor()
        c.execute("SELECT botmessagechannel FROM voiceguildsettings WHERE guildID = %s", (guildID,))
        rtrn = c.fetchone()
        conn.commit()
        c.close()
    except Exception as e:
        print("Die Channel ID der konnte nicht aus der Datenbank empfangen werden.\n{e}")
    return bot.get_channel(rtrn)

async def deleteInvoking(message):
    if config["deleteInvokingMessageTimeout"] >= 0:
        try:
            await message.delete(delay=config["deleteInvokingMessageTimeout"])
        except Exception as e:
            print(f"Couldn't delete invoking message:\n`{e}`")
    channel = getBotMessageChannel(message.guild.id)
    if channel is None:
        channel = message.channel
    else:
        embed = discord.Embed(
            title = f'{message.author.mention} hat in {message.channel.name} ausgeführt:',
            description = f"{message.content}"
        )
        await channel.send(embed=embed)

setattr(bot, 'deleteInvoking', deleteInvoking)

async def send(ctx, embed):
    channel = getBotMessageChannel(ctx.guild.id)
    if channel is None:
        channel = ctx.channel
    if config["deleteBotMessageTimeout"] < 1:
        try:
            if type(embed) is discord.Embed:
                await channel.send(embed=embed)
            else:
                await channel.send(embed)
        except Exception as e:
            print(f"Couldn't delete send message:\n`{e}`")
    else:
        try:
            if type(embed) is discord.Embed:
                await channel.send(embed=embed, delete_after=config["deleteBotMessageTimeout"])
            else:
                await channel.send(embed, delete_after=config["deleteBotMessageTimeout"])
        except Exception as e:
            print(f"Couldn't delete send message:\n`{e}`")
setattr(bot, 'send', send)

if __name__ == '__main__':
    for extension in initial_extensions:
        try:
            bot.load_extension(extension)
        except Exception as e:
            print(f'Failed to load extension {extension}.', file=sys.stderr)
            traceback.print_exc()

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

@bot.command()
@bot.is_owner()
async def setBotChannel(ctx, *, botChannelId = 0):
    if botChannelId == 0:
        await send(ctx, "Bitte gib eine channel id an!")
        return
    try:
        conn = None
        conn = psycopg2.connect(host=config["db-addr"], user="postgres", password=config["db-pass"])
        c = conn.cursor()

        c.execute("SELECT botmessagechannel FROM voiceguildsettings WHERE guildID = %s", (ctx.guild.id,))
        botmessagechannel = c.fetchone()
        if botmessagechannel is None:
            c.execute("INSERT INTO voiceguildsettings VALUES (%s, %s, %s, %s)", (ctx.guild.id,f"{ctx.author.name}'s channel", 0, int(botChannelId)))
        else:
            c.execute ("UPDATE voiceguildsettings SET botmessagechannel = %s WHERE guildID = %s",(int(botChannelId), ctx.guild.id))

        conn.commit()
        conn.close()
        await send(ctx, "Die ID des Botchannel wurde geupdated!")
    except Exception as e:
        await send(ctx, f"Ich konnte die ID des Botchannel nicht updated!\n`{e}`")

bot.run(json.load(open('config.json'))['bot_token'])
