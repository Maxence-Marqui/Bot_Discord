import discord
from discord.ext import commands
import youtube_dl
import os
import asyncio
import googleapiclient.discovery
from urllib.parse import parse_qs, urlparse
import re
import random

youtube = googleapiclient.discovery.build("youtube", "v3", developerKey = "Insert youtube dev key")

classic_roll_pattern = re.compile(r"(\d*)d(\d*)")
success_roll_pattern= re.compile(r"(>(\d*)|<(\d*))")
add_minus_roll_pattern = re.compile(r"((\+)\d|(\-)\d)")
adv_disadv_pattern = re.compile(r"(adv|disadv)")
explosive_pattern = re.compile("exp")
add_pattern = re.compile("add")
duration_pattern= re.compile(r"[0-9]+")
playlist_pattern = re.compile(r"playlist")

def roll_the_dice(user_input):

    list_dice_roll = []
    list_new_dice_roll = []
    counter = 1
    success = 0
    dice_sum = 0

    def roll(dice_size):
        dice_rolled = random.randint(1, dice_size)
        return dice_rolled
    
    def fumble(dice,dice_size):
        if dice == dice_size:
            dice_rolled = roll(dice_size)
            nonlocal dice_sum
            dice_sum -= dice_rolled
            list_new_dice_roll.append(dice_rolled)
            fumble(dice_rolled,dice_size)
    
    def crit(dice,dice_size):
        if dice == dice_size:
            dice_rolled = roll(dice_size)
            nonlocal dice_sum
            dice_sum += dice_rolled
            list_new_dice_roll.append(dice_rolled)
            crit(dice_rolled,dice_size)

    def exploding_dice(dice,dice_size):

        if dice <= 1:
            dice_rolled = roll(dice_size)
            list_new_dice_roll.append(dice_rolled)
            nonlocal dice_sum
            dice_sum -= (dice_rolled+ dice)  
            fumble(dice_rolled,dice_size)

        if dice == dice_size:
            crit(dice,dice_size)

    classic_roll = re.search(classic_roll_pattern,user_input)
    success_roll = re.search(success_roll_pattern,user_input)
    add_minus_roll = re.search(add_minus_roll_pattern,user_input)
    adv_disadv_roll = re.search(adv_disadv_pattern,user_input)
    explosive_roll = re.search(explosive_pattern,user_input)
    add_roll = re.search(add_pattern, user_input)

    if classic_roll:

        while counter <= int(classic_roll.group(1)):
            dice_roll = roll(int(classic_roll.group(2)))
            counter +=1

            if explosive_roll:
                if dice_roll == int(classic_roll.group(2)) or dice_roll <= 1:
                    exploding_dice(dice_roll,int(classic_roll.group(2)))

            if adv_disadv_roll:
                dice_roll = [dice_roll, roll(int(classic_roll.group(2)))]
            
            if add_minus_roll:
                if add_minus_roll.group(1)[0] == "+":
                    dice_roll += int(add_minus_roll.group(1)[1:])
                    if adv_disadv_roll:
                        dice_roll[0] += int(add_minus_roll.group(1)[1:])
                        dice_roll[1] += int(add_minus_roll.group(1)[1:])

                if add_minus_roll.group(1)[0] == "-":
                    dice_roll -= int(add_minus_roll.group(1)[1:])
                    if adv_disadv_roll:
                        dice_roll[0] -= int(add_minus_roll.group(1)[1:])
                        if dice_roll[1]:
                            dice_roll[1] -= int(add_minus_roll.group(1)[1:])

            if success_roll:
                if dice_roll >= int(success_roll.group(2)):
                    if adv_disadv_roll:
                        if adv_disadv_roll.group(1) == "adv":
                            if min(dice_roll) >= int(success_roll.group(2)):
                                success += 1
                    success += 1
                if dice_roll == 1:
                    if adv_disadv_roll:
                        if adv_disadv_roll.group(1) == "adv":
                            if min(dice_roll) == 1:
                                success -= 1
                    success -= 1

            list_dice_roll.append(dice_roll)

            if add_roll:
                dice_sum += dice_roll
        
        for dice in list_new_dice_roll:
            list_dice_roll.append(dice)

        reponse = ("T'as fait {}".format(list_dice_roll))
        if adv_disadv_roll:
            reponse = re.sub("[[]","(", str(list_dice_roll))
            reponse = re.sub("[]]",")", reponse)
            reponse = re.sub("^\(","**[**", reponse)
            reponse = re.sub("\)$","**]**", reponse)
        if success_roll:
            reponse = ("{}\n{} succès".format(list_dice_roll,success))
        
        if add_roll:
            reponse = ("{}\n T'as fait {}".format(list_dice_roll,dice_sum))

        return reponse
    else:
        reponse = "T'as fait une erreur poto"
        return reponse

def download_song(server,url):
    ydl_opts = {
            "format":"bestaudio/best",
            'outtmpl': 'D:/Cours/Coding/Python/Bot Discord/'+str(server)+'/'+'%(title)s.%(ext)s',
            "postprocessors":[{
                "key":"FFmpegExtractAudio",
                "preferredcodec":"mp3",
                "preferredquality":"192",
            }]
        }

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
        
def video_info(url):
    youtube = googleapiclient.discovery.build("youtube", "v3", developerKey = "AIzaSyBmKsIDt9fWhylYo9bSkd1dZyV5Oxgo3KU")
    request = youtube.videos().list(
            part="contentDetails,snippet",
            id=url
        )
    response = request.execute()
    try:
        duration = response["items"][0]["contentDetails"]["duration"]
    except IndexError:
        print("Erreur")
        return

    title = response["items"][0]["snippet"]["title"]

    match_duration = re.findall(duration_pattern,duration)

    video_duration =[]
    for match in match_duration:
        video_duration.append(match)

    video_duration = list(reversed(video_duration))

    if video_duration[0]:
            if video_duration[1] or video_duration[2]:
                seconds = "et " + str(video_duration[0]) + " seconde(s)"
            else:
                seconds = str(video_duration[0]) + "seconde(s)"
    try :
        minutes = str(video_duration[1]) + " minute(s) "
    except IndexError:
        minutes = "0"
    try :
        hours = str(video_duration[2]) + " heure(s) "
    except IndexError:
        hours = "0"
    
    response_1 = ("Le titre est ",title)
    response_2 = ("La vidéo fait {}{}{}.\n".format(hours,minutes,seconds))

    return response_1,response_2

def get_videos_from_playlist(url):
    query = parse_qs(urlparse(url).query, keep_blank_values=True)
    playlist_id = query["list"][0]

    youtube = googleapiclient.discovery.build("youtube", "v3", developerKey = "AIzaSyBmKsIDt9fWhylYo9bSkd1dZyV5Oxgo3KU")

    request = youtube.playlistItems().list(
        part = "snippet",
        playlistId = playlist_id,
        maxResults = 50
    )
    response = request.execute()

    playlist_items = []
    while request is not None:
        response = request.execute()
        playlist_items += response["items"]
        request = youtube.playlistItems().list_next(request, response)

    for video in playlist_items:
        print(video["snippet"]["resourceId"]["videoId"])
        video_info(video["snippet"]["resourceId"]["videoId"])

def extract_video_id(url):
    query = urlparse(url)
    if query.hostname == 'youtu.be': return query.path[1:]
    if query.hostname in {'www.youtube.com', 'youtube.com'}:
        if query.path == '/watch': return parse_qs(query.query)['v'][0]
        if query.path[:7] == '/embed/': return query.path.split('/')[2]
        if query.path[:3] == '/v/': return query.path.split('/')[2]
    return None

path = os.getcwd()
print ("The current working directory is %s" % path)
client = commands.Bot(command_prefix = "!")

@client.command()
async def hello(ctx):
    await ctx.send('hi')

@client.command()
async def roll(ctx,roll):
    await ctx.send(roll_the_dice(roll))

@client.command()
async def play(ctx, url : str):

    if not os.path.exists(str(ctx.guild)):
        os.mkdir(str(ctx.guild))
    
    channel = ctx.author.voice.channel
    song_queue = []

    if not discord.utils.get(client.voice_clients,guild = ctx.guild):
        await channel.connect()
        voice = discord.utils.get(client.voice_clients,guild = ctx.guild)

    download_song(ctx.guild,url)

    #if re.search(playlist_pattern,url):
    #    await ctx.send(get_videos_from_playlist(url))
    #else:
    #    await ctx.send(video_info(extract_video_id(url)))

    for file in os.listdir(str(ctx.guild)):
        if file.endswith('.mp3'):
            song_queue.append(file)

    place_in_queue = 0

    while song_queue:
        try:
            voice.play(discord.FFmpegPCMAudio("D:/Cours/Coding/Python/Bot Discord/"+str(ctx.guild) + "/"+song_queue[place_in_queue]))
            while voice.is_playing() or voice.is_paused():
                await asyncio.sleep(1)
            os.remove("D:/Cours/Coding/Python/Bot Discord/"+str(ctx.guild) + "/"+song_queue[place_in_queue])
            place_in_queue += 1
        except IndexError:
            break
        
@client.command()
async def leave(ctx):
    try:
        voice = discord.utils.get(client.voice_clients, guild = ctx.guild)
        voice.stop()
        await voice.disconnect()
        for song in os.listdir(str(ctx.guild)):
            os.remove("D:/Cours/Coding/Python/Bot Discord/"+str(ctx.guild) + "/"+song)
    except AttributeError:
        await ctx.send("Le bot est pas connecté de base")

@client.command()
async def pause(ctx):
    try:
        voice = discord.utils.get(client.voice_clients, guild = ctx.guild)
        voice.pause()
        print("pause")
    except AttributeError:
        await ctx.send("Il y a rien a mettre en pause")

@client.command()
async def resume(ctx):
    try:
        voice = discord.utils.get(client.voice_clients, guild = ctx.guild)
        voice.resume()
        print("reprendre")
    except AttributeError:
        await ctx.send("Pas de musique a reprendre ou pas en pause de base")
    
@client.command()
async def skip(ctx):
    try:
        voice = discord.utils.get(client.voice_clients, guild = ctx.guild)
        voice.stop()
        print("skip")
    except AttributeError:
        await ctx.send("Pas de musique a reprendre ou pas en pause de base")

@client.command()
async def clear(ctx):
    voice = discord.utils.get(client.voice_clients, guild = ctx.guild)
    voice.stop()
    for song in os.listdir(str(ctx.guild)):
        os.remove("D:/Cours/Coding/Python/Bot Discord/"+str(ctx.guild) + "/"+song)

client.run("Insert discord token")
