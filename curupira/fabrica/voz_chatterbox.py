"""Voz suave do Curupira com Chatterbox multilíngue (pt), cena por cena.

Uso: /home/user/venv-chatter/bin/python voz_chatterbox.py <pasta_video> <pasta_build>
O tempo das cenas sai do áudio: cada cena dura a fala + respiros, nunca menos que no roteiro.
Saída: <build>/audio/<cena>.wav e falas.json (com inicio/fim da cena e inicio_fala).
"""
import json, re, sys
from pathlib import Path

import torch, torchaudio as ta
import yaml
from chatterbox.mtl_tts import ChatterboxMultilingualTTS
from difflib import SequenceMatcher
import unicodedata
import numpy as np
from faster_whisper import WhisperModel

sys.path.insert(0, str(Path(__file__).parent))
from voz import PRONUNCIA  # noqa: E402

AJUSTE = {"exaggeration": 0.35, "cfg_weight": 0.35, "temperature": 0.7}
RESPIRO_INI, RESPIRO_FIM = 0.25, 0.45


def para_tts(t):
    for a, b in PRONUNCIA:
        t = re.sub(a, b, t)
    return t


def aparar(w, sr, lim=0.008):
    x = w[0]
    idx = (x.abs() > lim).nonzero()
    if len(idx) == 0:
        return w
    a, b = int(idx[0]), int(idx[-1])
    return w[:, max(a - int(0.03 * sr), 0): b + int(0.1 * sr)]


def norm(w):
    w = unicodedata.normalize("NFD", w.lower())
    return re.sub(r"[^a-z0-9]", "", "".join(c for c in w if unicodedata.category(c) != "Mn"))


def ouvir(asr, w, sr):
    """Transcreve (16 kHz) e devolve palavras com tempos."""
    import torchaudio.functional as F
    y = F.resample(w, sr, 16000)[0].numpy().astype(np.float32)
    segs, _ = asr.transcribe(y, language="pt", word_timestamps=True)
    return [{"palavra": x.word.strip(), "ini": x.start, "fim": x.end} for s in segs for x in s.words]


def nota(texto, palavras):
    a = [norm(x) for x in texto.split() if norm(x)]
    b = [norm(x["palavra"]) for x in palavras if norm(x["palavra"])]
    return SequenceMatcher(None, "".join(a), "".join(b)).ratio()


def main(pasta_video: Path, build: Path):
    torch.set_num_threads(4)
    torch.manual_seed(7)
    rot = yaml.safe_load((pasta_video / "roteiro.yaml").read_text(encoding="utf8"))
    m = ChatterboxMultilingualTTS.from_pretrained(device="cpu")
    asr = WhisperModel("small", device="cpu", compute_type="int8")
    sys.path.insert(0, str(Path(__file__).parent))
    from tempos import mapear
    out = build / "audio"; out.mkdir(parents=True, exist_ok=True)
    info, t, palavras = [], 0.0, {}
    for c in rot["cenas"]:
        texto = para_tts(c["fala"])
        # referência para a nota: a fala original e a versão falada (o Whisper escreve "TCC", não "tê cê cê")
        melhor = None
        for tentativa in range(4):
            torch.manual_seed(100 + tentativa * 17 + len(c["id"]))
            w = aparar(m.generate(texto, language_id="pt", **AJUSTE), m.sr)
            ps = ouvir(asr, w, m.sr)
            n = max(nota(c["fala"], ps), nota(texto, ps))
            print(c["id"], "tentativa", tentativa, f"nota={n:.2f}", " ".join(x["palavra"] for x in ps), flush=True)
            if melhor is None or n > melhor[0]:
                melhor = (n, w, ps)
            if n >= 0.9:
                break
        n, w, ps = melhor
        ta.save(str(out / f"{c['id']}.wav"), w, m.sr)
        d = w.shape[-1] / m.sr
        dur = max(c["fim"] - c["inicio"], RESPIRO_INI + d + RESPIRO_FIM)
        palavras[c["id"]] = mapear(c["fala"], [{"palavra": x["palavra"], "ini": t + RESPIRO_INI + x["ini"], "fim": t + RESPIRO_INI + x["fim"]} for x in ps])
        info.append({"id": c["id"], "fala": c["fala"], "tts": texto, "duracao_fala": round(d, 3), "nota_fala": round(n, 3),
                     "inicio": round(t, 3), "fim": round(t + dur, 3), "inicio_fala": round(t + RESPIRO_INI, 3)})
        print(c["id"], f"fala={d:.2f}s cena={t:.2f}-{t + dur:.2f}", flush=True)
        t += dur
    (out / "falas.json").write_text(json.dumps(info, ensure_ascii=False, indent=1), encoding="utf8")
    (out / "palavras.json").write_text(json.dumps(palavras, ensure_ascii=False, indent=1), encoding="utf8")


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
