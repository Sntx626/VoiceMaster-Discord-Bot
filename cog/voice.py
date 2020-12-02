import asyncio
import json

import discord
from discord.ext import commands

config = json.load(open("config.json"))["VoiceMaster-Discord-Bot"]

async def askIfNew(self, ctx, check):
    await self.client.send(ctx, "**Möchtest du eine bereits existierende Kategorie und Channel verwenden?**(ja/nein):")
    try:
        answer = await self.client.wait_for('message', check=check, timeout = 60.0)
    except asyncio.TimeoutError:
        await self.client.send(ctx, "Antwort hat zu lang gebraucht!\nBitte erneut versuchen.")
    else:
        if answer.content == "ja":
            return False
        else:
            return True

async def askForCategory(self, ctx, check, new : bool):
    if new:
        await self.client.send(ctx, "**Bitte gebe nun den Namen der Kategrie ein, die erstellt werden soll: (z.B. Voice Channels)**")
    else:
        await self.client.send(ctx, "**Bitte gib nun die ID der Kategorie ein, die du verwenden möchtest:**")
    try:
        category = await self.client.wait_for('message', check=check, timeout = 60.0)
    except asyncio.TimeoutError:
        await self.client.send(ctx, "Antwort hat zu lang gebraucht!\nBitte erneut versuchen.")
    else:
        return category.content

async def askForChannel(self, ctx, check, new : bool):
    if new:
        await self.client.send(ctx, "**Bitte gib nun den Namen des Channels ein, den ich erstellen soll: (z.B. Join To Create)**")
    else:
        await self.client.send(ctx, "**Bitte gib nun die ID des Channels ein, den du verwenden möchtest:**")
    try:
        channel = await self.client.wait_for('message', check=check, timeout = 60.0)
    except asyncio.TimeoutError:
        await self.client.send(ctx, "Antwort hat zu lang gebraucht!\nBitte erneut versuchen.")
    else:
        return channel.content

class Voice(commands.Cog):
    def __init__(self, client):
        self.client = client
        # client.conn.execute("drop table voicechannel")
        # client.conn.execute("create table voicechannel(userID bigint, voiceID bigint)")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        channelID = await self.client.conn.fetchval("SELECT voiceChannelID FROM voiceguild WHERE guildid = $1", member.guild.id)
        try:
            if after.channel.id == channelID:
                categoryID = await self.client.conn.fetchval("SELECT voiceCategoryID FROM voiceguild WHERE guildID = $1", member.guild.id)
                settings = await self.client.conn.fetchrow("SELECT channelName, channelLimit FROM voiceusersettings WHERE userID = $1", member.id)
                limit = await self.client.conn.fetchval("SELECT channelLimit FROM voiceguildsettings WHERE guildID = $1", member.guild.id)
                if settings is None:
                    name = f"{member.name}'s channel"
                    if limit is None:
                        limit = 0
                else:
                    name = settings["channelname"]
                    if limit is None or not settings["channellimit"] == 0:
                        limit = settings["channellimit"]
                category = self.client.get_channel(categoryID)
                createdChannel = await member.guild.create_voice_channel(name,category=category)
                await member.move_to(createdChannel)
                await createdChannel.set_permissions(self.client.user, connect=True, read_messages=True)
                await createdChannel.edit(name=name, user_limit=limit)
                await self.client.conn.execute("INSERT INTO voicechannel VALUES ($1, $2)", member.id, createdChannel.id)
                def check(a,b,c):
                    return len(createdChannel.members) == 0
                await self.client.wait_for('voice_state_update', check=check)
                await createdChannel.delete()
                await self.client.conn.execute('DELETE FROM voicechannel WHERE userID=$1', member.id)
        except Exception as e:
            self.client.tExcept(e)

    @commands.group()
    async def voice(self, ctx):
        pass # creates group voice

    @voice.command()
    async def setup(self, ctx):
        await self.client.deleteInvoking(ctx.message)
        if ctx.author.id == ctx.guild.owner_id:
            def check(message):
                return message.author.id == ctx.author.id
            await self.client.send(ctx, "**Du hast 60 Sekunden jede Frage zu beantworten!**")
            new = askIfNew(self, ctx, check)
            category = askForCategory(self, ctx, check, new)
            channel = askForChannel(self, ctx, check, new)
            if new:
                try:
                    category = await ctx.guild.create_category_channel(category)
                    channel = await ctx.guild.create_voice_channel(channel, category=category)
                    voice = self.client.conn.fetchrow("SELECT * FROM voiceguild WHERE guildID=$1 AND ownerID=$2", ctx.guild.id, ctx.author.id)
                    if voice is None:
                        self.client.conn.execute("INSERT INTO voiceguild VALUES ($1, $2, $3, $4)", ctx.guild.id, ctx.author.id, channel.id, category.id)
                    else:
                        self.client.conn.execute("UPDATE voiceguild SET ownerID = $1, voiceChannelID = $2, voiceCategoryID = $3 WHERE guildID = $4", ctx.author.id, channel.id, category.id, ctx.guild.id)
                    await self.client.send(ctx, "**Du bist nun eingerichtet und bereit!**")
                except:
                    await self.client.send(ctx, f"Du hast die Namen nicht richtig eingegeben.\nBitte verwende `{ctx.prefix}voice setup` erneut!")
            else:
                try:
                    voice = self.client.conn.fetchrow("SELECT * FROM voiceguild WHERE guildID=$1 AND ownerID=$2", ctx.guild.id, ctx.author.id)
                    if voice is None:
                        self.client.conn.execute("INSERT INTO voiceguild VALUES ($1, $2, $3, $4)", ctx.guild.id, ctx.author.id, int(channel), int(category))
                    else:
                        self.client.conn.execute("UPDATE voiceguild SET ownerID = $1, voiceChannelID = $2, voiceCategoryID = $3 WHERE guildID = $4", ctx.author.id, int(channel), int(category), ctx.guild.id)
                    await self.client.send(ctx, "**Du bist nun eingerichtet und bereit!**")
                except:
                    await self.client.send(ctx, f"Du hast die Namen nicht richtig eingegeben.\nBitte verwende `{ctx.prefix}voice setup` erneut!")
        else:
            await self.client.send(ctx, f"Nur der Besitzer des Servers kann diese Einstellung vornehmen!")

    @setup.error
    async def info_error(self, ctx, error):
        self.client.tExcept(error)
    
    @voice.command()
    @commands.has_permissions(administrator=True)
    async def setCategoryId(self, ctx, newCategoryId):
        await self.client.deleteInvoking(ctx.message)
        try:
            await self.client.conn.execute("UPDATE voiceguild SET voiceCategoryID = $1 WHERE guildID = $2", int(newCategoryId), ctx.guild.id)
            await self.client.send(ctx, "Die ID der Kategorie wurde geupdated!")
        except Exception as e:
            await self.client.send(ctx, f"Die ID der Kategorie konnte nicht geupdated werden!\n`{e}`")

    @setCategoryId.error
    async def info_error(self, ctx, error):
        self.client.tExcept(error)
    
    @voice.command()
    @commands.has_permissions(administrator=True)
    async def setChannelId(self, ctx, newChannelId):
        await self.client.deleteInvoking(ctx.message)
        try:
            await self.client.conn.execute("UPDATE voiceguild SET voiceChannelID = $1 WHERE guildID = $2", int(newChannelId), ctx.guild.id)
            await self.client.send(ctx, "Die ID des Channels wurde geupdated!")
        except Exception as e:
            await self.client.send(ctx, f"Die ID des Channels konnte nicht geupdated werden!\n`{e}`")

    @setChannelId.error
    async def info_error(self, ctx, error):
        self.client.tExcept(error)

    @voice.command()
    async def setGuildChannelLimit(self, ctx, num : int):
        await self.client.deleteInvoking(ctx.message)
        if ctx.author.id == ctx.guild.owner_id:
            voice = await self.client.conn.fetchrow("SELECT * FROM voiceguildsettings WHERE guildID = $1", ctx.guild.id)
            if voice is None:
                await self.client.conn.execute("INSERT INTO voiceguildsettings VALUES ($1, $2, $3, $4)", ctx.guild.id, f"{ctx.author.name}'s channel", 0, 0)
            else:
                await self.client.conn.execute("UPDATE voiceguildsettings SET channelLimit = $1 WHERE guildID = $2", num, ctx.guild.id)
            await self.client.send(ctx, f"Du hast das Standardlimit für Sprachkanäle des Servers verändert!\nNeu: {num}")
        else:
            await self.client.send(ctx, f"Nur der besitzer des Servers kann diese Einstellung ändern!")

    @setGuildChannelLimit.error
    async def info_error(self, ctx, error):
        self.client.tExcept(error)

    @voice.command(aliases=["Lock", "sperren", "beschränken", "abschließen"])
    async def lock(self, ctx):
        await self.client.deleteInvoking(ctx.message)
        channelID = await self.client.conn.fetchval("SELECT voiceID FROM voicechannel WHERE userID = $1", ctx.author.id)
        if channelID is None:
            await self.client.send(ctx, f"Du besitzt keinen Channel.")
        else:
            role = discord.utils.get(ctx.guild.roles, name='@everyone')
            channel = self.client.get_channel(int(channelID))
            await channel.set_permissions(role, connect=False, read_messages=True)
            await self.client.send(ctx, f'Gesperrt! 🔒')

    @lock.error
    async def info_error(self, ctx, error):
        self.client.tExcept(error)

    @voice.command(aliases=["Unlock", "öffnen", "aufschließen"])
    async def unlock(self, ctx):
        await self.client.deleteInvoking(ctx.message)
        channelID = await self.client.conn.fetchval("SELECT voiceID FROM voicechannel WHERE userID = $1", ctx.author.id)
        if channelID is None:
            await self.client.send(ctx, f"Du besitzt keinen Channel.")
        else:
            role = discord.utils.get(ctx.guild.roles, name='@everyone')
            channel = self.client.get_channel(int(channelID))
            await channel.set_permissions(role, connect=True, read_messages=True)
            await self.client.send(ctx, f'Entsperrt! 🔓')

    @unlock.error
    async def info_error(self, ctx, error):
        self.client.tExcept(error)

    @voice.command(aliases=["Permit", "Allow", "allow", "gewähren", "Whitelist", "whitelist"])
    async def permit(self, ctx, member : discord.Member):
        await self.client.deleteInvoking(ctx.message)
        channelID = await self.client.conn.fetchval("SELECT voiceID FROM voicechannel WHERE userID = $1", ctx.author.id)
        if channelID is None:
            await self.client.send(ctx, f"Du besitzt keinen Channel.")
        else:
            channel = self.client.get_channel(int(channelID))
            await channel.set_permissions(member, connect=True)
            await self.client.send(ctx, f'Du hast {member.name} Zugriff auf deinen Channel gewährt. ✅')

    @permit.error
    async def info_error(self, ctx, error):
        self.client.tExcept(error)

    @voice.command(aliases=["Reject", "Deny", "verwähren", "Blacklist", "blacklist"])
    async def reject(self, ctx, member : discord.Member):
        await self.client.deleteInvoking(ctx.message)
        channelID = await self.client.conn.fetchval("SELECT voiceID FROM voicechannel WHERE userID = $1", id)
        if channelID is None:
            await self.client.send(ctx, f"Du besitzt keinen Channel.")
        else:
            channel = self.client.get_channel(int(channelID))
            for members in channel.members:
                if members.id == member.id:
                    channelID = await self.client.conn.fetchval("SELECT voiceChannelID FROM voiceguild WHERE guildID = $1", ctx.guild.id)
                    createChannel = self.client.get_channel(int(channelID))
                    await member.move_to(createChannel)
            await channel.set_permissions(member, connect=False,read_messages=True)
            await self.client.send(ctx, f'Du hast {member.name} Zugriff auf deinen Channel verwährt. ❌')

    @reject.error
    async def info_error(self, ctx, error):
        self.client.tExcept(error)

    @voice.command(aliases=["Limit", "Anzahl", "anzahl", "Max", "max", "Begrenzung", "begrenzung"])
    async def limit(self, ctx, limit):
        await self.client.deleteInvoking(ctx.message)
        channelID = await self.client.conn.fetchval("SELECT voiceID FROM voicechannel WHERE userID = $1", ctx.author.id)
        if channelID is None:
            await self.client.send(ctx, f"Du besitzt keinen Channel.")
        else:
            channel = self.client.get_channel(int(channelID))
            await channel.edit(user_limit = limit)
            await self.client.send(ctx, f'Du hast das Limit auf {limit} Benutzer gestellt!')
            voice = await self.client.conn.fetchval("SELECT channelName FROM voiceusersettings WHERE userID = $1", ctx.author.id)
            if voice is None:
                await self.client.conn.execute("INSERT INTO voiceusersettings VALUES ($1, $2, $3)", ctx.author.id, f'{ctx.author.name}', limit)
            else:
                await self.client.conn.execute("UPDATE voiceusersettings SET channelLimit = $1 WHERE userID = $2", limit, ctx.author.id)

    @limit.error
    async def info_error(self, ctx, error):
        self.client.tExcept(error)

    @voice.command()
    async def name(self, ctx,*, name=""):
        await self.client.deleteInvoking(ctx.message)
        if name == "":
            name = f"{ctx.author.name}'s Channel"
        channelID = await self.client.conn.fetchval("SELECT voiceID FROM voicechannel WHERE userID = $1", ctx.author.id)
        if channelID is None:
            await self.client.send(ctx, f"Du besitzt keinen Channel.")
        else:
            channel = self.client.get_channel(int(channelID))
            await channel.edit(name = name)
            await self.client.send(ctx, f'Du hast den Channelnamen zu `{name}` geändert!')
            voice = await self.client.conn.fetchval("SELECT channelName FROM voiceusersettings WHERE userID = $1", id)
            if voice is None:
                await self.client.conn.execute("INSERT INTO voiceusersettings VALUES ($1, $2, $3)", ctx.author.id, name, 0)
            else:
                await self.client.conn.execute("UPDATE voiceusersettings SET channelName = $1 WHERE userID = $2", name, ctx.author.id)

    @name.error
    async def info_error(self, ctx, error):
        self.client.tExcept(error)

    @voice.command()
    async def claim(self, ctx):
        await self.client.deleteInvoking(ctx.message)
        channel = ctx.author.voice.channel
        if channel == None:
            await self.client.send(ctx, f"Du befindest dich in keinen Channel.")
        else:
            userID = await self.client.conn.fetchval("SELECT userID FROM voicechannel WHERE voiceID = $1", channel.id)
            if userID is None:
                await self.client.send(ctx, f"Du kannst diesen Channel nicht besitzen!")
            else:
                for member in channel.members:
                    if member.id == int(userID):
                        owner = ctx.guild.get_member(int(userID))
                        await self.client.send(ctx, f"Dieser Channel ist bereits im Besitz von {owner.mention}!")
                        return
                await self.client.conn.execute("UPDATE voicechannel SET userID = $1 WHERE voiceID = $2", ctx.author.id, channel.id)
                await self.client.send(ctx, f"Du bist nun der Besitzer dieses Channels!")
                settings = await self.client.conn.fetchrow("SELECT channelName, channelLimit FROM voiceusersettings WHERE userID = $1", ctx.author.id)
                if not settings is None:
                    await channel.edit(name=settings["channelname"], user_limit=settings["channellimit"])

    @claim.error
    async def info_error(self, ctx, error):
        self.client.tExcept(error)

def setup(client):
    client.add_cog(Voice(client))
