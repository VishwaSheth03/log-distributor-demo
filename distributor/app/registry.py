from pydantic import BaseModel
from typing import List
import asyncio, logging, time

class Analyzer(BaseModel):
    id: str
    url: str
    weight: float
    current_weight: float = 0.0
    effective_weight: float = 0.0
    healthy: bool = True
    failures: int = 0
    last_check: float = 0.0

class AnalyzerRegistry:
    def __init__(self, analyzers: List[Analyzer], max_fail: int = 3):
        self.analyzers = analyzers
        self.max_fail = max_fail
        self._lock = asyncio.Lock()
    
    # Routing helper -- this is a weighted round-robin
    async def choose(self) -> Analyzer | None:
        async with self._lock:
            total = 0.0
            best = None
            for a in self.analyzers:
                if not a.healthy:
                    continue
                a.current_weight += a.effective_weight
                total += a.effective_weight
                if best is None or a.current_weight > best.current_weight:
                    best = a
            if best:
                best.current_weight -= total
                best.last_check = time.time()
            return best
    
    # Health management
    async def mark_failure(self, aid: str):
        async with self._lock:
            a = next(x for x in self.analyzers if x.id == aid)
            a.failures += 1
            if a.failures >= self.max_fail:
                a.healthy = False
                a.effective_weight = 0.0
                logging.warning("Analyzer %s marked UNHEALTHY after %d failures", a.id, a.failures)
    
    async def mark_success(self, aid: str):
        async with self._lock:
            a = next(x for x in self.analyzers if x.id == aid)
            a.failures = 0
            if not a.healthy:
                a.healthy = True
                a.effective_weight = a.weight
                logging.info("Analyzer %s marked HEALTHY", aid)