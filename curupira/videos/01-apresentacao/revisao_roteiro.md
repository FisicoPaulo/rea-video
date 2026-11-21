DEVOLVER

# Revisão do roteiro: vídeo 01, apresentação (versão 2)

Revisor: curupira-revisor-roteiro. Fontes: `curupira/biblia.md`, site `/home/user/eguatex/eguatex.github.io`, app `/home/user/eguatex-app`.

A versão 2 resolveu os 4 médios e 5 dos 6 leves da versão 1. Sem problema crítico. Ficaram 2 médios novos, criados pelas próprias correções: o rótulo do botão de explicar erro na c5 e um buraco de 3 s sem gesto na c4. As duas correções são pequenas.

## Problemas

| cena | problema | gravidade | correção sugerida |
|---|---|---|---|
| c5 | O botão do log tem o rótulo **"Explicar"** (ícone de brilho) (`src/lib/components/ListaLogs.svelte:212`, `pt-BR.json` "log.explicar"). "Pedir para a IA explicar este erro" é só a dica de passar o mouse (`title`, `ListaLogs.svelte:208`, "log.explicar-dica"). O botão só aparece com a IA ligada (`{#if iaAtiva}`). O gesto "toca a dica 'Pedir para a IA explicar este erro'" e a captura (1) mostrariam um texto que não fica visível na tela. É o mesmo tipo de problema do "Compilar" da v1. | médio | Gesto: "toca o botão Explicar ao lado do erro". Captura (1): "erro no log com o botão Explicar" (se quiser a frase longa, gravar com o mouse parado em cima para a dica aparecer). Capturar com a IA já ligada. |
| c4 | Com a fala nova, os gestos caem em "clique" (~0,8 s) e "ladinho" (~3,8 s): cerca de 3 s sem gesto novo, acima da regra de um gesto a cada 2 s. | médio | Acrescentar um gesto em "PDF" (~2,1 s), por exemplo abre a mão em leque quando o PDF surge, ou aceno de cabeça com o "plim". |
| c7 | Intervalo de ~2,5 s entre "grátis" (~1,0 s) e "br" (~3,5 s). "Aponta para o endereço na tela" não diz qual tela (a do celular ou a cartela). | leve | Olhar para o celular em "eguatex"; dizer "aponta para o endereço na cartela" (ou na tela do celular). |
| c7 | O campo `olhar` diz só "câmera", mas em "fórmula" ele vira para o PDF. | leve | `olhar: "câmera, celular, PDF da equação, câmera"`. |
| c7 | Cartela cheia em 9:16: logo, lema, selo, endereço, PDF com a equação, Curupira em plano médio e celular na mão. | leve | Deixar o celular sair de quadro depois de "br" e posicionar o PDF atrás do Curupira, menor, com a equação legível. |
| c4 | "compilador" pode não dizer nada a quem nunca usou LaTeX. Mas a fala anterior ("Um clique, e o PDF aparece") já explica o efeito, então dá para entender. | leve | Opcional: "O LaTeX já vem junto, não precisa instalar nada à parte." |

## Itens da revisão anterior

| item v1 | situação na v2 |
|---|---|
| c4 botão "Compilar" (médio) | Resolvido. Fala "Um clique, e o PDF aparece aqui do ladinho."; gesto cita o rótulo real Recompilar (`PdfViewer.svelte:1231`). |
| c5 "Verificar a ABNT" ao mesmo tempo que a explicação (médio) | Resolvido. Captura (3) é uma conversa nova vazia com as sugestões; o gesto chama de "sugestão pronta" (`ChatIA.svelte:596-610`). Lembrete: a sugestão só aparece nos níveis "lê o projeto" e "sugere alterações". |
| c7 "que fórmula bonita" sem fórmula (médio) | Resolvido. PDF da pororoca com a equação ao lado da cartela e gesto em "fórmula". A equação F = G M_T M_L / d² é a mesma do exemplo do site (`index.html:106-118`, "A pororoca do Guamá", "lei de Newton"), coerente com a c3 e a c4. |
| c6 só 3 gestos (médio) | Resolvido. 5 gestos ("pés", "trás", "contrário", "TCC", "frente"), intervalos ≤ 2 s. |
| c4/c5/c7 intervalos de 2,5 a 2,8 s (leve) | c5 resolvido (7 gestos); a fala da c7 termina em 46,5 s, então o fim está resolvido. Sobra o intervalo de 2,5 s na c7, e a c4 piorou com a fala nova (ver tabela). |
| c5 IA precisa de internet (leve) | Resolvido no `texto_na_tela`. |
| c5 título "Assistente IA" (leve) | Resolvido: "Não redesenhar o título do painel". |
| c4 "LaTeX" repetido (leve) | Resolvido ("O compilador já vem junto"). |
| c4/c5 tela pequena em 9:16 (leve) | Não tratado; continua como nota de produção para a edição (recorte ou zoom). |
| c1 pés na entrada em `ia_video` (leve) | Resolvido: quadro corta acima dos joelhos. |

## Verdade (afirmações da v2)

- "O compilador já vem junto, não precisa instalar à parte": vale no computador (TinyTeX, `primeiros-passos.html`, `README.md` do app) e no celular ("O LaTeX já vem dentro do app", `primeiros-passos.html`). Ressalva: pacotes fora da distribuição embutida são baixados com internet ("faltando.pergunta").
- Assistente explica, corrige e confere a ABNT, vem desligado, usa internet e chave gratuita do Gemini: `assistente-ia.html`; `pt-BR.json` "ia.consentimento.texto", "ia.config.explicacao", "chat.sugestao.abnt".
- "eguatex ponto com ponto br": certo (`CNAME` = eguatex.com.br).
- O exemplo "A pororoca do Guamá" é do site, não vem pronto no app: para a "captura real" alguém digita esse texto no app. É viável, só precisa ficar combinado com a produção.

## Demais itens

- **Gancho:** igual à v1, prende.
- **Personagem:** travesso, amigo, paraense, sem deboche. O TCC encadernado com a capa da pororoca e o celular saindo do colar de folhas são adereços, não roupa, então não quebram a regra de roupa da bíblia.
- **Marca:** nenhum travessão (— ou –); textos oficiais exatos; ÉguaTeX certo; nenhum sistema citado (o celular aparece sem nome de sistema).
- **Produção:** `ia_video` 3,5 s de 47 s (7,4%). A c5 tem 3 capturas e 7 gestos em 9 s: dá para fazer, mas está no limite.
- **Português:** sem erro. "não precisa instalar à parte" sem objeto é elipse aceitável na fala.

## Palavras por segundo (contagem do revisor)

| cena | palavras | duração (s) | palavras/s | no roteiro | resultado |
|---|---|---|---|---|---|
| c1 | 8 | 3,5 | 2,29 | 2,3 | ok |
| c2 | 17 | 6,5 | 2,62 | 2,6 | ok |
| c3 | 18 | 7,0 | 2,57 | 2,6 | ok |
| c4 | 19 | 8,0 | 2,38 | 2,4 | ok |
| c5 | 21 | 9,0 | 2,33 | 2,3 | ok |
| c6 | 17 | 7,0 | 2,43 | 2,4 | ok |
| c7 | 12 | 6,0 (fala até 46,5: 5,5) | 2,00 (2,18 na fala) | 2,0 | ok |

Total 47,0 s. Nenhuma cena passa de 3 palavras/s.
