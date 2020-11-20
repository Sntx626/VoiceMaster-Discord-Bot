import psycopg2
import json

try:
    conn = None
    conn = psycopg2.connect(host=json.load(open("config.json"))["db-addr"], user="postgres", password=json.load(open("config.json"))["db-pass"])

    c = conn.cursor()

    # VoiceMaster
    try:
        c.execute('drop table voiceGuild')
    except:
        pass
    try:
        c.execute('drop table voicechannel')
    except:
        pass
    try:
        c.execute('drop table voiceusersettings')
    except:
        pass
    try:
        c.execute('drop table voiceguildsettings')
    except:
        pass

    # VoiceMaster
    c.execute('create table voiceGuild(guildID bigint, ownerID bigint, voiceChannelID bigint, voiceCategoryID bigint)')
    c.execute('create table voicechannel(userID bigint, voiceID bigint)')
    c.execute('create table voiceusersettings(userID bigint, channelName text, channelLimit int)')
    c.execute('create table voiceguildsettings(guildID bigint, ownerName text, channelLimit int, botmessagechannel bigint)')

    conn.commit()

    c.close()
except (Exception, psycopg2.DatabaseError) as error:
    print(error)
finally:
    try:
        if conn is not None:
            conn.close()
    except:
        pass
