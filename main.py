import csv
import telebot
import random
import requests
import feedparser
from bs4 import BeautifulSoup

# --- НАСТРОЙКИ ---
TOKEN = '8043800793:AAG7CPL1aDMxYC9Z0Wr9x92y9h9oqQhsRYY'
CHANNEL_NAME = '@highconcrete_news'
# -----------------

bot = telebot.TeleBot(TOKEN)

# RSS-ссылки (новости)
RSS_FEEDS = ['https://dwg.ru/rss', 'https://archi.ru/rss/news.xml']

# Выжимка по терраццо
TERRAZZO_DOCS = [
    {"title": "Рецептуры для столешниц (Direct Cast)", "desc": "Бесплатные рецептуры (объёмные пропорции) с AR-стекловолокном.", "url": "https://concretecountertopinstitute.com/free-training/concrete-countertop-mix-recipes/"},
    {"title": "Спецификация NTMA: Epoxy Terrazzo", "desc": "Актуальная спецификация по эпоксидному терраццо. Требования к основанию, пропорции, допуски.", "url": "https://ntma.com/wp-content/uploads/2024/01/Epoxy-Terrazzo-modified-11-20-23.pdf"},
    {"title": "Советские стандарты: мозаичные покрытия", "desc": "ТТК на мозаичное покрытие: состав смеси, укладка, уход.", "url": "https://www.zavodsz.ru/files/gost/TTK_%20Proizvodstvo%20rabot%20po%20ustrojstvu%20mozaichnogo%20pokrytiya%20pola.pdf"},
    {"title": "Технология GFRC для тонкостенных изделий", "desc": "GFRC-рецептура для раковин и мебели. Бэкерный слой 10–12 мм.", "url": "https://www.expressions-ltd.com/pages/gfrc-mix-recipe"}
]

def fetch_and_post():
    content_type = random.choice([1, 2, 3])
    
    if content_type == 1:
        print("Пытаюсь взять новость из RSS...")
        feed_url = random.choice(RSS_FEEDS)
        feed = feedparser.parse(feed_url)
        
        # --- ТОТ САМЫЙ ПРЕДОХРАНИТЕЛЬ ---
        if not feed.entries:
            print(f"❌ RSS-лента {feed_url} пуста или недоступна. Бот отменяет публикацию, чтобы не сломаться.")
            return # Тихо завершаем работу
        # --------------------------------
            
        entry = feed.entries[0]
        post_text = f"🏗 *Индустрия и тренды*\n\n*{entry.title}*\n\nСвежие сводки с рынка проектирования и архитектуры.\n\n🔗 [Читать источник]({entry.link})"
        bot.send_message(CHANNEL_NAME, text=post_text, parse_mode='Markdown')
        print("✅ Опубликована новость из RSS!")

    elif content_type == 2:
        # ФОРУМ ИЗ CSV
        try:
            ru_sites = []
            with open('sites.csv', mode='r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    if row['Регион'] == 'РФ':
                        ru_sites.append(row)
            
            if not ru_sites:
                print("❌ Нет сайтов РФ в базе.")
                return

            site = random.choice(ru_sites)
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(site['Ссылка'], headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            title = soup.title.string.strip() if soup.title else site['Категория']
            
            post_text = f"💬 *Обсуждения и практика*\n\n*{title}*\n\n{site['Описание']}\n\n🔗 [Перейти на площадку]({site['Ссылка']})"
            bot.send_message(CHANNEL_NAME, text=post_text, parse_mode='Markdown')
            print("✅ Опубликован пост с форума/научной базы!")
        except Exception as e:
            print(f"❌ Ошибка базы сайтов: {e}")

    elif content_type == 3:
        # ТЕХКАРТА ТЕРРАЦЦО
        doc = random.choice(TERRAZZO_DOCS)
        post_text = f"🔬 *Технологии и рецептуры*\n\n*{doc['title']}*\n\n{doc['desc']}\n\n🔗 [Изучить документацию]({doc['url']})"
        bot.send_message(CHANNEL_NAME, text=post_text, parse_mode='Markdown')
        print("✅ Опубликована техкарта по терраццо!")

if __name__ == '__main__':
    fetch_and_post()
