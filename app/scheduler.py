from apscheduler.schedulers.background import BackgroundScheduler
from app.database import SessionLocal
from app.models.search_cache import SearchCacheItem
from config import CACHE_TTL_SECONDS, CLEANUP_INTERVAL_SECONDS
from datetime import datetime, timedelta, timezone
import logging

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


class SchedulerConfig:
    
    @property
    def cache_ttl_seconds(self) -> int:
        return CACHE_TTL_SECONDS
    
    @property
    def cleanup_interval_seconds(self) -> int:
        return CLEANUP_INTERVAL_SECONDS


config = SchedulerConfig()


def cleanup_expired_cache():
    try:
        with SessionLocal() as db:
            cutoff_time = datetime.now(timezone.utc) - timedelta(seconds=config.cache_ttl_seconds)
            
            deleted_count = db.query(SearchCacheItem).filter(
                SearchCacheItem.created_at < cutoff_time
            ).delete(synchronize_session=False)
            
            db.commit()
            
            if deleted_count > 0:
                logger.info(f"[Cache Cleanup] Удалено {deleted_count} записей старше {config.cache_ttl_seconds} сек")
            else:
                logger.debug("[Cache Cleanup] Нет записей для удаления")
            
            return deleted_count
    except Exception as e:
        logger.error(f"[Cache Cleanup Error] {type(e).__name__}: {e}")
        return 0


def start_scheduler():
    if not scheduler.running:
        scheduler.add_job(
            cleanup_expired_cache,
            'interval',
            seconds=config.cleanup_interval_seconds,
            id='cleanup_cache',
            name='Cleanup expired search cache',
            replace_existing=True
        )
        scheduler.start()
        logger.info(
            f"[Scheduler] Запущен. "
            f"Интервал очистки: {config.cleanup_interval_seconds} сек, "
            f"TTL кэша: {config.cache_ttl_seconds} сек"
        )


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("[Scheduler] Остановлен")