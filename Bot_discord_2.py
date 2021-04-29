import discord
from discord.ext import commands
import youtube_dl
import os
import asyncio
import googleapiclient.discovery
from urllib.parse import parse_qs, urlparse
import re
import random

youtube = googleapiclient.discovery.build("youtube", "v3", developerKey = "Import youtube token")

classic_roll_pattern = re.compile(r"(\d*)d(\d*)")
success_roll_pattern= re.compile(r"(>(\d*)|<(\d*))")
add_minus_roll_pattern = re.compile(r"((\+)\d|(\-)\d)")
adv_disadv_pattern = re.compile(r"(adv|disadv)")
explosive_pattern = re.compile("exp")
add_pattern = re.compile("add")
hour_pattern= re.compile(r"[1-9]+H")
minute_pattern= re.compile(r"[1-9]+M")
second_pattern = re.compile(r"[1-9]+S")

playlist_pattern = re.compile(r"playlist")

server_queues = {}

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
                        print("adv")
                        if min(dice_roll) >= int(success_roll.group(2)):
                            print(min(dice_roll))
                            success += 1
                success += 1
            if dice_roll == 1:
                if adv_disadv_roll:
                    if adv_disadv_roll.group(1) == "adv":
                        print("adv")
                        if min(dice_roll) == 1:
                            print(min(dice_roll))
                            success -= 1
                success -= 1

        list_dice_roll.append(dice_roll)

        if add_roll:
            dice_sum += dice_roll
    
    for dice in list_new_dice_roll:
        list_dice_roll.append(dice)

    reponse = str((list_dice_roll))

    if success_roll:
        reponse = ("{} succès".format(success))
    
    if add_roll:
        reponse = ("T'as fait {} frérot".format(dice_sum))
    
    return str(list_dice_roll),str(reponse)

def download_song(url,vid_id):
    ydl_opts = {
            "format":"bestaudio/best",
            'outtmpl': 'D:/Cours/Coding/Python/Bot Discord/music_database/'+vid_id+'.%(ext)s',
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
        print("Impossible de trouver la durée")
        return

    title = response["items"][0]["snippet"]["title"]

    match_hour = re.findall(hour_pattern,duration)
    match_minute = re.findall(minute_pattern,duration)
    match_second = re.findall(second_pattern,duration)
    
    if match_hour:
        hours = str(match_hour[0].replace("H","")) + " heure(s)"
    else :
        hours = ""
    
    if match_minute:
        minutes = str(match_minute[0].replace("M","")) + " minute(s)"
    else :
        minutes = ""

    if match_second:
        if match_hour or match_minute:
            seconds = " et " + str(match_second[0].replace("S","")) + " seconde(s)"
        else:
            seconds = str(match_second[0].replace("S","")) + " seconde(s)"
    else :
        seconds = ""
    duration = ("La vidéo fait {}{}{}.".format(hours,minutes,seconds))
    return title,duration

def get_videos_from_playlist(url,queue):
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
        vid_id = video["snippet"]["resourceId"]["videoId"]
        try:
            vid_title, vid_duration = video_info(video["snippet"]["resourceId"]["videoId"])
        except TypeError:
            vid_title,vid_duration = None,None
        queue.append([vid_id,vid_title,vid_duration])
    return queue

def extract_video_id(url,queue):
    query = urlparse(url)
    if query.hostname == 'youtu.be': 
        vid_id = query.path[1:]
        vid_title, vid_duration = video_info(query.path[1:])
    if query.hostname in {'www.youtube.com', 'youtube.com'}:
        if query.path == '/watch': 
            vid_id = parse_qs(query.query)['v'][0]
            vid_title, vid_duration = video_info(parse_qs(query.query)['v'][0])
        if query.path[:7] == '/embed/': 
            vid_id = query.path.split('/')[2]
            vid_title, vid_duration =video_info(query.path.split('/')[2])
        if query.path[:3] == '/v/': 
            vid_id = query.path.split('/')[2]
            vid_title, vid_duration = video_info(query.path.split('/')[2])
    queue.append([vid_id,vid_title,vid_duration])
    return queue


path = os.getcwd()
print ("The current working directory is %s" % path)
client = commands.Bot(command_prefix = "?")

@client.command()
async def hello(ctx):
    await ctx.send('hi')

@client.command()
async def roll(ctx,*,roll):
    response1,response2 = roll_the_dice(roll)
    await ctx.send(response1)
    if not response1 == response2:
        await ctx.send(response2)

@client.command()
async def play(ctx, url : str):
    channel = ctx.author.voice.channel
    
    try:
        print(server_queues[str(ctx.guild)])
    except:
        server_queues[str(ctx.guild)] = []

    if not discord.utils.get(client.voice_clients,guild = ctx.guild):
        await channel.connect()

    voice = discord.utils.get(client.voice_clients,guild = ctx.guild)

    match_playlist = re.search(playlist_pattern,url)

    if match_playlist:
        server_queues[str(ctx.guild)] = get_videos_from_playlist(url,server_queues[str(ctx.guild)])
    else:
        server_queues[str(ctx.guild)] = extract_video_id(url,server_queues[str(ctx.guild)])

    end_queue = True

    place_in_queue = 0

    while end_queue:
        try:
            if server_queues[str(ctx.guild)][place_in_queue][0]+".mp3" not in os.listdir('D:/Cours/Coding/Python/Bot Discord/music_database/'):
                download_song("https://youtu.be/"+server_queues[str(ctx.guild)][place_in_queue][0],server_queues[str(ctx.guild)][place_in_queue][0])

            while voice.is_playing() or voice.is_paused():
                await asyncio.sleep(1)
            voice.play(discord.FFmpegPCMAudio("D:/Cours/Coding/Python/Bot Discord/music_database/"+server_queues[str(ctx.guild)][place_in_queue][0]+".mp3"))
            await ctx.send(server_queues[str(ctx.guild)][place_in_queue][1])
            await ctx.send(server_queues[str(ctx.guild)][place_in_queue][2])

            if place_in_queue+1 == len(server_queues[str(ctx.guild)]):
                end_queue = False
            
            server_queues[str(ctx.guild)].pop(place_in_queue)
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
    except AttributeError:
        await ctx.send("Pas de musique a reprendre ou pas en pause de base")

client.run("Import discord token")
