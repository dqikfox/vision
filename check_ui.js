const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({ headless: false });
  const page = await browser.newPage();

  // Capture console logs
  page.on('console', msg => {
    const type = msg.type();
    const text = msg.text();
    console.log(`[${type.toUpperCase()}] ${text}`);
  });

  // Capture errors
  page.on('pageerror', error => {
    console.log(`[PAGE ERROR] ${error.message}`);
  });

  // Capture failed requests
  page.on('requestfailed', request => {
    console.log(`[REQUEST FAILED] ${request.url()} - ${request.failure().errorText}`);
  });

  console.log('Navigating to http://localhost:8765...');
  await page.goto('http://localhost:8765', { waitUntil: 'networkidle0' });

  console.log('\nWaiting 10 seconds for model to load...');
  await new Promise(resolve => setTimeout(resolve, 10000));

  // Take screenshot
  await page.screenshot({ path: 'C:/project/vision/main_ui_screenshot.png', fullPage: true });
  console.log('\nScreenshot saved to main_ui_screenshot.png');

  // Check canvas
  const canvasExists = await page.evaluate(() => {
    const canvas = document.getElementById('heroAvatar');
    const container = document.getElementById('heroAvatarFrame');
    return {
      canvasExists: !!canvas,
      canvasTag: canvas?.tagName,
      canvasWidth: canvas?.width,
      canvasHeight: canvas?.height,
      containerExists: !!container,
      containerWidth: container?.clientWidth,
      containerHeight: container?.clientHeight,
      threeLoaded: typeof window.THREE !== 'undefined',
      gltfLoaded: typeof window.GLTFLoader !== 'undefined',
      avatarSceneExists: typeof window.avatarScene !== 'undefined',
      avatarModelExists: typeof window.avatarModel !== 'undefined' && window.avatarModel !== null
    };
  });

  console.log('\n=== Canvas Status ===');
  console.log(JSON.stringify(canvasExists, null, 2));

  // await browser.close();
  console.log('\nBrowser left open for manual inspection. Close when done.');
})();
