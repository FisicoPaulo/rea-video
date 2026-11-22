// Abre a interface real do ÉguaTeX (vite dev) com o backend falso e devolve a página pronta no projeto.
const { chromium } = require('playwright');
const fs = require('fs'); const path = require('path');
const AQUI = __dirname;
async function abrir(cena = {}, opcoes = {}) {
  const tex = fs.readFileSync(path.join(AQUI, 'pororoca/editor.tex'), 'utf8');
  const b = await chromium.launch();
  const ctx = await b.newContext({ viewport: opcoes.viewport || { width: 760, height: 760 }, deviceScaleFactor: opcoes.dsf || 1.42, colorScheme: 'light' });
  const p = await ctx.newPage();
  p.on('pageerror', e => console.error('ERRO PAGINA:', e.message));
  p.on('console', m => { if (m.type() === 'error') console.error('CONSOLE:', m.text().slice(0, 200)); });
  await p.route('**/__pdf', r => r.fulfill({ body: fs.readFileSync(path.join(AQUI, 'pororoca/main.pdf')), contentType: 'application/pdf' }));
  await p.addInitScript(c => { window.__CENA__ = c; }, { tex, pdfUrl: '/__pdf', ...cena });
  await p.addInitScript({ path: path.join(AQUI, 'mock-tauri.js') });
  await p.goto('http://127.0.0.1:5199/', { waitUntil: 'networkidle' });
  await p.waitForTimeout(1200);
  for (const nome of ['Agora não']) { const x = p.getByRole('button', { name: nome }); if (await x.count()) await x.first().click(); }
  return { b, p };
}
module.exports = { abrir };
if (require.main === module) (async () => {
  const { b, p } = await abrir();
  await p.screenshot({ path: process.argv[2] || 'a.png' });
  await p.getByText('A pororoca do Guamá').first().click();
  await p.waitForTimeout(2500);
  await p.screenshot({ path: (process.argv[2] || 'a.png').replace('.png', '_proj.png') });
  console.log((await p.evaluate(() => window.__log || [])).join(' '));
  await b.close();
})();
