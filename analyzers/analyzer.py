from fastapi import FastAPI
from fastapi.responses import JSONResponse
import asyncio, logging, signal, sys
import uvicorn

app = FastAPI(title="Analyzer MVP")

@app.post("/ingest")
async def ingest(packet: dict):
    # minimal ACK, we are NOT storing or processing the packet
    return JSONResponse({"status": "ok"})

@app.get("/health")
async def health():
    return JSONResponse({"status": "ok"})

def _graceful(sig, _frame):
    logging.warning("Analyzer shutting down")
    sys.exit(0)

signal.signal(signal.SIGINT, _graceful)
signal.signal(signal.SIGTERM, _graceful)

if __name__ == "__main__":
    uvicorn.run("analyzer:app", host="0.0.0.0", port=9000)
