FROM python:3.8.0-buster

# Install dependecies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy source code
COPY . .

# Run the bot
CMD ["python", "voicecreate.py"]
