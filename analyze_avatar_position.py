"""Analyze current avatar position and suggest optimal camera position"""
import json

from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()

    page.goto('http://localhost:8765', wait_until='networkidle')
    page.wait_for_timeout(4000)

    result = page.evaluate('''() => {
        if (!avatarModel || !avatarCamera) {
            return { error: 'Model or camera not found' };
        }

        // Get model bounding box
        const box = new THREE.Box3().setFromObject(avatarModel);
        const center = box.getCenter(new THREE.Vector3());
        const size = box.getSize(new THREE.Vector3());
        const min = box.min;
        const max = box.max;

        return {
            model: {
                center: { x: center.x, y: center.y, z: center.z },
                size: { x: size.x, y: size.y, z: size.z },
                min: { x: min.x, y: min.y, z: min.z },
                max: { x: max.x, y: max.y, z: max.z },
                position: {
                    x: avatarModel.position.x,
                    y: avatarModel.position.y,
                    z: avatarModel.position.z
                },
                scale: {
                    x: avatarModel.scale.x,
                    y: avatarModel.scale.y,
                    z: avatarModel.scale.z
                }
            },
            camera: {
                position: {
                    x: avatarCamera.position.x,
                    y: avatarCamera.position.y,
                    z: avatarCamera.position.z
                },
                fov: avatarCamera.fov,
                aspect: avatarCamera.aspect
            },
            canvas: {
                width: avatarRenderer.domElement.width,
                height: avatarRenderer.domElement.height
            }
        };
    }''')

    print("=== AVATAR ANALYSIS ===")
    print(json.dumps(result, indent=2))

    if 'model' in result:
        model = result['model']
        cam = result['camera']

        # Calculate optimal camera Y to center the model
        model_center_y = model['center']['y']
        model_min_y = model['min']['y']
        model_max_y = model['max']['y']
        model_height = model['size']['y']

        print("\n=== POSITIONING ANALYSIS ===")
        print(f"Model Y range: {model_min_y:.4f} to {model_max_y:.4f}")
        print(f"Model center Y: {model_center_y:.4f}")
        print(f"Model height: {model_height:.4f}")
        print(f"Current camera Y: {cam['position']['y']:.4f}")
        print(f"Current camera Z: {cam['position']['z']:.4f}")

        # Suggest optimal camera position
        # For a typical character, we want to frame from feet to head
        # Camera should look at roughly 40% up from bottom (chest level)
        optimal_look_at_y = model_min_y + (model_height * 0.4)

        print("\n=== RECOMMENDED CAMERA POSITION ===")
        print(f"Camera Y should be: {optimal_look_at_y:.4f}")
        print(f"LookAt Y should be: {optimal_look_at_y:.4f}")
        print("This will center the avatar showing from feet to head")

    browser.close()
