# -*- coding: utf-8 -*-
"""Connect to user's logged-in WeChat backend browser via CDP"""
import asyncio, sys, socket, time

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("playwright not installed")
    sys.exit(1)

def wait_for_port(port, timeout=15):
    """Wait until a port is listening."""
    start = time.time()
    while time.time() - start < timeout:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            result = s.connect_ex(('127.0.0.1', port))
            if result == 0:
                s.close()
                return True
        except:
            pass
        s.close()
        time.sleep(0.5)
    return False

async def main():
    port = 9222
    print(f"Checking if Edge CDP port {port} is ready...")
    if not wait_for_port(port):
        print(f"Port {port} not responding. Trying 9322...")
        port = 9322
        if not wait_for_port(port):
            print(f"Port {port} also not responding.")
            # Try to find any CDP-enabled browser
            for p in [9222, 9223, 9322, 9323, 9229, 9230]:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(1)
                if s.connect_ex(('127.0.0.1', p)) == 0:
                    print(f"Found port {p}.")
                    port = p
                    break
                s.close()
            else:
                print("No CDP-enabled browser found!")
                sys.exit(1)

    cdp_url = f'http://127.0.0.1:{port}'
    print(f"Connecting to {cdp_url}...")

    p = await async_playwright().start()
    browser = None
    try:
        browser = await p.chromium.connect_over_cdp(cdp_url, timeout=10000)
        print(f"Connected via CDP port {port}!")
        
        # Find the mp.weixin.qq.com page
        weixin_page = None
        for ctx in browser.contexts:
            for pg in ctx.pages:
                url = pg.url
                print(f"  Page: {await pg.title()} | {url[:80]}")
                if 'mp.weixin.qq.com' in url:
                    weixin_page = pg
        
        # Navigate to WeChat backend
        if weixin_page:
            target = weixin_page
            # Try to click on any menu item to ensure we're fully loaded
        else:
            ctxs = browser.contexts
            if ctxs:
                target = await ctxs[0].new_page()
            else:
                ctx = await browser.new_context()
                target = await ctx.new_page()
        
        print("Navigating to mp.weixin.qq.com...")
        await target.goto('https://mp.weixin.qq.com', wait_until='domcontentloaded', timeout=60000)
        await target.wait_for_timeout(5000)
        
        print(f"\nPage title: {await target.title()}")
        print(f"Page URL: {target.url}")
        
        # Save full content
        content = await target.content()
        with open(r'C:\Users\Administrator\.copaw\workspaces\CoPaw_QA_Agent_0.1beta1\media\weixin_backend.html', 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"HTML saved ({len(content)} chars)")
        
        # Screenshot
        screenshot_path = r'C:\Users\Administrator\.copaw\workspaces\CoPaw_QA_Agent_0.1beta1\media\weixin_backend.png'
        await target.screenshot(path=screenshot_path, full_page=True)
        print(f"Screenshot saved to {screenshot_path}")
        
        # Check if logged in (no login page)
        if 'login' in target.url.lower() or '扫码' in await target.title():
            print("\nNOT LOGGED IN - please log in and re-run.")
        else:
            print("\nLogged in! Data captured.")
            
        # Extract key text from page
        text = await target.inner_text('body')
        print(f"\nPage text preview (first 2000 chars):\n{text[:2000]}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if browser:
            await browser.close()
        await p.stop()

asyncio.get_event_loop().run_until_complete(main())
print("done")
