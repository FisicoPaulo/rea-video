"""Prepara um build do motion design: atuacao.json (poses e gestos), dados.json e imagens de apoio.

Uso: python preparar.py <pasta_build> [--telas <build_com_telas>]
"""
import argparse, json, shutil
from pathlib import Path

import cv2
import numpy as np

ARTE = Path("/home/user/rea-video/curupira/arte")


def lupa_pdf():
    pdf = cv2.imread(str(ARTE / "apoio/pdf_pagina.png"))
    g = cv2.cvtColor(pdf, cv2.COLOR_BGR2GRAY)
    lin = np.where((g < 200).sum(axis=1) > 0)[0]
    col = np.where((g < 200).sum(axis=0) > 0)[0]
    y0, y1 = max(lin[0] - 40, 0), min(lin[-1], int(pdf.shape[0] * 0.45))
    corte = pdf[y0:y1, max(col[0] - 40, 0):min(col[-1] + 40, pdf.shape[1])]
    cv2.imwrite(str(ARTE / "apoio/lupa_pdf.png"), corte)


def atuacao(palavras, cenas):
    def P(c, pref, n=0):
        k = 0
        for w in palavras[c]:
            if w["palavra"].strip(".,:?!").lower().startswith(pref.lower()):
                if k == n:
                    return w["ini"]
                k += 1
        raise KeyError(f"{c}: {pref}")
    ini = {c: v["inicio"] for c, v in cenas.items()}
    poses = [
        (0.0, "frente"), (P("c1", "sofre") - .08, "p5"), (P("c1", "TCC") - .12, "p3"),
        (ini["c2"], "p4"), (P("c2", "ÉguaTeX") - .1, "p1"), (P("c2", "Amazônia") - .1, "p2"),
        (ini["c3"], "p5"), (P("c3", "problema") - .05, "p4"), (P("c3", "jeito") - .1, "p2"),
        (ini["c4"], "p4"), (P("c4", "clique") - .1, "p3"), (P("c4", "ladinho") - .1, "p1"), (P("c4", "LaTeX") - .1, "p4"),
        (ini["c5"], "p5"), (P("c5", "explica") - .1, "p4"), (P("c5", "quiser") - .1, "p5"), (P("c5", "desligado") - .1, "p4"),
        (ini["c6"], "lado"),
        (ini["c7"], "p4"), (P("c7", "Baixa") - .1, "p1"), (P("c7", "fórmula") - .1, "p4"), (P("c7", "bonita") - .1, "p2"),
    ]
    gestos = [
        (P("c1", "sofre"), "inclina", 1.0), (P("c2", "Curupira"), "queixo", 1.0), (P("c2", "offline"), "aceno", 1.3),
        (P("c2", "Amazônia"), "aceno", 1.0), (P("c3", "internet"), "inclina", -0.8), (P("c3", "rio"), "inclina", 0.7),
        (P("c3", "escreve"), "aceno", 1.2), (P("c4", "PDF"), "olhar", -1.0), (P("c4", "junto"), "aceno", 1.3),
        (P("c4", "parte"), "nao", 1.0), (P("c5", "erro"), "inclina", -1.0), (P("c5", "explica"), "olhar", -0.8),
        (P("c5", "corrige"), "aceno", 1.3), (P("c5", "ABNT"), "inclina", 0.9), (P("c5", "quiser"), "aceno", 1.0),
        (P("c5", "desligado"), "queixo", 0.7), (P("c6", "pés"), "baixo", 1.0), (P("c6", "contrário"), "aceno", 1.0),
        (P("c6", "frente"), "queixo", 1.0), (P("c7", "grátis"), "aceno", 1.2), (P("c7", "br"), "olhar", -0.8),
        (P("c7", "fórmula"), "olhar", 1.2), (P("c7", "bonita"), "aceno", 1.2), (P("c7", "bonita"), "chama", 1.0),
    ]
    return {"poses": [{"t": round(t, 3), "pose": p} for t, p in poses],
            "gestos": [{"t": round(t, 3), "tipo": k, "amp": a} for t, k, a in gestos]}


def efeitos(palavras, cenas):
    def P(c, pref, n=0):
        k = 0
        for w in palavras[c]:
            if w["palavra"].strip(".,:?!").lower().startswith(pref.lower()):
                if k == n:
                    return w["ini"]
                k += 1
        raise KeyError(pref)
    e = [(0.1, "fogo_whoosh", 1.0), (0.4, "folhas", .7)]
    for i in range(4):
        e.append((P("c1", "sofre") + i * .16, "pop", .5))
    e += [(P("c2", "ÉguaTeX") - .2, "brilho", .9)]
    e += [(P("c2", p) - .05, "pop", .55) for p in ("editor", "gratuito", "offline", "Amazônia")]
    e += [(cenas["c3"]["inicio"] + .2, "pop", .6), (P("c3", "problema"), "sopro", .8), (P("c3", "rio") - .35, "agua", .6),
          (P("c3", "ônibus") - .3, "onibus", .5), (P("c3", "escreve") - .3, "teclas", .6)]
    tcl = P("c4", "clique") - .05
    e += [(cenas["c4"]["inicio"], "whoosh", .5), (tcl, "clique", 1.0), (tcl + 1.35, "plim", .9), (tcl + 1.5, "pop", .5),
          (P("c4", "LaTeX") - .15, "pop", .5), (P("c4", "LaTeX"), "plim", .4), (P("c4", "instalar"), "plim", .4)]
    e += [(cenas["c5"]["inicio"], "whoosh", .5), (P("c5", "erro"), "erro", .7), (P("c5", "assistente") + .15, "clique", .8),
          (P("c5", "corrige") - .1, "pop", .5), (P("c5", "corrige") + .35, "plim", .6), (P("c5", "ABNT") - .05, "brilho", .5),
          (P("c5", "quiser"), "interruptor", .7), (P("c5", "desligado"), "interruptor", .7)]
    ta, tp = P("c6", "Só"), P("c6", "O") - .05
    e += [(cenas["c6"]["inicio"], "whoosh", .6), (P("c6", "pés"), "whoosh", .4)]
    e += [(ta + (tp - ta) * k / 2 - .02, "passo", .8) for k in (1, 2)]
    e += [(P("c6", "TCC") - .05, "pop", .6), (P("c6", "frente"), "whoosh", .6)]
    e += [(cenas["c7"]["inicio"], "brilho", .7), (P("c7", "Baixa") - .05, "pop", .5), (P("c7", "eguatex"), "teclas", .4),
          (P("c7", "fórmula") - .35, "pop", .5), (P("c7", "bonita"), "brilho", .9)]
    return [{"t": round(t, 3), "nome": n, "vol": v} for t, n, v in e]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("build")
    ap.add_argument("--telas", default=None)
    a = ap.parse_args()
    b = Path(a.build)
    if a.telas and not (b / "telas").exists():
        shutil.copytree(Path(a.telas) / "telas", b / "telas")
    lupa_pdf()
    falas = json.loads((b / "audio/falas.json").read_text(encoding="utf8"))
    palavras = json.loads((b / "audio/palavras.json").read_text(encoding="utf8"))
    cenas = {f["id"]: {"inicio": f["inicio"], "fim": f["fim"], "inicio_fala": f["inicio_fala"]} for f in falas}
    (b / "atuacao.json").write_text(json.dumps(atuacao(palavras, cenas), ensure_ascii=False, indent=1), encoding="utf8")
    telas = {}
    for nome in ["c3_digitando", "c4_compilar", "c5_erro"]:
        pasta = b / "telas" / nome
        mk = json.loads((pasta / "marcas.json").read_text()) if (pasta / "marcas.json").exists() else {}
        telas[nome] = {"n": len(list(pasta.glob("*.png"))), "marcas": mk, **mk}
    dados = {"duracao": falas[-1]["fim"], "cenas": cenas, "palavras": palavras, "telas": telas}
    idx = b / "sprites/indice.json"
    if idx.exists():
        dados["sprites"] = json.loads(idx.read_text())
    (b / "efeitos.json").write_text(json.dumps(efeitos(palavras, cenas), ensure_ascii=False, indent=1), encoding="utf8")
    (b / "dados.json").write_text(json.dumps(dados, ensure_ascii=False), encoding="utf8")
    print("ok", dados["duracao"])


if __name__ == "__main__":
    main()
