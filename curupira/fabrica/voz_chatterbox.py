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
# Pronúncia para o Chatterbox: siglas soletradas com hífen (testado com o Whisper)
PRONUNCIA = [
    (r"\bÉguaTeX\b", "Égua Téc"),
    (r"eguatex ponto com ponto br\.", "égua-téks ponto com ponto bê-érre. ||"),
    (r"\bLaTeX\b", "Látec"),
    (r"\bTCC\b", "tê-cê-cê"),
    (r"\bABNT\b", "a-bê-ene-tê"),
    (r"\bUFPA\b", "u-efe-pê-á"),
    (r"\bPDF\b", "pê-dê-éfe"),
    (r"\bIA\b", "í-á"),
]
SIGLAS = {"TCC": ["tcc", "tc"], "IA": ["ia"], "ABNT": ["abnt", "bnt"], "PDF": ["pdf"], "eguatex": ["eguatex", "eguatexcombr", "eguatex.com.br"]}
PAUSA_PARTES = 0.38

# referência brasileira: o Chatterbox copia a pronúncia (sem ela, o "pt" sai com sotaque que não é o do Brasil)
REFERENCIA = "/home/user/rea-video/curupira/voz/referencia/ref_pm_alex.wav"  # menos "s" chiado (medido)
AJUSTE = {"exaggeration": 0.4, "cfg_weight": 0.6, "temperature": 0.7, "audio_prompt_path": REFERENCIA}
RESPIRO_INI, RESPIRO_FIM = 0.25, 0.4


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
        melhor = None
        wav = out / f"{c['id']}.wav"
        if SO and c["id"] not in SO and wav.exists():
            w, sr0 = ta.load(str(wav))
            if sr0 != m.sr:
                w = ta.functional.resample(w, sr0, m.sr)
            ps = ouvir(asr, w, m.sr)
            antigo = {f["id"]: f for f in json.loads((out / "falas.json").read_text(encoding="utf8"))}.get(c["id"], {})
            melhor = (antigo.get("nota_fala", nota(c["fala"], ps)), w, ps)
        for tentativa in range(0 if melhor else 8):
            torch.manual_seed(100 + tentativa * 17 + len(c["id"]))
            partes = [x.strip() for x in texto.split("||") if x.strip()]
            pedacos = []
            for k, parte in enumerate(partes):
                aj = dict(AJUSTE)
                if parte.endswith("!"):
                    aj["exaggeration"] = 0.6   # exclamação com mais energia
                pedacos.append(aparar(m.generate(parte, language_id="pt", **aj), m.sr))
                if k < len(partes) - 1:
                    pedacos.append(torch.zeros(1, int(PAUSA_PARTES * m.sr)))
            w = torch.cat(pedacos, dim=1)
            ps = ouvir(asr, w, m.sr)
            n = max(nota(c["fala"], ps), nota(texto, ps))
            ouvidas = {norm(x["palavra"]) for x in ps} | {norm("".join(x["palavra"] for x in ps))}
            for sig, formas in SIGLAS.items():
                if re.search(rf"\b{sig}\b", c["fala"]) and not any(any(f in o for o in ouvidas) if len(f) > 3 else f in ouvidas for f in formas):
                    n -= 0.12
            print(c["id"], "tentativa", tentativa, f"nota={n:.2f}", " ".join(x["palavra"] for x in ps), flush=True)
            if melhor is None or n > melhor[0]:
                melhor = (n, w, ps)
            if n >= 0.93:
                break
        n, w, ps = melhor
        ta.save(str(out / f"{c['id']}.wav"), w, m.sr)
        d = w.shape[-1] / m.sr
        dur = RESPIRO_INI + d + RESPIRO_FIM
        palavras[c["id"]] = mapear(c["fala"], [{"palavra": x["palavra"], "ini": t + RESPIRO_INI + x["ini"], "fim": t + RESPIRO_INI + x["fim"]} for x in ps])
        info.append({"id": c["id"], "fala": c["fala"], "tts": texto, "duracao_fala": round(d, 3), "nota_fala": round(n, 3),
                     "inicio": round(t, 3), "fim": round(t + dur, 3), "inicio_fala": round(t + RESPIRO_INI, 3)})
        print(c["id"], f"fala={d:.2f}s cena={t:.2f}-{t + dur:.2f}", flush=True)
        t += dur
    (out / "falas.json").write_text(json.dumps(info, ensure_ascii=False, indent=1), encoding="utf8")
    (out / "palavras.json").write_text(json.dumps(palavras, ensure_ascii=False, indent=1), encoding="utf8")


SO = []
if __name__ == "__main__":
    if len(sys.argv) > 3:
        SO = sys.argv[3].split(",")
    main(Path(sys.argv[1]), Path(sys.argv[2]))
