import asyncio, uuid, datetime, os, signal, logging, httpx, uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse

# --------------- configuration ----------------
DISTRIBUTOR_URL = os.getenv("DISTRIBUTOR_URL", "http://distributor:8000/log-packet")
EMITTER_ID = os.getenv("EMITTER_ID", "emitter-X")
INITIAL_RPS = float(os.getenv("RATE_RPS", "1.0"))
MAX_RPS = 10
assert 0 < INITIAL_RPS <= MAX_RPS, "RATE_RPS must be between 0 and {MAX_RPS}"

# --------------- state ----------------
rate_rps = float = INITIAL_RPS
paused = bool = False
buffer: asyncio.Queue = asyncio.Queue(maxsize=5000)

# --------------- FastAPI ----------------
app = FastAPI(title="Emitter {EMITTER_ID}")

@app.post("/rate")
async def set_rate(data: dict):
    """Set the rate limit for this emitter."""
    global rate_rps
    rps = data.get("rps", INITIAL_RPS)
    if rps <= 0 or rps > MAX_RPS:
        raise ValueError(f"rps must be between 0 and {MAX_RPS}")
    rate_rps = rps
    return {"rps": rate_rps}

@app.post("/pause")
async def pause():
    """Pause packet emission."""
    global paused
    paused = True
    return {"paused": True}

@app.post("/resume")
async def resume():
    """Resume packet emission."""
    global paused
    paused = False
    return {"paused": False}

@app.get("/metrics")
async def metrics():
    """Get current metrics."""
    return {
        "emitter_id": EMITTER_ID,
        "rate_rps": rate_rps,
        "paused": paused,
        "buffer_size": buffer.qsize()
    }

# --------------- packet generation ----------------
async def generator():
    while True:
        packet = {
            "packetId": str(uuid.uuid4()),
            "emitter": EMITTER_ID,
            "messages": [
                {
                    "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    "level": "INFO",
                    "service": "demo_service",
                    "host": EMITTER_ID,
                    "message": f"Sample log message from {EMITTER_ID}",
                }
            ]
        }
        try:
            await buffer.put(packet)
            logging.info("Generated packet: %s", packet["packetId"])
        except asyncio.QueueFull:
            _ = await buffer.get()
            await buffer.put(packet)  # retry putting the packet
        await asyncio.sleep(1 / rate_rps)  # control the rate of generation

async def sender():
    async with httpx.AsyncClient(timeout=5) as client:
        while True:
            if paused:
                await asyncio.sleep(1)
                continue
            packet = await buffer.get()
            try:
                response = await client.post(DISTRIBUTOR_URL, json=packet)
                if response.status_code == 202:
                    logging.info("Packet sent successfully: %s", packet["packetId"])
                else:
                    logging.error("Failed to send packet: %s, status code: %d", packet["packetId"], response.status_code)
            except Exception as exc:
                await buffer.put(packet)  # put back the packet if sending fails
                await asyncio.sleep(1)  # wait before retrying

@app.on_event("startup")
async def _startup():
    """Start the packet generator and sender."""
    logging.basicConfig(level=logging.INFO)
    asyncio.create_task(generator())
    asyncio.create_task(sender())
    logging.info("Emitter %s started with initial rate %f RPS", EMITTER_ID, INITIAL_RPS)

def main():
    uvicorn.run("emitter:app", host="0.0.0.0", port=int(os.getenv("PORT", "9100")))

if __name__ == "__main__":
    main()