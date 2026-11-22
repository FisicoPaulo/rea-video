APROVADO

# Revisão do roteiro: vídeo 01, apresentação (versão 3)

Revisor: curupira-revisor-roteiro. Fontes: `curupira/biblia.md`, site `/home/user/eguatex/eguatex.github.io`, app `/home/user/eguatex-app`.

A versão 3 resolve os 2 médios e os leves da segunda revisão. Sem problema crítico ou médio. Ficam só leves, que a edição pode ajustar sem voltar ao roteirista.

## Problemas restantes (todos leves)

| cena | problema | gravidade | correção sugerida |
|---|---|---|---|
| c3 | Entre "ônibus" (~4,3 s, corte para o ônibus) e "jeito" (~6,6 a 7,0 s) passam ~2,5 s sem gesto marcado. Escapou nas revisões anteriores. | leve | Começar a digitar logo depois do corte ou acrescentar um aceno de cabeça em "escreve" (~6,2 s). |
| c4 | O gesto em "PDF" fala do "PDF deslizando para o lado", mas a captura é real e no app o PDF aparece no próprio painel da direita, sem deslizar. | leve | "acompanha com os olhos o PDF aparecendo à direita", ou o deslize fica como efeito de edição sobre a captura. |
| c5 | A nota de 9:16 entrou só na c4; a c5 também mostra a tela do app (log e painel) com o Curupira no canto. | leve | Repetir na c5 a `nota_edicao` da c4 (tela na largura toda, recorte no log e no painel). |
| c7 | O conteúdo da tela do celular não está definido. | leve | Mostrar a página eguatex.com.br em tela cheia, sem barra de sistema (para não identificar sistema operacional). |

## Itens da segunda revisão

| item v2 | situação na v3 |
|---|---|
| c5 rótulo "Pedir para a IA explicar este erro" (médio) | Resolvido. Gesto e captura usam o botão "Explicar" com ícone de brilho, gravado com a IA ligada (`ListaLogs.svelte:204-212`, `pt-BR.json` "log.explicar"). |
| c4 ~3 s sem gesto (médio) | Resolvido. Gesto novo em "PDF" (~2,1 s); intervalos agora ≤ 1,7 s até "ladinho" e ≤ 2,1 s no resto. |
| c7 intervalo e "qual tela" (leve) | Resolvido. Gesto em "eguatex" (~2,0 s); "aponta para o endereço na cartela". |
| c7 `olhar` (leve) | Resolvido. |
| c7 cartela cheia (leve) | Resolvido. O celular sai de quadro em "br" e o PDF fica pequeno, atrás do Curupira. |
| c4 "compilador" para leigo (leve) | Resolvido. "O LaTeX já vem junto, não precisa instalar à parte." Vale no computador (TinyTeX, `primeiros-passos.html`) e no celular ("O LaTeX já vem dentro do app"). |
| c4 tela pequena em 9:16 (leve) | Resolvido com `nota_edicao`; falta repetir na c5 (ver tabela). |

## Conferência geral

- **Verdade:**
  - Botão "Recompilar": `PdfViewer.svelte:1231`.
  - Botão "Explicar" e painel "Assistente IA": `ChatIA.svelte:535`.
  - Sugestão "Verificar a ABNT": `ChatIA.svelte:609`, aparece nos níveis "lê o projeto" e "sugere alterações".
  - IA opcional, desligada, com internet e chave gratuita do Gemini: `assistente-ia.html`; `pt-BR.json` "ia.consentimento.texto".
  - Compila sem internet: `docs/o-que-funciona.md`.
  - Equação e exemplo da pororoca: `index.html:106-118` do site. O exemplo não vem pronto no app; alguém precisa digitá-lo antes da captura.
  - eguatex.com.br: `CNAME`.
- **Clareza:** um leigo entende o que é, o que faz (escreve sem internet, PDF em um clique, LaTeX junto, IA opcional) e onde baixar.
- **Gancho:** "Égua! Tu ainda sofre pra escrever o TCC?" com entrada em chamas prende nos 3 primeiros segundos.
- **Personagem:** travesso, amigo, paraense, sem deboche.
- **Movimento:** gestos presos a palavras, sem repetição seguida; nenhum intervalo passa de ~2,5 s.
- **Marca:**
  - Nenhum travessão (— ou –).
  - Descrição curta, lema e selo exatos.
  - ÉguaTeX escrito certo.
  - Nenhum sistema operacional citado.
- **Produção:** `ia_video` 3,5 s de 47 s (7,4%, limite 20%). Na c1 os pés ficam fora do quadro. A c6 é marionete, então os pés virados para trás ficam garantidos.
- **Português:** sem erro. O registro coloquial ("tu sofre", "pra", "baixa grátis") é intencional, pela bíblia §1.

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
