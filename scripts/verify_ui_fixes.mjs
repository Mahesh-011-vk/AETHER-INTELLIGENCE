import { spawn } from 'child_process';
import { writeFileSync, mkdirSync } from 'fs';
import path from 'path';

const CHROME_PATH = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const port = 9338;
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
  const listRes = await fetch(`http://127.0.0.1:${port}/json/list`);
  const listData = await listRes.json();
  const page = listData.find(p => p.type === 'page');

  const ws = new WebSocket(page.webSocketDebuggerUrl);
  await new Promise(res => ws.onopen = res);

  let id = 1;
  function send(method, params = {}) {
    return new Promise(resolve => {
      const mid = id++;
      const handler = (evt) => {
        const d = JSON.parse(evt.data);
        if (d.id === mid) {
          ws.removeEventListener('message', handler);
          resolve(d.result);
        }
      };
      ws.addEventListener('message', handler);
      ws.send(JSON.stringify({ id: mid, method, params }));
    });
  }

  await send('Page.enable');
  await send('DOM.enable');

  await send('Emulation.setDeviceMetricsOverride', {
    width: 1440,
    height: 900,
    deviceScaleFactor: 2,
    mobile: false
  });

  // Wait 1s for initial table load
  await new Promise(r => setTimeout(r, 1200));

  // 1. Switch to Jobs tab
  await send('Runtime.evaluate', {
    expression: `
      navigateTab('jobs');
    `
  });

  await new Promise(r => setTimeout(r, 1200));

  // Capture Jobs screenshot
  const shotJobs = await send('Page.captureScreenshot', { format: 'png' });
  writeFileSync(path.join(outDir, 'screenshot-jobs-verified.png'), Buffer.from(shotJobs.data, 'base64'));
  console.log('Saved screenshot-jobs-verified.png');

  // 2. Switch to Products tab and open drawer for first item
  await send('Runtime.evaluate', {
    expression: `
      navigateTab('products');
    `
  });
  await new Promise(r => setTimeout(r, 1000));

  await send('Runtime.evaluate', {
    expression: `
      const firstRow = currentData[0];
      if (firstRow) openDetail('products', firstRow.id || firstRow.name);
    `
  });
  await new Promise(r => setTimeout(r, 800));

  const shotProductDrawer = await send('Page.captureScreenshot', { format: 'png' });
  writeFileSync(path.join(outDir, 'screenshot-drawer-verified.png'), Buffer.from(shotProductDrawer.data, 'base64'));
  console.log('Saved screenshot-drawer-verified.png');

  // Verify contents
  const checkRes = await send('Runtime.evaluate', {
    expression: `
      (() => {
        const metaList = document.getElementById('drawer-meta');
        const actions = document.getElementById('drawer-actions');
        const firstRowCells = Array.from(document.querySelectorAll('#table-body tr:first-child td')).map(td => td.innerText.trim());
        return {
          metaHtml: metaList.innerHTML.length,
          metaDisplay: getComputedStyle(metaList).display,
          actionButtons: actions.innerText,
          firstRowCells
        };
      })()
    `,
    returnByValue: true
  });
  console.log('DOM check results:', JSON.stringify(checkRes.result.value, null, 2));

  ws.close();
} finally {
  chrome.kill();
}

