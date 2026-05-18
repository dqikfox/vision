"""Force render and check pixels"""

from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()

    page.goto('http://localhost:8765', wait_until='networkidle')
    page.wait_for_timeout(4000)

    # Force a manual render
    result = page.evaluate('''() => {
        if (!avatarRenderer || !avatarScene || !avatarCamera) {
            return { error: 'Missing renderer/scene/camera' };
        }

        // Force multiple renders
        for (let i = 0; i < 10; i++) {
            avatarRenderer.render(avatarScene, avatarCamera);
        }

        // Get canvas pixel data
        const canvas = avatarRenderer.domElement;
        const gl = canvas.getContext('webgl2') || canvas.getContext('webgl');
        const pixels = new Uint8Array(4);

        // Sample center pixel
        const cx = Math.floor(canvas.width / 2);
        const cy = Math.floor(canvas.height / 2);
        gl.readPixels(cx, cy, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, pixels);

        return {
            canvasSize: `${canvas.width}x${canvas.height}`,
            centerPixel: Array.from(pixels),
            sceneChildren: avatarScene.children.length,
            cameraPos: {
                x: avatarCamera.position.x,
                y: avatarCamera.position.y,
                z: avatarCamera.position.z
            },
            rendererInfo: {
                calls: avatarRenderer.info.render.calls,
                triangles: avatarRenderer.info.render.triangles
            }
        };
    }''')

    print("Manual render test:")
    for key, val in result.items():
        print(f"  {key}: {val}")

    browser.close()
