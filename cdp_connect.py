# -*- coding: utf-8 -*-
import sys
import asyncio

async def main():
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("playwright not installed")
        sys.exit(1)

    p = await async_playwright().start()
    try:
        browser = await p.chromium.connect_over_cdp('http://127.0.0.1:9227')
        print("Connected!")
        for ctx in browser.contexts:
            for pg in ctx.pages:
                print('URL:', pg.url)
                print('Title:', await pg.title())
        await browser.close()
    except Exception as e:
        print(f"Connect error: {e}")
    await p.stop()

asyncio.get_event_loop().run_until_complete(main())
