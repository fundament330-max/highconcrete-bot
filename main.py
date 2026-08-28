import csv
import telebot
import random
import requests
import feedparser
import io
from bs4 import BeautifulSoup

# --- НАСТРОЙКИ ---
TOKEN = '8043800793:AAG7CPL1aDMxYC9Z0Wr9x92y9h9oqQhsRYY' # Токен бота
CHANNEL_NEWS = '@highconcrete_news' # Канал для новостей и форумов
CHANNEL_NORMS = '@highconcrete_library' # Канал для техкарт
GOOGLE_SHEET_URL = 'https://docs.google.com/spreadsheets/d/1Gz9QdwnD4-GJsLr2VqnHawB75TOngXjrJYYKu1XjwEw/export?format=csv'
# -----------------

bot = telebot.TeleBot(TOKEN)

def fetch_and_post():
    print("Скачиваю единую базу из Google Таблицы...")
    try:
        response_csv = requests.get(GOOGLE_SHEET_URL)
        response_csv.raise_for_status() 
        
        # --- ЖЕЛЕЗОБЕТОННАЯ ЗАЩИТА ОТ НЕВИДИМЫХ СИМВОЛОВ ГУГЛА ---
        response_csv.encoding = 'utf-8-sig' 
        csv_data = response_csv.text
        
        print("ОТВЕТ ОТ ГУГЛА (первые 300 символов):")
        print(csv_data[:300])
        
        reader = csv.DictReader(io.StringIO(csv_data))
        if reader.fieldnames:
            reader.fieldnames = [str(col).strip() for col in reader.fieldnames]
            
        rss_feeds = []
        forums = []
        tech_docs = []
        
        for row in reader:
            content_type = row.get('Тип', '').strip().lower()
            link = row.get('Ссылка', '').strip()
            region = row.get('Регион', '').strip()
            
            if content_type == 'rss' and link:
                rss_feeds.append(row)
            elif content_type == 'форум' and region == 'РФ' and link:
                forums.append(row)
            elif content_type == 'техкарта' and link:
                tech_docs.append(row)
                
    except Exception as e:
        print(f"❌ Ошибка загрузки таблицы: {e}")
        return

    available_categories = []
    if rss_feeds: available_categories.append(1)
    if forums: available_categories.append(2)
    if tech_docs: available_categories.append(3)
    
    if not available_categories:
        print("❌ В таблице нет данных для публикации!")
        return
        
    choice = random.choice(available_categories)
    
    if choice == 1: 
        print("Выбрана рубрика: RSS-новости")
        feed_row = random.choice(rss_feeds)
        feed = feedparser.parse(feed_row['Ссылка'])
        
        if not feed.entries:
            print(f"❌ Лента {feed_row['Ссылка']} пуста.")
            return
            
        entry = feed.entries[0]
        
        image_url = None
        if 'enclosures' in entry and entry.enclosures:
            for enc in entry.enclosures:
                if 'image' in enc.get('type', ''):
                    image_url = enc.href
                    break
        if not image_url and 'media_thumbnail' in entry and entry.media_thumbnail:
             image_url = entry.media_thumbnail[0]['url']
             
        post_text = f"🏗 *Индустрия и тренды*\n\n*{entry.title}*\n\nСвежие сводки с рынка проектирования.\n\n🔗 [Читать источник]({entry.link})"
        
        if image_url:
            try:
                bot.send_photo(CHANNEL_NEWS, photo=image_url, caption=post_text, parse_mode='Markdown')
                print("✅ Опубликована новость с фото!")
            except:
                bot.send_message(CHANNEL_NEWS, text=post_text, parse_mode='Markdown')
        else:
            bot.send_message(CHANNEL_NEWS, text=post_text, parse_mode='Markdown')

    elif choice == 2: 
        print("Выбрана рубрика: Форумы")
        site = random.choice(forums)
        headers = {'User-Agent': 'Mozilla/5.0'}
        
        try:
            response = requests.get(site['Ссылка'], headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            title = soup.title.string.strip() if soup.title and soup.title.string else site.get('Название', 'Форум')
            
            og_img = soup.find('meta', property='og:image')
            image_url = og_img['content'] if og_img else None
            
            post_text = f"💬 *Обсуждения и практика*\n\n*{title}*\n\n{site.get('Описание', '')}\n\n🔗 [Перейти на площадку]({site['Ссылка']})"
            
            if image_url:
                try:
                    bot.send_photo(CHANNEL_NEWS, photo=image_url, caption=post_text, parse_mode='Markdown')
                    print("✅ Опубликован пост с форума с фото!")
                except:
                    bot.send_message(CHANNEL_NEWS, text=post_text, parse_mode='Markdown')
            else:
                bot.send_message(CHANNEL_NEWS, text=post_text, parse_mode='Markdown')
        except Exception as e:
            print(f"❌ Ошибка парсинга форума: {e}")

    elif choice == 3: 
        print("Выбрана рубрика: Техкарты")
        doc = random.choice(tech_docs)
        post_text = f"🔬 *Технологии и рецептуры*\n\n*{doc.get('Название', 'Документация')}*\n\n{doc.get('Описание', '')}\n\n🔗 [Изучить документацию]({doc['Ссылка']})"
        image_url = doc.get('Фото', '').strip()
        
        if image_url:
            try:
                bot.send_photo(CHANNEL_NORMS, photo=image_url, caption=post_text, parse_mode='Markdown')
                print("✅ Опубликована техкарта с фото!")
            except:
                bot.send_message(CHANNEL_NORMS, text=post_text, parse_mode='Markdown')
        else:
            bot.send_message(CHANNEL_NORMS, text=post_text, parse_mode='Markdown')
            print("✅ Опубликована техкарта (текст)!")

if __name__ == '__main__':
    fetch_and_post()
