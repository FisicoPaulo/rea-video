# Bíblia do Curupira (mascote do ÉguaTeX)

Regras fixas. Todo agente da fábrica de vídeos lê este arquivo antes de trabalhar.
Quebrar uma regra marcada com **[CRÍTICO]** reprova o vídeo direto, qualquer que seja a nota.

## 1. Quem ele é

- Protetor da floresta da lenda amazônica, agora mascote do **ÉguaTeX**, editor LaTeX gratuito e offline, feito na Amazônia.
- Na lenda tem o cabelo de fogo e os pés virados para trás, e quem segue as pegadas dele anda na direção errada.
  O ÉguaTeX usa essa teimosia: "aqui a ideia anda ao contrário", ou seja, LaTeX no computador de casa, sem internet, na beira do rio e no ônibus para a UFPA.
- Personalidade: travesso, confiante, simpático, um pouco exibido. Fala com o público como um amigo paraense ("tu", "égua", "pai d'égua").
  Nunca é arrogante nem debochado com quem não sabe LaTeX: ele ajuda.

## 2. Aparência

Referências em `curupira/arte/referencias/` (fora do git, ver README).

| Parte | Regra |
|---|---|
| Cabelo **[CRÍTICO]** | Chamas em degradê vermelho → laranja → amarelo nas pontas, volumoso e espetado. Sempre em movimento (tremula). |
| Rosto | Olhos castanhos grandes, sobrancelhas grossas e expressivas, orelhas pontudas. Sorriso de canto quando confiante. |
| Pele | Morena alaranjada, uniforme. Não pode mudar de tom entre planos. |
| Roupa | Colar de folhas verdes, saia de folhas, pulseiras e tornozeleiras de folhas. Nada mais (sem camisa, sem sapato). |
| Mãos **[CRÍTICO]** | 5 dedos em cada mão, proporção de criança/adolescente. |
| Pés **[CRÍTICO]** | **Virados para trás**: calcanhar para a frente, dedos para trás, em toda vista. As vistas de frente e de lado de `turnaround-PES-ERRADOS.jpg` estão erradas (pés para a frente) e não servem de referência para os pés. |
| Proporção | Corpo de criança de uns 10 a 12 anos, cabeça grande, estilo anime 2D com contorno fino e cor chapada com sombra suave. |

## 3. Paleta (do site eguatex.com.br)

| Nome | Cor | Uso |
|---|---|---|
| noite | `#1c0a2b` | fundo principal |
| roxo | `#7a35c4` | destaques, molduras |
| roxo-claro | `#c9a6f0` | textos secundários |
| fogo | `#ff5f15` | chamada, botões |
| brasa | `#e0243e` | ênfase |
| chama | `#ffb627` | brilho, palavras-chave na legenda |
| verde | `#3f9a37` | folhas, sucesso |
| texto | `#f3eafb` | legenda |

Detalhe gráfico da marca: `faixa-marajoara.svg`.

## 4. Expressões e gestos de referência

De `expressoes.jpg`: (1) oferecendo com a mão aberta e sorriso, (2) piscadela com aceno, (3) apontando sério para a câmera,
(4) sorriso calmo de canto, (5) surpresa com a mão aberta. Use como poses-chave; o movimento entre elas é o que dá vida.

## 5. Voz (a definir na etapa de voz)

- Fala normal: português do Brasil neutro, sem sotaque (pedido do Paulo em 22/11/2026). Voz suave e humana, nunca robótica (pedido do Paulo em 21/11/2026).
- Voz atual: Chatterbox multilíngue com a referência brasileira `curupira/voz/referencia/ref_pf_dora.wav` (fora do git).
- Ritmo: rápido nas piadas, mais lento e claro quando explica um passo.
- Uma voz única do ÉguaTeX: nunca clonar a voz de pessoa famosa ou de dublador sem contrato.
- Pronúncia de **ÉguaTeX**: a confirmar com o Paulo e a Jéssica (proposta: "É-gua-tec", como LaTeX dito "lá-tec"). Vale para todos os vídeos.

## 6. Movimento: ele nunca fica duro

1. Respiração contínua (ombros e peito sobem e descem, ciclo de 3 a 4 s).
2. Piscadas a cada 2 a 5 s, intervalo aleatório, às vezes piscada dupla.
3. Chamas do cabelo tremulam o tempo todo; folhas balançam com atraso em relação ao corpo (movimento secundário).
4. Antecipação antes de gesto grande e assentamento depois (pequeno rebote).
5. Acelera e desacelera, nunca movimento linear.
6. Cabeça inclina ou acena nas sílabas tônicas; olhar alterna entre câmera e a tela do app.
7. Peso: quando muda de pose, o quadril vai antes, o tronco depois, a cabeça por último.
8. Nunca o mesmo gesto duas vezes seguidas; nunca mais de 1,5 s totalmente parado.

## 7. Regras de texto (de IDENTIDADE.md do ÉguaTeX)

- Nome: **ÉguaTeX** (X maiúsculo). Curupira com inicial maiúscula.
- Lema: "Escreva LaTeX de qualquer lugar, mesmo sem internet."
- Descrição curta: "Editor LaTeX gratuito e offline, feito na Amazônia."
- Selo: "Feito na Amazônia" (capas e peças visuais, junto com o lema, sem a descrição curta).
- Sempre "feito na Amazônia", nunca "criado na Amazônia". "editor LaTeX", sem "de".
- Textos de apresentação não citam sistema (Windows, Android, Linux).
- **Nenhum texto usa travessão.**
- Site: eguatex.com.br. Instagram: @eguatex.

## 8. O que o ÉguaTeX faz (fonte: site e repositório do app)

- Escreve e compila LaTeX **sem internet**; o compilador já vem junto (não precisa instalar LaTeX à parte).
- PDF ao lado do texto, um clique em **Compilar**.
- Abas, vários arquivos por projeto, documento principal escolhido por projeto, temas claro e escuro.
- **Templates** prontos (TCC, artigos, relatórios).
- **Assistente de IA opcional** (vem desligado; chave gratuita do Gemini): tira dúvidas de LaTeX, explica e corrige erros de compilação,
  revisa o texto, ajuda com tabelas, fórmulas e figuras, confere a ABNT. Três níveis: só conversa, lê o projeto, sugere alterações aceitas uma por uma.
- Integração com o Google Drive.
- Gratuito, sem conta nem cadastro para instalar.
