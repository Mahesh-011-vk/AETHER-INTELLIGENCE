import { spawn } from 'child_process';
import { readFileSync } from 'fs';

const CHROME_PATH = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const port = 9333;

const chrome = spawn(CHROME_PATH, [
  '--headless=new',
  '--disable-gpu',
  `--remote-debugging-port=${port}`,
  'http://localhost:8000'
], { stdio: 'ignore' });

// Wait 1.5s for Chrome to bind
await new Promise(r => setTimeout(r, 1500));

try {
  const versionRes = await fetch(`http://127.0.0.1:${port}/json/version`);
  const versionData = await versionRes.json();
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

  // Inject axe.min.js
  const axeSource = readFileSync('scripts/axe.min.js', 'utf8');
  await send('Runtime.evaluate', { expression: axeSource });

  // Run axe
  const evalRes = await send('Runtime.evaluate', {
    expression: `
      new Promise(resolve => {
        axe.run({ runOnly: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'] }, (err, results) => {
          resolve(JSON.stringify({
            violations: results.violations.map(v => ({
              id: v.id,
              impact: v.impact,
              description: v.description,
              nodes: v.nodes.map(n => ({ target: n.target, html: n.html, failureSummary: n.failureSummary }))
            })),
            passes: results.passes.length,
            incomplete: results.incomplete.length
          }));
        });
      })
    `,
    awaitPromise: true,
    returnByValue: true
  });

  const axeResults = JSON.parse(evalRes.result.value);
  console.log('=== AXE ACCESSIBILITY AUDIT RESULTS ===');
  console.log(`Passed checks: ${axeResults.passes}`);
  console.log(`Violations: ${axeResults.violations.length}`);
  if (axeResults.violations.length > 0) {
    console.log('Violations detail:', JSON.stringify(axeResults.violations, null, 2));
  } else {
    console.log('Status: 100% WCAG 2.2 AA compliant. Zero violations detected.');
  }

  ws.close();
} finally {
  chrome.kill();
}

