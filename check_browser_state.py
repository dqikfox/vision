import asyncio

from pyppeteer import launch


async def check_browser():
    browser = await launch(headless=False, args=['--no-sandbox'])
    page = await browser.newPage()

    # Collect console messages
    console_messages = []
    async def on_console(msg):
        console_messages.append(f"[{msg.type}] {msg.text}")
        print(f"[{msg.type.upper()}] {msg.text}")

    page.on('console', lambda msg: asyncio.ensure_future(on_console(msg)))

    # Collect errors
    page.on('pageerror', lambda err: print(f"[PAGE ERROR] {err}"))

    print("Navigating to http://localhost:8765...")
    await page.goto('http://localhost:8765')

    print("\nWaiting 10 seconds for model to load...")
    await asyncio.sleep(10)

    # Check page state
    result = await page.evaluate('''() => {
        return {
            canvasExists: !!document.getElementById('heroAvatar'),
            containerExists: !!document.getElementById('heroAvatarFrame'),
            threeLoaded: typeof THREE !== 'undefined',
            gltfLoaderLoaded: typeof GLTFLoader !== 'undefined',
            avatarSceneExists: typeof avatarScene !== 'undefined',
            avatarModelExists: typeof avatarModel !== 'undefined' && avatarModel !== null,
            canvasWidth: document.getElementById('heroAvatar')?.width,
            canvasHeight: document.getElementById('heroAvatar')?.height
        };
    }''')

    print("\n=== Page State ===")
    for key, value in result.items():
        print(f"{key}: {value}")

    await page.screenshot({'path': 'C:/project/vision/browser_check.png', 'fullPage': True})
    print("\nScreenshot saved to browser_check.png")

    print("\nBrowser left open. Press Ctrl+C to close.")
    await asyncio.sleep(300)  # Keep open for 5 minutes
    await browser.close()

if __name__ == '__main__':
    try:
        asyncio.run(check_browser())
    except KeyboardInterrupt:
        print("\nClosed.")
