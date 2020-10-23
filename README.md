# VoiceMaster

Discord bot created to change the way servers run, instead of having permanent channels you can now create temporary ones that delete themselves once they are empty.

Originally I developed this bot with a small scale in mind as it was only meant to be used in my Discord server at the time, as time went on I decided to release it to the public and make the bot public so that everyone could benefit from it.

Since it was only meant to be used for my personal server I didn't write it very efficiently or very scalable which caused many issues down the line, sqlite really limits the bot as it suggests in the title Lite, it's not meant for big scale development with lots of requests.

So after the bot started growing I decided to rewrite it from scratch and make it a lot more efficient and re write the database structure and start using Postgresql and Asyncpg to deal with the database stuff.

The code on this repository is very old but still functional I will keep it functional and update any breaking changes done to Discord or Discord.py so that everyone can benefit from it.

I released the source code so that it might be some help to developers maybe teach them or just simply allow users to host their own version.

I won't be releasing any new updates and won't be releasing the new source code, I have discontinued any updates and won't be helping people with hosting it there are Discord servers that will deal with that.

Python Discord server:
https://discord.gg/python

Discord.py Discord server:
https://discord.gg/dpy

Our discord server:
https://discord.gg/y9pgpbt

Use our public bot:
https://voicemaster.xyz/

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

