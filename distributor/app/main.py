from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse
import asyncio, os, json, signal, logging, httpx, time, pathlib
from fastapi.staticfiles import StaticFiles
from prometheus_client import Counter, Gauge, generate_latest
from .registry import AnalyzerRegistry, Analyzer

app = FastAPI(title="Log Distributor MVP v3")

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

# --------------- metrics ----------------
PACKETS_RX = Counter("packets_received_total", "Packets received from emitters") # tracks incoming packets to the distributor
PACKETS_TX = Counter("packets_forwarded_total", "Packets forwarded to analyzers", ["analyzer_id"]) # tracks packets sent to analyzers
QUEUE_SIZE = Gauge("queue_size", "Packets in the distributor queue")

# --------------- HTTP client and queue ----------------
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
        PACKETS_RX.inc()
        QUEUE_SIZE.set(QUEUE.qsize())
        return JSONResponse({"status": "queued"}, status_code=202)
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        logging.exception("failed to enqueue")
        return JSONResponse({"error": str(exc)}, status_code=500)

@app.get("/registry")
async def list_registry():
    return [a.model_dump() for a in registry.analyzers]

@app.post("/registry/add")
async def add_analyzer(data: dict):
    await registry.add(**data, current_weight=0, effective_weight=data.get("weight", 1.0))
    return {"added": data["id"]}

@app.delete("/registry/{aid}")
async def remove_analyzer(aid: str):
    await registry.remove(aid)
    return {"removed": aid}

@app.post("/analyzer/{aid}/enable")
async def enable_analyzer(aid: str):
    await registry.toggle_admin(aid, True)
    return {"status": "enabled", "analyzer_id": aid}

@app.post("/analyzer/{aid}/disable")
async def disable_analyzer(aid: str):
    await registry.toggle_admin(aid, False)
    return {"status": "disabled", "analyzer_id": aid}

# ----------------- Prometheus Metrics ----------------
@app.get("/metrics")
def prom_metrics():
    return PlainTextResponse(generate_latest())

# ---------------- WebSocket for real-time updates ----------------
clients: set[WebSocket] = set()

@app.websocket("/ws/metrics")
async def ws_metrics(ws: WebSocket):
    await ws.accept()
    clients.add(ws)
    try:
        while True:
            await asyncio.sleep(1)
            def _tx_for(a_id: str) -> int:
                try:
                    return PACKETS_TX.labels(a_id)._value.get()     # after first .inc()
                except KeyError:
                    return 0

            payload = {
                "ts": time.time(),
                "queue_depth": QUEUE.qsize(),
                "analyzers": [
                    {
                        "id": a.id,
                        "effective_weight": a.effective_weight,
                        "healthy": a.healthy,
                        "admin_enabled": a.admin_enabled,
                        "tx_packets": _tx_for(a.id),
                    }
                    for a in registry.analyzers
                ],
                "packets_rx": PACKETS_RX._value.get(),
            }
            await ws.send_json(payload)
    except WebSocketDisconnect:
        pass
    finally:
        clients.discard(ws)

# ---------------- Background worker ----------------
async def dispatcher():
    """Pop packet -> pick analyzer -> forward"""
    while True:
        packet = await QUEUE.get()
        target = await registry.choose()
        if not target:
            logging.error("No healthy analyzers! Dropping packet: %s", packet)
            continue
        try:
            response = await HTTP.post(target.url, json=packet)
            if response.status_code == 200:
                PACKETS_TX.labels(target.id).inc()
                await registry.mark_success(target.id)
            else:
                await registry.mark_failure(target.id)
        except Exception as exc:
            logging.error("HTTP request failed for %s: %s", target.id, exc)
            await registry.mark_failure(target.id)

async def health_probe():
    while True:
        await asyncio.sleep(2)
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

@app.on_event("startup")
async def _startup():
    asyncio.create_task(dispatcher())
    asyncio.create_task(health_probe())
    logging.info("Log Distributor started")

def _sigterm(*_):
    logging.warning("SIGTERM-shutting down")
    raise SystemExit()

signal.signal(signal.SIGTERM, _sigterm)

app.mount("/", StaticFiles(directory=os.getenv("STATIC_DIR", pathlib.Path(__file__).parent / "static"), html=True), name="static")