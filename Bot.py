import telebot
import requests
import time
from datetime import datetime
import pytz
import jdatetime
import logging
import os
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# Logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
# Read the API token from GitHub Secrets
API_TOKEN = os.environ.get('API_TOKEN')
if not API_TOKEN:
    logger.error("API_TOKEN not found in environment variables!")
    exit()

CHANNEL_ID = '@proxyfig'  # Your new channel ID
# List of new proxy URLs
PROXY_URLS = [
    'https://raw.githubusercontent.com/yebekhe/TelegramV2rayCollector/main/sub/mtproto',
    'https://raw.githubusercontent.com/ip-scanner/proxy-list/main/proxies/mtproto.txt',
    'https://raw.githubusercontent.com/ALIILAPRO/Proxy/main/mtproto.txt'
]

# Initialize the bot
bot = telebot.TeleBot(API_TOKEN)

# Function to fetch proxies from the given URLs
def fetch_proxies():
    all_proxies = set()  # Use a set to automatically handle duplicates
    for url in PROXY_URLS:
        try:
            response = requests.get(url)
            response.raise_for_status()  # Raise an exception for HTTP errors
            proxies = response.text.splitlines()
            # Filter out empty lines and specific unwanted lines
            valid_proxies = {p for p in proxies if p.strip() and p.startswith('https://t.me/proxy?')}
            all_proxies.update(valid_proxies)
            logger.info(f"Fetched {len(valid_proxies)} valid proxies from {url}.")
        except requests.RequestException as e:
            logger.error(f"Error fetching proxies from {url}: {e}")
    
    logger.info(f"Total unique proxies fetched: {len(all_proxies)}")
    return list(all_proxies)

# Function to send a message with multiple inline buttons to the Telegram channel
def send_message_with_buttons(proxies):
    tehran_tz = pytz.timezone('Asia/Tehran')
    now = datetime.now(tehran_tz)
    j_now = jdatetime.datetime.fromgregorian(datetime=now)
    
    date_str = j_now.strftime("%Y/%m/%d")
    time_str = now.strftime("%H:%M:%S")
    
    text = (
        f"✅ **New Proxies Ready!**\n"
        f"ᴘᴏᴡᴇʀᴇᴅ ʙʏ ᴘʀᴏxʏғɪɢ 🚀\n\n"
        f"🕘 {time_str} | 📅 {date_str}"
    )
    
    markup = InlineKeyboardMarkup(row_width=2)
    if proxies:
        buttons = []
        for i, proxy in enumerate(proxies):
            button_text = f"🔗 Connect Proxy #{i+1}"
            button = InlineKeyboardButton(text=button_text, url=proxy)
            buttons.append(button)
        
        # Adding buttons to markup
        markup.add(*buttons)
    
    bot.send_message(CHANNEL_ID, text, reply_markup=markup, parse_mode="Markdown")
    logger.info(f"Sent a message with {len(proxies)} proxy buttons to {CHANNEL_ID}.")

# Function to send proxies to the Telegram channel in batches
def send_proxies_to_channel(proxies):
    batch_size = 5  # Number of proxies per message
    for i in range(0, len(proxies), batch_size):
        batch = proxies[i:i + batch_size]
        if batch:
            try:
                send_message_with_buttons(batch)
                # Delay between messages to avoid hitting Telegram API limits
                if i + batch_size < len(proxies):
                    logger.info("Waiting for 10 seconds before sending the next batch...")
                    time.sleep(10)
            except Exception as e:
                logger.error(f"Error sending message: {e}")

# Main function to run the bot
def main():
    logger.info("Starting proxy fetching process...")
    proxies = fetch_proxies()
    if proxies:
        send_proxies_to_channel(proxies)
        logger.info("All proxies have been sent successfully.")
    else:
        logger.warning("No proxies were fetched. Exiting.")

# Entry point of the script
if __name__ == "__main__":
    main()
