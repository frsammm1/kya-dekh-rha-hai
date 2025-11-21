from flask import Flask
import logging
import time
from threading import Thread

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Keep-alive counter
counter = 0

def heartbeat():
    """Send logs every second to keep instance alive"""
    global counter
    while True:
        counter += 1
        logger.info(f"💚 Heartbeat #{counter} - Bot is alive and running")
        time.sleep(1)

# Start heartbeat in background
Thread(target=heartbeat, daemon=True).start()

@app.route('/')
def home():
    logger.info("🏠 Health check received")
    return f"✅ Bot Running! Heartbeats: {counter}", 200

@app.route('/health')
def health():
    logger.info("💊 Health endpoint pinged")
    return "OK", 200

@app.route('/ping')
def ping():
    logger.info("🏓 Ping received")
    return "PONG", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
