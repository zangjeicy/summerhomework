"""Open JinguRuiXi in AdsPower browser via CDP."""
import asyncio
import json
import websockets

BROWSER_WS = "ws://127.0.0.1:57231/devtools/browser/692e3216-82be-4b77-8e23-0ae6033fbf17"
PAGE_URL = "http://127.0.0.1:8000/"

async def main():
    async with websockets.connect(BROWSER_WS) as ws:
        cmd = {"id": 1, "method": "Target.createTarget", "params": {"url": PAGE_URL, "newWindow": False}}
        await ws.send(json.dumps(cmd))
        resp = await asyncio.wait_for(ws.recv(), timeout=10)
        result = json.loads(resp)
        tid = result.get("result", {}).get("targetId")
        print(f"Target: {tid}")

    if tid:
        async with websockets.connect(f"ws://127.0.0.1:57231/devtools/page/{tid}") as ws:
            await asyncio.sleep(3)
            await ws.send(json.dumps({"id": 2, "method": "Runtime.evaluate", "params": {"expression": "document.title", "returnByValue": True}}))
            resp = await asyncio.wait_for(ws.recv(), timeout=5)
            r = json.loads(resp)
            title = r.get("result", {}).get("result", {}).get("value", "N/A")
            print(f"页面标题: {title}")

            await ws.send(json.dumps({"id": 3, "method": "Runtime.evaluate", "params": {"expression": "document.body?.innerText?.substring(0,300) || ''", "returnByValue": True}}))
            resp = await asyncio.wait_for(ws.recv(), timeout=5)
            r = json.loads(resp)
            text = r.get("result", {}).get("result", {}).get("value", "")
            print(f"页面内容:\n{text}")
            print("\n✅ 金股睿析页面已通过 AdsPower 浏览器打开！")

asyncio.run(main())