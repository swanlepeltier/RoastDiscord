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
        
        # Construct the prompt
        # KoboldCPP usually handles raw completion. We need to structure it like a chat or just raw continuation.
        # Since we are using a roast persona, let's treat it as a chat or instruction.
        # Simple format: System Prompt + User Query + AI Response Start
        
        full_prompt = f"{ROAST_PROMPT}\n\nUser: {user_message}\nAI:"
        
        async with message.channel.typing():
            response = await generate_response(full_prompt)
        
        await message.reply(response)

    await bot.process_commands(message)

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)