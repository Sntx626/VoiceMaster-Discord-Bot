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

def getBotMessageChannel(guildID, channel):
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
    getChannel = bot.get_channel(rtrn[0])
    if rtrn == None:
        return channel
    else:
        return getChannel

async def deleteInvoking(message):
    if config["deleteInvokingMessageTimeout"] >= 0:
        try:
            await message.delete(delay=config["deleteInvokingMessageTimeout"])
        except Exception as e:
            print(f"Couldn't delete invoking message:\n`{e}`")
    channel = getBotMessageChannel(message.guild.id, message.channel)
    if channel is None:
        channel = message.channel
    else:
        embed = discord.Embed(
            title = f'{message.content}',
            description = f"... wurde von <@!{message.author.id}> in #{message.channel.name} ausgeführt."
        )
        await channel.send(embed=embed)

setattr(bot, 'deleteInvoking', deleteInvoking)

async def send(ctx, input):
    channel = getBotMessageChannel(ctx.guild.id, ctx.channel)
    if channel == None:
        channel = ctx.channel
    if config["deleteBotMessageTimeout"] < 1:
        try:
            if type(input) is discord.Embed:
                await ctx.send(embed=input, delete_after=config["deleteBotMessageTimeout"])
                await channel.send(embed=input)
            else:
                embed = discord.Embed(
                    title = f"{input}",
                    description = f'{ctx.author.mention}'
                )
                await ctx.send(embed=embed, delete_after=config["deleteBotMessageTimeout"])
                await channel.send(embed=embed)
        except Exception as e:
            print(f"Couldn't delete send message:\n`{e}`")
    else:
        try:
            if type(input) is discord.Embed:
                await ctx.send(embed=input, delete_after=config["deleteBotMessageTimeout"])
                await channel.send(embed=input)
            else:
                embed = discord.Embed(
                    title = f"{input}",
                    description = f'{ctx.author.mention}'
                )
                await ctx.send(embed=embed, delete_after=config["deleteBotMessageTimeout"])
                await channel.send(embed=embed)
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
async def setBotChannel(ctx, *, botChannelId = 0):
    if not ctx.author.id == config["owner_id"]:
        await send(ctx, "Du bist nicht berechtigt diese Einstellung vorzunehmen!")
        return
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

@bot.command()
async def Reset(ctx, *, arg : str):
    if arg == "True" and ctx.author.id == config["owner_id"]:  
        try:
            conn = None
            conn = psycopg2.connect(host=json.load(open("config.json"))["db-addr"], user="postgres", password=json.load(open("config.json"))["db-pass"])
            c = conn.cursor()
        
            c.execute('drop table voicechannel')
            conn.commit()

            c.execute('create table voicechannel(userID bigint, voiceID bigint)')
            conn.commit()

            c.close()

            await send(ctx, "Die aktuelle Channelliste wurde zurückgesetzt!")
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)

bot.run(json.load(open('config.json'))['bot_token'])
