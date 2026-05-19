from sqlalchemy import Column, Integer, String, Float, DateTime, func
from datetime import datetime
from app.database import Base


class SearchCacheItem(Base):
    __tablename__ = "search_cache"

    id = Column(Integer, primary_key=True, index=True)
    query = Column(String, nullable=False, index=True)
    marketplace = Column(String, nullable=False, index=True)
    title = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    rating = Column(Float, default=0.0)
    reviews_count = Column(Integer, default=0)
    url = Column(String)
    result_rank = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now(), default=datetime.utcnow)