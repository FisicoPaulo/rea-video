"""Curupira em adesivo (contorno branco), quadro a quadro, para o motion design em HTML.

Uso: python sprites.py <pasta_build> [--fps 30]
Lê <build>/audio (falas, palavras, bocas) e <build>/atuacao.json (poses e gestos por tempo).
Escreve <build>/sprites/<n>.png (transparente, 1000x1300; pescoço sempre em (500, 700)) e
<build>/sprites/lado_<n>.png para a cena de corpo inteiro de lado.
"""
import argparse, json, math, random, sys
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import marionete as M  # noqa: E402

CW, CH, PIV = 1000, 1300, (500, 700)
ESC = 0.62
LW, LH, LPIV, LESC = 760, 1400, (380, 470), 0.62


def mola(dt, amp, periodo=0.4, amort=0.15):
    return 0.0 if dt < 0 else amp * math.exp(-dt / amort) * math.cos(2 * math.pi * dt / periodo)


def suave(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


class Atuacao:
    def __init__(self, build: Path):
        a = build / "audio"
        self.falas = json.loads((a / "falas.json").read_text(encoding="utf8"))
        self.palavras = json.loads((a / "palavras.json").read_text(encoding="utf8"))
        self.bocas = []
        for f in self.falas:
            for c in json.loads((a / f"{f['id']}_boca.json").read_text())["mouthCues"]:
                self.bocas.append((f["inicio_fala"] + c["start"], f["inicio_fala"] + c["end"], c["value"]))
        at = json.loads((build / "atuacao.json").read_text(encoding="utf8"))
        self.chaves = sorted((k["t"], k["pose"]) for k in at["poses"])
        self.gestos = sorted((g["t"], g["tipo"], g.get("amp", 1.0)) for g in at["gestos"])
        r = random.Random(3)
        self.piscadas, t = [], 0.8
        while t < 200:
            self.piscadas.append(t)
            if r.random() < 0.2:
                self.piscadas.append(t + 0.28)
            t += r.uniform(2.0, 4.5)
        self.acenos = [(w["ini"], 0.3 + 0.4 * r.random()) for ws in self.palavras.values() for w in ws if len(w["palavra"]) > 3]

    def pose(self, t):
        p = self.chaves[0][1]
        for tk, nome in self.chaves:
            if tk <= t:
                p = nome
        return p

    def estado(self, t):
        e = M.Estado(t=t)
        e.respira = math.sin(2 * math.pi * t / 3.6)
        rot = 1.6 * M._ruido(t * 0.7, 1.0); dx = 2.5 * M._ruido(t * 0.6, 2.0); dy = 1.5 * M._ruido(t * 0.8, 3.0)
        for t0, amp in self.acenos:
            dt = t - t0
            if -0.05 < dt < 0.8:
                dy += 4.0 * amp * mola(dt, 1, 0.42, 0.14); rot += 0.8 * amp * mola(dt, 1, 0.5, 0.16)
        for t0, tipo, amp in self.gestos:
            dt = t - t0
            if dt < -0.3 or dt > 2.5:
                continue
            if tipo == "aceno":
                dy += 7 * amp * mola(dt, 1, 0.42, 0.15)
            elif tipo == "queixo":
                k = suave(dt / 0.35) * (1 - suave((dt - 1.4) / 0.5)); dy -= 6 * amp * k; rot -= 3 * amp * k
            elif tipo == "nao":
                if 0 <= dt < 0.9:
                    rot += 6 * amp * math.sin(2 * math.pi * 3.2 * dt) * math.exp(-dt / 0.45)
            elif tipo == "inclina":
                k = suave(dt / 0.25) * (1 - suave((dt - 1.0) / 0.4)); rot += 6 * amp * k
            elif tipo == "olhar":
                k = suave(dt / 0.3) * (1 - suave((dt - 1.6) / 0.4)); rot += 5 * amp * k; dx += 5 * amp * k
            elif tipo == "baixo":
                k = suave(dt / 0.3) * (1 - suave((dt - 1.0) / 0.4)); rot += 12 * amp * k; dy += 4 * amp * k
            elif tipo == "chama":
                e.energia_chama = 1 + 1.5 * math.exp(-max(dt, 0) / 0.5)
        e.cab_rot, e.cab_dx, e.cab_dy = rot, dx, dy
        e.boca = "X"
        for a, b, v in self.bocas:
            if a <= t < b:
                e.boca = v; break
        for tp in self.piscadas:
            dt = t - tp
            if 0 <= dt < 0.2:
                e.piscar = [0.55, 1.0, 1.0, 0.6, 0.2, 0.0][min(int(dt * 30), 5)]
        return e


def adesivo(bgra, borda=11):
    """Contorno branco e leve sombra interna de adesivo."""
    a = bgra[:, :, 3]
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * borda + 1, 2 * borda + 1))
    fora = cv2.dilate(a, k)
    fora = cv2.GaussianBlur(fora, (0, 0), 1.0)
    out = np.zeros_like(bgra)
    out[:, :, :3] = 255
    out[:, :, 3] = fora
    al = a[:, :, None].astype(np.float32) / 255
    out[:, :, :3] = (out[:, :, :3] * (1 - al) + bgra[:, :, :3] * al).astype(np.uint8)
    return out


def no_quadro(img, pose, cw, ch, piv, esc):
    p = M.POSES[pose]
    m = np.float32([[esc, 0, piv[0] - p.pescoco[0] * M.ESCALA * esc], [0, esc, piv[1] - p.pescoco[1] * M.ESCALA * esc]])
    return cv2.warpAffine(img, m, (cw, ch), flags=cv2.INTER_AREA, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))


_AT = None


def _init(build):
    global _AT
    _AT = Atuacao(Path(build))
    for p in M.POSES.values():   # adesivo: o busto termina no corte natural, com contorno
        p.prolonga = False


def _um(args):
    n, fps, out = args
    t = n / fps
    pose = _AT.pose(t)
    e = _AT.estado(t)
    img = M.renderizar(pose, e)
    if pose == "lado":
        q = no_quadro(img, pose, LW, LH, LPIV, LESC)
        nome = f"lado_{n:05d}.png"
    else:
        q = no_quadro(img, pose, CW, CH, PIV, ESC)
        nome = f"{n:05d}.png"
    cv2.imwrite(str(Path(out) / nome), adesivo(q), [cv2.IMWRITE_PNG_COMPRESSION, 1])
    return pose


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("build")
    ap.add_argument("--fps", type=int, default=30)
    a = ap.parse_args()
    build = Path(a.build)
    out = build / "sprites"; out.mkdir(exist_ok=True)
    falas = json.loads((build / "audio/falas.json").read_text(encoding="utf8"))
    dur = falas[-1]["fim"]
    n = int(math.ceil(dur * a.fps))
    with ProcessPoolExecutor(4, initializer=_init, initargs=(str(build),)) as ex:
        poses = list(ex.map(_um, [(i, a.fps, str(out)) for i in range(n)], chunksize=16))
    (out / "indice.json").write_text(json.dumps({"fps": a.fps, "n": n, "poses": poses}), encoding="utf8")
    print("sprites", n)


if __name__ == "__main__":
    main()
