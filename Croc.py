import sys
import discord
import asyncio
import os
import subprocess
# Discord bot token
TOKEN = YOUR_TOKEN
# Initialize Discord client
intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

# Global variable to track if croc code is generating
gen = False

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')

@bot.event
async def on_message(message):
    global gen

    # Ignore messages from the bot itself
    if message.author == bot.user:
        return
    if message.content.startswith("$status"):
       await message.channel.send("online")
    if message.content.startswith('$croc'):
        # Check if croc code is generating
        if gen:
            await message.channel.send("Croc already generating a code. Queuing....")
            # If generating, loop until it finishes
            while gen:
                await asyncio.sleep(10)
        # Extract file path from the message
        file_path = message.content[6:].strip()
        file_path = "/media/root/EXTHDD/files/" + file_path
        print(file_path)
        # Check if file path exists
        if not os.path.exists(file_path):
            await message.channel.send(f"{message.author.mention} File path doesn't exist.")
            return

        # Run croc command to generate croc code
        gen = True
        await message.channel.send(f"{message.author.mention} Generating Croc code...")
        await bot.change_presence(activity=discord.file(name="Croc Code Gen: " + file_path))
        print('gen for ' + file_path)
        croc_process = await asyncio.create_subprocess_shell(
            f'nohup croc --no-compress send {file_path} > Scripts/croc_codes.txt')

        # Continuously check if the file has a line that starts with 'croc'
        croc_code = ""
        while True:
            try:
                with open('Scripts/croc_codes.txt', 'r') as f:
                    lines = f.readlines()
                for line in lines:
                    if line.startswith("croc"):
                        croc_code = line.strip()
                        break

                if croc_code:
                    break
            except FileNotFoundError:
                pass
            await asyncio.sleep(5) # Wait for 5 seconds before checking again

        # Send croc code to Discord channel
        file_name = os.path.basename(file_path)
        croc_code = croc_code.strip("croc")
        await message.channel.send(f'{message.author.mention} Croc file for {file_name} is:\n```{croc_code}```')
        await bot.change_presence(activity=discord.file(name="Doing nothing"))
        gen = False


    elif message.content.startswith('$reset'):
        # Terminate the bot process
        python = sys.executable
        subprocess.Popen([python, *sys.argv])
        #subprocess.Popen(['nohup', '/usr/bin/python3', 'Scripts/croc.py', '>', 'Scripts/croc_codes.txt'])
        # Terminate the bot process
        await message.channel.send("Resetting bot...")
        await bot.close()
