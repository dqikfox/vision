"""
Simple check - inject JavaScript into running page to get canvas state
"""

js_check = """
(function() {
    const canvas = document.getElementById('heroAvatar');
    const container = document.getElementById('heroAvatarFrame');

    return {
        canvas_exists: !!canvas,
        canvas_width: canvas?.width || 0,
        canvas_height: canvas?.height || 0,
        canvas_client_width: canvas?.clientWidth || 0,
        canvas_client_height: canvas?.clientHeight || 0,
        container_exists: !!container,
        container_width: container?.clientWidth || 0,
        container_height: container?.clientHeight || 0,
        three_loaded: typeof THREE !== 'undefined',
        gltf_loaded: typeof GLTFLoader !== 'undefined',
        scene_exists: typeof avatarScene !== 'undefined',
        model_exists: typeof avatarModel !== 'undefined' && avatarModel !== null,
        renderer_exists: typeof avatarRenderer !== 'undefined',
        boot_visible: document.getElementById('boot')?.style.display !== 'none'
    };
})()
"""

print("JavaScript to run in browser console (F12):")
print("="*60)
print(js_check)
print("="*60)
print("\nCopy the above, paste into main UI console, press Enter")
print("Then tell me the results")
