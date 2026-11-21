"""Trilha (carimbó eletrônico leve, sintetizado), efeitos sonoros e mixagem com a voz.

Uso: python audio.py <pasta_build>
Lê <build>/audio/*.wav + falas.json, <build>/efeitos.json. Escreve <build>/mix.wav e <build>/audio/trilha.wav.
Tudo é gerado aqui (sem músicas ou efeitos de terceiros).
"""
import json, math, subprocess, sys
from pathlib import Path

import numpy as np
import soundfile as sf

SR = 48000
DUR = 47.0
BPM = 104
rng = np.random.RandomState(42)


def env(n, a=0.005, d=0.2, forma=2.0):
    t = np.arange(n) / SR
    e = np.minimum(t / a, 1.0) * np.exp(-t / d) ** (1 / forma)
    return e


def tambor(freq=70, dur=0.35, vol=1.0):
    n = int(dur * SR); t = np.arange(n) / SR
    f = freq * (1 + 1.6 * np.exp(-t / 0.02))
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.12)
    x += 0.3 * rng.randn(n) * np.exp(-t / 0.01)
    return x * vol


def maraca(dur=0.07, vol=0.3):
    n = int(dur * SR)
    x = rng.randn(n)
    x = np.diff(np.concatenate([[0], x]))  # agudo
    return x * env(n, 0.003, 0.03) * vol


def corda(freq, dur=0.5, vol=0.5):
    """Karplus-Strong (som de corda dedilhada, tipo banjo)."""
    n = int(dur * SR); p = int(SR / freq)
    buf = rng.uniform(-1, 1, p); out = np.zeros(n)
    for i in range(n):
        out[i] = buf[i % p]
        buf[i % p] = 0.5 * (buf[i % p] + buf[(i + 1) % p]) * 0.994
    return out * vol


def baixo(freq, dur=0.3, vol=0.5):
    n = int(dur * SR); t = np.arange(n) / SR
    x = np.sin(2 * np.pi * freq * t) + 0.3 * np.sin(4 * np.pi * freq * t)
    return x * env(n, 0.01, 0.18) * vol


def colocar(buf, x, t):
    i = int(t * SR)
    if i >= len(buf):
        return
    j = min(len(buf), i + len(x))
    buf[i:j] += x[:j - i]


def trilha():
    n = int((DUR + 1) * SR)
    m = np.zeros(n)
    batida = 60 / BPM
    # escala pentatônica de Lá menor (carimbó costuma ser maior; aqui maior: Dó)
    notas = {"C4": 261.63, "D4": 293.66, "E4": 329.63, "G4": 392.0, "A4": 440.0, "C5": 523.25, "D5": 587.33, "E5": 659.25}
    melodia = ["E4", "G4", "A4", "G4", "E4", "D4", "C4", "D4", "E4", "G4", "C5", "A4", "G4", "E4", "D4", "E4"]
    acordes_baixo = [130.81, 130.81, 174.61, 196.0]  # C C F G
    compasso = 0
    t = 0.0
    while t < DUR:
        for b in range(4):
            tb = t + b * batida
            # curimbó: grave no 1 e no "e" do 2, médio no 3
            if b in (0, 2):
                colocar(m, tambor(68, vol=0.9), tb)
            if b == 1:
                colocar(m, tambor(68, vol=0.5), tb + batida * 0.5)
            if b == 3:
                colocar(m, tambor(110, 0.2, vol=0.45), tb)
            for k in range(4):  # maracas em semicolcheias, acento no contratempo
                colocar(m, maraca(vol=0.18 if k % 2 == 0 else 0.3), tb + k * batida / 4)
            colocar(m, baixo(acordes_baixo[compasso % 4], 0.32, 0.45), tb if b % 2 == 0 else tb + batida * 0.5)
        # melodia dedilhada (só a partir do 2º compasso, para entrar com a fala)
        if compasso >= 1:
            for k in range(4):
                nota = melodia[(compasso * 4 + k) % len(melodia)]
                colocar(m, corda(notas[nota], 0.45, 0.32), t + k * batida + (batida * 0.5 if k % 2 else 0))
        t += 4 * batida
        compasso += 1
    m = m[: int(DUR * SR)]
    # fade de entrada e saída
    fi, fo = int(0.3 * SR), int(1.5 * SR)
    m[:fi] *= np.linspace(0, 1, fi); m[-fo:] *= np.linspace(1, 0, fo)
    return m / (np.max(np.abs(m)) + 1e-9)


# ---------------------------------------------------------------- efeitos
def ruido_filtrado(n, f0, f1):
    x = rng.randn(n)
    # varredura simples: passa-baixa de 1 polo com corte variando
    out = np.zeros(n); y = 0.0
    cortes = np.linspace(f0, f1, n)
    for i in range(n):
        a = 1 - math.exp(-2 * math.pi * cortes[i] / SR)
        y += a * (x[i] - y); out[i] = y
    return out


def fx(nome):
    if nome in ("fogo_whoosh", "whoosh"):
        n = int(0.7 * SR); x = ruido_filtrado(n, 300, 5000) * np.sin(np.linspace(0, np.pi, n)) ** 2
        if nome == "fogo_whoosh":
            x += 0.4 * ruido_filtrado(n, 80, 400) * np.exp(-np.arange(n) / SR / 0.4)
        return x * 3
    if nome == "folhas":
        n = int(0.6 * SR); x = np.zeros(n)
        for k in range(14):
            colocar_local(x, maraca(0.04, 0.5), rng.uniform(0, 0.5))
        return x
    if nome == "pop":
        n = int(0.12 * SR); t = np.arange(n) / SR
        return np.sin(2 * np.pi * (300 + 900 * np.exp(-t / 0.02)) * t) * np.exp(-t / 0.04)
    if nome in ("brilho", "plim"):
        n = int(0.9 * SR); t = np.arange(n) / SR
        fs = [1318.5, 1975.5, 2637.0] if nome == "brilho" else [1567.98, 2093.0]
        x = sum(np.sin(2 * np.pi * f * t) * np.exp(-t / (0.35 - 0.08 * i)) for i, f in enumerate(fs))
        if nome == "brilho":
            x += 0.3 * ruido_filtrado(n, 4000, 9000) * np.exp(-t / 0.15)
        return x * 0.5
    if nome == "estalo":
        n = int(0.05 * SR); return rng.randn(n) * np.exp(-np.arange(n) / SR / 0.006) * 1.2
    if nome == "clique":
        n = int(0.04 * SR); t = np.arange(n) / SR
        return (np.sin(2 * np.pi * 2200 * t) * 0.6 + rng.randn(n) * 0.4) * np.exp(-t / 0.006)
    if nome == "sopro":
        n = int(0.6 * SR); return ruido_filtrado(n, 2500, 400) * np.sin(np.linspace(0, np.pi, n)) * 2
    if nome == "agua":
        n = int(1.4 * SR); x = ruido_filtrado(n, 600, 600) * 0.8
        return x * (0.6 + 0.4 * np.sin(np.arange(n) / SR * 2 * np.pi * 1.3)) * np.sin(np.linspace(0, np.pi, n))
    if nome == "onibus":
        n = int(2.5 * SR); t = np.arange(n) / SR
        return (ruido_filtrado(n, 150, 150) * 1.5 + 0.2 * np.sin(2 * np.pi * 55 * t)) * np.sin(np.linspace(0, np.pi, n))
    if nome == "teclas":
        n = int(1.8 * SR); x = np.zeros(n)
        tt = 0.0
        while tt < 1.7:
            colocar_local(x, fx("clique") * rng.uniform(0.4, 0.8), tt); tt += rng.uniform(0.07, 0.15)
        return x
    if nome == "erro":
        n = int(0.35 * SR); t = np.arange(n) / SR
        return np.sign(np.sin(2 * np.pi * 180 * t)) * 0.25 * np.exp(-t / 0.2)
    if nome == "interruptor":
        return np.concatenate([fx("clique"), np.zeros(int(0.05 * SR)), fx("clique") * 0.6])
    return np.zeros(10)


def colocar_local(buf, x, t):
    i = int(t * SR); j = min(len(buf), i + len(x))
    if i < len(buf):
        buf[i:j] += x[:j - i]


def lufs_norm(x, alvo):
    """Normaliza pela intensidade média (aproximação de LUFS por RMS com porta)."""
    blocos = x[: len(x) // 4800 * 4800].reshape(-1, 4800)
    rms = np.sqrt((blocos ** 2).mean(axis=1) + 1e-12)
    ativos = rms[rms > np.max(rms) * 0.05]
    nivel = 20 * np.log10(np.sqrt((ativos ** 2).mean()) + 1e-12)
    return x * 10 ** ((alvo - nivel) / 20)


def main(build: Path):
    a = build / "audio"
    falas = json.loads((a / "falas.json").read_text(encoding="utf8"))
    n = int(DUR * SR)
    voz = np.zeros(n)
    for f in falas:
        y, sr = sf.read(a / f"{f['id']}.wav")
        if y.ndim > 1:
            y = y.mean(axis=1)
        if sr != SR:
            idx = np.arange(0, len(y), sr / SR)
            y = np.interp(idx, np.arange(len(y)), y)
        colocar_local(voz, y, f["inicio_fala"])
    voz = lufs_norm(voz, -16.0)
    m = trilha()
    sf.write(a / "trilha.wav", m, SR)
    m = lufs_norm(m, -27.0)
    # abaixa a trilha quando ele fala (ducking suave)
    envv = np.convolve(np.abs(voz), np.ones(int(0.05 * SR)) / int(0.05 * SR), "same")
    duck = 1 - 0.45 * np.clip(envv / (np.max(envv) * 0.15), 0, 1)
    duck = np.convolve(duck, np.ones(int(0.15 * SR)) / int(0.15 * SR), "same")
    m = m * duck
    ef = np.zeros(n)
    for e in json.loads((build / "efeitos.json").read_text(encoding="utf8")):
        if e["vol"] > 0:
            colocar_local(ef, fx(e["nome"]) * e["vol"], e["t"])
    ef = ef / (np.max(np.abs(ef)) + 1e-9) * 0.35
    mix = voz + m + ef
    pico = np.max(np.abs(mix))
    if pico > 0.97:
        mix *= 0.97 / pico
    sf.write(build / "mix.wav", np.stack([mix, mix], axis=1), SR)
    print("mix ok", f"pico={np.max(np.abs(mix)):.2f}")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
