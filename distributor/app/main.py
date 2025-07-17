from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import asyncio, os, json, signal, logging, httpx
from .registry import AnalyzerRegistry, Analyzer

app = FastAPI(title="Log Distributor MVP v2")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)

# --------------- configuration ----------------
# Expect env ANALYZERS_JSON like:
# [{"id":"a1","url":"http://analyzer1:9000/ingest","weight":0.6},
#  {"id":"a2","url":"http://analyzer2:9000/ingest","weight":0.4}]
an_json = os.getenv("ANALYZERS_JSON", "[]")
if not an_json:
    raise RuntimeError("ANALYZERS_JSON environment variable is not set")
raw_list = json.loads(an_json)
analyzers = [Analyzer(**x, effective_weight=x["weight"]) for x in raw_list]
registry = AnalyzerRegistry(analyzers)

# Async HTTP client shared by workers
HTTP = httpx.AsyncClient(timeout=httpx.Timeout(5.0, connect=2.0))

# In-memory queue
QUEUE: asyncio.Queue = asyncio.Queue(maxsize=10_000)

# --------------- API endpoints ----------------
@app.post("/log-packet")
async def ingest(packet: dict):
    """Emitters POST packets here."""
    try:
        await QUEUE.put(packet)  # may await if queue is full
        return JSONResponse({"status": "queued"}, status_code=202)
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        logging.exception("failed to enqueue")
        return JSONResponse({"error": str(exc)}, status_code=500)

@app.get("/metrics") # demo metrics
async def metrics():
    counts = {a.id: a.current_weight for a in registry.analyzers}
    return JSONResponse({"counts": counts, "queue_size": QUEUE.qsize()})

# ---------------- Background worker ----------------
async def dispatcher():
    """Pop packet -> pick analyzer -> forward."""
    while True:
        packet = await QUEUE.get()
        target = await registry.choose()
        if not target:
            logging.error("No healthy analyzers! Dropping packet: %s", packet)
            continue
        try:
            response = await HTTP.post(target.url, json=packet)
            if response.status_code != 200:
                logging.error("Failed to send packet to %s: %s", target.id, response.text)
                await registry.mark_failure(target.id)
            else:
                await registry.mark_success(target.id)
                logging.info("Packet sent to %s successfully", target.id)
        except Exception as exc:
            logging.error("HTTP request failed for %s: %s", target.id, exc)
            await registry.mark_failure(target.id)

async def health_probe():
    while True:
        await asyncio.sleep(2) # simple health check
        for a in registry.analyzers:
            try:
                response = await HTTP.get(a.url.replace("/ingest", "/health"))
                ok = response.status_code == 200
            except Exception as exc:
                ok = False
            if ok:
                await registry.mark_success(a.id)
            else:
                await registry.mark_failure(a.id)
                logging.warning("Analyzer %s is unhealthy", a.id)

@app.on_event("startup")
async def _startup():
    for _ in range(4):
        asyncio.create_task(dispatcher())
    
    asyncio.create_task(health_probe())
    logging.info("Log Distributor started with %d analyzers", len(registry.analyzers))

def _sigterm(*_):
    logging.warning("SIGTERM-shutting down")
    raise SystemExit()

signal.signal(signal.SIGTERM, _sigterm)