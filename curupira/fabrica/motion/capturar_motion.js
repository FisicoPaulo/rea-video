// Captura o motion design quadro a quadro (tempo controlado) e entrega JPEGs ao ffmpeg.
// Uso: node capturar_motion.js <url_build_relativa> <saida.mp4> [fps] [de] [ate] [--quadros t1,t2,...]
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const fs = require('fs');
(async () => {
  const [build, saida, fpsArg, deArg, ateArg, ...resto] = process.argv.slice(2);
  const fps = +(fpsArg || 60);
  const qi = resto.indexOf('--quadros');
  const quadros = qi >= 0 ? resto[qi + 1].split(',').map(Number) : null;
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  p.on('pageerror', e => console.error('ERRO PAGINA:', e.message));
  await p.goto(`http://127.0.0.1:8765/rea-video/curupira/fabrica/motion/index.html?build=${encodeURIComponent(build)}`, { waitUntil: 'load' });
  const dur = await p.evaluate(() => window.iniciar());
  if (quadros) {
    for (const t of quadros) {
      await p.evaluate(t => window.renderizar(t), t);
      await p.screenshot({ path: `${saida}_${t.toFixed(2)}.jpg`, type: 'jpeg', quality: 90 });
    }
    await b.close(); return;
  }
  const de = +(deArg || 0), ate = Math.min(+(ateArg || dur), dur);
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'mjpeg', '-i', '-',
    '-c:v', 'libx264', '-preset', 'medium', '-crf', '17', '-pix_fmt', 'yuv420p', '-r', String(fps), saida], { stdio: ['pipe', 'inherit', 'inherit'] });
  const n0 = Math.round(de * fps), n1 = Math.round(ate * fps);
  const t0 = Date.now();
  for (let n = n0; n < n1; n++) {
    const t = n / fps;
    await p.evaluate(t => window.renderizar(t), t);
    const buf = await p.screenshot({ type: 'jpeg', quality: 93 });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (n % (fps * 2) === 0) console.log(`${t.toFixed(1)}s (${((Date.now() - t0) / 1000).toFixed(0)}s)`);
  }
  ff.stdin.end();
  await new Promise(r => ff.on('close', r));
  await b.close();
})();
