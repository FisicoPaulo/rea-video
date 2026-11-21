"""Marionete 2D do Curupira a partir das poses de referência.

Cada pose é uma imagem recortada (RGBA). Por quadro, um único remap deforma a imagem de forma contínua
(sem emendas): cabeça girando presa ao pescoço, respiração, chamas tremulando, folhas balançando.
Boca (Rhubarb A..H, X) e piscadas são desenhadas por cima, acompanhando a cabeça.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path

import cv2
import numpy as np

CAMADAS = Path("/home/user/rea-video/curupira/arte/camadas")
ESCALA = 2.0  # trabalha em 2x da arte original

CONTORNO = (20, 26, 59)       # BGR de #3b1a14 (contorno escuro quente)
BOCA_DENTRO = (40, 32, 110)   # #6e2028
LINGUA = (106, 110, 228)      # #e46e6a
DENTE = (246, 248, 252)
CILIO = (16, 22, 43)          # #2b1610


@dataclass
class Olho:
    c: tuple            # centro (x, y) na arte original
    r: tuple            # raios (rx, ry)
    pisca: bool = True


@dataclass
class Pose:
    nome: str
    boca_c: tuple
    boca_apagar: tuple          # (x0, y0, x1, y1) a apagar (boca original)
    angulo: float               # inclinação do rosto em graus (positivo = horário)
    olhos: list
    pescoco: tuple              # pivô da cabeça
    queixo_y: float             # abaixo disso a cabeça não gira
    cabeca_x: tuple = (-1e9, 1e9)  # faixa x da cabeça (mãos fora dela não giram)
    dist_olhos: float = 113.0
    pele: tuple | None = None   # amostra de pele (x, y)
    corte_baixo: int = 10000    # apaga abaixo disto (restos do recorte)
    apagar_caixas: list = field(default_factory=list)  # caixas (x0,y0,x1,y1) com restos de outras poses
    arquivo: str = ''
    perfil: bool = False
    prolonga: bool = True
    img: np.ndarray | None = field(default=None, repr=False)
    pesos: dict = field(default_factory=dict, repr=False)


POSES = {
    "p4": Pose("p4", (226, 384), (186, 370, 268, 396), -2, [Olho((168, 318), (34, 28)), Olho((281, 314), (37, 28))],
               (226, 452), 438, dist_olhos=113, pele=(226, 360)),
    "p3": Pose("p3", (282, 382), (252, 360, 312, 404), 10, [Olho((243, 300), (33, 27)), Olho((342, 318), (29, 25))],
               (300, 455), 428, cabeca_x=(215, 1e9), dist_olhos=101, pele=(300, 350)),
    "p5": Pose("p5", (250, 388), (222, 360, 278, 414), 15, [Olho((205, 290), (31, 29)), Olho((320, 322), (29, 28))],
               (255, 458), 442, cabeca_x=(-1e9, 365), dist_olhos=118, pele=(260, 345)),
    "p1": Pose("p1", (357, 340), (322, 312, 394, 368), 23, [Olho((325, 245), (31, 26)), Olho((420, 287), (26, 23))],
               (330, 425), 400, cabeca_x=(232, 1e9), dist_olhos=103, pele=(370, 300), corte_baixo=498,
               apagar_caixas=[(0, 470, 200, 550)]),
    "p2": Pose("p2", (250, 377), (203, 350, 294, 404), 15, [Olho((210, 287), (31, 27), pisca=False), Olho((325, 325), (30, 14), pisca=False)],
               (250, 452), 434, cabeca_x=(-1e9, 420), dist_olhos=117, pele=(250, 330), corte_baixo=500),
    "frente": Pose("frente", (216, 301), (191, 293, 243, 311), 0, [Olho((178, 257), (22, 16)), Olho((250, 260), (22, 16))],
                   (215, 346), 332, dist_olhos=72, pele=(200, 290), arquivo="corpo_frente_rgba.png", corte_baixo=730, prolonga=False),
    "lado": Pose("lado", (277, 296), None, -6, [Olho((263, 233), (11, 15))], (212, 338), 322, dist_olhos=50,
                 pele=(250, 275), arquivo="corpo_lado_pes_certos.png", perfil=True),
}


def _hsv_mascaras(rgba: np.ndarray):
    bgr = rgba[:, :, :3]
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV).astype(np.float32)
    h, s, v = hsv[:, :, 0] * 2, hsv[:, :, 1] / 255, hsv[:, :, 2] / 255
    a = rgba[:, :, 3] / 255.0
    cabelo = (((h < 48) | (h > 335)) & (s > 0.80) & (v > 0.45)).astype(np.float32) * a
    folha = ((h > 70) & (h < 170) & (s > 0.35)).astype(np.float32) * a
    return cabelo, folha


def carregar(nome: str) -> Pose:
    pose = POSES[nome]
    if pose.img is not None:
        return pose
    rgba = cv2.imread(str(CAMADAS / (pose.arquivo or f"{nome}_rgba.png")), cv2.IMREAD_UNCHANGED)
    # alfa limpo: tira franjas semitransparentes do fundo
    a = rgba[:, :, 3].astype(np.float32)
    a = np.clip((a - 60) * 255.0 / 150.0, 0, 255)
    rgba[:, :, 3] = a.astype(np.uint8)
    rgba[pose.corte_baixo:, :, 3] = 0
    for (x0, y0, x1, y1) in pose.apagar_caixas:
        rgba[y0:y1, x0:x1, 3] = 0
    if not pose.perfil and pose.prolonga:
        # prolonga o tronco para baixo (o corte fica escondido atrás da folhagem da frente)
        px, py = pose.pele
        pose.cor_pele = tuple(int(v) for v in np.median(rgba[py - 6:py + 6, px - 6:px + 6, :3].reshape(-1, 3), axis=0))
        linhas = np.where((rgba[:, :, 3] > 200).sum(axis=1) > 40)[0]
        ult = int(linhas[-1]) - 3
        ext = 260
        base_lin = rgba[ult - 2:ult - 1].copy()
        hsv_l = cv2.cvtColor(base_lin[:, :, :3], cv2.COLOR_BGR2HSV)
        verde = (hsv_l[:, :, 0] > 35) & (hsv_l[:, :, 0] < 90)
        base_lin[verde, :3] = pose.cor_pele
        base_lin[:, :, :3] = cv2.GaussianBlur(base_lin[:, :, :3], (1, 31), 0)
        novo = np.zeros((ult + ext, rgba.shape[1], 4), np.uint8)
        novo[:ult] = rgba[:ult]
        novo[ult:] = base_lin
        sombra = np.linspace(1.0, 0.75, ext)[:, None, None]
        novo[ult:, :, :3] = (novo[ult:, :, :3] * sombra).astype(np.uint8)
        rgba = novo
    # apaga a boca original com a cor da pele (inpaint)
    x0, y0, x1, y1 = pose.boca_apagar or (0, 0, 0, 0)
    m = np.zeros(rgba.shape[:2], np.uint8)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    if pose.boca_apagar:
        cv2.ellipse(m, (int(cx), int(cy)), (int((x1 - x0) / 2 * 1.22), int((y1 - y0) / 2 * 1.3)), pose.angulo, 0, 360, 255, -1)
        rgba[:, :, :3] = cv2.inpaint(rgba[:, :, :3], m, 7, cv2.INPAINT_TELEA)
    # amostra de pele (mediana em volta do ponto)
    px, py = pose.pele
    pose.cor_pele = tuple(int(v) for v in np.median(rgba[py - 6:py + 6, px - 6:px + 6, :3].reshape(-1, 3), axis=0))
    # sobe para 2x
    rgba = cv2.resize(rgba, None, fx=ESCALA, fy=ESCALA, interpolation=cv2.INTER_LANCZOS4)
    H, W = rgba.shape[:2]
    cabelo, folha = _hsv_mascaras(rgba)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    S = ESCALA
    # peso da cabeça: 1 acima do queixo, cai até o pescoço; 0 fora da faixa x da cabeça
    qy, py2 = pose.queixo_y * S, pose.pescoco[1] * S
    wy = np.clip((py2 - yy) / max(py2 - qy, 1), 0, 1)
    xa, xb = pose.cabeca_x[0] * S, pose.cabeca_x[1] * S
    wx = np.clip((xx - xa) / (20 * S), 0, 1) * np.clip((xb - xx) / (20 * S), 0, 1)
    cab = cv2.GaussianBlur((wy * wx).astype(np.float32), (0, 0), 6 * S)
    # chamas: mais solta quanto mais longe do centro do rosto
    fx, fy = pose.boca_c[0] * S, (pose.boca_c[1] - 70) * S
    dist = np.sqrt((xx - fx) ** 2 + (yy - fy) ** 2)
    solta = np.clip((dist - 90 * S) / (120 * S), 0, 1) ** 1.3
    cab_chama = cv2.GaussianBlur(cv2.dilate(cabelo, np.ones((5, 5), np.uint8)), (0, 0), 3 * S) * solta
    fol = cv2.GaussianBlur(folha, (0, 0), 3 * S) * (yy > qy)
    pose.img = rgba
    pose.pesos = {"cabeca": cab, "chama": cab_chama.astype(np.float32), "folha": fol.astype(np.float32),
                  "yy": yy, "xx": xx}
    return pose


def _ruido(t: float, semente: float) -> float:
    """Ruído suave em [-1, 1] (soma de senos incomensuráveis)."""
    return (math.sin(t * 1.13 + semente) * 0.5 + math.sin(t * 2.71 + semente * 1.7) * 0.3
            + math.sin(t * 4.37 + semente * 2.3) * 0.2)


@dataclass
class Estado:
    """O que muda a cada quadro."""
    t: float
    cab_rot: float = 0.0     # graus
    cab_dx: float = 0.0      # px (arte original)
    cab_dy: float = 0.0
    respira: float = 0.0     # -1..1
    boca: str = "X"
    piscar: float = 0.0      # 0 aberto .. 1 fechado
    energia_chama: float = 1.0


def deformar(pose: Pose, e: Estado) -> np.ndarray:
    P = pose.pesos
    S = ESCALA
    xx, yy = P["xx"], P["yy"]
    H, W = xx.shape
    mapx = xx.copy()
    mapy = yy.copy()
    # respiração: corpo sobe e alarga levemente a partir da base
    base = H
    k = 0.006 * e.respira
    mapy += (yy - base) * k * (1 - P["cabeca"]) - 2.0 * S * e.respira * P["cabeca"] * 0.6
    # cabeça: rotação em torno do pescoço + translação, com peso suave
    cx, cy = pose.pescoco[0] * S, pose.pescoco[1] * S
    th = math.radians(-e.cab_rot)
    c, s = math.cos(th), math.sin(th)
    dx, dy = xx - cx, yy - cy
    rx = cx + c * dx - s * dy - e.cab_dx * S
    ry = cy + s * dx + c * dy - e.cab_dy * S
    w = P["cabeca"]
    mapx += (rx - xx) * w
    mapy += (ry - yy) * w
    # chamas: ondas que sobem, amplitude maior nas pontas
    t = e.t
    a = 2.6 * S * e.energia_chama
    ch = P["chama"]
    mapx += ch * a * (np.sin(yy * 0.045 / S + t * 7.0) * 0.6 + np.sin(xx * 0.03 / S - t * 4.3) * 0.4)
    mapy += ch * a * 0.8 * (np.sin(xx * 0.05 / S + t * 6.1) * 0.5 + np.sin(yy * 0.02 / S + t * 9.0) * 0.5) + ch * a * 0.5
    # folhas: balanço com atraso
    fo = P["folha"]
    mapx += fo * 1.2 * S * math.sin(t * 2.3 - 0.8)
    mapy += fo * 0.8 * S * math.sin(t * 3.1 - 1.1)
    return cv2.remap(pose.img, mapx.astype(np.float32), mapy.astype(np.float32), cv2.INTER_LINEAR,
                     borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))


def _transformar_ponto(pose: Pose, e: Estado, p):
    """Leva um ponto da arte original para a imagem deformada (2x), seguindo a cabeça."""
    S = ESCALA
    cx, cy = pose.pescoco
    th = math.radians(e.cab_rot)
    x, y = p[0] - cx, p[1] - cy
    xr = cx + math.cos(th) * x - math.sin(th) * y + e.cab_dx
    yr = cy + math.sin(th) * x + math.cos(th) * y + e.cab_dy - 2.0 * e.respira * 0.6
    return xr * S, yr * S


def _forma_boca(v: str):
    """Forma da boca em coordenadas unitárias (largura 1 = largura do sorriso neutro).
    Devolve (largura, altura_abertura, sorriso, dentes_cima, lingua, redonda)."""
    return {
        "X": (0.95, 0.00, 0.10, 0, 0, 0),
        "A": (0.70, 0.00, 0.04, 0, 0, 0),
        "B": (0.66, 0.16, 0.06, 1, 0, 0),
        "C": (0.70, 0.34, 0.05, 1, 1, 0),
        "D": (0.76, 0.52, 0.04, 1, 1, 0),
        "E": (0.52, 0.34, 0.00, 0, 1, 1),
        "F": (0.32, 0.26, 0.00, 0, 0, 1),
        "G": (0.62, 0.16, 0.02, 2, 0, 0),
        "H": (0.66, 0.36, 0.03, 1, 2, 0),
    }.get(v, (0.95, 0.0, 0.1, 0, 0, 0))


def desenhar_boca_perfil(img, pose, e):
    S = ESCALA
    lw, ab, sor, dentes, lingua, redonda = _forma_boca(e.boca)
    if ab <= 0:
        return
    cx, cy = _transformar_ponto(pose, e, pose.boca_c)
    L = pose.dist_olhos * 0.62 * S
    ang = pose.angulo + e.cab_rot
    camada = np.zeros((img.shape[0], img.shape[1], 4), np.uint8)
    w, h = L * (0.42 if not redonda else 0.26), max(L * ab * 0.55, 2)
    # cunha: canto da boca dentro do rosto, abertura no lábio
    pts = np.array([[cx - w, cy], [cx + w * 0.15, cy - h * 0.45], [cx + w * 0.2, cy + h * 0.55]], np.float32)
    M = cv2.getRotationMatrix2D((cx, cy), -ang, 1.0)
    pts = cv2.transform(pts[None], M)[0]
    cv2.fillPoly(camada, [np.round(pts * 4).astype(np.int32)], (*BOCA_DENTRO, 255), cv2.LINE_AA, shift=2)
    cv2.polylines(camada, [np.round(pts * 4).astype(np.int32)], True, (*CONTORNO, 255), max(int(1.2 * S), 2), cv2.LINE_AA, shift=2)
    _compor(img, camada)


def desenhar_boca(img: np.ndarray, pose: Pose, e: Estado):
    if pose.perfil:
        return desenhar_boca_perfil(img, pose, e)
    S = ESCALA
    L = pose.dist_olhos * 0.62 * S
    cx, cy = _transformar_ponto(pose, e, pose.boca_c)
    ang = pose.angulo + e.cab_rot
    lw, ab, sor, dentes, lingua, redonda = _forma_boca(e.boca)
    w = L * lw
    h = L * ab
    camada = np.zeros((img.shape[0], img.shape[1], 4), np.uint8)
    M = cv2.getRotationMatrix2D((0, 0), -ang, 1.0)

    def pts(lista):
        arr = np.array(lista, np.float32)
        arr = arr @ M[:, :2].T
        arr[:, 0] += cx
        arr[:, 1] += cy
        return np.round(arr * 4).astype(np.int32)  # subpixel (shift=2)

    esp = max(int(round(2.2 * S)), 2)
    if h < 1.0:
        # boca fechada: curva com sorriso nas pontas
        n = 24
        k = L * sor
        lin = [(-w / 2 + w * i / n, 0.0) for i in range(n + 1)]
        lin = [(x, k * 0.5 - k * (2 * x / w) ** 2) for x, _ in lin]
        cv2.polylines(camada, [pts(lin)], False, (*CONTORNO, 255), esp, cv2.LINE_AA, shift=2)
    else:
        n = 32
        cont = []
        for i in range(n + 1):
            u = math.pi * i / n
            x = -math.cos(u) * w / 2
            if redonda:
                ytop = -h * 0.5 * math.sin(u)
            else:
                ytop = -h * 0.18 * math.sin(u) - L * sor * (1 - (2 * x / w) ** 2) * 0.4
            cont.append((x, ytop))
        for i in range(n + 1):
            u = math.pi * i / n
            x = math.cos(u) * w / 2
            ybot = h * (0.5 if redonda else 0.82) * math.sin(u)
            cont.append((x, ybot))
        poly = pts(cont)
        cv2.fillPoly(camada, [poly], (*BOCA_DENTRO, 255), cv2.LINE_AA, shift=2)
        # língua (metade de baixo) e dentes (faixa de cima), recortados pela boca
        clip = np.zeros(img.shape[:2], np.uint8)
        cv2.fillPoly(clip, [poly], 255, cv2.LINE_AA, shift=2)
        extra = np.zeros_like(camada)
        if lingua:
            ly = h * (0.42 if lingua == 1 else 0.05)
            cv2.ellipse(extra, (int(cx + 0), int(cy + ly + h * 0.35)), (int(w * 0.34), int(h * 0.45 + 2)), ang, 180, 360,
                        (*LINGUA, 255), -1, cv2.LINE_AA)
        if dentes:
            th = max(h * (0.28 if dentes == 1 else 0.45), 2.5 * S)
            dent = [(-w * 0.42, -h * 0.25), (w * 0.42, -h * 0.25), (w * 0.38, -h * 0.25 + th), (-w * 0.38, -h * 0.25 + th)]
            cv2.fillPoly(extra, [pts(dent)], (*DENTE, 255), cv2.LINE_AA, shift=2)
        extra[clip == 0] = 0
        m = extra[:, :, 3] > 0
        camada[m] = extra[m]
        cv2.polylines(camada, [poly], True, (*CONTORNO, 255), esp, cv2.LINE_AA, shift=2)
    _compor(img, camada)


def desenhar_piscada(img: np.ndarray, pose: Pose, e: Estado):
    if e.piscar <= 0.05:
        return
    S = ESCALA
    camada = np.zeros((img.shape[0], img.shape[1], 4), np.uint8)
    pele = pose.cor_pele
    ang = pose.angulo + e.cab_rot
    for o in pose.olhos:
        if not o.pisca:
            continue
        cx, cy = _transformar_ponto(pose, e, o.c)
        rx, ry = o.r[0] * S, o.r[1] * S
        f = min(e.piscar, 1.0)
        # pálpebra desce: cobre de cima até a linha
        linha_y = -ry + 2 * ry * (0.55 + 0.45 * f) * f
        mask = np.zeros(img.shape[:2], np.uint8)
        cv2.ellipse(mask, (int(cx), int(cy - ry * 0.08)), (int(rx * 1.22), int(ry * 1.32)), ang, 0, 360, 255, -1, cv2.LINE_AA)
        corte = np.zeros_like(mask)
        M = cv2.getRotationMatrix2D((cx, cy), -ang, 1.0)
        ret = np.array([[cx - rx * 1.3, cy - ry * 1.4], [cx + rx * 1.3, cy - ry * 1.4], [cx + rx * 1.3, cy + linha_y], [cx - rx * 1.3, cy + linha_y]], np.float32)
        ret = cv2.transform(ret[None], M)[0]
        cv2.fillPoly(corte, [np.int32(ret)], 255)
        mask = cv2.bitwise_and(mask, corte)
        mask = cv2.GaussianBlur(mask, (0, 0), 1.2 * S)
        sel = mask > 8
        camada[sel, :3] = pele
        camada[sel, 3] = np.maximum(camada[sel, 3], mask[sel])
        # linha dos cílios (curva para baixo quando fechado)
        n = 20
        cur = []
        for i in range(n + 1):
            x = -rx + 2 * rx * i / n
            y = linha_y + (ry * 0.35 * f) * (1 - (x / rx) ** 2)
            cur.append((x, y))
        arr = np.array(cur, np.float32)
        arr = cv2.transform(arr[None] + np.array([cx, cy], np.float32), cv2.getRotationMatrix2D((cx, cy), -ang, 1.0))[0]
        cv2.polylines(camada, [np.round(arr * 4).astype(np.int32)], False, (*CILIO, 255), max(int(3.2 * S), 2), cv2.LINE_AA, shift=2)
    _compor(img, camada)


def _compor(base: np.ndarray, cam: np.ndarray):
    a = cam[:, :, 3:4].astype(np.float32) / 255.0
    base[:, :, :3] = (base[:, :, :3] * (1 - a) + cam[:, :, :3] * a).astype(np.uint8)


def renderizar(nome: str, e: Estado) -> np.ndarray:
    """Devolve o Curupira (BGRA, 2x) para o estado dado."""
    pose = carregar(nome)
    img = deformar(pose, e)
    desenhar_piscada(img, pose, e)
    desenhar_boca(img, pose, e)
    return img
