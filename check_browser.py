"""
Use Playwright to check what's actually rendering
"""
import asyncio


async def check_page():
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("Playwright not installed. Install with: pip install playwright")
        print("Then run: playwright install")
        return

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await p.new_page()

        # Capture console messages
        console_messages = []
        page.on('console', lambda msg: console_messages.append(f"{msg.type}: {msg.text}"))

        # Capture errors
        errors = []
        page.on('pageerror', lambda err: errors.append(str(err)))

        print("Loading page...")
        await page.goto('http://localhost:8765/simple_3d_test.html')

        # Wait for model to load
        await asyncio.sleep(5)

        # Take screenshot
        await page.screenshot(path='C:/project/vision/playwright_screenshot.png')
        print("Screenshot saved to playwright_screenshot.png")

        # Get page info
        title = await page.title()
        url = page.url

        print(f"\nPage: {title}")
        print(f"URL: {url}")

        # Get status text
        try:
            info_text = await page.locator('#info').text_content()
            print(f"\nStatus: {info_text}")
        except:
            print("\nStatus element not found")

        print(f"\n=== Console Messages ({len(console_messages)}) ===")
        for msg in console_messages:
            print(msg)

        if errors:
            print(f"\n=== Errors ({len(errors)}) ===")
            for err in errors:
                print(err)

        await browser.close()

if __name__ == '__main__':
    asyncio.run(check_page())
