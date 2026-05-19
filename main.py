import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from fastapi.staticfiles import StaticFiles
from app.database import get_db, SessionLocal
from app.models.product import Product
from app.models.search_cache import SearchCacheItem
from app.scraper.wildberries import search as search_wildberries
from app.scraper.yandex import search as search_yandex
from app.scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(title="Marketplace Analyzer", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")


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
    query_text = q.strip().lower()

    def normalize_product(item: dict) -> dict:
        return {
            "marketplace": item.get("marketplace", "unknown"),
            "title": item.get("title", ""),
            "price": float(item.get("price", 0) or 0),
            "rating": float(item.get("rating", 0) or 0),
            "reviews_count": int(item.get("reviews_count", item.get("reviews", 0)) or 0),
            "url": item.get("url", ""),
        }

    def get_top_n(items: list, n: int = 3) -> list:
        return sorted(
            items,
            key=lambda item: (-item.get("rating", 0), -item.get("reviews_count", 0), item.get("price", 0))
        )[:n]

    def get_hero_item(items: list) -> dict | None:
        if not items:
            return None
        return sorted(items, key=lambda item: (-item.get("rating", 0), item.get("price", 0)))[0]

    def serialize_cached(item: SearchCacheItem) -> dict:
        return {
            "marketplace": item.marketplace,
            "title": item.title,
            "price": float(item.price or 0),
            "rating": float(item.rating or 0),
            "reviews_count": int(item.reviews_count or 0),
            "url": item.url or "",
        }

    def get_cached_items(query_text: str) -> list[SearchCacheItem]:
        with SessionLocal() as db:
            return db.query(SearchCacheItem).filter(
                SearchCacheItem.query == query_text
            ).order_by(SearchCacheItem.result_rank).all()

    def save_search_cache(query_text: str, items: list[dict]) -> None:
        with SessionLocal() as db:
            db.query(SearchCacheItem).filter(
                SearchCacheItem.query == query_text
            ).delete(synchronize_session=False)
            for rank, item in enumerate(items, start=1):
                db.add(SearchCacheItem(
                    query=query_text,
                    marketplace=item["marketplace"],
                    title=item["title"],
                    price=item["price"],
                    rating=item["rating"],
                    reviews_count=item["reviews_count"],
                    url=item["url"],
                    result_rank=rank,
                ))
            db.commit()

    cached_items = await asyncio.to_thread(get_cached_items, query_text)
    if cached_items:
        all_cached = [serialize_cached(item) for item in cached_items]
        wb_top5 = [item for item in all_cached if item["marketplace"] == "wildberries"][:5]
        yandex_top5 = [item for item in all_cached if item["marketplace"] == "yandex"][:5]
        hero = get_hero_item(wb_top5 + yandex_top5)
        return {
            "hero": hero,
            "top3": {
                "wildberries": get_top_n(wb_top5, n=3),
                "yandex": get_top_n(yandex_top5, n=3),
            }
        }

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

    await asyncio.to_thread(save_search_cache, query_text, wb_top5 + yandex_top5)

    all_candidates = wb_top5 + yandex_top5
    hero = get_hero_item(all_candidates)

    return {
        "hero": hero,
        "top3": {
            "wildberries": get_top_n(wb_top5, n=3),
            "yandex": get_top_n(yandex_top5, n=3),
        }
    }