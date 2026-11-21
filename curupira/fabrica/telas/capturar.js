// Grava sequências de quadros da interface real do ÉguaTeX (backend falso) para as cenas c3, c4 e c5.
// Uso: node capturar.js <pasta_saida>
const fs = require('fs'); const path = require('path');
const { abrir } = require('./abrir');
const OUT = process.argv[2] || 'telas_out';
const TEX = fs.readFileSync(path.join(__dirname, 'pororoca/editor.tex'), 'utf8');

async function entrar(p) {
  await p.getByText('A pororoca do Guamá').first().click();
  await p.waitForTimeout(1800);
  // fecha o painel de arquivos para o editor e o PDF ganharem largura
  const rail = p.locator('button[aria-label*="rquivos"], button[title*="rquivos"]').first();
  if (await rail.count()) { await rail.click(); await p.waitForTimeout(500); }
}

function gravador(p, pasta) {
  fs.mkdirSync(pasta, { recursive: true });
  let i = 0; const t0 = Date.now(); const tempos = []; const marcas = {};
  return {
    marca(nome) { marcas[nome] = i; },
    async quadro() { const f = path.join(pasta, String(i).padStart(4, '0') + '.png'); await p.screenshot({ path: f }); tempos.push((Date.now() - t0) / 1000); i++; },
    fim() { fs.writeFileSync(path.join(pasta, 'tempos.json'), JSON.stringify(tempos)); fs.writeFileSync(path.join(pasta, 'marcas.json'), JSON.stringify(marcas)); return i; },
  };
}

async function editorFoco(p) { const ed = p.locator('.cm-content').first(); await ed.click(); return ed; }

(async () => {
  // c3: digitando o parágrafo da pororoca
  {
    const inicio = TEX.split('A pororoca é')[0];
    const fim = '\\begin{equation}\n  F = G \\frac{M_T M_L}{d^2}\n\\end{equation}\n\\end{document}\n';
    const { b, p } = await abrir({ tex: inicio + '\n' + fim, localStorage: { 'eguatex.consentimento-ia': '2026-11-15-chave-api' } });
    await entrar(p);
    await editorFoco(p);
    // cursor na linha vazia depois de \section
    await p.keyboard.press('Control+Home');
    for (let k = 0; k < 6; k++) await p.keyboard.press('ArrowDown');
    await p.keyboard.press('End');
    const g = gravador(p, path.join(OUT, 'c3_digitando'));
    await g.quadro();
    const par = 'A pororoca é uma onda de maré que sobe o rio Guamá.\nEla nasce da atração entre a Terra e a Lua,\ndada pela lei de Newton:';
    for (let i = 0; i < par.length; i += 3) { await p.keyboard.type(par.slice(i, i + 3)); await g.quadro(); }
    for (let k = 0; k < 8; k++) await g.quadro();
    console.log('c3', g.fim()); await b.close();
  }
  // c4: um clique, PDF ao lado
  {
    const { b, p } = await abrir({ tempoCompilar: 900, localStorage: { 'eguatex.consentimento-ia': '2026-11-15-chave-api' } });
    await entrar(p);
    const g = gravador(p, path.join(OUT, 'c4_compilar'));
    for (let k = 0; k < 6; k++) await g.quadro();
    const btn = p.getByRole('button', { name: /Recompilar/ }).first();
    await btn.hover(); for (let k = 0; k < 3; k++) await g.quadro();
    g.marca('clique');
    await btn.click();
    for (let k = 0; k < 24; k++) { await g.quadro(); await p.waitForTimeout(60); }
    await p.locator('[aria-label^="Nível de zoom"]').first().click(); await p.waitForTimeout(200); await g.quadro();
    await p.getByText('100%', { exact: true }).first().click(); await p.waitForTimeout(500);
    for (let k = 0; k < 10; k++) { await g.quadro(); await p.waitForTimeout(60); }
    console.log('c4', g.fim()); await b.close();
  }
  // c5: erro, botão Explicar, painel Assistente IA, conversa nova com as sugestões
  {
    const texErro = TEX.replace('{d^2}', '{d^2');
    const explicacao = 'O erro está na linha 11: o comando \\frac abriu uma chave em {d^2 e não fechou.\n\nCorreção: troque {d^2 por {d^2}.\n\nDepois é só compilar de novo.';
    const { b, p } = await abrir({
      tex: texErro, ia: true, tempoCompilar: 700,
      erro: { log: '! Missing } inserted.\nl.11   F = G \\frac{M_T M_L}{d^2', erros: [{ mensagem: 'Missing } inserted.', tipo: 'erro', linha: 11, arquivo: 'main.tex' }] },
      localStorage: { 'eguatex.consentimento-ia': '2026-11-15-chave-api' },
    }, { viewport: { width: 900, height: 800 }, dsf: 1.2 });
    await p.addInitScript(() => {});
    await p.evaluate(txt => { window.__iaAgente = async () => { await new Promise(r => setTimeout(r, 1400)); return { parts: [{ text: txt }], modeloUsado: 'gemini-2.5-flash' }; }; }, explicacao);
    await entrar(p);
    const g = gravador(p, path.join(OUT, 'c5_erro'));
    await p.getByRole('button', { name: /Recompilar/ }).first().click();
    for (let k = 0; k < 16; k++) { await g.quadro(); await p.waitForTimeout(60); }
    const explicar = p.getByRole('button', { name: /Explicar/ }).first();
    if (await explicar.count()) {
      await explicar.scrollIntoViewIfNeeded(); await explicar.hover(); for (let k = 0; k < 3; k++) await g.quadro();
      g.marca('explicar');
      await explicar.click();
      for (let k = 0; k < 30; k++) { await g.quadro(); await p.waitForTimeout(80); }
    } else console.error('SEM BOTAO EXPLICAR');
    g.marca('corrige');
    // corrige: fecha a chave na linha 11 e compila de novo (agora sem erro)
    await p.evaluate(() => { window.__CENA__.erro = null; });
    await editorFoco(p);
    await p.keyboard.press('Control+End');
    await p.keyboard.press('ArrowUp'); await p.keyboard.press('ArrowUp');
    await p.keyboard.press('Home'); await p.keyboard.press('ArrowLeft');
    await p.keyboard.type('}');
    for (let k = 0; k < 3; k++) await g.quadro();
    await p.getByRole('button', { name: /Recompilar|Compilar/ }).first().click().catch(() => {});
    for (let k = 0; k < 14; k++) { await g.quadro(); await p.waitForTimeout(70); }
    const nova = p.getByRole('button', { name: /Nova conversa/i }).first();
    g.marca('nova');
    if (await nova.count()) { await nova.click(); await p.waitForTimeout(400); for (let k = 0; k < 14; k++) await g.quadro(); }
    else console.error('SEM NOVA CONVERSA');
    console.log('c5', g.fim()); await b.close();
  }
})();
