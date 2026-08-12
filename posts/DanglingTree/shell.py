import asyncio
import websockets
import ssl
import sys

async def main():
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    uri = "wss://nb-1be3782a8afd3ad5.cohort.htb/terminal/ws"
    async with websockets.connect(uri, ssl=ssl_context) as ws:
        async def reader():
            try:
                async for msg in ws:
                    sys.stdout.write(msg if isinstance(msg, str) else msg.decode(errors='replace'))
                    sys.stdout.flush()
            except Exception as e:
                print(f"\n[reader closed: {e}]")

        reader_task = asyncio.create_task(reader())

        loop = asyncio.get_event_loop()
        while True:
            cmd = await loop.run_in_executor(None, sys.stdin.readline)
            if not cmd:
                break
            await ws.send(cmd)  # includes trailing \n from readline

asyncio.run(main())
