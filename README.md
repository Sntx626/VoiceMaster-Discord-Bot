# VoiceMaster

Dedicated bot for creating temp voice channels with commands for changing permissions.

This bot runs on discord.py rw If you need help with the code use the discord.py server :  [https://discord.gg/r3sSKJJ](https://discord.gg/r3sSKJJ)

As there is a very high demand for me to release the source code for my bot I've finally decided to release it.

This was just a small project that got quite big, I wrote the bot in a day so the code is pretty sloppy.

Enjoy the code, don't try to release it as your own bot. :)

If you'd like to support the bot you could pay for my coffee and the servers using the link below <3  [https://www.paypal.me/ssanaizadeh](https://www.paypal.me/ssanaizadeh)

Support Server for the bot: https://discord.gg/y9pgpbt

**This version of the bot is sufficient enough for casual use on afew servers, I have no intention what so ever of updating it nor will support anyone with hosting it.**

**I won't be releasing the new version of the bots source code either so don't ask.**

# How to setup the bot:

0. (prerequisite) Install the [Docker Engine](https://docs.docker.com/engine/install/)

1. Clone the bot repository with:
```
git clone https://github.com/Sntx626/VoiceMaster-Discord-Bot.git
```

2. Open `setup.json.example` in a text editor and add:
- Your bot prefix
- Your bot token
- The user id of the bot owner

Then save file as `setup.json`.

3. Build the dockerimage of the bot with:
```
docker build -t voicemaster .
```

4. Start the bot with:
```
docker run -d --name VoiceMaster voicemaster
```

