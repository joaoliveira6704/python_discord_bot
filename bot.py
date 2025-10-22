# bot.py
import discord
import os
import requests
import json
import random
import asyncio
import time
from mutagen.mp3 import MP3
from dotenv import load_dotenv
import yt_dlp
import re

#invite link: https://discord.com/oauth2/authorize?client_id=908067744178667530&scope=bot

load_dotenv()
TOKEN = os.getenv("TOKEN")

# Regex pattern to detect YouTube URLs
YOUTUBE_URL_PATTERN = r'(https?://(?:www\.)?youtube\.com/watch\?v=[\w-]+)'


intents = discord.Intents.all()
intents.message_content = True

client = discord.Client(intents=intents)

audio = [] # audios list
pictures = [] # pictures list
audioRandom="" # empty string for audio purposes
prefix="!" # Message prefix for the bot to answer
xpNeeded = 10 # How many messages the user must send using prefix to level up
song_queue = []  # Queue to hold YouTube songs only

spamActive = False  # Keeps track of spam state for each user

def get_quote():
  """Gets motivational quote from api"""
  response = requests.get("https://zenquotes.io/api/random")
  json_data = json.loads(response.text)
  quote = json_data[0]['q'] + " -" + json_data[0]['a']
  return(quote)

async def play_audio(song):
    """Handles playing audio from YouTube"""
    try:
        audio_source = discord.FFmpegPCMAudio(song['url'], executable="C:/discord_bot_lib/ffmpeg/bin/ffmpeg.exe")

        channel = song['voice_channel']
        voice_client = await channel.connect()

        voice_client.play(audio_source, after=after_playing)
        await song['text_channel'].send(f"Now playing: **{song['title']}**")

    except Exception as e:
        print(f"An error occurred while playing: {e}")


def after_playing(error):
    """Just for audio debug"""
    if error:
        print(f"Error: {error}")
    else:
        print("Finished playing.")

def list_files(dirPath):
    """Lists files"""
    audio = []
    pictures = []
    if dirPath == ".\\audios\\":
      for file in os.listdir(dirPath):
          if os.path.isfile(os.path.join(dirPath, file)):
            audio.append(file)
      return audio

    elif dirPath == ".\\images\\":
      for file in os.listdir(dirPath):
          if os.path.isfile(os.path.join(dirPath, file)):
            pictures.append(file)
      return pictures

def random_audio(audio):
  audioRandom = random.choice(audio)
  return audioRandom

def check_value(userID, value):
  userID = str(userID)
  isValid = True
  cont = True
  # Validate the value input
  try:
    value = int(value)
  except ValueError:
    cont = False # Return False if the value is not a valid integer
  if cont == False:
    isValid = False
  else:
    # Ensure the directory exists
    if not os.path.exists(".\\level_system\\"):
      os.mkdir(".\\level_system\\")

    file_path = ".\\level_system\\levels.csv"

    # Create the file if it doesn't exist
    if not os.path.exists(file_path):
      with open(file_path, "w") as f:
        pass

    # Load current levels into a dictionary for easier handling
    levels = {}

    with open(file_path, "r") as f:
      for line in f:
        fields = line.strip().split(";")
        if len(fields) == 3:  # Ensure the line format is correct
          levels[fields[0]] = (int(fields[1]), (int(fields[2])))
        if fields[0] == userID:
          if int(fields[1]) < int(value):
            isValid = False
  return isValid

def save_level(userID):
  userID = str(userID)
  # Ensure the directory exists
  if not os.path.exists(".\\level_system\\"):
    os.mkdir(".\\level_system\\")

  file_path = ".\\level_system\\levels.csv"

  # Create the file if it doesn't exist
  if not os.path.exists(file_path):
    with open(file_path, "w") as f:
      pass

  # Load current levels into a dictionary for easier handling
  levels = {}

  with open(file_path, "r") as f:
    for line in f:
      fields = line.strip().split(";")
      if len(fields) == 3:  # Ensure the line format is correct
        levels[fields[0]] = (int(fields[1]), (int(fields[2])))

  # Update or add the user level
  if userID in levels:
    total_level = levels[userID][0] + 1
  else:
    total_level = 1

  current_level = (total_level - 1) // xpNeeded + 1  # Current level increments by 1 every X total levels

   # Update the dictionary
  levels[userID] = (total_level, current_level)

  # Write back the updated levels to the file
  with open(file_path, "w") as f:
    for uid, (total, current) in levels.items():
      f.write(f"{uid};{total};{current}\n")
  
  f.close()
  return total_level

def show_level(userID):
  userID = str(userID)
  file_path = ".\\level_system\\levels.csv"

  # Return 0 if the file or user data doesn't exist
  if not os.path.exists(file_path):
    return 0, 1  # Default to total level 0 and current level 1

  # Read levels and find the user
  with open(file_path, "r") as f:
    for line in f:
      fields = line.strip().split(";")
      if len(fields) == 3 and fields[0] == userID:
        total_level = int(fields[1])
        current_level = int(fields[2])
        return total_level, current_level

  return 0, 1  # Default if user not found

def add_xpgift(userID, xpAdd):
  userID = str(userID)
  # Ensure the directory exists
  if not os.path.exists(".\\level_system\\"):
    os.mkdir(".\\level_system\\")

  file_path = ".\\level_system\\levels.csv"

  # Create the file if it doesn't exist
  if not os.path.exists(file_path):
    with open(file_path, "w") as f:
      pass

  # Load current levels into a dictionary for easier handling
  levels = {}

  with open(file_path, "r") as f:
    for line in f:
      fields = line.strip().split(";")
      if len(fields) == 3:  # Ensure the line format is correct
        levels[fields[0]] = (int(fields[1]), (int(fields[2])))

  # Update or add the user level
  if userID in levels:
    total_level = levels[userID][0] + xpAdd
  else:
    total_level = 1

  current_level = (total_level - 1) // xpNeeded + 1  # Current level increments by 1 every X total levels

   # Update the dictionary
  levels[userID] = (total_level, current_level)

  # Write back the updated levels to the file
  with open(file_path, "w") as f:
    for uid, (total, current) in levels.items():
      f.write(f"{uid};{total};{current}\n")
  
  f.close()
  return xpAdd, current_level, total_level

def reset_account(userID):
  userID = str(userID)
  # Ensure the directory exists
  if not os.path.exists(".\\level_system\\"):
    os.mkdir(".\\level_system\\")

  file_path = ".\\level_system\\levels.csv"

  # Create the file if it doesn't exist
  if not os.path.exists(file_path):
    with open(file_path, "w") as f:
      pass

  # Load current levels into a dictionary for easier handling
  levels = {}

  with open(file_path, "r") as f:
    for line in f:
      fields = line.strip().split(";")
      if len(fields) == 3:  # Ensure the line format is correct
        levels[fields[0]] = (int(fields[1]), (int(fields[2])))

  # Update or add the user level
  if userID in levels:
    total_level = 0
  else:
    total_level = 0

  current_level = 1

   # Update the dictionary
  levels[userID] = (total_level, current_level)

  # Write back the updated levels to the file
  with open(file_path, "w") as f:
    for uid, (total, current) in levels.items():
      f.write(f"{uid};{total};{current}\n")
  
  f.close()
  return total_level, current_level

def gambling(userID, value, userChoice):
  win = False
  userID = str(userID)
  # Ensure the directory exists
  if not os.path.exists(".\\level_system\\"):
    os.mkdir(".\\level_system\\")

  file_path = ".\\level_system\\levels.csv"

  # Create the file if it doesn't exist
  if not os.path.exists(file_path):
    with open(file_path, "w") as f:
      pass

  # Load current levels into a dictionary for easier handling
  levels = {}

  with open(file_path, "r") as f:
    for line in f:
      fields = line.strip().split(";")
      if len(fields) == 3:  # Ensure the line format is correct
        levels[fields[0]] = (int(fields[1]), (int(fields[2])))

  optionServer = [("🔴", 50), ("⚫", 50), ("🟢", 1)] #string, weight

  # Create the weighted list
  weightedList = [string for string, weight in optionServer for _ in range(weight)]

  # Make a random choice
  serverChoice = random.choice(weightedList)

  if serverChoice == userChoice:
    win = True
    if serverChoice == "🔴" or serverChoice == "⚫":
      # Update or add the user level
      if userID in levels:
        total_level = levels[userID][0] + int(value)
      else:
        total_level = 1
    elif serverChoice == "🟢":
      # Update or add the user level
      if userID in levels:
        total_level = levels[userID][0] + int(value) * 13
      else:
        total_level = 1
    else:
      print("Error")
      return
  else:
    # Update or add the user level
    if userID in levels:
      total_level = levels[userID][0] - (int(value))
    else:
      total_level = 1

  if total_level <= 0:
    total_level=0
    current_level = 1  # Current level is 1
  else:
    current_level = (total_level - 1) // xpNeeded + 1  # Current level increments by 1 every X total levels

  # Update the dictionary
  levels[userID] = (total_level, current_level)

  # Write back the updated levels to the file
  with open(file_path, "w") as f:
    for uid, (total, current) in levels.items():
      f.write(f"{uid};{total};{current}\n")
  
  f.close()
  return total_level, current_level, serverChoice, win

@client.event
async def on_ready():
  #await client.user.edit(username="The Crock")
  #await client.user.edit(avatar=pfp)
  print('You have logged in as {0.user}'.format(client))
  richPresence = discord.Activity(type=discord.ActivityType.listening, name="!help")
  
  await client.change_presence(status=discord.Status.online, activity=richPresence)

@client.event
async def on_message(message):
  global xpNeeded
  global spamActive
  if message.author == client.user:
    return

  if message.content.startswith(prefix):
    level = save_level(message.author.id)
    if int(level)%xpNeeded==0:
      await message.channel.send(f"{message.author.mention}, you leveled up! You are now level **{((level/xpNeeded)+1):.0f}**!")
    if message.content == prefix + "help":
      help_message = "**Available Commands**:\n\n- `!help` - Displays this list of commands.\n- `!crock` - Returns a personalized message based on the author.\n- `!find me` - Makes the bot join the voice channel you're in.\n- `!motivation` - Sends you a motivational quote.\n- `!quit` - Makes the bot leave the voice channel.\n- `!send dm` - Sends you a direct message.\n- `!list audios` - Lists all available audio files.\n- `!play [audio name]` - Plays the specified audio file. Use `!play something` to play a random audio.\n- `!spam start` - Spams your @ and sends you random images until you use `!spam stop`.\n- `!dice [value]` - Roll a dice and try your luck!\n- `!gamble [value]` - You enter Crock's casino and you can try your luck!\n- `!level` - Shows user their level and XP needed to level up.\n\nIf you encounter any issues or have questions, contact the bot administrator!"
      await message.channel.send(help_message)

    elif message.content == prefix + "crock":
      quote = get_quote()
      await message.channel.send(f"**I am the crock!**\n\n||{message.author.display_name}||!\n\n" + quote)
    elif message.content == prefix + "find me":
      if message.guild.voice_client:
        await message.channel.send("I am already looking for you!\n\n**DON'T TEST ME!**\n\n" + get_quote())
      elif message.author.voice:
        channel = message.author.voice.channel
        await channel.connect()
        await message.channel.send(f"**IM THE CROCK** and I am coming for you, I will start serching in {channel.name}.\n\n" + get_quote())
      else:
        await message.channel.send("If you are not connected I cannot enter a channel.\n\n" + get_quote())
    elif message.content == prefix + "quit":
      if message.guild.voice_client:
        await message.guild.voice_client.disconnect()
        await message.channel.send("I did not find you, but I will, I am the crock, **THE REAL CROCK!**\n\n**IM COMING FOR YOU**\n\n" + get_quote())
      else:
        await message.channel.send("I cannot leave somewhere I am not in.\n\n" + get_quote())
    elif message.content == prefix + "send dm":
      await client.create_dm(message.author)
      await message.channel.send("I sent you a dm, but don´t tell anyone!")
      await message.author.send("What do you want?")
    elif message.content == prefix + "list audios":
      audio = list_files(".\\audios\\")
      audioList=""
      for title in audio:
        audioList += (f"- {title[:-4]}\n")
      await message.channel.send(f"**Available Audios:**\n\n{audioList}")
    elif message.content.startswith(prefix + "play"):
      choice = message.content[len(prefix + "play"):].strip().lower()  # Removes extra spaces and converts message to lowecase
      audio = list_files(".\\audios\\")
      FFMPEG_OPTIONS = {'options': '-vn'}
      
      if not message.author.voice:
          await message.channel.send("You need to be in a voice channel for me to play something.")
          return

      if not choice:
          await message.channel.send("You need to tell me an audio to play! You sent an empty string!")
          return

      if choice == "something":
          audioRandom = random_audio(audio)
          audioPath = f".\\audios\\{audioRandom}"
          choice = audioRandom[:-4]
      else:
          audioPath = f".\\audios\\{choice}.mp3"
          if not os.path.exists(audioPath): 
              await message.channel.send(f"**{choice}** was not found, please try again.")
              return

      audio_source = discord.FFmpegPCMAudio(audioPath, executable="C:/discord_bot_lib/ffmpeg/bin/ffmpeg.exe", **FFMPEG_OPTIONS)
      channel = message.author.voice.channel
      voice_client = await channel.connect()

      voice_client.play(audio_source, after=after_playing)
      audioDuration = MP3(audioPath).info.length

      await message.channel.send(f"Now playing audio: **{choice.capitalize()}**")

      await asyncio.sleep(audioDuration)

      await voice_client.disconnect()
    elif message.content == prefix + "spam start":
      if spamActive:
        await message.channel.send("Spam is already active!")
        return
      spamActive = True
      await message.channel.send(f"Starting spam for {message.author.mention}!")

      while spamActive == True:
        user = await client.fetch_user(message.author.id)
        await message.channel.send(f'{user.mention}')
        await client.create_dm(user)
        pictures = list_files(".\\images\\")
        await user.send(file=discord.File(".\\images\\"+random.choice(pictures)))
        await asyncio.sleep(0.1)
    elif message.content == prefix + "spam stop":
      if not spamActive:
         await message.channel.send("No active spam session!")
         return
      spamActive = False
      await message.channel.send(f"Spam stopped for {message.author.mention}!")
    elif message.content == prefix + "level":
      totalCredits, currentLevel = show_level(message.author.id)
      await message.channel.send(f"{message.author.mention} you are level `{int(currentLevel):.0f}`\n- Credits needed for next level: `{((int(currentLevel)*xpNeeded)-totalCredits):.0f}`")
    elif message.content == prefix + "credits":
      totalCredits, currentLevel = show_level(message.author.id)
      await message.channel.send(f"{message.author.mention} you have `{int(totalCredits):.0f}` credits.\n- Amount of credits needed for next level: `{((int(currentLevel)*xpNeeded)-totalCredits):.0f}`")
    elif message.content == prefix + "motivation":
      quote = get_quote()
      await message.channel.send(f"{message.author.mention}, here is your motivational quote:\n\n`{quote}`")
    elif message.content.startswith(prefix + "dice"):
      dice = ["1","2","3","4","5","6"]
      options = ["Absolutely Nothing!", "xplevel"]
      numberUser = message.content[6:].strip()
      if numberUser not in dice:
        await message.channel.send(f"Invalid!\n{message.author.mention} pick a number between 1 and 6.")
        return
      number = random.randint(1,6)
      if int(numberUser) != number:
        await message.channel.send(f"{message.author.mention} I won! The number I rolled was {number}")
      else:
        chosenOpt = random.choice(options)
        await message.channel.send(f"{message.author.mention} You won and you get...")
        time.sleep(4)
        await message.channel.send("Processing...")
        time.sleep(4)
        await message.channel.send("Wait one more second...")
        time.sleep(4)
        if chosenOpt == "xplevel":
          xpGift, currentLvl, totalXP = add_xpgift(message.author.id,random.randint(3,8))
          await message.channel.send(f"{message.author.mention}, you got a xp gift!")
          time.sleep(1)
          await message.channel.send(f"{message.author.mention} XP Gift: `{xpGift}`\n\nCurrent XP: `{totalXP}`\nCurrent Level: `{currentLvl}`")
          time.sleep(1)
          await message.channel.send(f"{message.author.mention} Bonus Gift! Redeem it now: <https://2no.co/2tGVZ5>")
        else:
          await message.channel.send("absolutely nothing!")
    elif message.content == prefix + "reset account":
      confirm_message = await message.channel.send("Are you sure you want to reset your account? React with ✅ or ❌.")
        
      # Add reactions for the user to choose from
      await confirm_message.add_reaction("✅")
      await confirm_message.add_reaction("❌")

      # Check for the user's reaction
      def check(reaction, user):
        return user == message.author and str(reaction.emoji) in ["✅", "❌"] and reaction.message.id == confirm_message.id

      try:
        reaction, user = await client.wait_for("reaction_add", timeout=30.0, check=check)
        if str(reaction.emoji) == "✅":
          await message.channel.send("Account Reseting!\n\n")
          xpNew, levelNew = reset_account(message.author.id)
          await message.channel.send(f"{message.author.mention}, your account has been successfuly reseted!\n\nXP:`{xpNew}`\nLevel:`{levelNew}`")
        elif str(reaction.emoji) == "❌":
          await message.channel.send("Action canceled!")
          return
      except asyncio.TimeoutError:
        await message.channel.send("No response received. Action timed out.")
    elif message.content.startswith(prefix + "gamble"):
      if message.content[8:].strip() == "":
        await message.channel.send("Invalid! Usage **`!gamble value`**")
        return
      else:
        totalCredits, nothing = show_level(message.author.id)
        bet = message.content[8:].strip()
        if bet == "all in" or bet == "allin":
          isValid = True
          bet = totalCredits

          confirmMessage = await message.channel.send(f"- Credits in bet: `{bet}`\nAre you sure you want to bet all your credits?")
          # Add reactions for the user to choose from
          await confirmMessage.add_reaction("✅")
          await confirmMessage.add_reaction("❌")
          
          # Check for the user's reaction
          def check(reaction, user):
            return user == message.author and str(reaction.emoji) in ["✅", "❌"] and reaction.message.id == confirmMessage.id

          try:
            reaction, user = await client.wait_for("reaction_add", timeout=10.0, check=check)
            if str(reaction.emoji) == "✅":
              await message.channel.send("Thank you for your bet")
            elif str(reaction.emoji) == "❌":
              await message.channel.send("Action canceled!")
              return
          except asyncio.TimeoutError:
            await message.channel.send("No response received. Action timed out.")
        else:
          isValid = check_value(message.author.id, bet)
        if isValid == True:
          betMessage = await message.channel.send(f"Welcome to **THE CROCK CASINO**\n- Credits: `{totalCredits}`\nSo you want to bet? React with 🔴(2x) ⚫(2x) 🟢(14x) or cancel with ❌")
          # Add reactions for the user to choose from
          await betMessage.add_reaction("🔴")
          await betMessage.add_reaction("⚫")
          await betMessage.add_reaction("🟢")
          await betMessage.add_reaction("❌")

          # Check for the user's reaction
          def check(reaction, user):
            return user == message.author and str(reaction.emoji) in ["🔴", "⚫", "🟢", "❌"] and reaction.message.id == betMessage.id
          
          try:
            reaction, user = await client.wait_for("reaction_add", timeout=30.0, check=check)
            if str(reaction.emoji) == "🔴":
              await message.channel.send("Bet on red!")
              total_level, current_level, bot_choice, win = gambling(message.author.id, bet, "🔴")
            elif str(reaction.emoji) == "⚫":
              await message.channel.send("Bet on black!")
              total_level, current_level, bot_choice, win = gambling(message.author.id, bet, "⚫")
            elif str(reaction.emoji) == "🟢":
              await message.channel.send("Bet on green!")
              total_level, current_level, bot_choice, win = gambling(message.author.id, bet, "🟢")
            elif str(reaction.emoji) == "❌":
              await message.channel.send("Bet canceled!")
              return
          except asyncio.TimeoutError:
            await message.channel.send("No response received. Action timed out.")

          if bot_choice == "🔴" or "⚫":
              multiplier = "2x"
          elif bot_choice == "🟢":
              multiplier = "14x"

          if win == True:
            await message.channel.send(f"\nYou won!\n- Bet: `{bet}` {bot_choice}\n-Multiplier: `{multiplier}`\n\n-Current Stats:\n-XP: `{total_level}`\n-Level: `{current_level}`")
          else:
            await message.channel.send(f"\nYou Lost!\n- Bet: `{bet}`\n- Result: {bot_choice}\n-Multiplier: `{multiplier}`\n\n-Current Stats:\n-XP: `{total_level}`\n-Level: `{current_level}`")
        else:
          await message.channel.send("Invalid amount or not a value! Usage `!gamble value`")
          return
    elif message.content.startswith(prefix + "youtube"):
      query = message.content[len(prefix + "youtube"):].strip()

      if not query:
        await message.channel.send("You need to provide a search term!")
        return

      youtube_url_match = re.match(YOUTUBE_URL_PATTERN, query)

      if youtube_url_match:
        video_url = youtube_url_match.group(0)
        track_name = "Youtube Video"
      
        if not message.author.voice:
              await message.channel.send("You need to be in a voice channel.")
              return

        # Add to song queue 
        song_queue.append({'source': 'youtube', 'url': video_url, 'title': track_name, 'voice_channel': message.author.voice.channel, 'text_channel': message.channel})

        # If the bot isn't already playing, start playing the first song in the queue
        if len(song_queue) == 1:
          await play_audio(song_queue[0])
      else:
        try:
          ydl_opts = {
            'format': 'bestaudio/best',
            'extractaudio': True,
            'quiet': True,
          }

          with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch:{query} audio", download=False)
                      
            if not info['entries']:
              await message.channel.send("No results found on YouTube.")
              return
                      
            video_url = info['entries'][0]['url']
            track_name = info['entries'][0]['title']

            # Check if the user is in a voice channel
            if not message.author.voice:
              await message.channel.send("You need to be in a voice channel.")
              return

            # Add to song queue 
            song_queue.append({'source': 'youtube', 'url': video_url, 'title': track_name, 'voice_channel': message.author.voice.channel, 'text_channel': message.channel})

            # If the bot isn't already playing, start playing the first song in the queue
            if len(song_queue) == 1:
              await play_audio(song_queue[0])

        except Exception as e:
          await message.channel.send(f"An error occurred: {e}")
client.run(TOKEN)