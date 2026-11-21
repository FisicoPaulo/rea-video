"""Gera a fala do Curupira cena por cena (Kokoro pt-BR + timbre próprio).

Uso: python voz.py <pasta_do_video> <pasta_build>
Saída: <build>/audio/<cena>.wav (24 kHz, já com o timbre) e <build>/audio/falas.json
"""
import json, subprocess, sys, re
from pathlib import Path

import numpy as np
import soundfile as sf
import yaml
from kokoro_onnx import Kokoro

FERR = Path("/home/user/ferramentas")
VOZ_BASE = "pf_dora"
SEMITONS = 3.0          # timbre do Curupira: mais jovem que a voz base
FOLGA_FIM = 0.45        # segundos livres no fim de cada cena

# Pronúncia: o texto da legenda continua o original; a TTS recebe isto.
PRONUNCIA = [
    (r"\bÉguaTeX\b", "Égua Téc"),
    (r"eguatex ponto com ponto br", "égua téc, ponto com, ponto bê érre"),
    (r"\bLaTeX\b", "Látec"),
    (r"\bTCC\b", "tê cê cê"),
    (r"\bABNT\b", "á bê ene tê"),
    (r"\bUFPA\b", "u éfe pê á"),
    (r"\bPDF\b", "pê dê éfe"),
    (r"\bIA\b", "í á"),
    (r"\bCurupira\b", "Curupíra"),
]


def para_tts(texto: str) -> str:
    for a, b in PRONUNCIA:
        texto = re.sub(a, b, texto)
    return texto


def timbre(entrada: Path, saida: Path):
    subprocess.run(["rubberband", "-q", "-p", str(SEMITONS), str(entrada), str(saida)],
                   check=True, capture_output=True)
    # presença, leve compressão e limpeza de cauda
    tmp = saida.with_suffix(".tmp.wav")
    subprocess.run(["sox", str(saida), str(tmp), "highpass", "90", "equalizer", "3500", "1.2q", "3",
                    "compand", "0.02,0.15", "6:-30,-20,-10,-6,0,-3", "-2", "0", "0.05"],
                   check=True, capture_output=True)
    tmp.replace(saida)


def main(pasta_video: Path, build: Path):
    roteiro = yaml.safe_load((pasta_video / "roteiro.yaml").read_text(encoding="utf8"))
    k = Kokoro(str(FERR / "kokoro-v1.0.onnx"), str(FERR / "voices-v1.0.bin"))
    out = build / "audio"
    out.mkdir(parents=True, exist_ok=True)
    info = []
    for c in roteiro["cenas"]:
        dur_cena = c["fim"] - c["inicio"]
        alvo = dur_cena - FOLGA_FIM - 0.25  # 0,25 s de respiro antes da fala
        texto = para_tts(c["fala"])
        vel = 0.95
        for _ in range(6):
            a, sr = k.create(texto, voice=VOZ_BASE, speed=vel, lang="pt-br")
            # corta silêncio das pontas
            idx = np.where(np.abs(a) > 0.01)[0]
            a = a[max(idx[0] - int(0.03 * sr), 0): idx[-1] + int(0.08 * sr)]
            if len(a) / sr <= alvo:
                break
            vel = round(vel * (len(a) / sr) / alvo * 1.02, 3)
        bruto = out / f"{c['id']}_bruto.wav"
        sf.write(bruto, a, sr)
        final = out / f"{c['id']}.wav"
        timbre(bruto, final)
        bruto.unlink()
        d = sf.info(final).duration
        info.append({"id": c["id"], "fala": c["fala"], "tts": texto, "velocidade": vel,
                     "duracao_fala": round(d, 3), "duracao_cena": dur_cena,
                     "inicio_fala": round(c["inicio"] + 0.25, 3)})
        print(c["id"], f"vel={vel}", f"fala={d:.2f}s", f"cena={dur_cena:.2f}s")
    (out / "falas.json").write_text(json.dumps(info, ensure_ascii=False, indent=1), encoding="utf8")


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
