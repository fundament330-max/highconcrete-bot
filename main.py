import csv
import telebot
import random
import requests
import feedparser
from bs4 import BeautifulSoup

# --- НАСТРОЙКИ ---
TOKEN = '8043800793:AAG7CPL1aDMxYC9Z0Wr9x92y9h9oqQhsRYY' # Не забудь вставить свой токен!
CHANNEL_NAME = '@highconcrete_news'
# -----------------

bot = telebot.TeleBot(TOKEN)

RSS_FEEDS = ['https://dwg.ru/rss', 'https://archi.ru/rss/news.xml']

TERRAZZO_DOCS = [
    {"title": "Рецептуры для столешниц (Direct Cast)", "desc": "Бесплатные рецептуры (объёмные пропорции) с AR-стекловолокном.", "url": "https://concretecountertopinstitute.com/free-training/concrete-countertop-mix-recipes/", "img": "https://stroy-podskazka.ru/images/article/orig/2019/08/izgotovlenie-betonnoj-stoleshnicy-svoimi-rukami-5.jpg"},
    {"title": "Спецификация NTMA: Epoxy Terrazzo", "desc": "Актуальная спецификация по эпоксидному терраццо. Требования к основанию, пропорции, допуски.", "url": "https://ntma.com/wp-content/uploads/2024/01/Epoxy-Terrazzo-modified-11-20-23.pdf", "img": "https://www.terrazzco.com/wp-content/uploads/2017/04/Epoxy-Terrazzo-Design-1024x682.jpg"},
    {"title": "Советские стандарты: мозаичные покрытия", "desc": "ТТК на мозаичное покрытие: состав смеси, укладка, уход.", "url": "https://www.zavodsz.ru/files/gost/TTK_%20Proizvodstvo%20rabot%20po%20ustrojstvu%20mozaichnogo%20pokrytiya%20pola.pdf", "img": "https://pol-master.com/wp-content/uploads/2014/11/mozaichnyj-betonnyj-pol.jpg"},
    {"title": "Технология GFRC для тонкостенных изделий", "desc": "GFRC-рецептура для раковин и мебели. Бэкерный слой 10–12 мм.", "url": "https://www.expressions-ltd.com/pages/gfrc-mix-recipe", "img": "https://cdn.shopify.com/s/files/1/1393/7797/files/GFRC_1024x1024.jpg"}
]

def fetch_and_post():
    content_type = random.choice([1, 2, 3])
    
    if content_type == 1:
        print("Пытаюсь взять новость из RSS...")
        feed_url = random.choice(RSS_FEEDS)
        feed = feedparser.parse(feed_url)
        
        if not feed.entries:
            print(f"❌ RSS-лента {feed_url} пуста. Отмена.")
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
        
        post_text = f"🏗 *Индустрия и тренды*\n\n*{entry.title}*\n\nСвежие сводки с рынка проектирования и архитектуры.\n\n🔗 [Читать источник]({entry.link})"
        
        if image_url:
            try:
                bot.send_photo(CHANNEL_NAME, photo=image_url, caption=post_text, parse_mode='Markdown')
                print("✅ Опубликована новость с фото!")
            except Exception as e:
                print(f"⚠️ Ошибка загрузки фото ({e}). Публикую текст.")
                bot.send_message(CHANNEL_NAME, text=post_text, parse_mode='Markdown')
        else:
            bot.send_message(CHANNEL_NAME, text=post_text, parse_mode='Markdown')
            print("✅ Опубликована новость (текст)!")

    elif content_type == 2:
        try:
            ru_sites = []
            with open('sites.csv', mode='r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    if row['Регион'] == 'РФ':
                        ru_sites.append(row)
            
            if not ru_sites:
                return

            site = random.choice(ru_sites)
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(site['Ссылка'], headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            title = soup.title.string.strip() if soup.title else site['Категория']
            
            og_img = soup.find('meta', property='og:image')
            image_url = og_img['content'] if og_img else None
            
            post_text = f"💬 *Обсуждения и практика*\n\n*{title}*\n\n{site['Описание']}\n\n🔗 [Перейти на площадку]({site['Ссылка']})"
            
            if image_url:
                try:
                    bot.send_photo(CHANNEL_NAME, photo=image_url, caption=post_text, parse_mode='Markdown')
                    print("✅ Опубликован пост с форума с фото!")
                except Exception as e:
                    print(f"⚠️ Ошибка загрузки фото ({e}). Публикую текст.")
                    bot.send_message(CHANNEL_NAME, text=post_text, parse_mode='Markdown')
            else:
                bot.send_message(CHANNEL_NAME, text=post_text, parse_mode='Markdown')
                print("✅ Опубликован пост с форума (текст)!")
        except Exception as e:
            print(f"❌ Ошибка базы сайтов: {e}")

    elif content_type == 3:
        doc = random.choice(TERRAZZO_DOCS)
        post_text = f"🔬 *Технологии и рецептуры*\n\n*{doc['title']}*\n\n{doc['desc']}\n\n🔗 [Изучить документацию]({doc['url']})"
        image_url = doc.get("img")
        
        if image_url:
            try:
                bot.send_photo(CHANNEL_NAME, photo=image_url, caption=post_text, parse_mode='Markdown')
                print("✅ Опубликована техкарта с фото!")
            except Exception as e:
                print(f"⚠️ Ошибка загрузки фото ({e}). Публикую текст.")
                bot.send_message(CHANNEL_NAME, text=post_text, parse_mode='Markdown')
        else:
            bot.send_message(CHANNEL_NAME, text=post_text, parse_mode='Markdown')
            print("✅ Опубликована техкарта (текст)!")

if __name__ == '__main__':
    fetch_and_post()
