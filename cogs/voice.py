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
                        await member.send("Creating channels too quickly you've been put on a 15 second cooldown!")
                        await asyncio.sleep(15)
                    c.execute("SELECT voiceCategoryID FROM voiceguild WHERE guildID = %s", (guildID,))
                    voice=c.fetchone()
                    c.execute("SELECT channelName, channelLimit FROM voiceusersettings WHERE userID = %s", (member.id,))
                    setting=c.fetchone()
                    c.execute("SELECT channelLimit FROM voiceguildsettings WHERE guildID = %s", (guildID,))
                    guildSetting=c.fetchone()
                    if setting is None:
                        name = f"{member.name}'s channel"
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
        await self.client.deleteInvoking(ctx.message)
        conn = None
        conn = psycopg2.connect(host=config["db-addr"], user="postgres", password=config["db-pass"])
        c = conn.cursor()
        guildID = ctx.guild.id
        id = ctx.author.id
        if ctx.author.id == config['owner_id']:
            def check(m):
                return m.author.id == ctx.author.id
            await self.client.send(ctx, "**You have 60 seconds to answer each question!**")
            await self.client.send(ctx, "**Do you want to use a preexisting category and channel%s**(yes/no):")
            try:
                answer = await self.bot.wait_for('message', check=check, timeout = 60.0)
            except asyncio.TimeoutError:
                await self.client.send(ctx, 'Took too long to answer!')
            else:
                if answer.content == "no":
                    await self.client.send(ctx, f"**Enter the name of the category you wish to create the channels in:(e.g Voice Channels)**")
                    try:
                        category = await self.bot.wait_for('message', check=check, timeout = 60.0)
                    except asyncio.TimeoutError:
                        await self.client.send(ctx, 'Took too long to answer!')
                    else:
                        new_cat = await ctx.guild.create_category_channel(category.content)
                    await self.client.send(ctx, '**Enter the name of the voice channel: (e.g Join To Create)**')
                    try:
                        channel = await self.bot.wait_for('message', check=check, timeout = 60.0)
                    except asyncio.TimeoutError:
                        await self.client.send(ctx, 'Took too long to answer!')
                    else:
                        try:
                            channel = await ctx.guild.create_voice_channel(channel.content, category=new_cat)
                            c.execute("SELECT * FROM voiceguild WHERE guildID = %s AND ownerID=%s", (guildID, id))
                            voice=c.fetchone()
                            if voice is None:
                                c.execute ("INSERT INTO voiceguild VALUES (%s, %s, %s, %s)",(guildID,id,channel.id,new_cat.id))
                            else:
                                c.execute ("UPDATE voiceguild SET guildID = %s, ownerID = %s, voiceChannelID = %s, voiceCategoryID = %s WHERE guildID = %s",(guildID,id,channel.id,new_cat.id, guildID))
                            await self.client.send(ctx, "**You are all setup and ready to go!**")
                        except:
                            await self.client.send(ctx, "You didn't enter the names properly.\nUse `.voice setup` again!")
                else:
                    await self.client.send(ctx, f"**Enter the id of the category you wish to use:**")
                    try:
                        categoryId = await self.bot.wait_for('message', check=check, timeout = 60.0)
                    except asyncio.TimeoutError:
                        await self.client.send(ctx, 'Took too long to answer!')
                    else:
                        await self.client.send(ctx, f"**Enter the id of the channel you wish to use:**")
                        try:
                            channelId = await self.bot.wait_for('message', check=check, timeout = 60.0)
                        except asyncio.TimeoutError:
                            await self.client.send(ctx, 'Took too long to answer!')
                        else:
                            c.execute("SELECT * FROM voiceguild WHERE guildID = %s AND ownerID=%s", (guildID, id))
                            voice=c.fetchone()
                            if voice is None:
                                c.execute ("INSERT INTO voiceguild VALUES (%s, %s, %s, %s)",(guildID,id,int(channelId.content),int(categoryId.content)))
                            else:
                                c.execute ("UPDATE voiceguild SET guildID = %s, ownerID = %s, voiceChannelID = %s, voiceCategoryID = %s WHERE guildID = %s",(guildID,id,int(channelId.content),int(categoryId.content), guildID))
                            await self.client.send(ctx, "**You are all setup and ready to go!**")
        else:
            await self.client.send(ctx, f"{ctx.author.mention} only the owner of the server can setup the bot!")
        conn.commit()
        conn.close()

    @setup.error
    async def info_error(self, ctx, error):
        print(error)
    
    @voice.command()
    @commands.has_permissions(administrator=True)
    async def setCategoryId(self, ctx, newCategoryId):
        await self.client.deleteInvoking(ctx.message)
        try:
            conn = None
            conn = psycopg2.connect(host=config["db-addr"], user="postgres", password=config["db-pass"])
            c = conn.cursor()
            c.execute ("UPDATE voiceguild SET voiceCategoryID = %s WHERE guildID = %s",(int(newCategoryId), ctx.guild.id))
            conn.commit()
            conn.close()
            await self.client.send(ctx, "Your category ID has been updated!")
        except Exception as e:
            await self.client.send(ctx, f"Couldn't update category ID\n`{e}`")
    
    @voice.command()
    @commands.has_permissions(administrator=True)
    async def setChannelId(self, ctx, newChannelId):
        await self.client.deleteInvoking(ctx.message)
        try:
            conn = None
            conn = psycopg2.connect(host=config["db-addr"], user="postgres", password=config["db-pass"])
            c = conn.cursor()
            c.execute ("UPDATE voiceguild SET voiceChannelID = %s WHERE guildID = %s",(int(newChannelId), ctx.guild.id))
            conn.commit()
            conn.close()
            await self.client.send(ctx, "Your channel ID has been updated!")
        except Exception as e:
            await self.client.send(ctx, f"Couldn't update channel ID\n`{e}`")

    @voice.command()
    async def setlimit(self, ctx, num):
        await self.client.deleteInvoking(ctx.message)
        conn = None
        conn = psycopg2.connect(host=config["db-addr"], user="postgres", password=config["db-pass"])
        c = conn.cursor()
        if ctx.author.id == config['owner_id']:
            c.execute("SELECT * FROM voiceguildsettings WHERE guildID = %s", (ctx.guild.id,))
            voice=c.fetchone()
            if voice is None:
                c.execute("INSERT INTO voiceguildsettings VALUES (%s, %s, %s)", (ctx.guild.id,f"{ctx.author.name}'s channel",num))
            else:
                c.execute("UPDATE voiceguildsettings SET channelLimit = %s WHERE guildID = %s", (num, ctx.guild.id))
            await self.client.send(ctx, "You have changed the default channel limit for your server!")
        else:
            await self.client.send(ctx, f"{ctx.author.mention} only the owner of the server can setup the bot!")
        conn.commit()
        conn.close()

    @voice.command()
    async def lock(self, ctx):
        await self.client.deleteInvoking(ctx.message)
        conn = None
        conn = psycopg2.connect(host=config["db-addr"], user="postgres", password=config["db-pass"])
        c = conn.cursor()
        id = ctx.author.id
        c.execute("SELECT voiceID FROM voicechannel WHERE userID = %s", (id,))
        voice=c.fetchone()
        if voice is None:
            await self.client.send(ctx, f"{ctx.author.mention} You don't own a channel.")
        else:
            channelID = voice[0]
            role = discord.utils.get(ctx.guild.roles, name='@everyone')
            channel = self.bot.get_channel(channelID)
            await channel.set_permissions(role, connect=False,read_messages=True)
            await self.client.send(ctx, f'{ctx.author.mention} Voice chat locked! 🔒')
        conn.commit()
        conn.close()

    @voice.command()
    async def unlock(self, ctx):
        await self.client.deleteInvoking(ctx.message)
        conn = None
        conn = psycopg2.connect(host=config["db-addr"], user="postgres", password=config["db-pass"])
        c = conn.cursor()
        id = ctx.author.id
        c.execute("SELECT voiceID FROM voicechannel WHERE userID = %s", (id,))
        voice=c.fetchone()
        if voice is None:
            await self.client.send(ctx, f"{ctx.author.mention} You don't own a channel.")
        else:
            channelID = voice[0]
            role = discord.utils.get(ctx.guild.roles, name='@everyone')
            channel = self.bot.get_channel(channelID)
            await channel.set_permissions(role, connect=True,read_messages=True)
            await self.client.send(ctx, f'{ctx.author.mention} Voice chat unlocked! 🔓')
        conn.commit()
        conn.close()

    @voice.command(aliases=["allow"])
    async def permit(self, ctx, member : discord.Member):
        await self.client.deleteInvoking(ctx.message)
        conn = None
        conn = psycopg2.connect(host=config["db-addr"], user="postgres", password=config["db-pass"])
        c = conn.cursor()
        id = ctx.author.id
        c.execute("SELECT voiceID FROM voicechannel WHERE userID = %s", (id,))
        voice=c.fetchone()
        if voice is None:
            await self.client.send(ctx, f"{ctx.author.mention} You don't own a channel.")
        else:
            channelID = voice[0]
            channel = self.bot.get_channel(channelID)
            await channel.set_permissions(member, connect=True)
            await self.client.send(ctx, f'{ctx.author.mention} You have permited {member.name} to have access to the channel. ✅')
        conn.commit()
        conn.close()

    @voice.command(aliases=["deny"])
    async def reject(self, ctx, member : discord.Member):
        await self.client.deleteInvoking(ctx.message)
        conn = None
        conn = psycopg2.connect(host=config["db-addr"], user="postgres", password=config["db-pass"])
        c = conn.cursor()
        id = ctx.author.id
        guildID = ctx.guild.id
        c.execute("SELECT voiceID FROM voicechannel WHERE userID = %s", (id,))
        voice=c.fetchone()
        if voice is None:
            await self.client.send(ctx, f"{ctx.author.mention} You don't own a channel.")
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
            await self.client.send(ctx, f'{ctx.author.mention} You have rejected {member.name} from accessing the channel. ❌')
        conn.commit()
        conn.close()



    @voice.command()
    async def limit(self, ctx, limit):
        await self.client.deleteInvoking(ctx.message)
        conn = None
        conn = psycopg2.connect(host=config["db-addr"], user="postgres", password=config["db-pass"])
        c = conn.cursor()
        id = ctx.author.id
        c.execute("SELECT voiceID FROM voicechannel WHERE userID = %s", (id,))
        voice=c.fetchone()
        if voice is None:
            await self.client.send(ctx, f"{ctx.author.mention} You don't own a channel.")
        else:
            channelID = voice[0]
            channel = self.bot.get_channel(channelID)
            await channel.edit(user_limit = limit)
            await self.client.send(ctx, f'{ctx.author.mention} You have set the channel limit to be '+ '{}!'.format(limit))
            c.execute("SELECT channelName FROM voiceusersettings WHERE userID = %s", (id,))
            voice=c.fetchone()
            if voice is None:
                c.execute("INSERT INTO voiceusersettings VALUES (%s, %s, %s)", (id,f'{ctx.author.name}',limit))
            else:
                c.execute("UPDATE voiceusersettings SET channelLimit = %s WHERE userID = %s", (limit, id))
        conn.commit()
        conn.close()


    @voice.command()
    async def name(self, ctx,*, name):
        await self.client.deleteInvoking(ctx.message)
        conn = None
        conn = psycopg2.connect(host=config["db-addr"], user="postgres", password=config["db-pass"])
        c = conn.cursor()
        id = ctx.author.id
        c.execute("SELECT voiceID FROM voicechannel WHERE userID = %s", (id,))
        voice=c.fetchone()
        if voice is None:
            await self.client.send(ctx, f"{ctx.author.mention} You don't own a channel.")
        else:
            channelID = voice[0]
            channel = self.bot.get_channel(channelID)
            await channel.edit(name = name)
            await self.client.send(ctx, f'{ctx.author.mention} You have changed the channel name to '+ '{}!'.format(name))
            c.execute("SELECT channelName FROM voiceusersettings WHERE userID = %s", (id,))
            voice=c.fetchone()
            if voice is None:
                c.execute("INSERT INTO voiceusersettings VALUES (%s, %s, %s)", (id,name,0))
            else:
                c.execute("UPDATE voiceusersettings SET channelName = %s WHERE userID = %s", (name, id))
        conn.commit()
        conn.close()

    @voice.command()
    async def claim(self, ctx):
        await self.client.deleteInvoking(ctx.message)
        x = False
        conn = None
        conn = psycopg2.connect(host=config["db-addr"], user="postgres", password=config["db-pass"])
        c = conn.cursor()
        channel = ctx.author.voice.channel
        if channel == None:
            await self.client.send(ctx, f"{ctx.author.mention} you're not in a voice channel.")
        else:
            id = ctx.author.id
            c.execute("SELECT userID FROM voicechannel WHERE voiceID = %s", (channel.id,))
            voice=c.fetchone()
            if voice is None:
                await self.client.send(ctx, f"{ctx.author.mention} You can't own that channel!")
            else:
                for data in channel.members:
                    if data.id == voice[0]:
                        owner = ctx.guild.get_member(voice [0])
                        await self.client.send(ctx, f"{ctx.author.mention} This channel is already owned by {owner.mention}!")
                        x = True
                if x == False:
                    await self.client.send(ctx, f"{ctx.author.mention} You are now the owner of the channel!")
                    c.execute("UPDATE voicechannel SET userID = %s WHERE voiceID = %s", (id, channel.id))
            conn.commit()
            conn.close()

def setup(bot):
    bot.add_cog(Voice(bot))
