DEVOLVER

# Revisão do roteiro: vídeo 01, apresentação (versão 1)

Revisor: curupira-revisor-roteiro. Fontes: `curupira/biblia.md`, site `/home/user/eguatex/eguatex.github.io`, app `/home/user/eguatex-app`.

Sem problema crítico. Há 4 problemas médios (dois de verdade na tela do app, um de clareza no fechamento e um de movimento), por isso volta.

## Problemas

| cena | problema | gravidade | correção sugerida |
|---|---|---|---|
| c4 | O botão visível na barra do PDF se chama **Recompilar**, não "Compilar" (`src/lib/components/PdfViewer.svelte:1231`, `dados/i18n/pt-BR.json` "compilar.recompilar"). "Compilar" existe só como item de menu e da paleta de comandos, com Ctrl+Enter (`src/lib/comandos.ts:36`, "menu.compilar"). O site e a ajuda do app dizem "clique em Compilar", mas o gesto "toca o botão Compilar" e a tela do app mostrariam um botão que não existe com esse nome. | médio | Trocar a fala por "Um clique, e o PDF aparece aqui do ladinho." e o gesto por "toca o botão verde de compilar". Se quiser manter a palavra, mostrar na tela o menu com "Compilar" e o atalho Ctrl+Enter. Avisar o Paulo da divergência entre site/ajuda ("Compilar") e o rótulo do botão ("Recompilar"); a bíblia §8 repete "um clique em Compilar". |
| c5 | "Verificar a ABNT" existe, mas é uma **sugestão pronta** (chip) do painel, não um botão (`dados/i18n/pt-BR.json` "chat.sugestao.abnt"; `src/lib/components/ChatIA.svelte:609`). Ela só aparece com a conversa vazia e com o nível "lê o projeto" ou "sugere alterações" (no nível "só conversa" aparece "Como configurar ABNT com abnTeX2?"). A `tela_app` mostra o chip ao mesmo tempo que o assistente explica um erro, o que o app não faz. | médio | Dividir a tela: primeiro o painel vazio com as sugestões ("Corrigir...", "Revisar...", "Verificar a ABNT"), depois o erro e a explicação. Escrever "sugestão Verificar a ABNT" no roteiro, não "botão". |
| c7 | "Égua, que fórmula bonita!" fecha o vídeo sem nenhuma fórmula na tela (a cartela final só tem logo, lema, selo e endereço; a fórmula apareceu na c4, 16 s antes). Quem nunca viu o app não entende a piada da última frase. | médio | Pôr o PDF da pororoca com a equação de Newton ao lado da cartela e o Curupira olhando para ela em "bonita", ou trocar a frase por algo ligado à cena, por exemplo "Égua, bora escrever!" ou "Te vejo lá, pai d'égua!". |
| c6 | Só 3 gestos em 7 s: "pés" (~1,2 s), "contrário" (~4,5 s), "frente" (~7 s). Intervalo de ~3,3 s sem gesto novo entre "pés" e "contrário", acima da regra de um gesto a cada 2 s. | médio | Acrescentar um gesto em "trás" (levanta um pé e mostra o calcanhar para a frente, sorriso travesso) e outro em "TCC" (aponta para a câmera de leve) antes de "frente". |
| c4, c5, c7 | Intervalos de 2,5 a 2,8 s entre gestos (c4: "Compilar"→"ladinho"; c5: "explica"→"ABNT"; c7: "grátis"→"br" e "br"→"bonita"). Na c7 o gesto de "bonita" cai no último quadro da cena e pode ser cortado. | leve | c4: aceno de cabeça em "PDF". c5: inclina a cabeça em "corrige". c7: olhar para o endereço em "ponto com" e terminar a fala 0,5 s antes do fim para o aceno respirar. |
| c5 | O assistente usa a Gemini API e precisa de internet e de uma chave gratuita do Gemini (`dados/i18n/pt-BR.json` "ia.consentimento.texto", "ia.config.explicacao"). A cena vem logo depois de "Sem internet? Sem problema." e pode passar a ideia de que a IA também funciona offline. A fala não afirma isso, então não é falsa. | leve | No `texto_na_tela`: "Assistente de IA opcional" e, menor, "usa internet e chave gratuita do Gemini". |
| c5 | O título do painel no app é "Assistente IA" (`dados/i18n/pt-BR.json` "chat.titulo"; `ChatIA.svelte:535`), e o roteiro descreve "painel do Assistente de IA". Na fala e na legenda "assistente de IA" está certo (o site usa assim). | leve | Na captura, deixar o título real do painel; não redesenhar o painel com "Assistente de IA". |
| c4 | "instalar LaTeX à parte" repete "LaTeX" da frase anterior. | leve | "O LaTeX já vem junto, não precisa instalar nada à parte." |
| c4, c5 | Tela de computador com texto à esquerda e PDF à direita dentro de 9:16 fica pequena. | leve | Recortar a captura (só o trecho do editor e do PDF que importa) ou usar zoom animado. |
| c1 | A entrada em `ia_video` com "aterrissa" pode mostrar os pés, e a bíblia marca os pés virados para trás como **[CRÍTICO]**; IA de vídeo costuma errar isso. | leve | Manter os pés fora do quadro na entrada (plano médio desde o primeiro quadro) ou fazer a aterrissagem em `marionete_2d`. |

## Verificações pedidas

- **Botão "Compilar":** não existe com esse rótulo na barra. O botão principal diz "Recompilar" (e "Compilando..." enquanto roda). "Compilar" é item de menu e da paleta de comandos (Ctrl+Enter). O site (`index.html`, `primeiros-passos.html`) e a ajuda do app (`src/lib/components/ComoUsarModal.svelte:33`) dizem "clique em Compilar". Ver tabela, c4.
- **"Verificar a ABNT":** existe como sugestão pronta no painel do assistente (app: `ChatIA.svelte:609`; site: `assistente-ia.html`, chips "Revisar o trecho selecionado" e "Verificar a ABNT"). Não é botão fixo. Ver tabela, c5.
- **Painel de Assistente de IA:** existe (`src/lib/components/ChatIA.svelte`, título "Assistente IA"). Vem desligado e usa chave do Gemini (`assistente-ia.html`: "Ele é opcional e vem desligado"). Explicar erro: dica "Pedir para a IA explicar este erro" no log (`pt-BR.json` "log.explicar-dica"). Corrigir: nível de sugestões aceitas uma por uma (`assistente-ia.html`).
- **"Não precisa instalar LaTeX à parte":** vale de forma geral. Computador: "Não precisa ser administrador nem instalar o LaTeX à parte: o TinyTeX já vem junto" (`primeiros-passos.html`; `README.md` e `DEPENDENCIAS.md` do app, TinyTeX embutido com 2.920 pacotes). Celular: "O LaTeX já vem dentro do app" (`primeiros-passos.html`; `termos.html`: "TinyTeX no computador e TeX Live no celular"). Ressalvas que não invalidam a frase: pacote fora da distribuição embutida é baixado do TeX Live com internet (`pt-BR.json` "faltando.pergunta", "log.baixar-pacote-dica"), e o site prevê o aviso raro "Nenhum compilador LaTeX foi encontrado" no computador.
- **"eguatex ponto com ponto br":** certo. `CNAME` do site = `eguatex.com.br`; links canônicos `https://eguatex.com.br/...`; bíblia §7.
- **Travessão:** nenhum travessão (— ou –) no roteiro, nas falas nem nos textos na tela.

## Demais itens

- **Verdade (outras afirmações):** gratuito e offline, feito na Amazônia (`pt-BR.json` "app.descricao"; `index.html`); escrever e compilar sem internet (`docs/o-que-funciona.md`, linha "Compila e mostra o PDF sem internet"; `privacidade.html`); PDF ao lado, à direita (`ComoUsarModal.svelte:33`; `index.html`); assistente explica, corrige, confere a ABNT, vem desligado (`assistente-ia.html`, `index.html`).
- **Clareza:** boa nas c1 a c6; o fechamento da c7 falha (ver tabela).
- **Gancho:** "Égua! Tu ainda sofre pra escrever o TCC?" com entrada em chamas prende nos 3 primeiros segundos.
- **Personagem:** travesso, amigo e paraense ("égua", "tu", "ladinho", piada dos pés), sem deboche.
- **Marca:** descrição curta, lema e selo exatos; ÉguaTeX escrito certo em todos os campos; nenhum sistema operacional citado; "feito na Amazônia", "editor LaTeX" sem "de".
- **Produção:** `ia_video` 3,5 s de 47 s (7,4%), dentro do limite de 20%. Técnicas viáveis.
- **Português:** sem erro. "Tu sofre", "tu escreve", "pra", "baixa grátis" são registro coloquial paraense intencional (bíblia §1).

## Palavras por segundo (contagem do revisor)

| cena | palavras | duração (s) | palavras/s | no roteiro | resultado |
|---|---|---|---|---|---|
| c1 | 8 | 3,5 | 2,29 | 2,3 | ok |
| c2 | 17 | 6,5 | 2,62 | 2,6 | ok |
| c3 | 18 | 7,0 | 2,57 | 2,6 | ok |
| c4 | 21 | 8,0 | 2,63 | 2,6 | ok |
| c5 | 21 | 9,0 | 2,33 | 2,3 | ok |
| c6 | 17 | 7,0 | 2,43 | 2,4 | ok |
| c7 | 12 | 6,0 | 2,00 | 2,0 | ok |

Total 47,0 s. Nenhuma cena passa de 3 palavras/s. Atenção: siglas soletradas (TCC, UFPA, PDF, ABNT) e "ponto com ponto br" alongam a fala; c2 e c4 são as mais apertadas.
