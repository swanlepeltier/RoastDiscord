import os
import discord
from discord.ext import commands
import aiohttp
import json

# Configuration
KOBOLD_API_URL = "http://localhost:5001/api/v1/generate"
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
SYSTEM_PROMPT_FILE = "roast.txt"

if not DISCORD_TOKEN:
    raise ValueError("DISCORD_TOKEN environment variable is not set.")

# Load Roast Persona
try:
    with open(SYSTEM_PROMPT_FILE, "r", encoding="utf-8") as f:
        ROAST_PROMPT = f.read()
except FileNotFoundError:
    print(f"Warning: {SYSTEM_PROMPT_FILE} not found. Using default prompt.")
    ROAST_PROMPT = "You are a mean roasting bot."

# Discord Bot Setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

async def generate_response(prompt):
    payload = {
        "prompt": prompt,
        "max_context_length": 2048,
        "max_length": 150,
        "temperature": 0.8,
        "top_p": 0.9,
        "rep_pen": 1.1,
        "stop_sequence": ["User:", "\nUser ", "User", "\n\n"],
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(KOBOLD_API_URL, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    # KoboldCPP response format check
                    if 'results' in data and len(data['results']) > 0:
                        return data['results'][0]['text'].strip()
                    else:
                        print(f"Unexpected response format: {data}")
                        return "Error: Unexpected API response format."
                else:
                    print(f"API Error: {response.status} - {await response.text()}")
                    return "Error: Could not connect to AI endpoint."
        except Exception as e:
            print(f"Connection Error: {e}")
            return "Error: Could not reach AI server."

@bot.event
async def on_ready():
    print(f"Connected as {bot.user}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # Check if the bot is mentioned
    if bot.user in message.mentions:
        # Remove the mention from the content to get the actual user message
        user_message = message.content.replace(f"<@{bot.user.id}>", "").strip()
        
        # Fetch the last 10 messages from the channel history
        history = []
        async for msg in message.channel.history(limit=10):
            # Skip the command message itself and empty messages
            if msg.id == message.id or not msg.content:
                continue
            
            author_name = msg.author.display_name
            history.append(f"{author_name}: {msg.content}")

        # Reverse to get chronological order
        history_text = "\n".join(reversed(history))

        # Construct the prompt with history
        full_prompt = (
            f"{ROAST_PROMPT}\n\n"
            f"History:\n{history_text}\n\n"
            f"Current Chat:\n"
            f"{message.author.display_name}: {user_message}\n"
            f"AI:"
        )
        
        async with message.channel.typing():
            response = await generate_response(full_prompt)
        
        await message.reply(response)

    await bot.process_commands(message)

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)