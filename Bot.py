import telebot
import requests
import time
from datetime import datetime
import pytz
import jdatetime
import logging
import os
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Read the API token from GitHub Secrets
API_TOKEN = os.environ.get('API_TOKEN')
if not API_TOKEN:
    logger.error("API_TOKEN not found in environment variables!")
    exit()

CHANNEL_ID = '@proxyfig'  # Your channel ID

# List of websites to scrape for proxies (from the specified repository)
PROVIDER_URLS = [
    "https://mtpro.xyz/api",
    "https://proxy.mtproto.co/api",
    "http://www.mtg-proxy.com/api",
    "https://proxies.asrbilisim.com/api/mtproto"
]

# Initialize the bot
bot = telebot.TeleBot(API_TOKEN)


# --- New Scraping Logic ---
async def fetch_html(session, url):
    """Fetches HTML content from a single URL."""
    try:
        async with session.get(url, timeout=15) as response:
            if response.status == 200:
                return await response.text()
            else:
                logger.warning(f"Failed to fetch {url}. Status: {response.status}")
                return None
    except Exception as e:
        logger.error(f"Error fetching {url}: {e}")
        return None

async def fetch_all_proxies():
    """Scrapes all provider URLs concurrently to find proxy links."""
    all_proxies = set()
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'}
    
    async with aiohttp.ClientSession(headers=headers) as session:
        tasks = [fetch_html(session, url) for url in PROVIDER_URLS]
        html_contents = await asyncio.gather(*tasks)
        
        for content in html_contents:
            if content:
                # Using BeautifulSoup to parse the HTML content
                soup = BeautifulSoup(content, 'lxml')
                # Finding all <a> tags, as proxy links are usually in them
                for a_tag in soup.find_all('a'):
                    href = a_tag.get('href')
                    if href and ('tg://proxy?' in href or '/proxy?' in href):
                        # Clean up the link
                        if href.startswith('/proxy?'):
                           href = 'https://t.me' + href
                        all_proxies.add(href)

    logger.info(f"Total unique proxies found after scraping: {len(all_proxies)}")
    return list(all_proxies)


# --- Telegram Bot Functions (Mostly Unchanged) ---
def send_message_with_buttons(proxies):
    tehran_tz = pytz.timezone('Asia/Tehran')
    now = datetime.now(tehran_tz)
    j_now = jdatetime.datetime.fromgregorian(datetime=now)
    
    date_str = j_now.strftime("%Y/%m/%d")
    time_str = now.strftime("%H:%M:%S")
    
    text = (
        f"✅ **Fresh Proxies Scraped!**\n"
        f"ᴘᴏᴡᴇʀᴇᴅ ʙʏ ᴘʀᴏxʏғɪɢ 🚀\n\n"
        f"🕘 {time_str} | 📅 {date_str}"
    )
    
    markup = InlineKeyboardMarkup(row_width=2)
    if proxies:
        buttons = [InlineKeyboardButton(text=f"🔗 Connect Proxy #{i+1}", url=proxy) for i, proxy in enumerate(proxies)]
        markup.add(*buttons)
    
    bot.send_message(CHANNEL_ID, text, reply_markup=markup, parse_mode="Markdown")
    logger.info(f"Sent a message with {len(proxies)} proxy buttons to {CHANNEL_ID}.")

def send_proxies_to_channel(proxies):
    batch_size = 5
    for i in range(0, len(proxies), batch_size):
        batch = proxies[i:i + batch_size]
        if batch:
            try:
                send_message_with_buttons(batch)
                if i + batch_size < len(proxies):
                    logger.info("Waiting 10 seconds before the next batch...")
                    time.sleep(10)
            except Exception as e:
                logger.error(f"Error sending message: {e}")

# --- Main Execution ---
def main():
    logger.info("Starting proxy scraping process...")
    # Run the asynchronous scraping function
    proxies = asyncio.run(fetch_all_proxies())
    
    if proxies:
        send_proxies_to_channel(proxies)
        logger.info("All proxies have been sent successfully.")
    else:
        logger.warning("No proxies were found after scraping. Exiting.")

if __name__ == "__main__":
    main()
