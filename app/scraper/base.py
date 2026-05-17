from abc import ABC, abstractmethod
from typing import List, Dict

class BaseScraper(ABC):
    
    @abstractmethod
    async def search(self, query: str) -> List[Dict]:
        pass
    
    @property
    @abstractmethod
    def marketplace_name(self) -> str:
        pass