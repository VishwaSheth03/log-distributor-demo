"""
Minimal log‑emitter: sends one packet per second forever
CLI flags will come later.
"""
import httpx, asyncio, uuid, datetime, signal, sys

DISTRIBUTOR_URL = "http://distributor:8000/log-packet"  # changes in Compose
REQUEST_INTERVAL = 1.0

async def main():
    async with httpx.AsyncClient() as client:
        while True:
            packet = {
                "packetId": str(uuid.uuid4()),
                "emitter": "emitter-1",
                "messages": [
                    {
                        "ts": datetime.datetime.utcnow().isoformat() + "Z",
                        "level": "INFO",
                        "service": "demo",
                        "host": "emitter-1",
                        "msg": "hello"
                    }
                ]
            }
            try:
                r = await client.post(DISTRIBUTOR_URL, json=packet, timeout=5.0)
                print("sent", packet["packetId"], r.status_code)
            except Exception as e:
                print("send failed:", e)
            await asyncio.sleep(REQUEST_INTERVAL)

def _graceful(sig, _frame):
    print(f"\nReceived {sig!s}, exiting")
    sys.exit(0)

signal.signal(signal.SIGINT, _graceful)
signal.signal(signal.SIGTERM, _graceful)

if __name__ == "__main__":
    asyncio.run(main())
    