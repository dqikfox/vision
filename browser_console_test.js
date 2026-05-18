// Browser Console Test Script
// Open http://localhost:8765 and paste this into the browser console (F12)

console.clear();
console.log("🔍 Testing 3D Avatar Integration...\n");

const tests = {
  "Three.js loaded": typeof THREE !== 'undefined',
  "GLTFLoader available": typeof THREE !== 'undefined' && typeof THREE.GLTFLoader !== 'undefined',
  "Canvas element exists": !!document.getElementById('heroAvatar'),
  "Canvas is canvas (not img)": document.getElementById('heroAvatar')?.tagName === 'CANVAS',
  "heroAvatarFrame exists": !!document.getElementById('heroAvatarFrame'),
  "init3DAvatar function exists": typeof init3DAvatar === 'function',
  "avatarScene exists": typeof avatarScene !== 'undefined',
  "avatarRenderer exists": typeof avatarRenderer !== 'undefined',
  "avatarCamera exists": typeof avatarCamera !== 'undefined',
};

console.table(tests);

if (tests["avatarRenderer exists"] && avatarRenderer) {
  console.log("\n📊 Renderer Info:");
  console.log("  Size:", avatarRenderer.getSize(new THREE.Vector2()));
  console.log("  Pixel Ratio:", avatarRenderer.getPixelRatio());
}

if (tests["avatarScene exists"] && avatarScene) {
  console.log("\n🎬 Scene Info:");
  console.log("  Children count:", avatarScene.children.length);
  console.log("  Children:", avatarScene.children.map(c => c.type));
}

if (typeof avatarModel !== 'undefined' && avatarModel) {
  console.log("\n🤖 Model Info:");
  console.log("  Loaded:", true);
  console.log("  Position:", avatarModel.position);
  console.log("  Rotation:", avatarModel.rotation);
  console.log("  Scale:", avatarModel.scale);
} else {
  console.log("\n⏳ Model status: Loading or not loaded yet");
}

if (typeof avatarMixer !== 'undefined' && avatarMixer) {
  console.log("\n🎭 Animation Info:");
  console.log("  Mixer exists:", true);
  console.log("  Active actions:", avatarMixer._actions?.length || 0);
}

console.log("\n💡 Tips:");
console.log("  - Check Network tab (F12) for 'ultron-avatar.glb' request");
console.log("  - Look for any red errors in console");
console.log("  - Model loads async, so wait a few seconds");
console.log("  - Run this script again after a few seconds if model is loading");

// Test GLB fetch
console.log("\n🌐 Testing GLB fetch...");
fetch('/assets/ultron-avatar.glb')
  .then(r => {
    console.log(`✅ GLB fetch successful: ${r.status} ${r.statusText}`);
    console.log(`   Content-Type: ${r.headers.get('content-type')}`);
    console.log(`   Size: ${r.headers.get('content-length')} bytes`);
  })
  .catch(e => console.error('❌ GLB fetch failed:', e));
