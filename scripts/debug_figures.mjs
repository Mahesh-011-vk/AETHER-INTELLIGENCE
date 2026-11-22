import { spawn } from 'child_process';

const chrome = spawn('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', [
  '--headless=new', '--disable-gpu', '--remote-debugging-port=9336', 'http://localhost:8000'
]);

await new Promise(r => setTimeout(r, 1200));

try {
  const r = await fetch('http://127.0.0.1:9336/json/list');
  const list = await r.json();
  const p = list.find(x => x.type === 'page');
  const ws = new WebSocket(p.webSocketDebuggerUrl);
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

  const res = await send('Runtime.evaluate', {
    expression: `
      (() => {
        const el = document.querySelector('.ruled-figures');
        return {
          offsetHeight: el ? el.offsetHeight : null,
          innerHTML: el ? el.innerHTML : null
        };
      })()
    `,
    returnByValue: true
  });
  console.log('Result:', JSON.stringify(res.result.value, null, 2));
  ws.close();
} finally {
  chrome.kill();
}

