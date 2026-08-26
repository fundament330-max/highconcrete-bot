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
    print("Начинаю работу скрипта...")
    content_type = random.choice([1, 2])
    print(f"Выбран тип контента: {content_type}")
    
    if content_type == 1:
        print("Пытаюсь взять новость из RSS...")
        feed_url = random.choice(RSS_FEEDS)
        feed = feedparser.parse(feed_url)
        entry = feed.entries[0]
        post_text = f"**Индустрия и нормативы**\n\n*{entry.title}*\n\n[Читать подробнее]({entry.link})"
        bot.send_message(CHANNEL_NAME, text=post_text, parse_mode='Markdown')
        print("Новость из RSS успешно отправлена!")

    elif content_type == 2:
        print("Пытаюсь прочитать Гугл Таблицу...")
        response = requests.get(SHEET_URL)
        response.encoding = 'utf-8'
        text_data = response.text
        
        reader = list(csv.DictReader(io.StringIO(text_data)))
        if not reader:
            print("ОШИБКА: Таблица пустая или не удалось прочитать заголовки!")
            return
            
        print(f"Заголовки в таблице: {reader[0].keys()}")
        
        # Ищем РФ, игнорируя случайные пробелы и регистр букв
        ru_sites = []
        for row in reader:
            region_key = next((k for k in row.keys() if k and 'регион' in k.lower()), None)
            if region_key and row.get(region_key) and 'рф' in row.get(region_key).lower():
                ru_sites.append(row)
        
        print(f"Найдено сайтов РФ: {len(ru_sites)}")
        
        if not ru_sites:
            print("ОШИБКА: Не найдено ни одной строки с регионом РФ! Выхожу.")
            return
            
        site = random.choice(ru_sites)
        print("Выбран сайт для публикации, пробую отправить...")
        
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            site_resp = requests.get(site.get('Ссылка', ''), headers=headers, timeout=10)
            soup = BeautifulSoup(site_resp.text, 'html.parser')
            title = soup.title.string.strip() if soup.title else site.get('Категория', 'Форум')
            
            post_text = f"**{site.get('Категория', 'Форум')}**\n\n*{title}*\n\n{site.get('Описание', '')}\n\n[Перейти на площадку]({site.get('Ссылка', '')})"
            bot.send_message(CHANNEL_NAME, text=post_text, parse_mode='Markdown')
            print("Пост успешно отправлен!")
        except Exception as e:
            print(f"Отправляю текстовую заглушку. Ошибка парсинга: {e}")
            post_text = f"**{site.get('Категория', 'Форум')}**\n\n*{site.get('Источник', '')}*\n\n{site.get('Описание', '')}\n\n[Перейти на площадку]({site.get('Ссылка', '')})"
            bot.send_message(CHANNEL_NAME, text=post_text, parse_mode='Markdown')
            print("Пост-заглушка успешно отправлен!")

if __name__ == '__main__':
    fetch_and_post()
