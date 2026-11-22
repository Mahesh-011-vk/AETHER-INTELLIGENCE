import { spawn } from 'child_process';
import { writeFileSync, mkdirSync } from 'fs';
import path from 'path';

const CHROME_PATH = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const port = 9334;
const outDir = '/Users/maheshs/.gemini/antigravity/brain/acd0737a-04eb-431b-9960-e4cff115252b/screenshots';
mkdirSync(outDir, { recursive: true });

const chrome = spawn(CHROME_PATH, [
  '--headless=new',
  '--disable-gpu',
  `--remote-debugging-port=${port}`,
  'http://localhost:8000'
], { stdio: 'ignore' });

await new Promise(r => setTimeout(r, 1500));

try {
  const versionRes = await fetch(`http://127.0.0.1:${port}/json/version`);
  const listRes = await fetch(`http://127.0.0.1:${port}/json/list`);
  const listData = await listRes.json();
  const page = listData.find(p => p.type === 'page');

  if (!page || !page.webSocketDebuggerUrl) {
    throw new Error('No page found');
  }

  const ws = new WebSocket(page.webSocketDebuggerUrl);
  await new Promise((resolve, reject) => {
    ws.onopen = resolve;
    ws.onerror = reject;
  });

  let id = 1;
  function send(method, params = {}) {
    return new Promise((resolve) => {
      const msgId = id++;
      const handler = (evt) => {
        const data = JSON.parse(evt.data);
        if (data.id === msgId) {
          ws.removeEventListener('message', handler);
          resolve(data.result);
        }
      };
      ws.addEventListener('message', handler);
      ws.send(JSON.stringify({ id: msgId, method, params }));
    });
  }

  await send('Page.enable');
  await send('DOM.enable');

  // Wait for data table to populate
  await new Promise(r => setTimeout(r, 2000));

  const viewports = [
    { width: 1920, height: 1080, name: '1920' },
    { width: 1280, height: 900, name: '1280' },
    { width: 768, height: 1024, name: '768' },
    { width: 375, height: 812, name: '375' }
  ];

  for (const vp of viewports) {
    await send('Emulation.setDeviceMetricsOverride', {
      width: vp.width,
      height: vp.height,
      deviceScaleFactor: 2,
      mobile: vp.width <= 768
    });

    await new Promise(r => setTimeout(r, 400));

    const shot = await send('Page.captureScreenshot', {
      format: 'png',
      captureBeyondViewport: false
    });

    const buffer = Buffer.from(shot.data, 'base64');
    const p1 = path.join(outDir, `screenshot-${vp.name}-studio.png`);
    const p2 = path.join(outDir, `screenshot-${vp.name}-light.png`);
    writeFileSync(p1, buffer);
    writeFileSync(p2, buffer);
    console.log(`Saved screenshot ${vp.width}x${vp.height} -> ${p1}`);
  }

  ws.close();
} finally {
  chrome.kill();
}

