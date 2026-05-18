"""Get detailed 3D scene state"""
import json

from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()

    page.goto('http://localhost:8765', wait_until='networkidle')
    page.wait_for_timeout(4500)

    state = page.evaluate('''() => {
        return {
            camera: {
                position: avatarCamera ? {
                    x: avatarCamera.position.x,
                    y: avatarCamera.position.y,
                    z: avatarCamera.position.z
                } : null,
                rotation: avatarCamera ? {
                    x: avatarCamera.rotation.x,
                    y: avatarCamera.rotation.y,
                    z: avatarCamera.rotation.z
                } : null,
                fov: avatarCamera ? avatarCamera.fov : null
            },
            model: avatarModel ? {
                position: {
                    x: avatarModel.position.x,
                    y: avatarModel.position.y,
                    z: avatarModel.position.z
                },
                rotation: {
                    x: avatarModel.rotation.x,
                    y: avatarModel.rotation.y,
                    z: avatarModel.rotation.z
                },
                scale: {
                    x: avatarModel.scale.x,
                    y: avatarModel.scale.y,
                    z: avatarModel.scale.z
                },
                visible: avatarModel.visible,
                type: avatarModel.type
            } : null,
            scene: {
                childrenCount: avatarScene ? avatarScene.children.length : 0,
                background: avatarScene ? avatarScene.background : null
            },
            renderer: {
                width: avatarRenderer ? avatarRenderer.domElement.width : 0,
                height: avatarRenderer ? avatarRenderer.domElement.height : 0,
                renderCalls: avatarRenderer ? avatarRenderer.info.render.calls : 0,
                triangles: avatarRenderer ? avatarRenderer.info.render.triangles : 0
            }
        };
    }''')

    print(json.dumps(state, indent=2))
    browser.close()
