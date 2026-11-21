"""Tempo de cada palavra da fala (para legenda e gestos).

Acha os trechos de voz no áudio (silêncios > 110 ms), casa com as frases da fala (pontuação)
e distribui as palavras de cada frase pelo número de sílabas.
"""
import json, re, sys
from pathlib import Path
import numpy as np
import soundfile as sf

VOGAIS = re.compile(r"[aeiouáéíóúâêôãõày]+", re.I)
EXPANDE = {"ÉguaTeX": 4, "TCC": 3, "ABNT": 4, "UFPA": 4, "PDF": 3, "IA": 2, "LaTeX": 2, "br": 2, "eguatex": 4}


def silabas(p):
    limpo = re.sub(r"[^\wÀ-ú]", "", p)
    if limpo in EXPANDE:
        return EXPANDE[limpo]
    return max(1, len(VOGAIS.findall(limpo)))


def trechos(y, sr, lim=0.02, gap=0.11):
    env = np.convolve(np.abs(y), np.ones(int(0.01 * sr)) / int(0.01 * sr), "same")
    voz = env > lim
    out, ini, sil = [], None, 0
    for i in range(0, len(voz), int(0.005 * sr)):
        if voz[i]:
            if ini is None:
                ini = i
            sil = i
        elif ini is not None and (i - sil) / sr > gap:
            out.append((ini / sr, sil / sr)); ini = None
    if ini is not None:
        out.append((ini / sr, sil / sr))
    return out


def frases(fala):
    partes = re.split(r"(?<=[\.\?\!,:])\s+", fala.strip())
    return [p for p in partes if p]


def alinhar(fala, wav, inicio):
    y, sr = sf.read(wav)
    tr = trechos(y, sr)
    fs = frases(fala)
    # junta trechos até ter o mesmo número de frases (os maiores silêncios separam as frases)
    while len(tr) > len(fs):
        gaps = [tr[i + 1][0] - tr[i][1] for i in range(len(tr) - 1)]
        i = int(np.argmin(gaps)); tr[i] = (tr[i][0], tr[i + 1][1]); del tr[i + 1]
    if len(tr) < len(fs):  # menos trechos que frases: divide pela proporção de sílabas
        total = (tr[0][0], tr[-1][1]); tr = []
        pesos = [sum(silabas(w) for w in f.split()) for f in fs]; acc = total[0]
        for p in pesos:
            d = (total[1] - total[0]) * p / sum(pesos); tr.append((acc, acc + d)); acc += d
    palavras = []
    for f, (a, b) in zip(fs, tr):
        ws = f.split(); pesos = [silabas(w) for w in ws]; acc = a
        for w, p in zip(ws, pesos):
            d = (b - a) * p / sum(pesos)
            palavras.append({"palavra": w, "ini": round(inicio + acc, 3), "fim": round(inicio + acc + d, 3)})
            acc += d
    return palavras


def _norm(w):
    import unicodedata
    w = unicodedata.normalize("NFD", w.lower())
    return re.sub(r"[^a-z0-9]", "", "".join(c for c in w if unicodedata.category(c) != "Mn"))


def mapear(fala, tts_palavras):
    """Leva os tempos das palavras faladas (texto da TTS) para as palavras da legenda."""
    from difflib import SequenceMatcher
    orig = fala.split()
    a = [_norm(w) for w in orig]
    b = [_norm(w["palavra"]) for w in tts_palavras]
    out = [None] * len(orig)
    for tag, i1, i2, j1, j2 in SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if tag == "equal":
            for k in range(i2 - i1):
                out[i1 + k] = (tts_palavras[j1 + k]["ini"], tts_palavras[j1 + k]["fim"])
        elif i2 > i1:
            if j2 > j1:
                ini, fim = tts_palavras[j1]["ini"], tts_palavras[j2 - 1]["fim"]
            else:
                ini = fim = (tts_palavras[j1 - 1]["fim"] if j1 > 0 else tts_palavras[0]["ini"])
            n = i2 - i1
            for k in range(n):
                out[i1 + k] = (ini + (fim - ini) * k / n, ini + (fim - ini) * (k + 1) / n)
    return [{"palavra": w, "ini": round(t[0], 3), "fim": round(t[1], 3)} for w, t in zip(orig, out)]


if __name__ == "__main__":
    audio = Path(sys.argv[1])
    falas = json.loads((audio / "falas.json").read_text(encoding="utf8"))
    tudo = {}
    for f in falas:
        falado = alinhar(f["tts"], audio / f"{f['id']}.wav", f["inicio_fala"])
        tudo[f["id"]] = mapear(f["fala"], falado)
        print(f["id"], " ".join(f"{w['palavra']}@{w['ini']:.2f}" for w in tudo[f["id"]]))
    (audio / "palavras.json").write_text(json.dumps(tudo, ensure_ascii=False, indent=1), encoding="utf8")
