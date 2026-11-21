"""Monta o vídeo 01 do Curupira quadro a quadro (1080x1920, 30 fps).

Uso: python montagem.py <pasta_build> [--de S --ate S] [--previa PASSO]
Lê <build>/audio (falas, palavras, bocas) e <build>/telas (capturas reais do app).
Escreve <build>/video_mudo.mp4 e <build>/efeitos.json (efeitos sonoros para o audio.py).
"""
from __future__ import annotations

import argparse, json, math, random, subprocess, sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).parent))
import marionete as M  # noqa: E402

W, H, FPS = 1080, 1920, 30
DUR = 47.0
ARTE = Path("/home/user/rea-video/curupira/arte")
FONTE = "/home/user/ferramentas/fontes/bricolage-grotesque/files/bricolage-grotesque-latin-800-normal.woff"
FONTE7 = "/home/user/ferramentas/fontes/atkinson-hyperlegible/files/atkinson-hyperlegible-latin-700-normal.woff"

# paleta (BGR)
NOITE = (43, 10, 28)
ROXO = (196, 53, 122)
FOGO = (21, 95, 255)
BRASA = (62, 36, 224)
CHAMA = (39, 182, 255)
VERDE = (55, 154, 63)
TEXTO = (251, 234, 243)

random.seed(7)
EFEITOS: list[dict] = []


def efeito(t, nome, vol=1.0):
    EFEITOS.append({"t": round(t, 3), "nome": nome, "vol": vol})


# ---------------------------------------------------------------- utilidades de imagem
def compor(fundo: np.ndarray, cam: np.ndarray, x: int, y: int, alfa: float = 1.0):
    """Cola BGRA em BGR na posição (x, y) (canto superior esquerdo)."""
    h, w = cam.shape[:2]
    x0, y0, x1, y1 = max(x, 0), max(y, 0), min(x + w, fundo.shape[1]), min(y + h, fundo.shape[0])
    if x1 <= x0 or y1 <= y0:
        return
    c = cam[y0 - y:y1 - y, x0 - x:x1 - x]
    a = c[:, :, 3:4].astype(np.float32) / 255.0 * alfa
    roi = fundo[y0:y1, x0:x1]
    roi[:] = (roi * (1 - a) + c[:, :, :3] * a).astype(np.uint8)


def transformar(cam: np.ndarray, ancora_src, ancora_dst, escala=1.0, rot=0.0, sx=1.0, sy=1.0):
    """Leva o BGRA para o quadro inteiro: ponto ancora_src vai para ancora_dst, com escala e rotação."""
    ax, ay = ancora_src
    m = cv2.getRotationMatrix2D((0, 0), -rot, 1.0)
    m[:, :2] = m[:, :2] @ np.diag([escala * sx, escala * sy])
    m[:, 2] = np.array(ancora_dst) - m[:, :2] @ np.array([ax, ay])
    return cv2.warpAffine(cam, m, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))


def compor_cheio(fundo, cam_cheio, alfa=1.0):
    a = cam_cheio[:, :, 3:4].astype(np.float32) / 255.0 * alfa
    fundo[:] = (fundo * (1 - a) + cam_cheio[:, :, :3] * a).astype(np.uint8)


def suave(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def mola(dt, amp=1.0, periodo=0.32, amort=0.16):
    """Resposta de mola (passa do ponto e assenta)."""
    if dt < 0:
        return 0.0
    return amp * math.exp(-dt / amort) * math.cos(2 * math.pi * dt / periodo)


def ruido(t, s):
    return M._ruido(t, s)


def texto_img(txt, tam, cor=TEXTO, contorno=(43, 10, 28), esp=0, fonte=FONTE, larg_max=None, entre=1.05):
    f = ImageFont.truetype(fonte, tam)
    linhas = [txt]
    if larg_max:
        linhas, atual = [], ""
        for w in txt.split():
            teste = (atual + " " + w).strip()
            if f.getlength(teste) > larg_max and atual:
                linhas.append(atual); atual = w
            else:
                atual = teste
        linhas.append(atual)
    alt = int(tam * entre)
    larg = int(max(f.getlength(l) for l in linhas)) + 2 * esp + 8
    img = Image.new("RGBA", (larg, alt * len(linhas) + 2 * esp + int(tam * 0.35)), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for i, l in enumerate(linhas):
        x = (larg - f.getlength(l)) / 2
        d.text((x, esp + i * alt), l, font=f, fill=(cor[2], cor[1], cor[0], 255),
               stroke_width=esp, stroke_fill=(contorno[2], contorno[1], contorno[0], 255))
    return cv2.cvtColor(np.array(img), cv2.COLOR_RGBA2BGRA)


def pilula(txt, tam=58, cor_fundo=FOGO, cor_txt=(255, 255, 255), pad=(38, 16)):
    t = texto_img(txt, tam, cor_txt, esp=0)
    h, w = t.shape[:2]
    img = np.zeros((h + 2 * pad[1], w + 2 * pad[0], 4), np.uint8)
    r = (h + 2 * pad[1]) // 2
    cv2.rectangle(img, (r, 0), (img.shape[1] - r, img.shape[0] - 1), (*cor_fundo, 255), -1, cv2.LINE_AA)
    cv2.circle(img, (r, r), r, (*cor_fundo, 255), -1, cv2.LINE_AA)
    cv2.circle(img, (img.shape[1] - r - 1, r), r, (*cor_fundo, 255), -1, cv2.LINE_AA)
    compor_bgra(img, t, pad[0], pad[1] - int(tam * 0.08))
    return img


def compor_bgra(base, cam, x, y):
    h, w = cam.shape[:2]
    roi = base[y:y + h, x:x + w]
    a = cam[:, :, 3:4].astype(np.float32) / 255
    roi[:, :, :3] = (roi[:, :, :3] * (1 - a) + cam[:, :, :3] * a).astype(np.uint8)
    roi[:, :, 3] = np.maximum(roi[:, :, 3], cam[:, :, 3])


def escalar_bgra(img, s):
    return cv2.resize(img, None, fx=s, fy=s, interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_CUBIC)


def colar_centro(fundo, cam, cx, cy, escala=1.0, alfa=1.0, rot=0.0):
    if escala <= 0.01 or alfa <= 0.01:
        return
    if rot:
        cheio = transformar(cam, (cam.shape[1] / 2, cam.shape[0] / 2), (cx, cy), escala, rot)
        compor_cheio(fundo, cheio, alfa)
        return
    c = escalar_bgra(cam, escala) if abs(escala - 1) > 1e-3 else cam
    compor(fundo, c, int(cx - c.shape[1] / 2), int(cy - c.shape[0] / 2), alfa)


def pop(t, t0, dur=0.45):
    """Escala de entrada com mola: 0 -> 1.08 -> 1."""
    dt = t - t0
    if dt < 0:
        return 0.0
    if dt < 0.14:
        return suave(dt / 0.14) * 1.08
    return 1.0 + mola(dt - 0.14, 0.08, 0.3, 0.12)


def sombra(cam, raio=28, deslocy=18, opac=0.45):
    h, w = cam.shape[:2]
    pad = raio * 2
    s = np.zeros((h + 2 * pad, w + 2 * pad, 4), np.uint8)
    s[pad:pad + h, pad:pad + w, 3] = (cam[:, :, 3] * opac).astype(np.uint8)
    s[:, :, 3] = cv2.GaussianBlur(s[:, :, 3], (0, 0), raio / 2)
    return s, pad, deslocy


def cantos_redondos(img_bgr, r=26, borda=None):
    h, w = img_bgr.shape[:2]
    a = np.zeros((h, w), np.uint8)
    cv2.rectangle(a, (r, 0), (w - r, h), 255, -1); cv2.rectangle(a, (0, r), (w, h - r), 255, -1)
    for cx, cy in [(r, r), (w - r - 1, r), (r, h - r - 1), (w - r - 1, h - r - 1)]:
        cv2.circle(a, (cx, cy), r, 255, -1, cv2.LINE_AA)
    out = np.dstack([img_bgr, a])
    if borda:
        cv2.rectangle(out, (1, 1), (w - 2, h - 2), (*borda, 255), 3, cv2.LINE_AA)
        out[:, :, 3] = a
    return out


# ---------------------------------------------------------------- fundo: floresta noturna
def fazer_floresta(semente=3):
    rnd = np.random.RandomState(semente)
    Wf, Hf = W + 240, H + 240
    yy = np.linspace(0, 1, Hf)[:, None]
    topo, base = np.array([70, 16, 43], np.float32), np.array(NOITE, np.float32)
    img = (topo * (1 - yy) + base * yy)[:, None, :].repeat(Wf, 1).reshape(Hf, Wf, 3)
    img = img.astype(np.float32)
    camadas = []
    for camada, (n, cor, desfoque, esc) in enumerate([(26, (52, 30, 40), 18, 1.4), (22, (36, 48, 22), 9, 1.0), (16, (20, 38, 12), 4, 0.8)]):
        c = np.zeros((Hf, Wf, 4), np.float32)
        for _ in range(n):
            x = rnd.randint(-100, Wf + 100)
            y = rnd.choice([rnd.randint(-100, 500), rnd.randint(Hf - 700, Hf + 100), rnd.randint(-100, Hf)])
            L = rnd.randint(160, 420) * esc
            ang = rnd.uniform(0, 360)
            folha = np.zeros((Hf, Wf), np.uint8)
            cv2.ellipse(folha, (int(x), int(y)), (int(L), int(L * 0.36)), ang, 0, 360, 255, -1, cv2.LINE_AA)
            cv2.line(folha, (int(x - L * math.cos(math.radians(ang))), int(y - L * math.sin(math.radians(ang)))),
                     (int(x + L * math.cos(math.radians(ang))), int(y + L * math.sin(math.radians(ang)))), 120, 6, cv2.LINE_AA)
            m = folha > 0
            c[m, :3] = cor
            c[m, 3] = folha[m] / 255.0 * rnd.uniform(0.55, 0.95)
        c[:, :, 3] = cv2.GaussianBlur(c[:, :, 3], (0, 0), desfoque)
        camadas.append(c)
    # brilho quente atrás do personagem
    gy, gx = np.mgrid[0:Hf, 0:Wf]
    brilho = np.exp(-(((gx - Wf / 2) / 520) ** 2 + ((gy - Hf * 0.46) / 640) ** 2))
    img += brilho[:, :, None] * np.array([8, 30, 70], np.float32)
    return img, camadas


FLORESTA = None


def fundo_floresta(t, foco=1.0):
    global FLORESTA
    if FLORESTA is None:
        FLORESTA = fazer_floresta()
    base, camadas = FLORESTA
    img = base.copy()
    for i, c in enumerate(camadas):
        dx = int(120 + math.sin(t * 0.13 + i) * (8 + 10 * i))
        dy = int(120 + math.cos(t * 0.11 + i * 2) * (6 + 8 * i))
        sub = c[dy:dy + H, dx:dx + W]
        a = sub[:, :, 3:4]
        img[dy:dy + H, dx:dx + W] = img[dy:dy + H, dx:dx + W] * (1 - a) + sub[:, :, :3] * a
    out = img[120:120 + H, 120:120 + W].clip(0, 255).astype(np.uint8)
    return out


# ---------------------------------------------------------------- partículas
class Brasas:
    def __init__(self, n=34, semente=11):
        r = random.Random(semente)
        self.p = [(r.uniform(0, W), r.uniform(0, H), r.uniform(18, 60), r.uniform(1.6, 4.2), r.uniform(0, 6.28)) for _ in range(n)]

    def desenhar(self, img, t, alfa=1.0):
        cam = np.zeros((H, W, 3), np.uint8)
        for x0, y0, vel, tam, fase in self.p:
            y = (y0 - vel * t) % (H + 80) - 40
            x = x0 + math.sin(t * 0.9 + fase) * 24
            br = 0.55 + 0.45 * math.sin(t * 5 + fase * 3)
            cor = tuple(int(c * br) for c in (40, 150, 255))
            cv2.circle(cam, (int(x), int(y)), int(tam * 2.6), tuple(int(c * 0.25) for c in cor), -1, cv2.LINE_AA)
            cv2.circle(cam, (int(x), int(y)), int(tam), cor, -1, cv2.LINE_AA)
        cam = cv2.GaussianBlur(cam, (0, 0), 1.2)
        img[:] = np.clip(img.astype(np.int16) + (cam * alfa).astype(np.int16), 0, 255).astype(np.uint8)


BRASAS = Brasas()


def fazer_folhagem(semente=21):
    rnd = np.random.RandomState(semente)
    Hb = 760
    c = np.zeros((Hb, W + 200, 4), np.float32)
    for k in range(40):
        x = rnd.randint(-60, W + 260); y = rnd.randint(330, Hb + 60)
        L = rnd.randint(150, 290); ang = rnd.uniform(200, 340)
        cor = [(18, 34, 10), (26, 52, 16), (30, 22, 40)][k % 3]
        m = np.zeros((Hb, W + 200), np.uint8)
        cv2.ellipse(m, (x, y), (L, int(L * 0.34)), ang, 0, 360, 255, -1, cv2.LINE_AA)
        sel = m > 0
        c[sel, :3] = cor
        c[sel, 3] = np.maximum(c[sel, 3], m[sel] / 255.0)
    c[:, :, 3] = cv2.GaussianBlur(c[:, :, 3], (0, 0), 3)
    # parte de baixo fechada
    c[560:, :, :3] = np.where(c[560:, :, 3:4] > 0.1, c[560:, :, :3], (14, 26, 8))
    c[560:, :, 3] = 1.0
    out = np.zeros((Hb, W + 200, 4), np.uint8)
    out[:, :, :3] = c[:, :, :3].astype(np.uint8); out[:, :, 3] = (c[:, :, 3] * 255).astype(np.uint8)
    return out


FOLHAGEM = None


def folhagem(img, t, topo=1660):
    global FOLHAGEM
    if FOLHAGEM is None:
        FOLHAGEM = fazer_folhagem()
    dx = int(100 + 18 * math.sin(t * 0.8))
    compor(img, FOLHAGEM[:, dx:dx + W], 0, topo - 300 + int(4 * math.sin(t * 1.1)), 1.0)


def explosao(img, t, t0, cx, cy, n=46, semente=5, escala=1.0):
    """Chamas e folhas saindo de um ponto (entrada do Curupira)."""
    dt = t - t0
    if dt < 0 or dt > 1.6:
        return
    r = random.Random(semente)
    cam = np.zeros((H, W, 4), np.uint8)
    for i in range(n):
        ang = r.uniform(0, 2 * math.pi)
        v = r.uniform(500, 1300) * escala
        x = cx + math.cos(ang) * v * dt * (1 - dt * 0.35)
        y = cy + math.sin(ang) * v * dt * (1 - dt * 0.35) + 300 * dt * dt
        vida = max(0.0, 1 - dt / r.uniform(0.7, 1.5))
        if vida <= 0:
            continue
        if i % 3 == 0:
            L = r.uniform(18, 34) * escala
            cv2.ellipse(cam, (int(x), int(y)), (int(L), int(L * 0.4)), math.degrees(ang) + dt * 400, 0, 360, (*VERDE, int(255 * vida)), -1, cv2.LINE_AA)
        else:
            tam = r.uniform(8, 22) * escala * (0.4 + vida)
            cor = CHAMA if i % 2 else FOGO
            cv2.circle(cam, (int(x), int(y)), int(tam), (*cor, int(230 * vida)), -1, cv2.LINE_AA)
    # clarão
    if dt < 0.35:
        k = 1 - dt / 0.35
        cv2.circle(cam, (int(cx), int(cy)), int(140 + 500 * dt), (*CHAMA, int(150 * k)), -1, cv2.LINE_AA)
    cam[:, :, 3] = cv2.GaussianBlur(cam[:, :, 3], (0, 0), 1.5)
    compor_cheio(img, cam)


# ---------------------------------------------------------------- dados do build
class Dados:
    def __init__(self, build: Path):
        a = build / "audio"
        self.falas = {f["id"]: f for f in json.loads((a / "falas.json").read_text(encoding="utf8"))}
        self.palavras = json.loads((a / "palavras.json").read_text(encoding="utf8"))
        self.bocas = []
        for cid, f in self.falas.items():
            cues = json.loads((a / f"{cid}_boca.json").read_text())["mouthCues"]
            for c in cues:
                self.bocas.append((f["inicio_fala"] + c["start"], f["inicio_fala"] + c["end"], c["value"]))
        self.bocas.sort()
        self.telas = {}
        for nome in ["c3_digitando", "c4_compilar", "c5_erro"]:
            pasta = build / "telas" / nome
            arqs = sorted(pasta.glob("*.png"))
            self.telas[nome] = arqs

    def boca(self, t):
        for a, b, v in self.bocas:
            if a <= t < b:
                return v
        return "X"

    def palavra(self, cena, texto, n=0):
        """Tempo de início da n-ésima palavra que começa com 'texto' na cena."""
        k = 0
        for w in self.palavras[cena]:
            if w["palavra"].strip(".,:?!").lower().startswith(texto.lower()):
                if k == n:
                    return w["ini"]
                k += 1
        raise KeyError(f"{cena}: {texto}")

    def tela(self, nome, i):
        arqs = self.telas[nome]
        i = int(min(max(i, 0), len(arqs) - 1))
        return arqs[i]


_CACHE_TELA = {}


def ler_tela(caminho):
    if caminho not in _CACHE_TELA:
        if len(_CACHE_TELA) > 40:
            _CACHE_TELA.clear()
        _CACHE_TELA[caminho] = cv2.imread(str(caminho))
    return _CACHE_TELA[caminho]


# ---------------------------------------------------------------- o Curupira em cena
class Ator:
    """Controla pose, cabeça, piscadas e boca do Curupira ao longo do tempo."""

    def __init__(self, dados: Dados, chaves, gestos=(), semente=1):
        self.d = dados
        self.chaves = sorted(chaves)       # [(t, pose)]
        self.gestos = sorted(gestos)       # [(t, tipo, amp)]
        r = random.Random(semente)
        self.piscadas = []
        t = r.uniform(0.6, 1.6)
        while t < DUR + 2:
            self.piscadas.append(t)
            if r.random() < 0.18:
                self.piscadas.append(t + 0.28)
            t += r.uniform(1.8, 4.6)
        # acenos automáticos nas palavras com 2+ sílabas
        self.acenos = []
        for cena, ws in dados.palavras.items():
            for w in ws:
                if len(w["palavra"]) > 3:
                    self.acenos.append((w["ini"], 0.35 + 0.35 * r.random()))

    def pose_em(self, t):
        atual, ant, tt = self.chaves[0][1], None, -99
        for tk, p in self.chaves:
            if tk <= t:
                ant, atual, tt = atual, p, tk
        return atual, ant, tt

    def estado(self, t):
        e = M.Estado(t=t)
        e.respira = math.sin(2 * math.pi * t / 3.6)
        rot = 1.6 * ruido(t * 0.7, 1.0)
        dx = 2.5 * ruido(t * 0.6, 2.0)
        dy = 1.5 * ruido(t * 0.8, 3.0)
        for t0, amp in self.acenos:
            dt = t - t0
            if -0.05 < dt < 0.8:
                dy += 4.0 * amp * mola(dt, 1, 0.42, 0.14)
                rot += 0.8 * amp * mola(dt, 1, 0.5, 0.16)
        for t0, tipo, amp in self.gestos:
            dt = t - t0
            if dt < -0.3 or dt > 2.5:
                continue
            if tipo == "aceno":
                dy += 7 * amp * mola(dt, 1, 0.42, 0.15)
            elif tipo == "queixo":   # orgulho: queixo sobe e fica
                k = suave(dt / 0.35) * (1 - suave((dt - 1.4) / 0.5))
                dy -= 6 * amp * k; rot -= 3 * amp * k
            elif tipo == "nao":      # balança a cabeça
                if 0 <= dt < 0.9:
                    rot += 6 * amp * math.sin(2 * math.pi * 3.2 * dt) * math.exp(-dt / 0.45)
            elif tipo == "inclina":  # inclina para um lado e volta
                k = suave(dt / 0.25) * (1 - suave((dt - 1.0) / 0.4))
                rot += 6 * amp * k
            elif tipo == "olhar":    # vira para a tela (sustentado)
                k = suave(dt / 0.3) * (1 - suave((dt - 1.6) / 0.4))
                rot += 5 * amp * k; dx += 5 * amp * k
        e.cab_rot, e.cab_dx, e.cab_dy = rot, dx, dy
        e.boca = self.d.boca(t)
        for tp in self.piscadas:
            dt = t - tp
            if 0 <= dt < 0.2:
                e.piscar = [0.55, 1.0, 1.0, 0.6, 0.2, 0.0][min(int(dt * FPS), 5)]
        return e

    def desenhar(self, img, t, ancora, escala, rot_extra=0.0, alfa=1.0, sx=1.0, sy=1.0):
        pose, ant, tt = self.pose_em(t)
        e = self.estado(t)
        # corpo inteiro balança um pouco (peso)
        bx = 6 * ruido(t * 0.5, 7.0)
        by = 4 * ruido(t * 0.6, 8.0) + 3 * e.respira
        br = 0.8 * ruido(t * 0.45, 9.0) + rot_extra
        dt = t - tt
        # pop da troca de pose (passa do ponto e assenta) + antecipação antes da próxima
        esc = 1.0 + mola(dt, 0.045, 0.34, 0.13) if ant else 1.0
        prox = [tk for tk, _ in self.chaves if tk > t]
        if prox:
            falta = prox[0] - t
            if falta < 0.14:
                esc *= 1 - 0.022 * suave(1 - falta / 0.14)
                by += 7 * suave(1 - falta / 0.14)
        def um(nome, a):
            p = M.carregar(nome)
            cam = M.renderizar(nome, e)
            piv = (p.pescoco[0] * M.ESCALA, p.pescoco[1] * M.ESCALA)
            cheio = transformar(cam, piv, (ancora[0] + bx, ancora[1] + by), escala * esc, br, sx, sy)
            compor_cheio(img, cheio, a * alfa)
        if ant and dt < 0.1:
            k = suave(dt / 0.1)
            um(ant, 1 - k)
            um(pose, k)
        else:
            um(pose, 1.0)


# ---------------------------------------------------------------- legenda palavra a palavra
class Legenda:
    def __init__(self, dados: Dados):
        self.grupos = []
        for cena, ws in dados.palavras.items():
            g = []
            for w in ws:
                g.append(w)
                fim_frase = w["palavra"][-1] in ".?!:,"
                if len(g) >= 3 or fim_frase:
                    self.grupos.append(g); g = []
            if g:
                self.grupos.append(g)
        self.f = ImageFont.truetype(FONTE, 84)
        self.cache = {}

    def desenhar(self, img, t, y=1430, x=W / 2):
        for i, g in enumerate(self.grupos):
            ini = g[0]["ini"] - 0.06
            prox = self.grupos[i + 1][0]["ini"] - 0.06 if i + 1 < len(self.grupos) else 1e9
            fim = min(g[-1]["fim"] + 0.35, prox)
            if not (ini <= t < fim):
                continue
            atual = max([k for k, w in enumerate(g) if w["ini"] <= t + 0.02] or [0])
            chave = (i, atual)
            if chave not in self.cache:
                self.cache[chave] = self._render(g, atual)
            cam, = self.cache[chave]
            dtw = t - g[atual]["ini"]
            esc = 1.0 + (mola(dtw, 0.035, 0.25, 0.08) if dtw >= 0 else 0)
            entra = suave((t - ini) / 0.12)
            colar_centro(img, cam, x, y + (1 - entra) * 30, esc, entra)
            return

    def _render(self, g, atual):
        palavras = [w["palavra"] for w in g]
        esp = 9
        larg = [self.f.getlength(p + " ") for p in palavras]
        total = sum(larg)
        img = Image.new("RGBA", (int(total) + 60, 140), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        x = 30
        for k, p in enumerate(palavras):
            cor = (255, 182, 39, 255) if k == atual else (243, 234, 251, 255)
            d.text((x, 12), p, font=self.f, fill=cor, stroke_width=esp, stroke_fill=(28, 10, 43, 255))
            x += larg[k]
        return (cv2.cvtColor(np.array(img), cv2.COLOR_RGBA2BGRA),)


# ---------------------------------------------------------------- objetos de cena
def icone_wifi(tam=220, riscado=True):
    img = np.zeros((tam, tam, 4), np.uint8)
    c = (tam // 2, int(tam * 0.78))
    cv2.circle(img, (tam // 2, tam // 2), tam // 2 - 4, (*TEXTO, 235), -1, cv2.LINE_AA)
    for r in (0.18, 0.32, 0.46):
        cv2.ellipse(img, c, (int(tam * r), int(tam * r)), 0, 225, 315, (*ROXO, 255), int(tam * 0.06), cv2.LINE_AA)
    cv2.circle(img, (c[0], c[1] - 2), int(tam * 0.05), (*ROXO, 255), -1, cv2.LINE_AA)
    if riscado:
        cv2.line(img, (int(tam * 0.2), int(tam * 0.2)), (int(tam * 0.8), int(tam * 0.8)), (*BRASA, 255), int(tam * 0.08), cv2.LINE_AA)
    return img


def logo_bgra(tam):
    im = cv2.imread(str(ARTE / "referencias/curupira.png"), cv2.IMREAD_UNCHANGED)
    return cv2.resize(im, (tam, tam), interpolation=cv2.INTER_AREA)


def marca_texto(tam=120):
    """'ÉguaTeX' como no site: É em fogo, resto claro."""
    e = texto_img("É", tam, FOGO, esp=0)
    resto = texto_img("guaTeX", tam, TEXTO, esp=0)
    h = max(e.shape[0], resto.shape[0])
    img = np.zeros((h, e.shape[1] + resto.shape[1] - 10, 4), np.uint8)
    compor_bgra(img, e, 0, 0); compor_bgra(img, resto, e.shape[1] - 10, 0)
    return img


def faixa_marajoara(largura=W, alt=34):
    import cairosvg, io
    png = cairosvg.svg2png(url=str(ARTE / "referencias/faixa-marajoara.svg"), output_height=alt)
    tile = cv2.imdecode(np.frombuffer(png, np.uint8), cv2.IMREAD_UNCHANGED)
    reps = largura // tile.shape[1] + 2
    faixa = np.hstack([tile] * reps)[:, :largura]
    if faixa.shape[2] == 3:
        faixa = np.dstack([faixa, np.full(faixa.shape[:2], 255, np.uint8)])
    return faixa


def cenario_rio(t):
    img = np.zeros((H, W, 3), np.float32)
    yy = np.linspace(0, 1, H)[:, None, None]
    img[:] = np.array([90, 24, 52], np.float32) * (1 - yy) + np.array([60, 20, 30], np.float32) * yy
    out = img.astype(np.uint8)
    cv2.circle(out, (820, 330), 110, (210, 235, 250), -1, cv2.LINE_AA)
    lua = cv2.GaussianBlur(out, (0, 0), 30); out = cv2.addWeighted(out, 0.7, lua, 0.5, 0)
    # mata na outra margem
    for i in range(14):
        x = i * 90 - 20; h = 140 + (i * 53) % 90
        cv2.ellipse(out, (x, 900), (90, h), 0, 180, 360, (20, 40, 14), -1, cv2.LINE_AA)
    cv2.rectangle(out, (0, 900), (W, H), (70, 30, 40), -1)
    # água: faixas que correm
    for k in range(26):
        y = 920 + k * 40
        fase = t * (1.5 + k * 0.05) + k
        for x0 in range(-200, W + 200, 260):
            x = int(x0 + (fase * 60) % 260)
            cv2.line(out, (x, y), (x + 120, y), (120, 70, 90) if k % 2 else (150, 110, 160), 3, cv2.LINE_AA)
    # reflexo da lua
    cv2.ellipse(out, (820, 1000), (40, 140), 0, 0, 360, (170, 180, 200), -1, cv2.LINE_AA)
    return cv2.GaussianBlur(out, (0, 0), 1.0)


def proa_barco():
    img = np.zeros((520, W + 200, 4), np.uint8)
    pts = np.array([[0, 140], [W + 200, 60], [W + 120, 520], [80, 520]], np.int32)
    cv2.fillPoly(img, [pts], (30, 62, 110, 255), cv2.LINE_AA)
    for k in range(1, 5):
        cv2.line(img, (40, 140 + k * 90), (W + 160, 60 + k * 95), (22, 44, 82, 255), 6, cv2.LINE_AA)
    cv2.line(img, (0, 140), (W + 200, 60), (40, 90, 160, 255), 22, cv2.LINE_AA)
    return img


def cenario_onibus(t):
    out = np.full((H, W, 3), (58, 30, 44), np.uint8)
    # janela
    jx0, jy0, jx1, jy1 = 60, 260, 1020, 1000
    jan = np.zeros((jy1 - jy0, jx1 - jx0, 3), np.uint8)
    jan[:] = (70, 30, 30)
    for i in range(12):
        x = int((i * 170 - t * 700) % (jx1 - jx0 + 400)) - 200
        cv2.line(jan, (x, 420 + (i * 37) % 140), (x + 160, 420 + (i * 37) % 140), (60, 200, 255), 8, cv2.LINE_AA)
    for i in range(7):
        x = int((i * 260 - t * 320) % (jx1 - jx0 + 400)) - 200
        cv2.rectangle(jan, (x, 300 - (i * 41) % 120), (x + 150, 760), (40, 22, 26), -1)
        for wy in range(330, 700, 60):
            cv2.rectangle(jan, (x + 25, wy), (x + 55, wy + 30), (90, 200, 250), -1)
    jan = cv2.GaussianBlur(jan, (0, 0), 3)
    out[jy0:jy1, jx0:jx1] = jan
    cv2.rectangle(out, (jx0, jy0), (jx1, jy1), (90, 60, 74), 26, cv2.LINE_AA)
    cv2.line(out, (W // 2, jy0), (W // 2, jy1), (90, 60, 74), 20)
    # encosto do banco
    cv2.rectangle(out, (0, 1180), (W, H), (60, 40, 120), -1)
    cv2.rectangle(out, (0, 1180), (W, 1220), (80, 60, 150), -1)
    return out


def notebook(tela_bgr, larg=760):
    h_tela = int(larg * 0.62)
    img = np.zeros((h_tela + 140, larg + 120, 4), np.uint8)
    cv2.rectangle(img, (60, 0), (60 + larg, h_tela + 30), (40, 40, 46, 255), -1, cv2.LINE_AA)
    t = cv2.resize(tela_bgr, (larg - 30, h_tela))
    img[15:15 + h_tela, 75:75 + larg - 30, :3] = t
    img[15:15 + h_tela, 75:75 + larg - 30, 3] = 255
    base = np.array([[0, h_tela + 40], [larg + 120, h_tela + 40], [larg + 60, h_tela + 140], [60, h_tela + 140]], np.int32)
    cv2.fillPoly(img, [base], (70, 70, 78, 255), cv2.LINE_AA)
    cv2.line(img, (0, h_tela + 40), (larg + 120, h_tela + 40), (110, 110, 120, 255), 8, cv2.LINE_AA)
    return img


def tcc_livro(larg=300):
    h = int(larg * 1.35)
    img = np.zeros((h, larg, 4), np.uint8)
    cv2.rectangle(img, (0, 0), (larg - 1, h - 1), (120, 40, 20, 255), -1, cv2.LINE_AA)
    cv2.rectangle(img, (0, 0), (26, h - 1), (90, 28, 14, 255), -1)
    t1 = texto_img("TCC", int(larg * 0.24), CHAMA)
    t2 = texto_img("A pororoca do Guamá", int(larg * 0.1), TEXTO, larg_max=larg * 0.8)
    compor_bgra(img, t1, (larg - t1.shape[1]) // 2 + 10, int(h * 0.18))
    compor_bgra(img, t2, (larg - t2.shape[1]) // 2 + 10, int(h * 0.52))
    return img


def pegada(tam=70):
    """Pegada do Curupira: dedos para a ESQUERDA (pés virados para trás, ele anda para a direita)."""
    img = np.zeros((tam, int(tam * 1.6), 4), np.uint8)
    cv2.ellipse(img, (int(tam * 0.95), tam // 2), (int(tam * 0.5), int(tam * 0.26)), 0, 0, 360, (70, 120, 160, 230), -1, cv2.LINE_AA)
    for k, (dx, dy) in enumerate([(-0.55, -0.22), (-0.62, -0.05), (-0.6, 0.12), (-0.52, 0.27), (-0.42, 0.38)]):
        cv2.circle(img, (int(tam * (0.95 + dx)), int(tam * (0.5 + dy))), int(tam * 0.08), (70, 120, 160, 230), -1, cv2.LINE_AA)
    return img


def celular(tela, larg=300):
    h = int(larg * 2.0)
    img = np.zeros((h, larg, 4), np.uint8)
    cv2.rectangle(img, (0, 0), (larg - 1, h - 1), (30, 26, 34, 255), -1, cv2.LINE_AA)
    t = cv2.resize(tela, (larg - 24, h - 24))
    img[12:h - 12, 12:larg - 12, :3] = t[:, :, :3]
    img[12:h - 12, 12:larg - 12, 3] = 255
    return cantos_redondos(img[:, :, :3], 34) if False else img


# ---------------------------------------------------------------- roteiro de cenas
class Video:
    def __init__(self, build: Path):
        self.b = build
        self.d = Dados(build)
        d = self.d
        P = d.palavra
        self.leg = Legenda(d)
        self.marca = marca_texto(132)
        self.logo = logo_bgra(400)
        self.desc2 = texto_img("Editor LaTeX gratuito e offline, feito na Amazônia.", 50, TEXTO, larg_max=860, esp=0, fonte=FONTE7)
        self.faixa = faixa_marajoara()
        self.wifi = icone_wifi(230)
        self.barco = proa_barco()
        self.livro = tcc_livro(300)
        self.pegada = pegada(64)
        self.site = cv2.imread(str(ARTE / "apoio/site_celular.png"))
        self.pdf = cv2.imread(str(ARTE / "apoio/pdf_pagina.png"))
        self.banners = {
            "c3": pilula("Funciona sem internet", 60),
            "c4": pilula("Um clique, PDF pronto", 60),
            "c5": pilula("Assistente de IA opcional", 58, ROXO),
        }
        self.nota_ia = texto_img("usa internet e chave gratuita do Gemini", 36, (216, 182, 199), esp=0, fonte=FONTE7)
        self.lema = texto_img("Escreva LaTeX de qualquer lugar, mesmo sem internet.", 58, TEXTO, larg_max=900, esp=0)
        self.selo = pilula("Feito na Amazônia", 46, (40, 17, 42), CHAMA, pad=(30, 12))
        self.endereco = texto_img("eguatex.com.br", 96, CHAMA, esp=0)
        # quando as telas mudam (para casar com a fala)
        self.t_clique = P("c4", "clique") - 0.05
        # ---- poses e gestos do Curupira (bustos)
        chaves = [
            (0.0, "p4"),
            (P("c1", "sofre") - 0.08, "p5"),
            (P("c1", "TCC") - 0.12, "p3"),
            (3.5, "p4"),
            (P("c2", "ÉguaTeX") - 0.1, "p1"),
            (P("c2", "offline") - 0.1, "p3"),
            (P("c2", "Amazônia") - 0.1, "p2"),
            (10.0, "p5"),                       # mostra o wifi na palma da mão
            (P("c3", "problema") - 0.05, "p4"),
            (P("c3", "jeito") - 0.1, "p2"),
            (17.0, "p4"),
            (P("c4", "clique") - 0.1, "p3"),
            (P("c4", "ladinho") - 0.1, "p1"),
            (P("c4", "LaTeX") - 0.1, "p4"),
            (P("c4", "junto") - 0.1, "p2"),
            (P("c4", "parte") - 0.25, "p4"),
            (25.0, "p5"),
            (P("c5", "explica") - 0.1, "p4"),
            (P("c5", "corrige") - 0.1, "p3"),
            (P("c5", "ABNT") - 0.1, "p2"),
            (P("c5", "quiser") - 0.1, "p5"),
            (P("c5", "desligado") - 0.1, "p4"),
            (41.0, "p1"),
            (P("c7", "grátis") - 0.1, "p5"),
            (P("c7", "br") - 0.1, "p3"),
            (P("c7", "fórmula") - 0.1, "p4"),
            (P("c7", "bonita") - 0.1, "p2"),
        ]
        gestos = [
            (P("c1", "sofre"), "inclina", 1.0),
            (P("c2", "Curupira"), "queixo", 1.0),
            (P("c2", "Amazônia"), "aceno", 1.0),
            (P("c3", "internet"), "inclina", -0.8),
            (P("c3", "escreve"), "aceno", 1.2),
            (P("c4", "PDF"), "olhar", -1.0),
            (P("c4", "parte"), "nao", 1.0),
            (P("c5", "erro"), "inclina", -1.0),
            (P("c5", "explica"), "olhar", -0.8),
            (P("c5", "quiser"), "aceno", 1.0),
            (P("c5", "desligado"), "queixo", 0.7),
            (P("c7", "fórmula"), "olhar", 1.0),
            (P("c7", "bonita"), "aceno", 1.2),
        ]
        self.ator = Ator(d, chaves, gestos)
        # c6: corpo de lado
        self.ator_lado = Ator(d, [(0.0, "lado")], [(P("c6", "pés"), "aceno", 1.2), (P("c6", "frente"), "queixo", 1.0)], semente=4)
        self._efeitos_fixos()

    def _efeitos_fixos(self):
        P = self.d.palavra
        efeito(0.12, "fogo_whoosh", 1.0)
        efeito(0.45, "folhas", 0.7)
        efeito(P("c1", "TCC") - 0.1, "pop", 0.6)
        efeito(P("c2", "ÉguaTeX") - 0.05, "brilho", 0.9)
        efeito(P("c2", "offline"), "estalo", 0.7)
        efeito(10.05, "pop", 0.6)
        efeito(P("c3", "problema"), "sopro", 0.8)
        efeito(P("c3", "rio") - 0.3, "agua", 0.6)
        efeito(P("c3", "ônibus") - 0.25, "onibus", 0.5)
        efeito(P("c3", "escreve") - 0.2, "teclas", 0.6)
        efeito(self.t_clique, "clique", 1.0)
        efeito(self.t_clique + 1.35, "plim", 0.9)
        efeito(P("c5", "erro") - 0.1, "erro", 0.7)
        efeito(P("c5", "assistente") + 0.2, "clique", 0.8)
        efeito(P("c5", "explica") + 0.4, "plim", 0.6)
        efeito(P("c5", "ABNT") - 0.2, "brilho", 0.6)
        efeito(P("c5", "desligado"), "interruptor", 0.8)
        efeito(34.0, "whoosh", 0.6)
        efeito(P("c6", "trás") + 0.1, "risadinha", 0.0)
        efeito(P("c7", "Baixa") - 0.1, "pop", 0.6)
        efeito(P("c7", "bonita"), "brilho", 0.9)

    # -------------------------------------------------------- cada cena
    def quadro(self, t):
        if t < 3.5:
            img = self.c1(t)
        elif t < 10.0:
            img = self.c2(t)
        elif t < 17.0:
            img = self.c3(t)
        elif t < 25.0:
            img = self.c4(t)
        elif t < 34.0:
            img = self.c5(t)
        elif t < 41.0:
            img = self.c6(t)
        else:
            img = self.c7(t)
        for tc in (3.5, 10.0, 17.0, 25.0, 34.0, 41.0):
            dt = t - tc
            if -0.05 <= dt < 0.1:
                k = 1 - abs(dt) / 0.1
                img = cv2.addWeighted(img, 1.0, np.full_like(img, (30, 120, 255)), 0.22 * max(k, 0), 0)
        x, y = self.pos_legenda(t)
        self.leg.desenhar(img, t, y=y, x=x)
        return img

    def pos_legenda(self, t):
        if 17.0 <= t < 34.0:
            return 640, 1410
        if 34.0 <= t < 41.0:
            return W / 2, 1800
        return W / 2, 1700

    # bustos: pescoço em (x, 1560), escala 0.8; a folhagem esconde o corte do tronco
    def c1(self, t):
        img = fundo_floresta(t)
        BRASAS.desenhar(img, t, 0.8)
        explosao(img, t, 0.1, W / 2, 1050)
        P = self.d.palavra
        ent = pop(t, 0.12, 0.5)
        if ent > 0:
            zoom = 1.0 + 0.12 * suave((t - P("c1", "TCC") + 0.1) / 0.5)
            self.ator.desenhar(img, t, (W / 2, 1580), 0.88 * ent * zoom)
        folhagem(img, t)
        return img

    def c2(self, t):
        img = fundo_floresta(t)
        BRASAS.desenhar(img, t, 0.7)
        P = self.d.palavra
        tl = P("c2", "ÉguaTeX") - 0.05
        self.ator.desenhar(img, t, (W / 2 + 40, 1590), 0.8)
        e = pop(t, tl)
        if e > 0:
            colar_centro(img, self.logo, W / 2, 330, e * 0.62, min(1, (t - tl) / 0.15), rot=3 * ruido(t, 3))
            colar_centro(img, self.marca, W / 2, 590, e)
            ed = pop(t, tl + 0.35)
            if ed > 0:
                colar_centro(img, self.desc2, W / 2, 735, ed)
        folhagem(img, t)
        return img

    def c3(self, t):
        P = self.d.palavra
        t_rio = P("c3", "rio") - 0.35
        t_onibus = P("c3", "ônibus") - 0.3
        if t < t_rio:
            img = fundo_floresta(t)
            BRASAS.desenhar(img, t, 0.7)
            self.ator.desenhar(img, t, (W / 2 - 60, 1590), 0.8)
            t_sopra = P("c3", "problema")
            e = pop(t, 10.08)
            wx, wy = W / 2 - 60 + 330, 1330
            if t < t_sopra:
                colar_centro(img, self.wifi, wx, wy, e * 0.85, rot=6 * ruido(t * 2, 1))
            else:
                k = (t - t_sopra) / 0.5
                if k < 1:
                    colar_centro(img, self.wifi, wx + 60 * k, wy - 160 * k, 0.85 + 0.4 * k, 1 - k)
                self.fumaca(img, t - t_sopra, wx, wy - 30)
            folhagem(img, t)
        elif t < t_onibus:
            img = cenario_rio(t)
            balanco = 6 * math.sin(t * 2.2)
            self.ator.desenhar(img, t, (W / 2, 1520 + balanco), 0.85, rot_extra=1.5 * math.sin(t * 2.2))
            compor(img, self.barco, -100, 1450 + int(balanco), 1.0)
        else:
            img = cenario_onibus(t)
            vib = 2 * math.sin(t * 31)
            self.ator.desenhar(img, t, (W / 2, 1420 + vib), 0.8)
            n = len(self.d.telas["c3_digitando"])
            i = (t - (t_onibus + 0.2)) / (17.0 - t_onibus - 0.6) * (n - 1)
            tela = ler_tela(self.d.tela("c3_digitando", i))
            nb = notebook(tela, 860)
            compor(img, nb, (W - nb.shape[1]) // 2, 1250 + int(vib), 1.0)
        self.banner(img, t, "c3", 10.15, 17.0, y=210)
        return img

    def fumaca(self, img, dt, x, y):
        if dt < 0 or dt > 1.2:
            return
        cam = np.zeros((H, W, 4), np.uint8)
        r = random.Random(3)
        for i in range(14):
            a = r.uniform(-0.6, 0.6)
            d = 60 + 260 * dt * r.uniform(0.6, 1.2)
            cx, cy = x + math.sin(a) * d, y - math.cos(a) * d * 1.2
            cv2.circle(cam, (int(cx), int(cy)), int(30 + 70 * dt), (200, 190, 205, int(160 * (1 - dt / 1.2))), -1, cv2.LINE_AA)
        cam[:, :, 3] = cv2.GaussianBlur(cam[:, :, 3], (0, 0), 12)
        compor_cheio(img, cam)

    def janela_app(self, img, tela_bgr, cy=760, larg=1020, t=0.0, t0=0.0):
        h = int(tela_bgr.shape[0] * larg / tela_bgr.shape[1])
        tl = cv2.resize(tela_bgr, (larg, h), interpolation=cv2.INTER_AREA)
        cam = cantos_redondos(tl, 26)
        e = pop(t, t0) if t - t0 < 0.6 else 1.0
        s, pad, dy = sombra(cam)
        colar_centro(img, s, W / 2, cy + dy, e, 1.0)
        colar_centro(img, cam, W / 2, cy, e, 1.0)
        return (W / 2 - larg / 2, cy - h / 2, larg, h)

    def c4(self, t):
        img = fundo_floresta(t)
        BRASAS.desenhar(img, t, 0.5)
        if t < self.t_clique:
            i = min(8, (t - 17.0) / (self.t_clique - 17.0) * 8)
        else:
            i = 9 + (t - self.t_clique) / 0.075
        tela = ler_tela(self.d.tela("c4_compilar", i))
        self.janela_app(img, tela, cy=800, t=t, t0=17.0)
        self.ator.desenhar(img, t, (220, 1720), 0.52)
        folhagem(img, t, topo=1760)
        self.banner(img, t, "c4", 17.15, 25.0, y=190)
        return img

    def c5(self, t):
        img = fundo_floresta(t)
        BRASAS.desenhar(img, t, 0.5)
        P = self.d.palavra
        t_err, t_exp, t_abnt = 25.15, P("c5", "assistente") + 0.15, P("c5", "ABNT") - 0.6
        if t < t_exp:
            i = min(15, (t - t_err) / 0.06)
        elif t < t_abnt:
            i = min(16 + (t - t_exp) / 0.09, 48)
        else:
            i = 49 + (t - t_abnt) / 0.08
        tela = ler_tela(self.d.tela("c5_erro", i))
        x, y, w, h = self.janela_app(img, tela, cy=820, t=t, t0=25.0)
        if t > t_abnt + 0.4:
            k = suave((t - t_abnt - 0.4) / 0.3)
            f = w / tela.shape[1]
            cx, cy = x + 256 * f, y + 611 * f
            cv2.ellipse(img, (int(cx), int(cy)), (int((185 * k + 10) * f), int((34 * k + 6) * f)), 0, 0, 360, CHAMA, 7, cv2.LINE_AA)
        self.ator.desenhar(img, t, (220, 1720), 0.52)
        folhagem(img, t, topo=1760)
        self.banner(img, t, "c5", 25.15, 34.0, y=190)
        if t > 25.4:
            colar_centro(img, self.nota_ia, W / 2, 285, 1.0, suave((t - 25.4) / 0.3))
        return img

    def c6(self, t):
        P = self.d.palavra
        img = fundo_floresta(t)
        BRASAS.desenhar(img, t, 0.6)
        chao_y = 1640
        cv2.rectangle(img, (0, chao_y), (W, H), (24, 44, 20), -1)
        cv2.line(img, (0, chao_y), (W, chao_y), (40, 80, 34), 6, cv2.LINE_AA)
        t_anda, t_para = P("c6", "Só"), P("c6", "O", 0) - 0.05
        x0, dist, passos = 300, 330, 3
        dur = max(t_para - t_anda, 0.6)
        prog = min(max((t - t_anda) / dur, 0), 1)
        fase = prog * passos
        k_pulo = fase - int(fase) if 0 < prog < 1 else 0
        x = x0 + dist * suave(prog)
        pulo = 80 * math.sin(math.pi * k_pulo)
        sy = 1 + (0.04 * math.sin(math.pi * k_pulo) if 0 < prog < 1 else 0)
        for st in range(passos + 1):
            if prog > 0 and prog * passos >= st:
                px = x0 + dist * suave(st / passos)
                compor(img, self.pegada, int(px - 60), chao_y + 22, 0.9)
        S = 0.64
        lado = M.carregar("lado")
        pes_y = 968 * M.ESCALA
        piv_y = lado.pescoco[1] * M.ESCALA
        piv_x = lado.pescoco[0] * M.ESCALA
        pes_x = 166 * M.ESCALA
        anc = (x + (piv_x - pes_x) * S, chao_y - pulo - (pes_y - piv_y) * S * sy)
        cena = img
        self.ator_lado.desenhar(cena, t, anc, S, sy=sy)
        t_tcc, t_frente = P("c6", "TCC"), P("c6", "frente")
        if t > t_tcc - 0.05:
            e = pop(t, t_tcc - 0.05)
            vai = suave((t - t_frente) / 0.7)
            colar_centro(cena, self.livro, min(x + 330, W - 190), 1050 + 80 * vai, e * (0.75 + 0.75 * vai), rot=-8 + 8 * vai)
        # câmera: em "pés" desce até os pés; abre de novo quando ele começa a andar
        t_pes = P("c6", "pés")
        zp = suave((t - t_pes + 0.05) / 0.55) * (1 - suave((t - t_anda + 0.35) / 0.45))
        if zp > 0.001:
            z = 1 + 1.3 * zp
            alvo = (x - 10, chao_y - 70)
            tx = W / 2 - alvo[0] * z
            ty = H * 0.55 - alvo[1] * z
            m = np.float32([[z, 0, tx * zp], [0, z, ty * zp + (1 - zp) * 0]])
            m[0, 2] = (1 - zp) * 0 + zp * tx + (1 - zp) * (-(z - 1) * alvo[0]) * 0
            cena = cv2.warpAffine(cena, np.float32([[z, 0, alvo[0] - z * alvo[0] + (W / 2 - alvo[0]) * zp],
                                                    [0, z, alvo[1] - z * alvo[1] + (H * 0.55 - alvo[1]) * zp]]),
                                  (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        return cena

    def c7(self, t):
        P = self.d.palavra
        img = fundo_floresta(t)
        BRASAS.desenhar(img, t, 0.9)
        colar_centro(img, self.logo, W / 2, 230, pop(t, 41.0) * 0.42)
        colar_centro(img, self.marca, W / 2, 440, pop(t, 41.1) * 0.85)
        colar_centro(img, self.lema, W / 2, 590, pop(t, 41.25))
        colar_centro(img, self.selo, W / 2, 725, pop(t, 41.35))
        t_end = P("c7", "eguatex")
        e_end = pop(t, t_end)
        if e_end > 0:
            colar_centro(img, self.endereco, W / 2, 850, e_end * (1 + 0.03 * math.sin(t * 6)))
        # PDF pequeno atrás do Curupira, à direita
        pdf = self.pdf[0:int(self.pdf.shape[0] * 0.40)]
        pdfc = cantos_redondos(cv2.resize(pdf, (380, int(380 * pdf.shape[0] / pdf.shape[1]))), 14)
        t_f = P("c7", "fórmula") - 0.3
        colar_centro(img, pdfc, 850, 1130, pop(t, t_f) * 0.95, rot=6)
        self.ator.desenhar(img, t, (W / 2 - 40, 1640), 0.72)
        t_cel, t_guarda = P("c7", "Baixa") - 0.05, P("c7", "br")
        if t_cel <= t < t_guarda + 0.35:
            e = pop(t, t_cel)
            sai = suave((t - t_guarda) / 0.35)
            cel = celular(self.site, 240)
            colar_centro(img, cel, 150 - 160 * sai, 1240 + 300 * sai, e * 0.8, 1 - sai, rot=-10 + 10 * suave((t - P("c7", "eguatex")) / 0.3))
        folhagem(img, t)
        compor(img, self.faixa, 0, H - self.faixa.shape[0], 1.0)
        return img

    def banner(self, img, t, cena, t0, t1, y=200):
        b = self.banners[cena]
        e = pop(t, t0)
        sai = suave((t - (t1 - 0.25)) / 0.25)
        if e > 0 and sai < 1:
            colar_centro(img, b, W / 2, y - 40 * sai, e, 1 - sai)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("build")
    ap.add_argument("--de", type=float, default=0.0)
    ap.add_argument("--ate", type=float, default=DUR)
    ap.add_argument("--quadros", type=str, default="", help="tempos separados por vírgula: salva PNGs")
    ap.add_argument("--saida", default="video_mudo.mp4")
    a = ap.parse_args()
    build = Path(a.build)
    v = Video(build)
    if a.quadros:
        out = build / "quadros"; out.mkdir(exist_ok=True)
        for s in a.quadros.split(","):
            t = float(s)
            cv2.imwrite(str(out / f"q_{t:06.2f}.jpg"), v.quadro(t), [cv2.IMWRITE_JPEG_QUALITY, 90])
        return
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", str(build / a.saida)]
    ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    n0, n1 = int(a.de * FPS), int(a.ate * FPS)
    for n in range(n0, n1):
        t = n / FPS
        ff.stdin.write(v.quadro(t).tobytes())
        if n % 60 == 0:
            print(f"{t:5.1f}s", flush=True)
    ff.stdin.close(); ff.wait()
    (build / "efeitos.json").write_text(json.dumps(EFEITOS, ensure_ascii=False, indent=1), encoding="utf8")


if __name__ == "__main__":
    main()
