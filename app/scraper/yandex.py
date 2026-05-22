import undetected_chromedriver as uc
import time
from urllib.parse import quote
from bs4 import BeautifulSoup
import re
from typing import List, Dict

def parse_products(html: str) -> List[Dict]:
    soup = BeautifulSoup(html, 'html.parser')
    cards = soup.find_all(attrs={"data-zone-name": "productSnippet"})
    results = []
    for card in cards:
        title_tag = card.find(attrs={"data-auto": "snippet-title"})
        title = title_tag.get_text(strip=True) if title_tag else ''

        price = 0
        price_tag = card.find(attrs={"data-auto": "snippet-price-current"})
        if price_tag:
            price_text = price_tag.get_text(strip=True)
            digits = re.sub(r'\D', '', price_text)
            if digits:
                price = int(digits)

        rating = 0
        reviews = 0
        rating_block = card.find(attrs={"data-auto": "reviews"})
        if rating_block:
            rating_span = rating_block.find(class_=re.compile(r'rating__value|ds-rating__value'))
            if rating_span:
                rating_text = rating_span.get_text(strip=True)
                rating_match = re.search(r'(\d+(?:[.,]\d+)?)', rating_text)
                if rating_match:
                    rating = float(rating_match.group(1).replace(',', '.'))
            reviews_text = rating_block.get_text(separator=' ')
            reviews_match = re.search(r'\((\d+)\)', reviews_text)
            if reviews_match:
                reviews = int(reviews_match.group(1))
            count_match = re.search(r'\((\d+)\)\s*·\s*(\d+)', reviews_text)
            if count_match:
                reviews = int(count_match.group(1))

        link_tag = card.find('a', href=re.compile(r'/card/'))
        link = ''
        if link_tag:
            link = link_tag.get('href')
            if link.startswith('/'):
                link = 'https://market.yandex.ru' + link

        if title and price:
            results.append({
                "marketplace": "yandex",
                "title": title,
                "price": price,
                "rating": rating,
                "reviews_count": reviews,
                "url": link,
            })
    return results


def search(query: str) -> List[Dict]:
    url = f"https://market.yandex.ru/search?text={quote(query)}&qrfrom=1"

    options = uc.ChromeOptions()
    options.binary_location = "/usr/bin/google-chrome-stable"
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    options.add_argument('--headless')
    driver = uc.Chrome(options=options, version_main=148)
    driver.get(url)

    time.sleep(5)
    for _ in range(5):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)

    html = driver.page_source
    driver.quit()

    products = parse_products(html)
    filtered = [p for p in products if p['rating'] > 4.5 and p['reviews_count'] >= 30]
    sorted_products = sorted(filtered, key=lambda p: p['price'])
    return sorted_products[:5]


if __name__ == "__main__":
    query = input("Введите товар для поиска: ")
    results = search(query)
    if results:
        for p in results:
            print(p)
    else:
        print("Нет товаров, соответствующих условиям: рейтинг > 4.5 и отзывов > 30")