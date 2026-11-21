// Motion design do vídeo do Curupira. Tudo é função do tempo t: renderizar(t) desenha o quadro exato.
// Os dados vêm de <build>/dados.json (falas, palavras, sprites, telas).
"use strict";
const W = 1080, H = 1920;
const q = new URLSearchParams(location.search);
const BUILD = q.get("build");
let D = null;

// ---------------------------------------------------------------- utilidades
const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const lerp = (a, b, k) => a + (b - a) * k;
const eOut = k => 1 - Math.pow(1 - clamp(k), 3);
const eIn = k => Math.pow(clamp(k), 3);
const eIO = k => { k = clamp(k); return k < .5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2; };
const eExpo = k => (k = clamp(k)) === 1 ? 1 : 1 - Math.pow(2, -10 * k);
const eBack = (k, s = 1.70158) => { k = clamp(k) - 1; return k * k * ((s + 1) * k + s) + 1; };
const mola = (dt, amp = 1, per = .4, am = .15) => dt < 0 ? 0 : amp * Math.exp(-dt / am) * Math.cos(2 * Math.PI * dt / per);
// entrada com mola: 0 antes de t0; passa de 1 e assenta
const pop = (t, t0, d = .38) => t < t0 ? 0 : (t - t0 < d * .55 ? eOut((t - t0) / (d * .55)) * 1.08 : 1 + mola(t - t0 - d * .55, .08, .32, .1));
const ruido = (t, s) => Math.sin(t * 1.13 + s) * .5 + Math.sin(t * 2.71 + s * 1.7) * .3 + Math.sin(t * 4.37 + s * 2.3) * .2;
const el = (tag, cls, pai, html) => { const e = document.createElement(tag); if (cls) e.className = cls; if (html !== undefined) e.innerHTML = html; (pai || document.body).appendChild(e); return e; };
const tf = (e, { x = 0, y = 0, s = 1, sx = 1, sy = 1, r = 0, o = 1, blur = 0 } = {}) => {
  e.style.transform = `translate(${x}px,${y}px) rotate(${r}deg) scale(${s * sx},${s * sy})`;
  e.style.opacity = o;
  e.style.filter = blur > 0.05 ? `blur(${blur}px)` : "";
};
const $ = id => document.getElementById(id);

function P(cena, pref, n = 0) {
  let k = 0;
  for (const w of D.palavras[cena]) {
    if (w.palavra.replace(/[.,:?!]/g, "").toLowerCase().startsWith(pref.toLowerCase())) { if (k === n) return w.ini; k++; }
  }
  throw new Error(`${cena}: ${pref}`);
}
const C = id => D.cenas[id];
// visibilidade de cena com transição: entra com zoom e desfoque, sai com zoom
function cenaVis(t, id, entra = .22, sai = .18) {
  const c = C(id);
  const kin = clamp((t - c.inicio + .04) / entra), kout = clamp((c.fim - t) / sai);
  return { k: Math.min(kin, kout), kin, kout, ativa: t >= c.inicio - .04 && t < c.fim + .02 };
}

// imagens com espera de decodificação
const pendentes = [];
function setSrc(img, url) {
  if (img.dataset.src === url) return;
  img.dataset.src = url;
  img.src = url;
  pendentes.push(img.decode().catch(() => {}));
}
const tela = (nome, i) => {
  const n = D.telas[nome].n;
  i = Math.round(clamp(i, 0, n - 1));
  return `${BUILD}/telas/${nome}/${String(i).padStart(4, "0")}.png`;
};

// ---------------------------------------------------------------- fundo vivo
const fundo = {};
function montarFundo() {
  const f = $("fundo");
  fundo.blobs = [["#ff5f15", 520, 300, 700], ["#7a35c4", 640, 760, 1300], ["#e0243e", 420, 200, 1500], ["#3f9a37", 380, 900, 400]]
    .map(([cor, tam, x, y]) => { const b = el("div", "blob", f); b.style.background = cor; b.style.width = b.style.height = tam + "px"; b.dataset.x = x; b.dataset.y = y; return b; });
  fundo.folhas = [];
  for (let i = 0; i < 14; i++) {
    const fo = el("div", "folha", f);
    const x = (i * 197) % 1300 - 100, y = i % 2 ? (i * 131) % 380 - 80 : 1500 + (i * 89) % 520;
    fo.dataset.x = x; fo.dataset.y = y; fo.dataset.r = (i * 47) % 180;
    fo.style.background = i % 3 ? "#10230d" : "#2a1a3a";
    fundo.folhas.push(fo);
  }
  // brasas
  fundo.brasas = [];
  for (let i = 0; i < 30; i++) {
    const b = el("div", "abs", f);
    const tam = 4 + (i * 7) % 9;
    b.style.cssText += `width:${tam}px;height:${tam}px;border-radius:50%;background:#ffb627;box-shadow:0 0 ${tam * 3}px #ff5f15;`;
    b.dataset.x = (i * 233) % W; b.dataset.y = (i * 397) % H; b.dataset.v = 25 + (i * 13) % 50; b.dataset.f = i;
    fundo.brasas.push(b);
  }
}
function fundoVivo(t) {
  fundo.blobs.forEach((b, i) => tf(b, { x: +b.dataset.x + 90 * ruido(t * .25, i * 3), y: +b.dataset.y + 70 * ruido(t * .21, i * 5 + 1) }));
  fundo.folhas.forEach((f, i) => tf(f, { x: +f.dataset.x + 14 * Math.sin(t * .6 + i), y: +f.dataset.y + 8 * Math.cos(t * .5 + i), r: +f.dataset.r + 4 * Math.sin(t * .7 + i * 2) }));
  fundo.brasas.forEach(b => {
    const v = +b.dataset.v, fi = +b.dataset.f;
    const y = ((+b.dataset.y - v * t) % (H + 100) + H + 100) % (H + 100) - 50;
    tf(b, { x: +b.dataset.x + 22 * Math.sin(t * .9 + fi), y, o: .35 + .45 * (0.5 + 0.5 * Math.sin(t * 4 + fi * 2)) });
  });
}

// ---------------------------------------------------------------- legenda cinética
const leg = { grupos: [], spans: [] };
function montarLegenda() {
  for (const id of Object.keys(D.palavras)) {
    let g = [];
    for (const w of D.palavras[id]) {
      g.push(w);
      if (g.length >= 3 || /[.?!:,]$/.test(w.palavra)) { leg.grupos.push(g); g = []; }
    }
    if (g.length) leg.grupos.push(g);
  }
}
function legenda(t, topo) {
  const box = $("legenda");
  box.style.top = topo + "px";
  let gi = -1;
  for (let i = 0; i < leg.grupos.length; i++) {
    const g = leg.grupos[i], ini = g[0].ini - .05;
    const prox = i + 1 < leg.grupos.length ? leg.grupos[i + 1][0].ini - .05 : 1e9;
    if (t >= ini && t < Math.min(g[g.length - 1].fim + .35, prox)) { gi = i; break; }
  }
  if (gi !== leg.atual) {
    box.innerHTML = "";
    leg.spans = gi < 0 ? [] : leg.grupos[gi].map(w => el("span", "pal", box, w.palavra.replace(/[,:]$/, "")));
    leg.atual = gi;
  }
  if (gi < 0) return;
  const g = leg.grupos[gi];
  g.forEach((w, k) => {
    const sp = leg.spans[k];
    const dt = t - w.ini;
    const vis = dt > -0.04;
    sp.classList.toggle("atual", dt >= -0.02 && (k === g.length - 1 || t < g[k + 1].ini - .02));
    const e = vis ? eBack(clamp((dt + .04) / .22), 2.2) : 0;
    tf(sp, { y: (1 - e) * 40, s: .6 + .4 * e + (sp.classList.contains("atual") ? mola(dt, .06, .25, .08) + .04 : 0), o: clamp((dt + .04) / .1) });
  });
}

// ---------------------------------------------------------------- Curupira (adesivo)
const curu = {};
function montarCuru() {
  curu.trocas = [];
  const ps = D.sprites.poses;
  for (let i = 1; i < ps.length; i++) if (ps[i] !== ps[i - 1]) curu.trocas.push({ t: i / D.sprites.fps, de: ps[i - 1], para: ps[i] });
}
function poseEm(t) { const i = clamp(Math.floor(t * D.sprites.fps), 0, D.sprites.n - 1); return [i, D.sprites.poses[i]]; }
// posição base por cena (pescoço do adesivo no ponto x,y)
function desenharCuru(t, { x, y, s, r = 0, o = 1 }) {
  const [i, pose] = poseEm(t);
  const lado = pose === "lado";
  const box = lado ? $("lado") : $("curu"), outro = lado ? $("curu") : $("lado");
  outro.style.opacity = 0;
  setSrc(lado ? $("ladoimg") : $("curuimg"), `${BUILD}/sprites/${lado ? "lado_" : ""}${String(i).padStart(5, "0")}.png`);
  if (lado) return box;
  // troca de pose: amassa e estica (pose a pose com mola) + antecipação
  let sx = 1, sy = 1, dy = 0, dr = 0;
  for (const tr of curu.trocas) {
    const dt = t - tr.t;
    if (dt > -0.12 && dt < 0) { const k = eIn(1 + dt / .12); sx *= 1 + .04 * k; sy *= 1 - .05 * k; dy += 10 * k; }
    if (dt >= 0 && dt < .7) { sy *= 1 + mola(dt, .07, .34, .12); sx *= 1 - mola(dt, .05, .34, .12); dr += mola(dt, 2.5, .5, .15); }
  }
  // balanço de adesivo (vivo, nunca parado)
  const bob = 8 * Math.sin(t * 2 * Math.PI / 2.4);
  tf(box, { x: x - 500 + 6 * ruido(t * .5, 7), y: y - 700 + bob + dy, s, sx, sy, r: r + dr + 1.2 * ruido(t * .45, 9), o });
  return box;
}

// ---------------------------------------------------------------- cenas
const S = {};
function svg(pai, w, h, inner, cls = "abs") { const d = el("div", cls, pai); d.innerHTML = `<svg width="${w}" height="${h}" viewBox="0 0 ${w} ${h}" xmlns="http://www.w3.org/2000/svg">${inner}</svg>`; return d; }

function montarCenas() {
  const raiz = $("cenas");
  const nova = id => { const c = el("div", "cena", raiz); c.id = "cena_" + id; return c; };

  // c1: gancho. Cartões de erro do TCC aparecem em volta.
  const c1 = nova("c1");
  S.c1 = { c: c1, erros: [] };
  const msgs = [["! Undefined control sequence", -20, 250, -6], ["TCC_final_v7_agora_vai.tex", 140, 520, 5], ["! Missing $ inserted", 470, 330, 4], ["Overfull \\hbox (13.2pt too wide)", 300, 760, -3]];
  for (const [m, x, y, r] of msgs) {
    const e = el("div", "abs codigo", c1, `<span class="ruim">${m.replace(/</g, "&lt;")}</span>`);
    e.style.fontSize = "38px"; e.dataset.x = x; e.dataset.y = y; e.dataset.r = r;
    S.c1.erros.push(e);
  }
  S.c1.chamas = [];
  for (let i = 0; i < 40; i++) { const p = el("div", "abs", c1); const tam = 18 + (i * 11) % 40; p.style.cssText += `width:${tam}px;height:${tam}px;border-radius:${i % 3 ? "50%" : "50% 0"};background:${i % 3 === 0 ? "#3f9a37" : i % 2 ? "#ffb627" : "#ff5f15"};`; S.c1.chamas.push(p); }

  // c2: logo, marca letra a letra, chips
  const c2 = nova("c2");
  S.c2 = { c: c2 };
  S.c2.kicker = el("div", "abs kicker", c2, "conheça o");
  S.c2.logo = el("img", "abs", c2); S.c2.logo.src = "/rea-video/curupira/arte/referencias/curupira.png"; S.c2.logo.style.width = "420px";
  S.c2.marca = el("div", "abs titulo", c2); S.c2.marca.style.fontSize = "150px";
  S.c2.letras = [..."ÉguaTeX"].map((ch, i) => { const s = el("span", "", S.c2.marca, ch); s.style.display = "inline-block"; if (i === 0) { s.style.color = "#ff5f15"; } return s; });
  S.c2.chips = [["editor LaTeX", "", "editor"], ["gratuito", "verde", "gratuito"], ["offline", "roxo", "offline"], ["feito na Amazônia", "fogo", "Amazônia"]]
    .map(([txt, cls, pal]) => { const e = el("div", "abs chip " + cls, c2, txt); e.dataset.pal = pal; return e; });

  // c3: sem internet -> rio -> ônibus
  const c3 = nova("c3");
  S.c3 = { c: c3 };
  S.c3.titulo = el("div", "abs titulo", c3, "Sem <em>internet</em>?"); S.c3.titulo.style.fontSize = "120px";
  S.c3.wifi = svg(c3, 360, 360, `<circle cx="180" cy="180" r="170" fill="#f3eafb"/><g fill="none" stroke="#7a35c4" stroke-width="22" stroke-linecap="round"><path d="M70 160 Q180 60 290 160"/><path d="M110 205 Q180 140 250 205"/></g><circle cx="180" cy="255" r="20" fill="#7a35c4"/><line x1="80" y1="80" x2="280" y2="280" stroke="#e0243e" stroke-width="30" stroke-linecap="round"/>`);
  S.c3.ok = el("div", "abs chip verde", c3, "✓ funciona offline");
  S.c3.fumaca = [...Array(12)].map(() => { const f = el("div", "abs", c3); f.style.cssText += "width:120px;height:120px;border-radius:50%;background:#e8deef;filter:blur(18px);"; return f; });
  // rio (vetor chapado, com parallax)
  S.c3.rio = el("div", "abs", c3); S.c3.rio.style.cssText += "inset:0;width:1080px;height:1920px;";
  S.c3.rio.innerHTML = `<svg width="1080" height="1920" viewBox="0 0 1080 1920">
    <defs><linearGradient id="ceu" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#2b1046"/><stop offset="1" stop-color="#5a2a6a"/></linearGradient></defs>
    <rect width="1080" height="1920" fill="url(#ceu)"/>
    <circle id="lua" cx="230" cy="360" r="110" fill="#fbe9c8"/>
    <g id="morro2"><path d="M-200 980 Q100 760 380 930 T960 880 T1500 940 V1100 H-200Z" fill="#3b1f4f"/></g>
    <g id="mata"><path d="M-300 1040 q60-150 120 0 q50-200 110 0 q70-170 130 0 q60-210 120 0 q60-140 120 0 q50-190 110 0 q70-160 130 0 q60-200 120 0 q60-150 120 0 q60-190 120 0 q70-150 130 0 q60-180 120 0 V1120 H-300Z" fill="#16301a"/></g>
    <rect y="1100" width="1080" height="820" fill="#2f2350"/>
    <g id="ondas"></g>
    <path id="reflexo" d="M200 1120 h60 l-10 300 h-40z" fill="#fbe9c8" opacity=".35"/>
  </svg>`;
  S.c3.ondas = S.c3.rio.querySelector("#ondas");
  for (let k = 0; k < 18; k++) { const l = document.createElementNS("http://www.w3.org/2000/svg", "path"); l.setAttribute("stroke", k % 2 ? "#5b4a8a" : "#7a68a8"); l.setAttribute("stroke-width", "6"); l.setAttribute("stroke-linecap", "round"); l.setAttribute("fill", "none"); S.c3.ondas.appendChild(l); }
  S.c3.barco = svg(c3, 1300, 520, `<path d="M0 150 L1300 70 L1200 520 L120 520Z" fill="#7a4a2a"/><path d="M0 150 L1300 70" stroke="#a8693e" stroke-width="28"/><path d="M60 260 L1250 190 M90 360 L1230 300 M110 450 L1210 400" stroke="#5e3820" stroke-width="10"/>`);
  // ônibus
  S.c3.onibus = el("div", "abs", c3); S.c3.onibus.style.cssText += "inset:0;width:1080px;height:1920px;";
  S.c3.onibus.innerHTML = `<svg width="1080" height="1920" viewBox="0 0 1080 1920">
    <rect width="1080" height="1920" fill="#3a2142"/>
    <clipPath id="jan"><rect x="70" y="240" width="940" height="760" rx="40"/></clipPath>
    <g clip-path="url(#jan)"><rect x="70" y="240" width="940" height="760" fill="#24103a"/><g id="predios"></g><g id="luzes"></g></g>
    <rect x="70" y="240" width="940" height="760" rx="40" fill="none" stroke="#6b4a78" stroke-width="30"/>
    <rect x="530" y="240" width="22" height="760" fill="#6b4a78"/>
    <rect y="1130" width="1080" height="790" fill="#5b2a8a"/><rect y="1130" width="1080" height="40" fill="#7a3ab0"/>
  </svg>`;
  S.c3.predios = S.c3.onibus.querySelector("#predios"); S.c3.luzes = S.c3.onibus.querySelector("#luzes");
  for (let k = 0; k < 10; k++) {
    const g = document.createElementNS("http://www.w3.org/2000/svg", "g");
    const h = 260 + (k * 97) % 320;
    g.innerHTML = `<rect x="0" y="${1000 - h}" width="170" height="${h}" fill="${k % 2 ? "#1a0b27" : "#140820"}"/>` + [...Array(6)].map((_, j) => `<rect x="${24 + (j % 3) * 46}" y="${1000 - h + 30 + Math.floor(j / 3) * 70}" width="26" height="36" fill="#ffb627" opacity="${(k + j) % 3 ? .9 : .3}"/>`).join("");
    S.c3.predios.appendChild(g);
  }
  for (let k = 0; k < 8; k++) { const l = document.createElementNS("http://www.w3.org/2000/svg", "rect"); l.setAttribute("height", "10"); l.setAttribute("rx", "5"); l.setAttribute("fill", k % 2 ? "#ff5f15" : "#ffd27a"); S.c3.luzes.appendChild(l); }
  S.c3.note = el("div", "abs", c3);
  S.c3.note.innerHTML = `<div style="width:820px;background:#2a2a32;border-radius:26px 26px 8px 8px;padding:18px;box-shadow:0 30px 60px rgba(0,0,0,.5)"><img id="noteimg" style="width:784px;border-radius:10px;display:block"></div><div style="width:960px;height:44px;margin-left:-70px;background:#4a4a56;border-radius:0 0 30px 30px"></div>`;
  S.c3.noteimg = S.c3.note.querySelector("#noteimg");

  // c4: janela do app, cursor, clique, lupa, lista
  const c4 = nova("c4");
  S.c4 = { c: c4 };
  S.c4.kicker = el("div", "abs kicker", c4, "um clique");
  S.c4.jan = el("div", "abs card", c4, `<div class="janela-topo"><i></i><i></i><i></i><b>ÉguaTeX</b></div><img>`); S.c4.jan.style.width = "1000px";
  S.c4.img = S.c4.jan.querySelector("img");
  S.c4.cursor = svg(c4, 64, 64, `<path d="M8 4 L8 52 L22 40 L32 60 L42 55 L32 36 L50 36 Z" fill="#fff" stroke="#22102f" stroke-width="4" stroke-linejoin="round"/>`);
  S.c4.onda = el("div", "abs onda", c4);
  S.c4.lupa = el("div", "abs card", c4, `<img src="/rea-video/curupira/arte/apoio/lupa_pdf.png">`); S.c4.lupa.style.cssText += "width:620px;border:8px solid #ffb627;";
  S.c4.lista = el("div", "abs lista", c4, `<h3><span>O que vem junto</span><span style="color:#8fd47f">✓</span></h3>
    <div class="item" data-pal="LaTeX"><span class="bola">✓</span>Compilador LaTeX<span class="st">já vem junto</span></div>
    <div class="item" data-pal="instalar"><span class="bola">✓</span>Instalar à parte<span class="st">não precisa</span></div>`);
  S.c4.itens = [...S.c4.lista.querySelectorAll(".item")];

  // c5: erro, explicar, correção, ABNT, interruptor
  const c5 = nova("c5");
  S.c5 = { c: c5 };
  S.c5.kicker = el("div", "abs kicker", c5, "assistente de IA");
  S.c5.jan = el("div", "abs card", c5, `<div class="janela-topo"><i></i><i></i><i></i><b>ÉguaTeX · Assistente IA</b></div><img>`); S.c5.jan.style.width = "1000px";
  S.c5.img = S.c5.jan.querySelector("img");
  S.c5.cursor = svg(c5, 64, 64, `<path d="M8 4 L8 52 L22 40 L32 60 L42 55 L32 36 L50 36 Z" fill="#fff" stroke="#22102f" stroke-width="4" stroke-linejoin="round"/>`);
  S.c5.onda = el("div", "abs onda", c5);
  S.c5.cod = el("div", "abs codigo", c5, `<span class="cmd">\\frac</span>{M_T M_L}<span id="c5ch" class="ruim">{d^2</span>`);
  S.c5.ch = S.c5.cod.querySelector("#c5ch");
  S.c5.abnt = el("div", "abs chip", c5, "✓ Verificar a ABNT");
  S.c5.inter = el("div", "abs", c5, `<div style="display:flex;align-items:center;gap:30px"><div class="inter"><div class="bot"></div></div><div><div style="font-size:56px;font-weight:800">IA</div><div id="c5rot" style="font-family:Atkinson;font-size:36px;color:#c9a6f0">vem desligada</div></div></div>`);
  S.c5.bot = S.c5.inter.querySelector(".bot"); S.c5.trilho = S.c5.inter.querySelector(".inter"); S.c5.rot = S.c5.inter.querySelector("#c5rot");
  S.c5.nota = el("div", "abs", c5, "usa internet e chave gratuita do Gemini"); S.c5.nota.style.cssText += "font-family:Atkinson;font-size:34px;color:#c9a6f0;";

  // c6: pés para trás, pegadas, TCC
  const c6 = nova("c6");
  S.c6 = { c: c6 };
  S.c6.chao = el("div", "abs", c6); S.c6.chao.style.cssText += "left:-200px;top:1560px;width:1480px;height:520px;background:linear-gradient(#2a4a22,#16301a);border-top:8px solid #4a7a3a;";
  S.c6.pegadas = [...Array(4)].map(() => svg(c6, 110, 70, `<ellipse cx="66" cy="35" rx="34" ry="18" fill="#a8763e"/>` + [[24, 18], [18, 30], [20, 42], [28, 52], [36, 60]].map(([x, y]) => `<circle cx="${x}" cy="${y}" r="7" fill="#a8763e"/>`).join("")));
  S.c6.seta = el("div", "abs", c6, `<div style="display:flex;align-items:center;gap:16px;font-size:44px;font-weight:800"><span style="font-size:80px;color:#ffb627">←</span><span>pegadas para trás</span></div>`);
  S.c6.livro = el("div", "abs", c6, `<div style="width:300px;height:400px;background:#1a3a8a;border-radius:10px 22px 22px 10px;box-shadow:inset 26px 0 0 #102a6a,0 24px 40px rgba(0,0,0,.5);display:flex;flex-direction:column;align-items:center;justify-content:center;gap:24px;padding-left:20px"><div style="font-size:90px;font-weight:800;color:#ffb627">TCC</div><div style="font-family:Atkinson;font-size:28px;text-align:center;color:#fff;padding:0 30px">A pororoca do Guamá</div></div>`);
  S.c6.frente = el("div", "abs titulo", c6, "pra <em>frente</em> →"); S.c6.frente.style.fontSize = "100px";

  // c7: cartela final
  const c7 = nova("c7");
  S.c7 = { c: c7 };
  S.c7.logo = el("img", "abs", c7); S.c7.logo.src = "/rea-video/curupira/arte/referencias/curupira.png"; S.c7.logo.style.width = "300px";
  S.c7.marca = el("div", "abs titulo", c7, `<span style="color:#ff5f15">É</span>guaTeX`); S.c7.marca.style.fontSize = "130px";
  S.c7.lema = el("div", "abs", c7); S.c7.lema.style.cssText += "width:940px;text-align:center;font-weight:800;font-size:58px;line-height:1.1;";
  S.c7.lemaPal = "Escreva LaTeX de qualquer lugar, mesmo sem internet.".split(" ").map(w => { const s = el("span", "", S.c7.lema, w); s.style.display = "inline-block"; s.style.marginRight = "16px"; return s; });
  S.c7.selo = el("div", "abs selo", c7, "Feito na Amazônia");
  S.c7.url = el("div", "abs", c7); S.c7.url.style.cssText += "font-weight:800;font-size:96px;color:#ffb627;";
  S.c7.cel = el("div", "abs", c7, `<div style="width:250px;height:500px;background:#1a1420;border-radius:40px;padding:12px;box-shadow:0 24px 40px rgba(0,0,0,.5)"><img src="/rea-video/curupira/arte/apoio/site_celular.png" style="width:226px;height:476px;object-fit:cover;object-position:top;border-radius:30px;display:block"></div>`);
  S.c7.lupa = el("div", "abs card", c7, `<img src="/rea-video/curupira/arte/apoio/lupa_pdf.png">`); S.c7.lupa.style.cssText += "width:470px;border:7px solid #ffb627;";
  S.c7.faixa = el("div", "abs", c7); S.c7.faixa.style.cssText += "left:0;top:1880px;width:1080px;height:40px;background:url('/rea-video/curupira/arte/referencias/faixa-marajoara.svg') repeat-x;background-size:auto 40px;";
}

// ---------------------------------------------------------------- desenho de cada cena
function c1(t, v) {
  const c = C("c1");
  S.c1.c.style.opacity = v.k;
  const t0 = c.inicio + .12;
  // chamas e folhas explodindo na entrada
  S.c1.chamas.forEach((p, i) => {
    const dt = t - t0, a = i * 2.39, vel = 520 + (i * 37) % 600;
    const vida = clamp(1 - dt / (0.7 + (i % 5) * .15));
    tf(p, { x: 540 + Math.cos(a) * vel * dt - 20, y: 1150 + Math.sin(a) * vel * dt + 380 * dt * dt, r: dt * 360, o: dt > 0 ? vida : 0, s: .5 + vida });
  });
  const ts = P("c1", "sofre");
  S.c1.erros.forEach((e, i) => {
    const ti = ts + i * .16;
    const k = pop(t, ti, .4);
    const shake = t > ti ? 6 * Math.sin((t - ti) * 40) * Math.exp(-(t - ti) / .3) : 0;
    tf(e, { x: +e.dataset.x + shake + 6 * ruido(t, i), y: +e.dataset.y + 10 * ruido(t * .8, i + 3), r: +e.dataset.r, s: k, o: clamp(k) });
  });
  const tTCC = P("c1", "TCC");
  const zoom = 1 + .1 * eIO((t - tTCC + .1) / .5);
  const ent = eBack(clamp((t - t0) / .45), 2);
  const pose = poseEm(t)[1];
  if (pose === "frente") desenharCuru(t, { x: 540, y: 990 + 600 * (1 - ent), s: 1.05 * zoom, o: clamp((t - t0) / .1) });
  else desenharCuru(t, { x: 540, y: 1260, s: 1.15 * zoom });
  return 1560;
}

function c2(t, v) {
  S.c2.c.style.opacity = v.k;
  const tl = P("c2", "ÉguaTeX") - .2;
  tf(S.c2.kicker, { x: 540 - 130, y: 140, o: clamp((t - tl + .2) / .2) * v.k });
  const kl = pop(t, tl, .5);
  tf(S.c2.logo, { x: 540 - 210, y: 170 + 30 * (1 - clamp(kl)), s: .62 * kl, r: 20 * (1 - clamp(kl)) + 3 * ruido(t, 2), o: clamp(kl) });
  tf(S.c2.marca, { x: 540 - 290, y: 470 });
  S.c2.letras.forEach((s, i) => { const k = eBack(clamp((t - tl - .1 - i * .05) / .3), 2.5); tf(s, { y: (1 - k) * 80, o: clamp(k * 1.5), r: (1 - k) * 12 }); });
  const pos = [[540, 660], [290, 770], [790, 770], [540, 880]];
  S.c2.chips.forEach((e, i) => {
    const tp = P("c2", e.dataset.pal) - .05;
    const k = pop(t, tp, .4);
    tf(e, { x: pos[i][0] - e.offsetWidth / 2, y: pos[i][1] + 4 * Math.sin(t * 2 + i), s: k, o: clamp(k), r: (i % 2 ? 3 : -3) * clamp(k) });
  });
  desenharCuru(t, { x: 600, y: 1540, s: .82 });
  return 1660;
}

function c3(t, v) {
  S.c3.c.style.opacity = v.k;
  const c = C("c3");
  const tRio = P("c3", "rio") - .35, tOn = P("c3", "ônibus") - .3, tPro = P("c3", "problema");
  const faseA = t < tRio, faseB = t >= tRio && t < tOn, faseC = t >= tOn;
  // A: sem internet
  const kt = pop(t, c.inicio + .05);
  tf(S.c3.titulo, { x: 540 - 360, y: 230, s: kt, o: faseA ? clamp(kt) : 0 });
  const kw = pop(t, c.inicio + .2);
  const voa = clamp((t - tPro) / .5);
  tf(S.c3.wifi, { x: 760 - 180 + 140 * eIn(voa), y: 760 - 300 * eIn(voa) + 10 * Math.sin(t * 3), s: (.8 + .5 * voa) * kw, r: 8 * ruido(t * 2, 1) + 40 * voa, o: faseA ? clamp(kw) * (1 - voa) : 0 });
  S.c3.fumaca.forEach((f, i) => { const dt = t - tPro, a = (i / 12) * Math.PI * 2; tf(f, { x: 820 + Math.cos(a) * 260 * eOut(dt / .8) - 60, y: 820 + Math.sin(a) * 200 * eOut(dt / .8) - 60, s: .5 + dt, o: faseA && dt > 0 ? clamp(1 - dt / 1) * .8 : 0 }); });
  const kok = pop(t, tPro + .2);
  tf(S.c3.ok, { x: 540 - 230, y: 440, s: kok, o: faseA ? clamp(kok) : 0 });
  // B: rio
  S.c3.rio.style.opacity = faseB ? 1 : 0;
  S.c3.barco.style.opacity = faseB ? 1 : 0;
  if (faseB) {
    const dt = t - tRio;
    S.c3.rio.querySelector("#morro2").setAttribute("transform", `translate(${-20 * dt},0)`);
    S.c3.rio.querySelector("#mata").setAttribute("transform", `translate(${-45 * dt},0)`);
    [...S.c3.ondas.children].forEach((l, k) => { const y = 1140 + k * 44, x = ((k * 173 - dt * (90 + k * 6)) % 1300 + 1300) % 1300 - 200; l.setAttribute("d", `M${x} ${y} h${120 + (k % 3) * 40} M${x + 520} ${y + 10} h90`); });
    tf(S.c3.barco, { x: -110, y: 1430 + 8 * Math.sin(t * 2.2), r: 1.2 * Math.sin(t * 2.2) });
  }
  // C: ônibus
  S.c3.onibus.style.opacity = faseC ? 1 : 0;
  S.c3.note.style.opacity = faseC ? 1 : 0;
  if (faseC) {
    const dt = t - tOn;
    [...S.c3.predios.children].forEach((g, k) => { const x = ((k * 230 - dt * 260) % 2300 + 2300) % 2300 - 300; g.setAttribute("transform", `translate(${x},0)`); });
    [...S.c3.luzes.children].forEach((l, k) => { const x = ((k * 300 - dt * 900) % 2400 + 2400) % 2400 - 300; l.setAttribute("x", x); l.setAttribute("y", 900 + (k * 37) % 80); l.setAttribute("width", 140); });
    const n = D.telas.c3_digitando.n;
    setSrc(S.c3.noteimg, tela("c3_digitando", (t - tOn - .15) / (c.fim - tOn - .5) * (n - 1)));
    const kn = pop(t, tOn + .05);
    tf(S.c3.note, { x: 130, y: 1290 + 2 * Math.sin(t * 31) + 200 * (1 - clamp(kn)), s: .95 * kn });
  }
  if (faseA) desenharCuru(t, { x: 430, y: 1430, s: .95 });
  else if (faseB) desenharCuru(t, { x: 540, y: 1360 + 8 * Math.sin(t * 2.2), s: 1.0, r: 1.2 * Math.sin(t * 2.2) });
  else desenharCuru(t, { x: 540, y: 1180 + 2 * Math.sin(t * 31), s: .82 });
  // ordem: barco/notebook na frente do adesivo
  const ordem = faseB ? S.c3.barco : S.c3.note;
  $("frente").appendChild(ordem);
  return 1640;
}

function c4(t, v) {
  S.c4.c.style.opacity = v.k;
  const c = C("c4");
  const tClique = P("c4", "clique") - .05, cl = D.telas.c4_compilar.clique;
  const i = t < tClique ? Math.min(cl - 1, (t - c.inicio) / (tClique - c.inicio) * (cl - 1)) : cl + (t - tClique) / .075;
  setSrc(S.c4.img, tela("c4_compilar", i));
  const kj = pop(t, c.inicio, .45);
  tf(S.c4.jan, { x: 40, y: 250 + 120 * (1 - clamp(kj)), s: .5 + .5 * kj, o: clamp(kj) });
  tf(S.c4.kicker, { x: 60, y: 175, o: clamp((t - c.inicio) / .3) });
  // cursor até o botão de compilar (barra do PDF) e clique
  const alvo = [40 + 1000 * (585 / 1079), 250 + 54 + 1000 * (85 / 1079)];
  const k = eIO((t - (tClique - .9)) / .8);
  const cx = lerp(820, alvo[0], k), cy = lerp(1300, alvo[1], k);
  const aperta = t > tClique && t < tClique + .12 ? .85 : 1;
  tf(S.c4.cursor, { x: cx - 8, y: cy - 4, s: aperta, o: t < tClique + 1.4 ? clamp((t - c.inicio - .3) / .2) : clamp(1 - (t - tClique - 1.4) / .3) });
  const dto = t - tClique;
  tf(S.c4.onda, { x: alvo[0] - 20, y: alvo[1] - 20, s: 1 + 5 * eOut(dto / .5), o: dto > 0 ? clamp(1 - dto / .5) : 0 });
  // lupa do PDF
  const tl = tClique + 1.5;
  const kl = pop(t, tl, .45);
  const sai = clamp((t - P("c4", "LaTeX") + .2) / .3);
  tf(S.c4.lupa, { x: 420 - 60 * sai, y: 760 + 30 * Math.sin(t * 1.5) - 80 * sai, s: kl * (1 - .35 * sai), r: -3, o: clamp(kl) * (1 - sai) });
  // lista do que vem junto
  const tLista = P("c4", "LaTeX") - .15;
  const kli = pop(t, tLista, .45);
  tf(S.c4.lista, { x: 130, y: 880, s: kli, o: clamp(kli) });
  S.c4.itens.forEach(it => { const tp = P("c4", it.dataset.pal); it.classList.toggle("ok", t > tp); const b = it.querySelector(".bola"); tf(b, { s: t > tp ? 1 + mola(t - tp, .35, .3, .1) : 1 }); });
  desenharCuru(t, { x: 230, y: 1560, s: .62 });
  return 1660;
}

function c5(t, v) {
  S.c5.c.style.opacity = v.k;
  const c = C("c5"), mk = D.telas.c5_erro.marcas;
  const tExp = P("c5", "assistente") + .15, tCor = P("c5", "corrige") - .1, tAbnt = P("c5", "ABNT") - .45;
  let i;
  if (t < tExp) i = Math.min(mk.explicar - 1, (t - c.inicio - .1) / .06);
  else if (t < tCor) i = Math.min(mk.explicar + (t - tExp) / Math.max(tCor - tExp, .3) * (mk.corrige - mk.explicar), mk.corrige - 1);
  else if (t < tAbnt) i = Math.min(mk.corrige + (t - tCor) / Math.max(tAbnt - tCor, .3) * (mk.nova - mk.corrige), mk.nova - 1);
  else i = mk.nova + (t - tAbnt) / .08;
  setSrc(S.c5.img, tela("c5_erro", i));
  const kj = pop(t, c.inicio, .45);
  const tErr = P("c5", "erro");
  const treme = t > tErr ? 14 * Math.sin((t - tErr) * 45) * Math.exp(-(t - tErr) / .25) : 0;
  tf(S.c5.jan, { x: 40 + treme, y: 250 + 120 * (1 - clamp(kj)), s: .5 + .5 * kj, o: clamp(kj) });
  tf(S.c5.kicker, { x: 60, y: 175, o: clamp((t - c.inicio) / .3) });
  tf(S.c5.nota, { x: 60, y: 1150, o: clamp((t - c.inicio - .3) / .3) });
  // cursor no botão Explicar (captura 900x800 css @1.2 = 1080x960)
  const f = 1000 / 1080, alvo = [40 + 1000 * 0, 0];
  alvo[0] = 40 + 1000 * (1040 / 1080); alvo[1] = 250 + 54 + 1000 * (103 / 1080) * 1.0;
  const k = eIO((t - (tExp - .8)) / .7);
  tf(S.c5.cursor, { x: lerp(700, alvo[0] - 40, k), y: lerp(1300, alvo[1], k), s: t > tExp - .05 && t < tExp + .08 ? .85 : 1, o: t < tExp + 1 ? clamp((t - c.inicio - .5) / .2) : clamp(1 - (t - tExp - 1) / .3) });
  const dto = t - tExp;
  tf(S.c5.onda, { x: alvo[0] - 60, y: alvo[1] - 20, s: 1 + 5 * eOut(dto / .5), o: dto > 0 ? clamp(1 - dto / .5) : 0 });
  // correção: {d^2 -> {d^2}
  const kc = pop(t, tCor, .4), feito = t > tCor + .45;
  S.c5.ch.textContent = feito ? "{d^2}" : "{d^2";
  S.c5.ch.className = feito ? "ok" : "ruim";
  const saiC = clamp((t - tAbnt) / .3);
  tf(S.c5.cod, { x: 160, y: 900, s: kc * (feito ? 1 + mola(t - tCor - .45, .06, .3, .1) : 1), o: clamp(kc) * (1 - saiC) });
  // ABNT
  const ka = pop(t, P("c5", "ABNT") - .05, .4);
  tf(S.c5.abnt, { x: 540 - 230, y: 920, s: ka, o: clamp(ka) * clamp(1 - (t - P("c5", "quiser") + .3) / .25) });
  // interruptor: liga em "quiser", desliga em "desligado"
  const tq = P("c5", "quiser"), td = P("c5", "desligado");
  const ki = pop(t, tq - .35, .4);
  const lig = clamp((t - tq) / .18) * (1 - clamp((t - td) / .18));
  S.c5.bot.style.transform = `translateX(${104 * eOut(lig)}px)`;
  S.c5.trilho.style.background = lig > .5 ? "#3f9a37" : "#4a3a5c";
  S.c5.rot.textContent = t > td ? "vem desligada" : (lig > .5 ? "ligada, se tu quiser" : "desligada");
  tf(S.c5.inter, { x: 250, y: 900, s: ki, o: clamp(ki) });
  desenharCuru(t, { x: 230, y: 1560, s: .62 });
  return 1660;
}

function c6(t, v) {
  S.c6.c.style.opacity = v.k;
  const c = C("c6");
  const tPes = P("c6", "pés"), tAnda = P("c6", "Só"), tPara = P("c6", "O") - .05, tTcc = P("c6", "TCC"), tFr = P("c6", "frente");
  const x0 = 330, dist = 360, passos = 2, chao = 1560;
  const prog = clamp((t - tAnda) / Math.max(tPara - tAnda, .6));
  const fase = prog * passos, n = Math.min(Math.floor(fase), passos - 1);
  const k = prog > 0 && prog < 1 ? fase - n : (prog >= 1 ? 1 : 0);
  const ar = clamp((k - .15) / .7);
  const x = x0 + dist * (n + eIO(ar)) / passos;
  const pulo = prog > 0 && prog < 1 ? 170 * Math.sin(Math.PI * ar) : 0;
  let sy = 1;
  if (prog > 0 && prog < 1) sy = k < .15 ? 1 - .12 * Math.sin(Math.PI * k / .15) : (k > .85 ? 1 - .14 * Math.sin(Math.PI * (k - .85) / .15) : 1 + .09 * Math.sin(Math.PI * ar));
  // câmera: desce até os pés em "pés"; abre na caminhada
  const zp = eIO((t - tPes + .05) / .5) * (1 - eIO((t - tAnda + .35) / .45));
  const z = 1 + 1.2 * zp, fx = x - 10, fy = chao - 60;
  S.c6.c.style.transformOrigin = `${fx}px ${fy}px`;
  S.c6.c.style.transform = `translate(${(540 - fx) * zp}px, ${(1150 - fy) * zp}px) scale(${z})`;
  const box = $("lado");
  box.style.transformOrigin = `${fx - (x - 380)}px ${fy - (chao - 1250)}px`;
  // pegadas no chão (dedos para trás)
  S.c6.pegadas.forEach((p, i) => { const px = x0 + dist * i / passos; const vis = prog > 0 && fase >= i - .1 + (i === 0 ? 0 : .05); tf(p, { x: px - 55, y: chao - 20, o: i <= passos && vis ? 1 : 0, s: vis ? pop(t, tAnda + (i / passos) * (tPara - tAnda)) : 0 }); });
  tf(S.c6.seta, { x: 120, y: 1700, o: clamp((t - tAnda - .5) / .3) * (1 - clamp((t - tTcc) / .3)) });
  // TCC
  const kl = pop(t, tTcc - .05, .45), vai = eIO((t - tFr) / .7);
  tf(S.c6.livro, { x: Math.min(x + 330, 1080 - 320) - 150 * vai, y: 980 + 60 * vai, s: kl * (.8 + .5 * vai), r: -8 + 8 * vai, o: clamp(kl) });
  tf(S.c6.frente, { x: 540 - 330, y: 260, s: pop(t, tFr, .4), o: clamp(pop(t, tFr, .4)) });
  // adesivo de lado: pivô nos pés
  desenharCuru(t, { x: 0, y: 0, s: 1 });
  const ladoBox = $("lado");
  const camT = `translate(${(540 - fx) * zp}px, ${(1150 - fy) * zp}px) scale(${z})`;
  ladoBox.style.transformOrigin = `0 0`;
  // a câmera também move o adesivo: aplica o mesmo zoom em torno do foco
  const X = x - 380, Y = chao - pulo - 1250;
  const zx = (X - fx) * z + fx + (540 - fx) * zp, zy = (Y - fy) * z + fy + (1150 - fy) * zp;
  ladoBox.style.transform = `translate(${zx}px, ${zy + 1250 * z * (1 - sy)}px) scale(${z}, ${z * sy})`;
  ladoBox.style.opacity = 1;
  return 1760;
}

function c7(t, v) {
  S.c7.c.style.opacity = v.k;
  const c = C("c7");
  const k1 = pop(t, c.inicio, .45);
  tf(S.c7.logo, { x: 540 - 150, y: 110 + 6 * Math.sin(t * 2), s: .7 * k1, o: clamp(k1), r: 3 * ruido(t, 1) });
  tf(S.c7.marca, { x: 540 - 250, y: 330, s: pop(t, c.inicio + .1), o: clamp(pop(t, c.inicio + .1)) });
  tf(S.c7.lema, { x: 70, y: 500 });
  S.c7.lemaPal.forEach((s, i) => { const kk = eBack(clamp((t - c.inicio - .25 - i * .06) / .3), 2); tf(s, { y: (1 - kk) * 40, o: clamp(kk * 1.4) }); });
  tf(S.c7.selo, { x: 540 - 190, y: 680, s: pop(t, c.inicio + .7), o: clamp(pop(t, c.inicio + .7)) });
  const tu = P("c7", "eguatex"), url = "eguatex.com.br";
  const nc = Math.floor(clamp((t - tu) / .9) * url.length);
  S.c7.url.textContent = url.slice(0, nc) + (t > tu && nc < url.length && Math.floor(t * 6) % 2 ? "|" : "");
  tf(S.c7.url, { x: 540 - 360, y: 800, s: 1 + (nc === url.length ? mola(t - tu - .9, .06, .3, .1) : 0) });
  // celular sobe do colar e volta
  const tc = P("c7", "Baixa") - .05, tg = P("c7", "br");
  const sobe = eOut((t - tc) / .35), desce = eIn((t - tg - .2) / .4);
  tf(S.c7.cel, { x: lerp(380, 70, sobe) + 80 * desce, y: lerp(1450, 1000, sobe) + 500 * desce, s: lerp(.4, .9, sobe) - .4 * desce, r: -12 + 12 * eIO((t - tu) / .3), o: t > tc ? clamp(sobe * 2) * (1 - desce) : 0 });
  const tf_ = P("c7", "fórmula") - .35, kl = pop(t, tf_, .45);
  tf(S.c7.lupa, { x: 560, y: 1000 + 10 * Math.sin(t * 1.5), s: kl, r: 5, o: clamp(kl) });
  desenharCuru(t, { x: 380, y: 1500, s: .78 });
  return 1640;
}

const ROTINAS = { c1, c2, c3, c4, c5, c6, c7 };

// ---------------------------------------------------------------- quadro
window.renderizar = async function (t) {
  pendentes.length = 0;
  fundoVivo(t);
  $("frente").innerHTML = "";
  let topoLeg = 1600;
  for (const id of Object.keys(ROTINAS)) {
    const v = cenaVis(t, id);
    const c = S[id].c;
    if (!v.ativa) { c.style.opacity = 0; continue; }
    // transição: entra com zoom/desfoque, sai com zoom
    const sc = 1 + .06 * (1 - eOut(v.kin)) - .03 * (1 - v.kout);
    if (id !== "c6") { c.style.transform = `scale(${sc})`; c.style.filter = v.kin < 1 ? `blur(${(1 - v.kin) * 14}px)` : ""; }
    const r = ROTINAS[id](t, v);
    if (t >= C(id).inicio && t < C(id).fim) topoLeg = r;
  }
  if (!(t >= C("c6").inicio - .04 && t < C("c6").fim)) $("lado").style.opacity = 0;
  const pose = poseEm(t)[1];
  if (pose === "lado") $("curu").style.opacity = 0;
  // flash de chama nas trocas de cena
  let fl = 0;
  for (const id of Object.keys(ROTINAS)) { const dt = t - C(id).inicio; if (dt > -.03 && dt < .12 && id !== "c1") fl = Math.max(fl, .35 * (1 - Math.abs(dt) / .12)); }
  $("flash").style.opacity = fl;
  legenda(t, topoLeg);
  await Promise.all(pendentes);
  await document.fonts.ready;
  return true;
};

window.iniciar = async function () {
  D = await (await fetch(`${BUILD}/dados.json`)).json();
  montarFundo(); montarLegenda(); montarCuru(); montarCenas();
  await document.fonts.ready;
  return D.duracao;
};
