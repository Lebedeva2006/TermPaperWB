import asyncio
from fastapi import FastAPI, Depends, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from fastapi.staticfiles import StaticFiles
from app.database import engine, Base, get_db
from app.models.product import Product
from app.scraper.wildberries import search as search_wildberries
from app.scraper.yandex import search as search_yandex

app = FastAPI(title="Marketplace Analyzer")
app.mount("/static", StaticFiles(directory="static"), name="static")

Base.metadata.create_all(bind=engine)


@app.get("/", response_class=HTMLResponse)
async def home():
    with open("templates/index.html", "r", encoding="utf-8") as f:
        return f.read()


@app.get("/test-db")
def test_database(db: Session = Depends(get_db)):
    try:
        count = db.query(Product).count()
        return {
            "status": "ok",
            "message": "БД подключена!",
            "products_in_db": count
        }
    except SQLAlchemyError as e:
        return {
            "status": "error",
            "message": f"Не удалось получить данные из БД: {e}",
        }


@app.get("/search")
async def search_products(q: str = Query(..., min_length=1)):
    def normalize_product(item: dict) -> dict:
        return {
            "marketplace": item.get("marketplace", "unknown"),
            "title": item.get("title", ""),
            "price": float(item.get("price", 0) or 0),
            "rating": float(item.get("rating", 0) or 0),
            "reviews_count": int(item.get("reviews_count", item.get("reviews", 0)) or 0),
            "url": item.get("url", ""),
        }

    def get_best_items(items: list, min_rating: float = 4.5, min_reviews: int = 30, top_n: int = 5) -> list:
        filtered = [
            item for item in items
            if item.get("rating", 0) >= min_rating and item.get("reviews_count", 0) >= min_reviews
        ]
        sorted_items = sorted(
            filtered,
            key=lambda item: (-item.get("rating", 0), -item.get("reviews_count", 0), item.get("price", 0))
        )
        return sorted_items[:top_n]

    def get_top_n(items: list, n: int = 3) -> list:
        return sorted(
            items,
            key=lambda item: (-item.get("rating", 0), -item.get("reviews_count", 0), item.get("price", 0))
        )[:n]

    def get_hero_item(items: list) -> dict | None:
        if not items:
            return None
        return sorted(items, key=lambda item: (-item.get("rating", 0), item.get("price", 0)))[0]

    def run_marketplace_search(func, name: str = ""):
        try:
            results = [normalize_product(item) for item in func(q)]
            print(f"[{name}] Got {len(results)} items")
            return results
        except Exception as e:
            print(f"[{name} Search Error] {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return []

    wildberries_items = await asyncio.to_thread(run_marketplace_search, search_wildberries, "WB")
    yandex_items = await asyncio.to_thread(run_marketplace_search, search_yandex, "Yandex")

    wb_top5 = wildberries_items[:5]
    yandex_top5 = yandex_items[:5]

    print(f"[Result] wb_top5={len(wb_top5)}, yandex_top5={len(yandex_top5)}")

    all_candidates = wb_top5 + yandex_top5
    hero = get_hero_item(all_candidates)

    return {
        "hero": hero,
        "top3": {
            "wildberries": get_top_n(wb_top5, n=3),
            "yandex": get_top_n(yandex_top5, n=3),
        }
    }
