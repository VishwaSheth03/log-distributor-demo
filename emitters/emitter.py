"""
Minimal log‑emitter: sends one packet per second forever
CLI flags will come later.
"""
import os, httpx, asyncio, uuid, datetime, signal, sys

DISTRIBUTOR_URL = os.getenv("DISTRIBUTOR_URL", "http://distributor:8000/log-packet")
RATE_RPS = float(os.getenv("RATE_RPS", "1.0"))

INTERVAL = 1.0 / RATE_RPS if RATE_RPS > 0 else 1.0

async def main():
    async with httpx.AsyncClient() as client:
        while True:
            packet = {
                "packetId": str(uuid.uuid4()),
                "emitter": "emitter-svc",
                "messages": [
                    {
                        "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                        "level": "INFO",
                        "service": "demo",
                        "host": "emitter-svc",
                        "msg": "hello"
                    }
                ]
            }
            try:
                r = await client.post(DISTRIBUTOR_URL, json=packet, timeout=5.0)
                print("sent", packet["packetId"], r.status_code)
            except Exception as e:
                print("send failed:", e)
            await asyncio.sleep(INTERVAL)

def _graceful(sig, _frame):
    print(f"\nReceived {sig!s}, exiting")
    sys.exit(0)

signal.signal(signal.SIGINT, _graceful)
signal.signal(signal.SIGTERM, _graceful)

if __name__ == "__main__":
    asyncio.run(main())
