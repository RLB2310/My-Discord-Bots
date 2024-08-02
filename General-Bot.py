import threading
import discord
import os
import random
import requests
import time
import asyncio
from discord.ext import tasks
import subprocess

# Stating Variables
files_folder = "/media/root/EXTHDD/files/"

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

# Commands list for $list command
commands_list = [
    {'command': '$help', 'description': 'Show help message for requests'},
    {'command': '$list', 'description': 'List available commands'},
    {'command': '$storage', 'description': 'Check the current storage status of the folder'},
    {'command': '$files', 'description': 'List of files'},
    {'command': '$add', 'description': 'Add file to backlog'},
    {'command': '$delete', 'description': 'Delete files from backlog'},
    {'command': '$scan', 'description': 'Scan files for malware'},
    {'command': '$temp', 'description': 'Check the server temperature'},
]

def read_all_names(filename):
    try:
        with open(filename, 'r') as file:
            names = file.readlines()
            # Remove newline characters from each name
            names = [name.strip() for name in names]
            return names
    except FileNotFoundError:
        print(f"File {filename} not found.")
        return []

# Adding files to the list
def check_and_append_name(filename, name):
    try:
        with open(filename, 'r') as file:
            # Check if the name is already in the file
            if name in file.read():
                return
    except FileNotFoundError:
        # If the file doesn't exist, create it
        pass

    # Append the name to the next line
    with open(filename, 'a') as file:
        file.write(f"{name}\n")

# Delete file from list
def check_and_delete_name(filename, name):
    try:
        with open(filename, 'r') as file:
            lines = file.readlines()
    except FileNotFoundError:
        return  # File not found, nothing to delete

    found = False
    for i, line in enumerate(lines):
        if line.strip() == name:
            found = True
            lines.pop(i)
            break

    if found:
        with open(filename, 'w') as wfile:
            wfile.writelines(lines)

def is_file_in_folder(file_name):
    normalized_file_name = file_name.replace(' ', '.').lower()
    for file in os.listdir(files_folder):
        if file.lower().startswith(normalized_file_name) or file.lower().startswith(normalized_file_name + '-Fit'):
            return True
    return False

async def run_clamav_scan(directory):
    try:
        # Run clamscan command using subprocess
        process = await asyncio.create_subprocess_exec(
            'clamscan', '-r', directory,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        # Check for errors in stderr
        if stderr:
            return f'Error during ClamAV scan:\n```{stderr.decode("utf-8")}```'
        # Get the last 10 lines of the stdout
        last_lines = '\n'.join(stdout.decode('utf-8').splitlines()[-8:])
        return f'Scan Result:\n```{last_lines}```'

    except Exception as e:
        return f'Error running ClamAV scan: ```{str(e)}```'

# Used when precise file name not found
def search_similar_files(requested_file):
    search_directory = files_folder
    requested_file_lower = requested_file.lower()

    similar_files = []
    for filename in os.listdir(search_directory):
        if requested_file_lower in filename.lower() or filename.lower().startswith(requested_file_lower[:4]):
            similar_files.append(os.path.join(search_directory, filename))

    return similar_files

# $storage command check size
def get_directory_size(directory):
   total_size = 0
   with os.scandir(directory) as it:
        for entry in it:
            if entry.is_file():
                total_size += entry.stat().st_size
            elif entry.is_dir():
                total_size += get_directory_size(entry.path)
   return total_size

# Function to start connection
@client.event
async def on_ready():
    print(f'have logged in as {client.user}')
# Message recieved
@client.event
async def on_message(message):
    if message.author == client.user:
        return


    elif message.content.startswith('$add'):
        file_name = message.content[len('$add'):].strip()
        if is_file_in_folder(file_name):
            check_and_delete_name("Scripts/files_to_do.txt", file_name)
            await message.channel.send(f"```{file_name} is already present in the folder. It has been removed from the list. The file has been Downloaded.```")
        else:
            check_and_append_name("Scripts/files_to_do.txt", file_name)
            await message.channel.send(f"```{file_name} has been added to the list if not already present.```")
y
    elif message.content.startswith('$help'):
        command_descriptions = [f"{cmd['command']}: {cmd['description']}" for cmd in commands_list]
        await message.channel.send("List of available commands:\n```" + '\n'.join(command_descriptions) + "```")

    elif message.content.startswith('$files'):
        files = sorted([file for file in os.listdir(folder)])
        stored_files_message = "Currently stored files:\n• {}".format('\n• '.join(file))

        to_do_files = sorted(read_all_names("files_todo.txt"))
        to_do_files_message = "List of files to get:\n• {}".format('\n• '.join(to_do_files))

        await message.channel.send("```" + stored_files_message + "```")
        await message.channel.send("```" + to_do_files_message + "```")

    elif message.content.startswith("$storage"):
        initial_size = get_directory_size(Folder)
        gb_init = initial_size / 1024**3
        await message.channel.send(f"```Folder is currently sized at {gb_init:.2f} GB's```")
        await message.channel.send(f"Calculating current status...")
        time.sleep(20)
        current_size = get_directory_size(Folder)
        if current_size > initial_size:
            await message.channel.send(f"```And the is increasing, now at {current_size / 1024**3:.2f} GB's...```")
        else:
            pass

    # ClamAV Scan
    elif message.content.startswith('$scan'):
        await message.channel.send("Scanning for malware... This may take up to 10 mins")
        scan_result = await run_clamav_scan('Folder')
        await message.channel.send(f'ClamAV Scan Results:\n```{scan_result}```')


    # Get temperature of the server
    elif message.content.startswith("$temp"):
        result = subprocess.run(['vcgencmd', 'measure_temp'], capture_output=True, text=True, check=True)
        temperature = result.stdout.strip().split('=')[1]
        await message.channel.send(f"```The temperature of the server is: {temperature}```")

    # Non-serious commands
    elif message.content.startswith("Hey bot"):
        await message.channel.send("What's up.")
    elif message.content.startswith("can you help"):
        await message.channel.send("Sure can. Use the $help command")
client.run(TOKEN)
