import asyncio
import json

import discord
import psycopg2
from discord.ext import commands

config = json.load(open("config.json"))

class Voice(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        conn = None
        conn = psycopg2.connect(host=config["db-addr"], user="postgres", password=config["db-pass"])
        c = conn.cursor()
        guildID = member.guild.id
        c.execute("SELECT voiceChannelID FROM voiceguild WHERE guildID = %s", (guildID,))
        voice=c.fetchone()
        if voice is None:
            pass #self.bot.tPrint("Voice is None")
        else:
            voiceID = voice[0]
            try:
                if after.channel.id == voiceID:
                    c.execute("SELECT * FROM voicechannel WHERE userID = %s", (member.id,))
                    cooldown=c.fetchone()
                    if cooldown is None or not config['large_server']:
                        pass
                    else:
                        await member.send("Du erstellst channel zu schnell und befindest dich nun in einem 15 Sekunden cooldown!")
                        await asyncio.sleep(15)
                    c.execute("SELECT voiceCategoryID FROM voiceguild WHERE guildID = %s", (guildID,))
                    voice=c.fetchone()
                    c.execute("SELECT channelName, channelLimit FROM voiceusersettings WHERE userID = %s", (member.id,))
                    setting=c.fetchone()
                    c.execute("SELECT channelLimit FROM voiceguildsettings WHERE guildID = %s", (guildID,))
                    guildSetting=c.fetchone()
                    if setting is None:
                        name = f"{member.name}'s Tisch"
                        if guildSetting is None:
                            limit = 0
                        else:
                            limit = guildSetting[0]
                    else:
                        if guildSetting is None:
                            name = setting[0]
                            limit = setting[1]
                        elif guildSetting is not None and setting[1] == 0:
                            name = setting[0]
                            limit = guildSetting[0]
                        else:
                            name = setting[0]
                            limit = setting[1]
                    categoryID = voice[0]
                    id = member.id
                    category = self.bot.get_channel(categoryID)
                    channel2 = await member.guild.create_voice_channel(name,category=category)
                    channelID = channel2.id
                    await member.move_to(channel2)
                    await channel2.set_permissions(self.bot.user, connect=True,read_messages=True)
                    await channel2.edit(name= name, user_limit = limit)
                    c.execute("INSERT INTO voicechannel VALUES (%s, %s)", (id,channelID))
                    conn.commit()
                    def check(a,b,c):
                        return len(channel2.members) == 0
                    await self.bot.wait_for('voice_state_update', check=check)
                    await channel2.delete()
                    #await asyncio.sleep(3)
                    c.execute('DELETE FROM voicechannel WHERE userID=%s', (id,))
            except:
                pass #self.bot.tExcept(e)
        conn.commit()
        conn.close()

    @commands.group()
    async def voice(self, ctx):
        pass

    @voice.command()
    async def setup(self, ctx):
        await self.bot.deleteInvoking(ctx.message)
        conn = None
        conn = psycopg2.connect(host=config["db-addr"], user="postgres", password=config["db-pass"])
        c = conn.cursor()
        guildID = ctx.guild.id
        id = ctx.author.id
        if ctx.author.id == config['owner_id']:
            def check(m):
                return m.author.id == ctx.author.id
            await self.bot.send(ctx, "**Du hast 60 Sekunden jede Frage zu beantworten!**")
            await self.bot.send(ctx, "**Möchtest du eine bereits existierende Kategorie und Channel verwenden?**(ja/nein):")
            try:
                answer = await self.bot.wait_for('message', check=check, timeout = 60.0)
            except asyncio.TimeoutError:
                await self.bot.send(ctx, 'Antwort hat zu lang gebraucht!')
            else:
                if answer.content == "nein":
                    await self.bot.send(ctx, f"**Bitte gebe nun den Namen der Kategrie ein, die erstellt werden soll: (z.B. Voice Channels)**")
                    try:
                        category = await self.bot.wait_for('message', check=check, timeout = 60.0)
                    except asyncio.TimeoutError:
                        await self.bot.send(ctx, 'Antwort hat zu lang gebraucht!')
                    else:
                        new_cat = await ctx.guild.create_category_channel(category.content)
                    await self.bot.send(ctx, '**Bitte gib nun den Namen des Sprachchannels ein, den ich erstellen soll: (z.B. Join To Create)**')
                    try:
                        channel = await self.bot.wait_for('message', check=check, timeout = 60.0)
                    except asyncio.TimeoutError:
                        await self.bot.send(ctx, 'Antwort hat zu lang gebraucht!')
                    else:
                        try:
                            channel = await ctx.guild.create_voice_channel(channel.content, category=new_cat)
                            c.execute("SELECT * FROM voiceguild WHERE guildID = %s AND ownerID=%s", (guildID, id))
                            voice=c.fetchone()
                            if voice is None:
                                c.execute ("INSERT INTO voiceguild VALUES (%s, %s, %s, %s)",(guildID,id,channel.id,new_cat.id))
                            else:
                                c.execute ("UPDATE voiceguild SET guildID = %s, ownerID = %s, voiceChannelID = %s, voiceCategoryID = %s WHERE guildID = %s",(guildID,id,channel.id,new_cat.id, guildID))
                            await self.bot.send(ctx, "**Du bist nun eingerichtet und bereit!**")
                        except:
                            await self.bot.send(ctx, "Du hast die Namen nicht richtig eingegeben.\nBitte verwende `.voice setup` nocheinmal!")
                else:
                    await self.bot.send(ctx, f"**Bitte gib nun die ID der Kategorie ein, die du verwenden möchtest:**")
                    try:
                        categoryId = await self.bot.wait_for('message', check=check, timeout = 60.0)
                    except asyncio.TimeoutError:
                        await self.bot.send(ctx, 'Antwort hat zu lang gebraucht!')
                    else:
                        await self.bot.send(ctx, f"**Bitte gib nun die ID des Channels ein, den du verwenden möchtest:**")
                        try:
                            channelId = await self.bot.wait_for('message', check=check, timeout = 60.0)
                        except asyncio.TimeoutError:
                            await self.bot.send(ctx, 'Antwort hat zu lang gebraucht!')
                        else:
                            c.execute("SELECT * FROM voiceguild WHERE guildID = %s AND ownerID=%s", (guildID, id))
                            voice=c.fetchone()
                            if voice is None:
                                c.execute ("INSERT INTO voiceguild VALUES (%s, %s, %s, %s)",(guildID,id,int(channelId.content),int(categoryId.content)))
                            else:
                                c.execute ("UPDATE voiceguild SET guildID = %s, ownerID = %s, voiceChannelID = %s, voiceCategoryID = %s WHERE guildID = %s",(guildID,id,int(channelId.content),int(categoryId.content), guildID))
                            await self.bot.send(ctx, "**Du bist nun eingerichtet und bereit!**")
        else:
            await self.bot.send(ctx, f"Nur der Besitzer des Servers kann diese Einstellung vornehmen!")
        conn.commit()
        conn.close()

    @setup.error
    async def info_error(self, ctx, error):
        print(error)
    
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setCategoryId(self, ctx, newCategoryId = 0):
        await self.bot.deleteInvoking(ctx.message)
        try:
            conn = None
            conn = psycopg2.connect(host=config["db-addr"], user="postgres", password=config["db-pass"])
            c = conn.cursor()
            c.execute ("UPDATE voiceguild SET voiceCategoryID = %s WHERE guildID = %s",(int(newCategoryId), ctx.guild.id))
            conn.commit()
            conn.close()
            await self.bot.send(ctx, "Die ID der Kategorie wurde geupdated!")
        except Exception as e:
            await self.bot.send(ctx, f"Die ID der Kategorie konnte nicht geupdated werden!\n`{e}`")
    
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setChannelId(self, ctx, newChannelId = 0):
        await self.bot.deleteInvoking(ctx.message)
        try:
            conn = None
            conn = psycopg2.connect(host=config["db-addr"], user="postgres", password=config["db-pass"])
            c = conn.cursor()
            c.execute ("UPDATE voiceguild SET voiceChannelID = %s WHERE guildID = %s",(int(newChannelId), ctx.guild.id))
            conn.commit()
            conn.close()
            await self.bot.send(ctx, "Die ID des Channels wurde geupdated!")
        except Exception as e:
            await self.bot.send(ctx, f"Die ID des Channels konnte nicht geupdated werden!\n`{e}`")

    @commands.command()
    @commands.is_owner()
    async def setlimit(self, ctx, num = 0):
        await self.bot.deleteInvoking(ctx.message)
        conn = None
        conn = psycopg2.connect(host=config["db-addr"], user="postgres", password=config["db-pass"])
        c = conn.cursor()
        if ctx.author.id == config['owner_id']:
            c.execute("SELECT * FROM voiceguildsettings WHERE guildID = %s", (ctx.guild.id,))
            voice=c.fetchone()
            if voice is None:
                c.execute("INSERT INTO voiceguildsettings VALUES (%s, %s, %s, %s)", (ctx.guild.id,f"{ctx.author.name}'s channel", 0, 0))
            else:
                c.execute("UPDATE voiceguildsettings SET channelLimit = %s WHERE guildID = %s", (num, ctx.guild.id))
            await self.bot.send(ctx, f"Du hast das Standardlimit für Sprachkanäle des Servers verändert!\nNeu: {num}")
        else:
            await self.bot.send(ctx, f"Nur der besitzer des Bots kann diese Einstellung ändern!")
        conn.commit()
        conn.close()

    @voice.command(aliases=["Lock", "sperren", "beschränken", "abschließen"])
    async def lock(self, ctx):
        await self.bot.deleteInvoking(ctx.message)
        conn = None
        conn = psycopg2.connect(host=config["db-addr"], user="postgres", password=config["db-pass"])
        c = conn.cursor()
        id = ctx.author.id
        c.execute("SELECT voiceID FROM voicechannel WHERE userID = %s", (id,))
        voice=c.fetchone()
        if voice is None:
            await self.bot.send(ctx, f"Du besitzt keinen Channel.")
        else:
            channelID = voice[0]
            role = discord.utils.get(ctx.guild.roles, name='@everyone')
            channel = self.bot.get_channel(channelID)
            await channel.set_permissions(role, connect=False,read_messages=True)
            await self.bot.send(ctx, f'Gesperrt! 🔒')
        conn.commit()
        conn.close()

    @voice.command(aliases=["Unlock", "öffnen", "aufschließen"])
    async def unlock(self, ctx):
        await self.bot.deleteInvoking(ctx.message)
        conn = None
        conn = psycopg2.connect(host=config["db-addr"], user="postgres", password=config["db-pass"])
        c = conn.cursor()
        id = ctx.author.id
        c.execute("SELECT voiceID FROM voicechannel WHERE userID = %s", (id,))
        voice=c.fetchone()
        if voice is None:
            await self.bot.send(ctx, f"Du besitzt keinen Channel.")
        else:
            channelID = voice[0]
            role = discord.utils.get(ctx.guild.roles, name='@everyone')
            channel = self.bot.get_channel(channelID)
            await channel.set_permissions(role, connect=True,read_messages=True)
            await self.bot.send(ctx, f'Entsperrt! 🔓')
        conn.commit()
        conn.close()

    @voice.command(aliases=["Permit", "Allow", "allow", "gewähren", "Whitelist", "whitelist"])
    async def permit(self, ctx, member : discord.Member):
        await self.bot.deleteInvoking(ctx.message)
        conn = None
        conn = psycopg2.connect(host=config["db-addr"], user="postgres", password=config["db-pass"])
        c = conn.cursor()
        id = ctx.author.id
        c.execute("SELECT voiceID FROM voicechannel WHERE userID = %s", (id,))
        voice=c.fetchone()
        if voice is None:
            await self.bot.send(ctx, f"Du besitzt keinen Channel.")
        else:
            channelID = voice[0]
            channel = self.bot.get_channel(channelID)
            await channel.set_permissions(member, connect=True)
            await self.bot.send(ctx, f'Du hast {member.name} Zugriff auf deinen Channel gewährt. ✅')
        conn.commit()
        conn.close()

    @voice.command(aliases=["Reject", "Deny", "verwähren", "Blacklist", "blacklist"])
    async def reject(self, ctx, member : discord.Member):
        await self.bot.deleteInvoking(ctx.message)
        conn = None
        conn = psycopg2.connect(host=config["db-addr"], user="postgres", password=config["db-pass"])
        c = conn.cursor()
        id = ctx.author.id
        guildID = ctx.guild.id
        c.execute("SELECT voiceID FROM voicechannel WHERE userID = %s", (id,))
        voice=c.fetchone()
        if voice is None:
            await self.bot.send(ctx, f"Du besitzt keinen Channel.")
        else:
            channelID = voice[0]
            channel = self.bot.get_channel(channelID)
            for members in channel.members:
                if members.id == member.id:
                    c.execute("SELECT voiceChannelID FROM voiceguild WHERE guildID = %s", (guildID,))
                    voice=c.fetchone()
                    channel2 = self.bot.get_channel(voice[0])
                    await member.move_to(channel2)
            await channel.set_permissions(member, connect=False,read_messages=True)
            await self.bot.send(ctx, f'Du hast {member.name} Zugriff auf deinen Channel verwährt. ❌')
        conn.commit()
        conn.close()

    @voice.command(aliases=["Limit", "Anzahl", "anzahl", "Max", "max"])
    async def limit(self, ctx, limit=0):
        await self.bot.deleteInvoking(ctx.message)
        conn = None
        conn = psycopg2.connect(host=config["db-addr"], user="postgres", password=config["db-pass"])
        c = conn.cursor()
        id = ctx.author.id
        c.execute("SELECT voiceID FROM voicechannel WHERE userID = %s", (id,))
        voice=c.fetchone()
        if voice is None:
            await self.bot.send(ctx, f"Du besitzt keinen Channel.")
        else:
            channelID = voice[0]
            channel = self.bot.get_channel(channelID)
            await channel.edit(user_limit = limit)
            await self.bot.send(ctx, f'Du hast das Limit auf {limit} Benutzer gestellt!')
            c.execute("SELECT channelName FROM voiceusersettings WHERE userID = %s", (id,))
            voice=c.fetchone()
            if voice is None:
                c.execute("INSERT INTO voiceusersettings VALUES (%s, %s, %s)", (id,f'{ctx.author.name}',limit))
            else:
                c.execute("UPDATE voiceusersettings SET channelLimit = %s WHERE userID = %s", (limit, id))
        conn.commit()
        conn.close()

    @voice.command(aliases=["Name", "umbennen"])
    async def name(self, ctx,*, name = ""):
        await self.bot.deleteInvoking(ctx.message)
        if name == "":
            name = f"{ctx.author.name}'s Tisch"
        conn = None
        conn = psycopg2.connect(host=config["db-addr"], user="postgres", password=config["db-pass"])
        c = conn.cursor()
        id = ctx.author.id
        c.execute("SELECT voiceID FROM voicechannel WHERE userID = %s", (id,))
        voice=c.fetchone()
        if voice is None:
            await self.bot.send(ctx, f"Du besitzt keinen Channel.")
        else:
            channelID = voice[0]
            channel = self.bot.get_channel(channelID)
            await channel.edit(name = name)
            await self.bot.send(ctx, f'Du hast den Channelnamen zu `{name}` geändert!')
            c.execute("SELECT channelName FROM voiceusersettings WHERE userID = %s", (id,))
            voice=c.fetchone()
            if voice is None:
                c.execute("INSERT INTO voiceusersettings VALUES (%s, %s, %s)", (id,name,0))
            else:
                c.execute("UPDATE voiceusersettings SET channelName = %s WHERE userID = %s", (name, id))
        conn.commit()
        conn.close()

    @voice.command(aliases=["Claim", "beanspruchen"])
    async def claim(self, ctx):
        await self.bot.deleteInvoking(ctx.message)
        x = False
        conn = None
        conn = psycopg2.connect(host=config["db-addr"], user="postgres", password=config["db-pass"])
        c = conn.cursor()
        channel = ctx.author.voice.channel
        if channel == None:
            await self.bot.send(ctx, f"Du befindest dich in keinen Channel.")
        else:
            id = ctx.author.id
            c.execute("SELECT userID FROM voicechannel WHERE voiceID = %s", (channel.id,))
            voice=c.fetchone()
            if voice is None:
                await self.bot.send(ctx, f"Du kannst diesen Channel nicht besitzen!")
            else:
                for data in channel.members:
                    if data.id == voice[0]:
                        owner = ctx.guild.get_member(voice [0])
                        await self.bot.send(ctx, f"Dieser Channel ist bereits im Besitz von {owner.mention}!")
                        x = True
                if x == False:
                    await self.bot.send(ctx, f"Du bist nun der Besitzer dieses Channels!")
                    c.execute("UPDATE voicechannel SET userID = %s WHERE voiceID = %s", (id, channel.id))
                    
                    c.execute("SELECT channelName, channelLimit FROM voiceusersettings WHERE userID = %s", (ctx.author.id,))
                    settings=c.fetchone()
                    if not settings is None:
                        await channel.edit(name=settings[0], user_limit=settings[1])
            conn.commit()
            conn.close()

def setup(bot):
    bot.add_cog(Voice(bot))
