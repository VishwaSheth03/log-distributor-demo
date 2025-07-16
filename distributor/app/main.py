from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import asyncio, signal, logging

app = FastAPI(title="Log Distributor MVP")

# Global hard‑coded queue for now
PACKET_QUEUE: asyncio.Queue = asyncio.Queue(maxsize=10000)

@app.post("/log-packet")
async def ingest(packet: dict):
    """Emitters POST packets here."""
    try:
        await PACKET_QUEUE.put(packet)  # may await if queue is full
        return JSONResponse({"status": "queued"}, status_code=202)
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        logging.exception("failed to enqueue")
        return JSONResponse({"error": str(exc)}, status_code=500)

@app.on_event("startup")
async def _startup():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    async def worker():
        """Dummy consumer pulls packets forever."""
        while True:
            packet = await PACKET_QUEUE.get()
            logging.info("Distributor received packet, packetId=%s", packet.get("packetId"))
            await asyncio.sleep(0.01)     # simulate work

    # Spin up 2 workers for demo
    for _ in range(2):
        asyncio.create_task(worker())

def _graceful_shutdown():
    logging.warning("SIGTERM received, shutting down…")
    raise SystemExit()

signal.signal(signal.SIGTERM, lambda *_: _graceful_shutdown())