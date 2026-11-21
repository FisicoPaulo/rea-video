# Fábrica de vídeos do Curupira

Vídeos em que o Curupira, mascote do ÉguaTeX, explica as funcionalidades do app.
Estrutura aprovada pelo Paulo em 21/11/2026.

## Fluxo

```
 [1] Roteirista ──► [2] Revisor de roteiro ──► (Paulo aprova o roteiro)
                          ▲  │ reprova
                          └──┘
 [3] Construtor ──► [4] Caçador de defeitos (cena por cena) ──┐
      ▲                                                       │ achou defeito
      └────────────── defeitos_vN.json ◄──────────────────────┘
                                   │ zero defeito crítico
                                   ▼
                      [5] Avaliador final (nota 0 a 10)
                       nota < 9 → volta ao [3] (ou ao [1] se o problema for o roteiro)
                       nota ≥ 9 → (Paulo assiste e aprova o final.mp4)
```

- Cada papel é um agente em `.claude/agents/curupira-*.md`, com contexto próprio.
- O caçador e o avaliador **não leem** as justificativas do construtor: só o vídeo, o roteiro aprovado e a bíblia.
- Limite de **4 voltas** construtor ↔ avaliador. Sem nota 9 na quarta, para e leva ao Paulo.
- Regras do personagem, da marca e do movimento: `biblia.md`.

## Pastas

```
curupira/
  biblia.md                 regras do personagem (todos leem)
  arte/                     referências e camadas recortadas (FORA DO GIT)
  voz/                      voz de referência e modelo (FORA DO GIT)
  videos/<NN-tema>/
    roteiro.yaml            [1] escreve, [2] revisa
    revisao_roteiro.md      [2]
    build_vN/               [3] (FORA DO GIT) cenas, áudio, render
    defeitos_vN.json        [4]
    avaliacao_vN.json       [5]
    final.mp4               aprovado (FORA DO GIT)
```

**Por que a arte fica fora do git:** este repositório (`FisicoPaulo/rea-video`) é público, e o nome e o desenho do Curupira
são marca registrada do ÉguaTeX (ver MARCA.md do site). Arte, voz e vídeos devem ir para um repositório privado
ou para o Google Drive.

## Técnica de produção (híbrida)

- **Cenas explicativas (maior parte):** Curupira recortado em camadas e animado como marionete 2D (estilo Live2D),
  boca pelo Rhubarb Lip Sync a partir da voz, montagem e telas do app no Remotion. Consistência total do personagem.
- **Cenas de impacto (abertura, transições):** vídeo por IA a partir das referências (Wan 2.2, InfiniteTalk),
  com o caçador em modo rigoroso para pés e mãos.
- **Voz:** timbre único criado (dublador ou voice design no VoxCPM) e clonado em Chatterbox ou GPT-SoVITS.

## Ferramentas do caçador

- Divisão em planos e revisão por VLM: `rea-video decompose` deste repositório.
- Quadros: `ffmpeg -i in.mp4 -vf fps=8 frames/%05d.png` por cena; olhar sequências, não quadros soltos.
- Congelamento: `ffmpeg -vf freezedetect=n=0.003:d=1.5`.
- Saltos de pose: diferença entre quadros vizinhos (pico isolado = salto).
- Fala: transcrever com Whisper e comparar com o roteiro e a legenda; medir o atraso boca ↔ áudio.

Os agentes "assistem" por quadros e áudio transcrito, não em tempo real. O olho do Paulo no fim é a última palavra.
