"""Check if renderer's canvas matches the DOM canvas"""
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()

    page.goto('http://localhost:8765', wait_until='networkidle')
    page.wait_for_timeout(4000)

    result = page.evaluate('''() => {
        const domCanvas = document.getElementById('heroAvatar');
        const rendererCanvas = avatarRenderer ? avatarRenderer.domElement : null;
        return {
            domCanvasExists: domCanvas !== null,
            rendererCanvasExists: rendererCanvas !== null,
            sameCanvas: domCanvas === rendererCanvas,
            domCanvasId: domCanvas ? domCanvas.id : null,
            rendererCanvasId: rendererCanvas ? rendererCanvas.id : null,
            domCanvasParent: domCanvas ? domCanvas.parentElement.id : null,
            rendererInDom: rendererCanvas ? document.body.contains(rendererCanvas) : false
        };
    }''')

    print("Canvas check:")
    for key, val in result.items():
        print(f"  {key}: {val}")

    browser.close()
