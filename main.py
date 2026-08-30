import csv
import telebot
import random
import requests
import feedparser
import io
import os
import time
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator

# --- НАСТРОЙКИ ---
TOKEN = '8043800793:AAG7CPL1aDMxYC9Z0Wr9x92y9h9oqQhsRYY' 
CHANNEL_NEWS = '@highconcrete_news'
CHANNEL_NORMS = '@highconcrete_library'
GOOGLE_SHEET_URL = 'https://docs.google.com/spreadsheets/d/1Gz9QdwnD4-GJsLr2VqnHawB75TOngXjrJYYKu1XjwEw/export?format=csv'
HISTORY_FILE = 'posted_urls.txt'
# -----------------

bot = telebot.TeleBot(TOKEN)

def translate_to_ru(text):
    if not text: 
        return ""
    try:
        return GoogleTranslator(source='auto', target='ru').translate(text)
    except Exception as e:
        print(f"Ошибка перевода: {e}")
        return text

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            return set(f.read().splitlines())
    return set()

def save_history(url):
    with open(HISTORY_FILE, 'a', encoding='utf-8') as f:
        f.write(f"{url}\n")

def fetch_and_post():
    history = load_history()
    print(f"Скачиваю базу... В памяти записей: {len(history)}")
    
    try:
        response_csv = requests.get(GOOGLE_SHEET_URL)
        response_csv.raise_for_status() 
        response_csv.encoding = 'utf-8-sig' 
        csv_data = response_csv.text
        
        reader = csv.DictReader(io.StringIO(csv_data))
        if reader.fieldnames:
            reader.fieldnames = [str(col).strip() for col in reader.fieldnames]
            
        rss_feeds, forums, tech_docs = [], [], []
        
        for row in reader:
            content_type = row.get('Тип', '').strip().lower()
            link = row.get('Ссылка', '').strip()
            
            if content_type == 'rss' and link:
                rss_feeds.append(row)
            elif content_type == 'форум' and link and link not in history:
                forums.append(row)
            elif content_type == 'техкарта' and link and link not in history:
                tech_docs.append(row)
                
    except Exception as e:
        print(f"❌ Ошибка загрузки таблицы: {e}")
        return

    # --- 1. ПРИОРИТЕТНАЯ ОБРАБОТКА ТЕХКАРТ (БЕЗ РУЛЕТКИ) ---
    if tech_docs:
        print(f"Найдено новых техкарт: {len(tech_docs)}. Отправляем в архив...")
        for doc in tech_docs:
            try:
                check = requests.head(doc['Ссылка'], headers={'User-Agent': 'Mozilla/5.0'}, timeout=5, allow_redirects=True)
                if check.status_code >= 400 and check.status_code != 405:
                    print(f"❌ Битая ссылка ({check.status_code}): {doc['Ссылка']}")
                    save_history(doc['Ссылка'])
                    continue
            except:
                pass

            ru_title = translate_to_ru(doc.get('Название', 'Документация'))
            ru_desc = translate_to_ru(doc.get('Описание', ''))
            post_text = f"*{ru_title}*\n{ru_desc}\n{doc['Ссылка']}"
            image_url = doc.get('Фото', '').strip()
            
            try:
                if image_url: 
                    bot.send_photo(CHANNEL_NORMS, photo=image_url, caption=post_text, parse_mode='Markdown')
                else: 
                    bot.send_message(CHANNEL_NORMS, text=post_text, parse_mode='Markdown')
                save_history(doc['Ссылка'])
                print(f"✅ Техкарта сохранена в базу: {ru_title}")
                time.sleep(2)
            except Exception as e:
                print("❌ Ошибка сохранения техкарты:", e)

    # --- 2. РУЛЕТКА ДЛЯ НОВОСТЕЙ И ФОРУМОВ ---
    available_categories = []
    if rss_feeds: available_categories.append(1)
    if forums: available_categories.append(2)
    
    if not available_categories:
        print("❌ Нет новых материалов для новостного канала!")
        return
        
    choice = random.choice(available_categories)
    
    if choice == 1: 
        print("Рубрика новостей: RSS")
        feed_row = random.choice(rss_feeds)
        feed = feedparser.parse(feed_row['Ссылка'])
        
        entry = None
        for item in feed.entries:
            if item.link not in history:
                entry = item
                break
                
        if not entry:
            print(f"❌ В этой RSS-ленте нет свежих новостей.")
            return
            
        image_url = None
        if 'enclosures' in entry and entry.enclosures:
            for enc in entry.enclosures:
                if 'image' in enc.get('type', ''):
                    image_url = enc.href
                    break
        if not image_url and 'media_thumbnail' in entry and entry.media_thumbnail:
             image_url = entry.media_thumbnail[0]['url']
             
        ru_title = translate_to_ru(entry.title)
        post_text = f"🏗 *Индустрия и тренды*\n\n*{ru_title}*\n\nСвежие сводки с рынка.\n\n🔗 [Читать источник]({entry.link})"
        
        try:
            if image_url: bot.send_photo(CHANNEL_NEWS, photo=image_url, caption=post_text, parse_mode='Markdown')
            else: bot.send_message(CHANNEL_NEWS, text=post_text, parse_mode='Markdown')
            save_history(entry.link)
            print("✅ Опубликована новость!")
        except Exception as e:
            print("❌ Ошибка отправки:", e)

    elif choice == 2: 
        print("Рубрика новостей: Форумы")
        site = random.choice(forums)
        headers = {'User-Agent': 'Mozilla/5.0'}
        
        try:
            response = requests.get(site['Ссылка'], headers=headers, timeout=10)
            if response.status_code >= 400:
                print(f"❌ Битая ссылка ({response.status_code}): {site['Ссылка']}")
                save_history(site['Ссылка']) 
                return
                
            soup = BeautifulSoup(response.text, 'html.parser')
            title = soup.title.string.strip() if soup.title and soup.title.string else site.get('Название', 'Форум')
            
            og_img = soup.find('meta', property='og:image')
            image_url = og_img['content'] if og_img else None
            
            ru_title = translate_to_ru(title)
            ru_desc = translate_to_ru(site.get('Описание', ''))
            
            post_text = f"💬 *Обсуждения и практика*\n\n*{ru_title}*\n\n{ru_desc}\n\n🔗 [Перейти на площадку]({site['Ссылка']})"
            
            if image_url:
                try: bot.send_photo(CHANNEL_NEWS, photo=image_url, caption=post_text, parse_mode='Markdown')
                except: bot.send_message(CHANNEL_NEWS, text=post_text, parse_mode='Markdown')
            else:
                bot.send_message(CHANNEL_NEWS, text=post_text, parse_mode='Markdown')
                
            save_history(site['Ссылка'])
            print("✅ Опубликован пост с форума!")
        except Exception as e:
            print(f"❌ Ошибка парсинга форума: {e}")
            save_history(site['Ссылка'])

if __name__ == '__main__':
    fetch_and_post()
