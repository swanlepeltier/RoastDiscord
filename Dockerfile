FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN pip install discord.py aiohttp

# Copy source code
COPY main.py .
COPY roast.txt .

# Run the bot
CMD ["python", "main.py"]
