import csv
import telebot
import random
import requests
import feedparser
from bs4 import BeautifulSoup
import io

# НАСТРОЙКИ
TOKEN = '8043800793:AAG7CPL1aDMxYC9Z0Wr9x92y9h9oqQhsRYY'
CHANNEL_NAME = '@highconcrete_news'
SHEET_URL = 'https://docs.google.com/spreadsheets/d/1znszruyFQu9AuXpe196rtBfLYB86MfFbnhZpSMsxgxE/export?format=csv&gid=0'

bot = telebot.TeleBot(TOKEN)
RSS_FEEDS = ['https://dwg.ru/rss', 'https://archi.ru/rss/news.xml']

def fetch_and_post():
    # Теперь скрипт выбирает только между реальными новостями и ТВОЕЙ базой из таблицы
    content_type = random.choice([1, 2])
    
    if content_type == 1:
        # Парсим реальные новости
        feed_url = random.choice(RSS_FEEDS)
        feed = feedparser.parse(feed_url)
        entry = feed.entries[0]
        post_text = f"**Индустрия и нормативы**\n\n*{entry.title}*\n\n[Читать подробнее]({entry.link})"
        bot.send_message(CHANNEL_NAME, text=post_text, parse_mode='Markdown')

    elif content_type == 2:
        # Берем данные ИЗ ТВОЕЙ ГУГЛ ТАБЛИЦЫ
        response = requests.get(SHEET_URL)
        response.encoding = 'utf-8'
        reader = csv.DictReader(io.StringIO(response.text))
        ru_sites = [row for row in reader if row.get('Регион') == 'РФ']
        
        if not ru_sites:
            return
            
        site = random.choice(ru_sites)
        
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            site_resp = requests.get(site['Ссылка'], headers=headers, timeout=10)
            soup = BeautifulSoup(site_resp.text, 'html.parser')
            title = soup.title.string.strip() if soup.title else site['Категория']
            
            post_text = f"**{site['Категория']}**\n\n*{title}*\n\n{site['Описание']}\n\n[Перейти на площадку]({site['Ссылка']})"
            bot.send_message(CHANNEL_NAME, text=post_text, parse_mode='Markdown')
        except:
            # На случай, если сайт долго отвечает, все равно публикуем информацию из таблицы
            post_text = f"**{site['Категория']}**\n\n*{site['Источник']}*\n\n{site['Описание']}\n\n[Перейти на площадку]({site['Ссылка']})"
            bot.send_message(CHANNEL_NAME, text=post_text, parse_mode='Markdown')

if __name__ == '__main__':
    fetch_and_post()
