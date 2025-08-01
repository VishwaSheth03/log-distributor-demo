from pydantic import BaseModel
from typing import List
import asyncio, logging, time

class Analyzer(BaseModel):
    id: str
    url: str
    weight: float = 1.0
    current_weight: float = 0.0
    effective_weight: float = 0.0
    healthy: bool = True
    admin_enabled: bool = True
    failures: int = 0
    last_check: float = 0.0

class AnalyzerRegistry:
    def __init__(self, analyzers: List[Analyzer], max_fail: int = 3):
        self.analyzers = analyzers
        self.max_fail = max_fail
        self._lock = asyncio.Lock()
        self._normalize_effective_weights()

    # gets an analyzer by ID
    def _by_id(self, aid: str) -> Analyzer:
        return next(x for x in self.analyzers if x.id == aid)
    
    # checks if an analyzer is healthy and eligible for routing
    def _eligible(self, a: Analyzer) -> bool:
        return a.healthy and a.admin_enabled and a.effective_weight > 0
    
    # normalizes effective weights based on current weights and total weight
    def _normalize_effective_weights(self):
        eligible = [a for a in self.analyzers if a.healthy and a.admin_enabled]

        if not eligible:
            for a in self.analyzers:
                a.effective_weight = 0.0
            return

        total = sum(a.weight for a in eligible)

        if total == 0:          # all weights were 0
            equalSplit = 1.0 / len(eligible)
            for a in self.analyzers:
                a.effective_weight = equalSplit if a in eligible else 0.0
        elif total < 1.0:       # lost weight, therefore spread evenly
            gap = (1.0 - total) / len(eligible)
            for a in self.analyzers:
                a.effective_weight = (a.weight + gap) if a in eligible else 0.0
        else:                   # total > 1.0, therefore scale down proportionally
            scale = 1.0 / total
            for a in self.analyzers:
                a.effective_weight = (a.weight * scale) if a in eligible else 0.0


    # Routing helper -- this is a weighted round-robin
    async def choose(self) -> Analyzer | None:
        async with self._lock:
            best = None
            total = 0.0
            for a in self.analyzers:
                if not self._eligible(a):
                    continue
                a.current_weight += a.effective_weight
                total += a.effective_weight
                if best is None or a.current_weight > best.current_weight:
                    best = a
            if best:
                best.current_weight -= total
            return best
    
    # Health management
    async def mark_failure(self, aid: str):
        async with self._lock:
            a = self._by_id(aid)
            a.failures += 1
            if a.failures >= self.max_fail and a.healthy:
                a.healthy = False
                a.current_weight = 0.0
                logging.warning("Analyzer %s marked UNHEALTHY after %d failures", aid, a.failures)
                logging.info("Effective weight for %s set to 0.0", aid)
                self._normalize_effective_weights()
    
    async def mark_success(self, aid: str):
        async with self._lock:
            a = self._by_id(aid)
            a.failures = 0
            if not a.healthy:
                logging.info("Analyzer %s marked HEALTHY", aid)
                a.current_weight = 0.0
            a.healthy = True
            a.effective_weight = a.weight
            self._normalize_effective_weights()
    
    async def toggle_admin(self, aid: str, enable: bool):
        async with self._lock:
            a = self._by_id(aid)
            if a.admin_enabled != enable:
                a.admin_enabled = enable
                a.current_weight = 0.0
                logging.info("Analyzer %s admin status changed to %s", aid, "ENABLED" if enable else "DISABLED")
                self._normalize_effective_weights()
                a.healthy = True if enable else False
    
    async def add(self, a: Analyzer):
        async with self._lock:
            if a.id in [x.id for x in self.analyzers]:
                raise ValueError(f"Analyzer with ID {a.id} already exists")
            a.last_check = time.time() + 5 # grace period before first health check
            self.analyzers.append(a)
            logging.info("Added new analyzer %s", a.id)
            self._normalize_effective_weights()
    
    async def remove(self, aid: str):
        async with self._lock:
            a = self._by_id(aid)
            self.analyzers.remove(a)
            logging.info("Removed analyzer %s", aid)
            self._normalize_effective_weights()