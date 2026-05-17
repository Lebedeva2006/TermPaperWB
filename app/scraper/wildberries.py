import undetected_chromedriver as uc
import time
from urllib.parse import quote
from bs4 import BeautifulSoup
from typing import List, Dict


def parse_products(html: str) -> List[Dict]:
    soup = BeautifulSoup(html, 'html.parser')
    cards = soup.select('article.product-card')
    results = []
    for card in cards:
        title_tag = card.select_one('.product-card__name')
        title = title_tag.text.strip().lstrip('/').strip() if title_tag else ''

        price = 0.0
        price_tag = card.select_one('ins.price__lower-price')
        if price_tag:
            price_text = price_tag.text.replace('₽', '').replace(' ', '').replace('\u00a0', '').strip()
            try:
                price = float(price_text)
            except:
                pass

        link_tag = card.select_one('a.product-card__link')
        link = link_tag.get('href') if link_tag else ''
        if link and not link.startswith('http'):
            link = 'https://www.wildberries.ru' + link
        external_id = card.get('data-nm-id', '') or (link.split('/')[-2] if link else '')

        rating = 0.0
        rating_tag = card.select_one('.address-rate-mini')
        if rating_tag:
            try:
                rating = float(rating_tag.text.replace(',', '.').strip())
            except:
                pass

        reviews = 0
        reviews_tag = card.select_one('.product-card__count')
        if reviews_tag:
            reviews_text = reviews_tag.text.replace('оценки', '').replace('оценок', '').replace(' ', '').strip()
            try:
                reviews = int(reviews_text)
            except:
                pass

        results.append({
            "marketplace": "wildberries",
            "external_id": external_id,
            "title": title,
            "price": price,
            "rating": rating,
            "reviews_count": reviews,
            "url": link,
        })
    return results


def search(query: str) -> List[Dict]:
    url = f"https://www.wildberries.ru/catalog/0/search.aspx?search={quote(query)}&frating=1&foriginal=1&meta_charcs=true"

    options = uc.ChromeOptions()
    options.binary_location = "/usr/bin/google-chrome-stable"
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    driver = uc.Chrome(options=options, headless=True)
    driver.get(url)

    time.sleep(15)
    html = driver.page_source
    driver.quit()

    products = parse_products(html)
    filtered = [p for p in products if p['rating'] > 4.7 and p['reviews_count'] > 30]
    sorted_products = sorted(filtered, key=lambda p: p['price'])
    return sorted_products[:5]


if __name__ == "__main__":
    query = input("Введите товар для поиска: ")
    results = search(query)
    for p in results:
        print(p)
