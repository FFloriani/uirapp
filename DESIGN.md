---
version: alpha
name: Uirapp
description: Design system 0.1 da extensão Uirapp, que deixa o WhatsApp Web mais privado e mais seu.
colors:
  primary: "#17627A"          # ação, seleção, ligado e foco no tema claro
  primary-hover: "#104D61"    # ação com o mouse em cima ou pressionada
  on-primary: "#FFFFFF"       # texto sobre ação
  bg: "#F4F7F8"               # fundo, neblina da manhã
  surface: "#FFFFFF"          # campo, diálogo e opção
  surface-hover: "#E4ECEF"    # linha com o mouse em cima e trilho neutro
  text: "#1E1E24"             # texto principal, o carvão do pássaro
  text-muted: "#55616A"       # texto de apoio e valor da linha
  line: "#D5DEE2"             # divisão, sem função de controle
  control: "#72828B"          # borda de campo e trilho desligado
  danger: "#A1173C"           # só erro e apagar, sempre com palavra
  on-danger: "#FFFFFF"        # texto sobre perigo
  warning: "#F7D9A0"          # aviso de que a proteção mudou
  on-warning: "#1E1E24"       # texto sobre aviso
  noite-primary: "#8FCFE0"    # ação, seleção, ligado e foco no tema escuro
  noite-primary-hover: "#B4E1EC" # ação com o mouse em cima, escuro
  noite-on-primary: "#0E2631" # texto sobre ação, escuro
  noite-bg: "#18242E"         # fundo, depois do pôr do sol
  noite-surface: "#21313D"    # campo, diálogo e opção, escuro
  noite-surface-hover: "#2B3E4B" # linha com o mouse em cima, escuro
  noite-text: "#EEF4F6"       # texto principal, escuro
  noite-text-muted: "#A9BAC4" # texto de apoio, escuro
  noite-line: "#344955"       # divisão, escuro
  noite-control: "#7F95A1"    # borda de campo e trilho desligado, escuro
  noite-danger: "#FF9DB3"     # erro e apagar, escuro
  noite-on-danger: "#3D0718"  # texto sobre perigo, escuro
  ceu-aberto: "#BCDDE8"       # palco com as conversas à vista, o amanhecer
  on-ceu-aberto: "#1E1E24"    # texto no amanhecer
  ceu-silencio: "#58758C"     # palco com as conversas escondidas, o anoitecer
  on-ceu-silencio: "#FFFFFF"  # texto no anoitecer
  ceu-alerta: "#F7D9A0"       # palco quando a proteção mudou
  ceu-neblina: "#C5CBCE"      # palco quando o WhatsApp Web está fechado
  galho: "#75523F"            # o galho onde o pássaro pousa
  folha: "#3E7183"            # as folhas do galho
  tarja: "#AFC0C8"            # cobre texto escondido, sempre opaca
  noite-tarja: "#47606F"      # tarja opaca no escuro
  escarlate: "#E63323"        # marca e mascote, nunca ação nem erro
  carvao: "#1E1E24"           # marca e mascote
  bico: "#FF8A3D"             # bico do mascote
  creme: "#FFF3E8"            # só o quadrado do ícone
  plumagem-laranja: "#F47A20" # cabeça do uirapuru-laranja
  plumagem-laranja-bico: "#FFD166" # bico da plumagem laranja
  plumagem-lenda: "#B5562B"   # cabeça do uirapuru-verdadeiro
  plumagem-lenda-corpo: "#4A332C" # corpo do uirapuru-verdadeiro
  plumagem-lenda-bico: "#E0A06A" # bico da plumagem da lenda
typography:
  display: { fontFamily: Sofia Sans, fontSize: 28px, fontWeight: 800, lineHeight: 1.05 }   # o estado no palco, um por tela
  title: { fontFamily: Sofia Sans, fontSize: 20px, fontWeight: 750, lineHeight: 1.2 }      # título da tela
  label: { fontFamily: Sofia Sans, fontSize: 16px, fontWeight: 650, lineHeight: 1.25 }     # linha, botão e rótulo
  body: { fontFamily: Sofia Sans, fontSize: 15px, fontWeight: 430, lineHeight: 1.4 }       # texto e campo
  small: { fontFamily: Sofia Sans, fontSize: 13px, fontWeight: 520, lineHeight: 1.35 }     # valor, atalho e erro
spacing:
  "1": 4px     # entre rótulo e apoio
  "2": 8px     # entre itens do mesmo grupo
  "3": 12px    # dentro de linha e campo
  "4": 16px    # margem da tela
  "5": 24px    # entre grupos
  "6": 32px    # respiro do palco
  "7": 48px    # entre seções de página
rounded:
  key: 5px      # tecla de atalho e tarja
  control: 10px # botão e campo
  panel: 18px   # diálogo e opção de plumagem
  round: 999px  # interruptor e botão flutuante
sizes:
  popup: 360px       # largura da janela da extensão
  popup-max: 600px   # altura máxima que o Chrome aceita
  hit: 44px          # menor alvo de clique
  row: 52px          # altura da linha
  icon: 22px         # ícone de linha
  mascot: 132px      # mascote no palco
  perch: 10px        # espessura do galho
motion:
  press: 120ms       # resposta ao toque
  change: 180ms      # troca de controle
  dusk: 420ms        # só o céu virando ao fazer silêncio
  ease: "cubic-bezier(.2,.8,.2,1)" # chega rápido e assenta
screens:
  popup: 360x600
  celular: 390x844
  desktop: 1440x900
themes:
  noite:
    primary: "{colors.noite-primary}"
    primary-hover: "{colors.noite-primary-hover}"
    on-primary: "{colors.noite-on-primary}"
    bg: "{colors.noite-bg}"
    surface: "{colors.noite-surface}"
    surface-hover: "{colors.noite-surface-hover}"
    text: "{colors.noite-text}"
    text-muted: "{colors.noite-text-muted}"
    line: "{colors.noite-line}"
    control: "{colors.noite-control}"
    danger: "{colors.noite-danger}"
    on-danger: "{colors.noite-on-danger}"
    tarja: "{colors.noite-tarja}"
components:
  page: { backgroundColor: "{colors.bg}", textColor: "{colors.text}", typography: "{typography.body}" }
  page-support: { backgroundColor: "{colors.bg}", textColor: "{colors.text-muted}", typography: "{typography.small}" }
  stage-open: { backgroundColor: "{colors.ceu-aberto}", textColor: "{colors.on-ceu-aberto}", typography: "{typography.display}" }
  stage-silence: { backgroundColor: "{colors.ceu-silencio}", textColor: "{colors.on-ceu-silencio}", typography: "{typography.display}" }
  stage-closed: { backgroundColor: "{colors.ceu-neblina}", textColor: "{colors.on-ceu-aberto}", typography: "{typography.display}" }
  stage-alert: { backgroundColor: "{colors.ceu-alerta}", textColor: "{colors.on-warning}", typography: "{typography.display}" }
  button-primary: { backgroundColor: "{colors.primary}", textColor: "{colors.on-primary}", typography: "{typography.label}", rounded: "{rounded.control}", height: "{sizes.hit}" }
  button-primary-hover: { backgroundColor: "{colors.primary-hover}", textColor: "{colors.on-primary}" }
  button-primary-disabled: { backgroundColor: "{colors.surface-hover}", textColor: "{colors.text-muted}" }
  button-quiet: { backgroundColor: "{colors.bg}", textColor: "{colors.primary}", typography: "{typography.label}", rounded: "{rounded.control}" }
  button-quiet-hover: { backgroundColor: "{colors.surface-hover}", textColor: "{colors.primary-hover}" }
  button-danger: { backgroundColor: "{colors.danger}", textColor: "{colors.on-danger}", typography: "{typography.label}", rounded: "{rounded.control}" }
  row: { backgroundColor: "{colors.bg}", textColor: "{colors.text}", typography: "{typography.label}", height: "{sizes.row}" }
  row-hover: { backgroundColor: "{colors.surface-hover}", textColor: "{colors.text}" }
  row-value: { backgroundColor: "{colors.bg}", textColor: "{colors.text-muted}", typography: "{typography.small}" }
  switch-on: { backgroundColor: "{colors.primary}", textColor: "{colors.on-primary}", rounded: "{rounded.round}" }
  segment-selected: { backgroundColor: "{colors.primary}", textColor: "{colors.on-primary}", rounded: "{rounded.control}" }
  field: { backgroundColor: "{colors.surface}", textColor: "{colors.text}", borderColor: "{colors.control}", rounded: "{rounded.control}" }
  field-focus: { backgroundColor: "{colors.surface}", textColor: "{colors.text}", borderColor: "{colors.primary}" }
  field-error: { backgroundColor: "{colors.surface}", textColor: "{colors.danger}", borderColor: "{colors.danger}" }
  swatch-selected: { backgroundColor: "{colors.surface}", textColor: "{colors.text}", borderColor: "{colors.primary}", rounded: "{rounded.panel}" }
  shortcut-key: { backgroundColor: "{colors.surface-hover}", textColor: "{colors.text}", typography: "{typography.small}", rounded: "{rounded.key}" }
  notice: { backgroundColor: "{colors.warning}", textColor: "{colors.on-warning}", typography: "{typography.small}" }
  toast: { backgroundColor: "{colors.text}", textColor: "{colors.bg}", typography: "{typography.small}", rounded: "{rounded.control}" }
  page-noite: { backgroundColor: "{colors.noite-bg}", textColor: "{colors.noite-text}" }
  page-support-noite: { backgroundColor: "{colors.noite-bg}", textColor: "{colors.noite-text-muted}" }
  button-primary-noite: { backgroundColor: "{colors.noite-primary}", textColor: "{colors.noite-on-primary}" }
  button-primary-hover-noite: { backgroundColor: "{colors.noite-primary-hover}", textColor: "{colors.noite-on-primary}" }
  button-primary-disabled-noite: { backgroundColor: "{colors.noite-surface-hover}", textColor: "{colors.noite-text-muted}" }
  button-danger-noite: { backgroundColor: "{colors.noite-danger}", textColor: "{colors.noite-on-danger}" }
  row-hover-noite: { backgroundColor: "{colors.noite-surface-hover}", textColor: "{colors.noite-text}" }
  field-noite: { backgroundColor: "{colors.noite-surface}", textColor: "{colors.noite-text}", borderColor: "{colors.noite-control}" }
  field-error-noite: { backgroundColor: "{colors.noite-surface}", textColor: "{colors.noite-danger}", borderColor: "{colors.noite-danger}" }
fontes:
  Sofia Sans: "ui/fontes/sofia-sans-latin-wght-normal.woff2"
---

## Overview

> Estado deste livro: versão 0.1, proposta do Claude feita a pedido do dono em 22/11/2026. Ele pediu o design
> system; ainda não aprovou item por item.

**Quando o uirapuru canta, a floresta silencia.** O Uirapp é isso numa extensão: um gesto e a sua tela fica quieta.
O pedido do dono tem três palavras, e cada decisão responde a uma delas.

- **Grátis:** nada na tela parece vitrine. Sem cadeado, selo PRO, oferta ou contagem de limite.
- **Seguro:** a pessoa vê o estado, não uma promessa. O céu, o olho do pássaro e o verbo do botão dizem juntos se as
  conversas estão escondidas.
- **Carismático:** o carisma mora num lugar só, o pássaro no galho. O resto da interface é quieto.

**Para quem:** quem usa o WhatsApp Web com gente por perto (trabalho, loja, live, tela dividida).
**Tarefa principal:** esconder tudo em um segundo e saber que escondeu.

**A assinatura é o poleiro.** Um galho atravessa a tela inicial e separa o céu, que é o estado, do chão, que são os
controles. Ao fazer silêncio o céu anoitece e o pássaro fecha o olho. No WhatsApp, cada foto escondida vira um
passarinho dormindo.

**Voz:** português simples, frase curta, verbo no botão, sem desculpa e sem susto. O texto diz só o essencial. O que
o programa pode decidir, o texto não explica.

| Situação | Dizemos | Não dizemos |
|---|---|---|
| Ação | Esconder conversas | Ativar proteção |
| Feito | Conversas escondidas | Sucesso! |
| Falha | O WhatsApp mudou. Cobri a tela inteira. | Ops, algo deu errado |
| Vazio | Nenhuma resposta ainda | Você não possui registros |
| Acesso | Envia para fora: nada | Segurança de nível militar |

## Colors

As cores vêm das duas horas em que o uirapuru canta: o amanhecer e o anoitecer.

- **O céu é estado, o tema é gosto.** `ceu-aberto` é conversa à vista e `ceu-silencio` é conversa escondida, iguais
  no tema claro e no escuro. Assim ninguém confunde tema escuro com silêncio. Com o WhatsApp fechado o céu fica
  em `ceu-neblina` e o olho aberto: olho fechado quer dizer escondido e nada mais.
- **O pássaro sempre tem céu atrás.** Sobre fundo escuro, solto, o corpo carvão some.
- **Azul de céu fundo (`primary`) é ação:** botão, seleção, ligado e foco.
- **Escarlate é o pássaro.** Nunca é botão, erro nem ligado. Erro tem cor própria (`danger`) e sempre vem com palavra.
- **Sem verde de WhatsApp e sem roxo de Pragmaz.**
- **Creme só existe no ícone,** para o corpo carvão não sumir na barra escura do navegador.
- Texto tem no mínimo 4,5:1 de contraste. Borda de controle, foco e trilho têm no mínimo 3:1.

As plumagens trocam apenas cabeça, corpo e bico do mascote: Vermelha (uirapuru-vermelho, a da marca), Laranja
(uirapuru-laranja) e Da lenda (uirapuru-verdadeiro, pardo-avermelhado). Nunca trocam cor de estado ou de ação.

## Typography

**Sofia Sans em tudo**, em pesos bem separados. É estreita o bastante para 360 px, tem acentos completos, diferencia
I, l e 1 e combina com o corpo redondo do pássaro sem imitar as letras da logo. Licença SIL OFL, no pacote, sem CDN.

- `display` aparece uma vez por tela e só no palco.
- Frase começa com maiúscula e segue em minúscula. Sem rótulo todo em maiúsculas e sem palavra colorida no título.
- O nome Uirapp é sempre o desenho `marca/nome.svg`, nunca digitado numa fonte.

## Layout

A janela tem 360 px de largura e até 600 px de altura. A tela inicial tem um foco:

```
| Uirapp                             |
|            céu = estado            |
|  (pássaro)   Conversas à vista     |
|=========== galho =================|
| [ Esconder conversas       Alt+S ] |
| Privacidade                      > |
| Plumagem               Vermelha  > |
| [ Buscar                         ] |
| Privacidade                Tudo  > |
| Respostas prontas             2  > |
| Aparência              Igarapé   > |
| ... (favoritos sobem para o topo)  |
```

- Tudo alinha à esquerda na margem `spacing.4`. O pássaro é o único que pousa fora da grade.
- Lista é linha com divisão, não uma pilha de cartões.
- Subtela: voltar, título e conteúdo. Uma ação principal, presa embaixo quando a lista rola.
- Alvo de clique nunca menor que `sizes.hit`.
- No WhatsApp, o Uirapp ocupa um botão redondo de 56 px, mais nada. O tema do WhatsApp muda as cores dele, não as do
  Uirapp.
- **Ninho** é a página inteira para o que não cabe em 360 px (atendimento, lembretes, estúdio de temas, desenho e
  backup). O topo é o mesmo céu com galho da janela; as partes são abas com ícone e palavra. Quadro de atendimento em
  colunas que rolam de lado no celular. Usa só os componentes e tokens deste livro.

## Elevation & Depth

Profundidade é cor e o galho, não sombra. Só o que está de fato por cima (diálogo, aviso passageiro, botão dentro
do WhatsApp) sai do plano, e por contorno ou véu. Sem brilho, vidro ou gradiente.

## Shapes

O raio diz o papel: tecla e tarja 5, controle 10, diálogo e plumagem 18, interruptor e botão flutuante redondos.
O galho tem pontas redondas e duas folhas. Ícones são Tabler (MIT): cheios para coisas, traço 2 para direção e ação
pequena. Ícone fica solto na linha, sem quadradinho colorido atrás.

**Marca**

- Use os arquivos de `marca/`, gerados por `scripts/marca.py`. Não redesenhe nem estique.
- Fundo claro: `logo-horizontal.svg`. Fundo escuro: `logo-horizontal-escura.svg`.
- Uma cor só: `simbolo-mono-preto.svg` ou `simbolo-mono-branco.svg`.
- 16 px usa `icone-16.svg`, que é um desenho próprio. Não reduza o ícone grande.
- Respiro em volta da logo: a altura da cabeça do pássaro até o olho. Logo horizontal nunca abaixo de 120 px.

## Components

Todos vivem em `ui/componentes.css` e usam só variáveis de `ui/tokens.css`, gerado deste arquivo.

| Componente | Estados |
|---|---|
| Palco com poleiro | à vista, silêncio, alerta, sem WhatsApp |
| Mascote | acordado, silêncio (olho fechado), cantando (algo deu certo), alerta (olho arregalado) |
| Botão | normal, mouse, pressionado, foco, desabilitado; principal, discreto, perigo |
| Linha | normal, mouse, foco, com valor |
| Interruptor | ligado, desligado, foco, desabilitado |
| Seletor de tema | normal, mouse, selecionado, foco |
| Plumagem | normal, mouse, selecionada, foco |
| Campo | normal, foco, preenchido, erro com frase, desabilitado |
| Lista de respostas | cheia, vazia, copiada |
| Diálogo | só para apagar |
| Aviso passageiro | confirma o que acabou de acontecer, com o verbo do botão |
| Tarja | texto, foto (passarinho dormindo), mídia, página inteira quando falha |
| Amostra de tema | normal, mouse, selecionada, foco; "do WhatsApp" é listrada |
| Ficha (Ninho) | normal, mouse, arrastando, coluna recebendo |

**Movimento:** só responde a uma ação. O céu vira em `motion.dusk` e o pássaro assenta 4 px no galho. Com movimento
reduzido no sistema, tudo troca na hora.

**Segurança que o componente garante**

- Texto de fora entra como texto, nunca como HTML.
- A tarja é opaca e tira a seleção. Desfoque não conta como esconder.
- Nome e prévia viram tarja de largura fixa, para o tamanho não entregar quem é.
- Na dúvida, cobre tudo: o estado de erro é mais fechado que o normal, nunca mais aberto.
- A janela carrega fonte, ícone e script só do pacote e não abre conexão.

## Do's and Don'ts

- Faça o estado aparecer em três sinais: cor, olho do pássaro e palavra.
- Faça o botão dizer o que acontece ao clicar, e o aviso repetir o mesmo verbo.
- Confira toda tela nos dois temas, em 360 px, só com teclado e com movimento reduzido.
- Não use escarlate em botão, erro ou seleção.
- Não use cadeado, selo PRO, preço, depoimento ou número inventado.
- Não ponha o mascote em linha, botão de ação ou título. Ele mora no poleiro, no vazio, na tarja de foto e no botão flutuante.
- Não use o logo, o telefone ou o verde do WhatsApp, e não sugira parceria com ele.
- Não escreva valor solto no CSS de uma tela. Mude aqui e rode `python scripts/montar.py`.
- Não copie código, texto, tema ou arte da Pragmaz.
