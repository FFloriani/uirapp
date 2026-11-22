# Como contribuir com o Uirapp

Obrigado por chegar até aqui. O Uirapp aceita relato de problema, ideia, tradução (inglês e espanhol) e teste em outros navegadores. Projeto de uma pessoa: a resposta pode levar alguns dias.

> [!IMPORTANT]
> Nunca poste print, vídeo ou trecho de uma conversa de verdade numa issue. Para mostrar um problema do Silêncio, diga o que apareceu (um nome, uma prévia, uma foto) e onde, sem o conteúdo.

## O que fica de fora

Estas ideias são recusadas, porque quebram as regras de segurança do projeto ([SECURITY.md](SECURITY.md)):

- enviar, agendar ou disparar mensagens sozinho, ou qualquer robô que aja na conta;
- servidor, conta, telemetria, anúncio ou código baixado da internet;
- mexer no código do WhatsApp Web, rodar no mundo da página ou trocar cabeçalhos de rede;
- guardar conversas, contatos ou mensagens apagadas de outras pessoas.

## Ajudar sem código

- **O WhatsApp mudou.** Se o Uirapp cobriu a tela e avisou, abra uma issue com a data, o navegador e a versão do Uirapp.
- **Tradução.** Cada frase da extensão está em [`extensao/fonte/frases.js`](extensao/fonte/frases.js), com o inglês e o espanhol ao lado.
- **Outro navegador.** Edge, Opera e Vivaldi nunca foram testados: conte o que funcionou e o que não.

## Rodar o projeto

Precisa de Python 3 (testado no 3.14) e, para os testes, Node.js (testado no 26) e o Brave ou o Google Chrome instalados no caminho padrão do Windows. Os testes de navegador rodam só no Windows.

```powershell
git clone https://github.com/FFloriani/uirapp.git
cd uirapp
python -m pip install pillow pyyaml playwright
python scripts/montar.py
node --test testes/regras.test.mjs
python scripts/testar.py brave
```

Saída esperada: `montado`, depois `pass 19` nas regras e, no fim do `testar.py`, a contagem de checagens com zero falhas. O `testar.py` abre o navegador num perfil descartável, com um WhatsApp de mentira e sem internet; não toca no seu navegador.

Depois de montar, carregue a pasta `extensao/uirapp` em `brave://extensions` (Modo do desenvolvedor, **Carregar sem compactação**). A cada mudança: montar, clicar em recarregar no cartão do Uirapp e apertar F5 na aba do WhatsApp Web.

### Comandos

| Comando | O que faz |
|---|---|
| `python scripts/montar.py` | Gera os tokens, as telas do protótipo, a vitrine e a extensão (pasta e ZIP) |
| `node --test testes/regras.test.mjs` | Testa as regras puras: telefone, Pix, variáveis, temas, exportação, senha e backup |
| `python scripts/testar.py [brave\|chrome] [--parado]` | Testa a extensão de verdade; `--parado` espera os 5 minutos reais do "parado" |
| `python testes/defeitos_plantados.py` | Planta 18 defeitos, um por vez, e exige que o `testar.py` pegue todos |
| `python scripts/testar_idioma.py` | Confere que toda frase das telas tem inglês e espanhol |
| `python scripts/conferir.py` | Confere o design system no Chrome: contraste, teclado, rede, temas e larguras |
| `python scripts/marca.py` | Gera a logo, o mascote e os ícones a partir do código |
| `python scripts/imagem_instalar.py` | Refaz a imagem do passo a passo de instalar |
| `python scripts/imagens_readme.py` | Refaz as imagens do README com dados de exemplo |

### Onde está cada coisa

| Caminho | O que é | Edita aqui? |
|---|---|---|
| `extensao/fonte/` | Código da extensão | Sim, e depois monta |
| `extensao/fonte/ancoras.json` | Os marcadores do WhatsApp Web, todos num lugar só | Sim, com o teste antes |
| `extensao/fonte/regras.js` | Regras puras: telefone, Pix, variáveis, temas, exportação, senha, backup | Sim, com teste |
| `extensao/fonte/frases.js` | Inglês e espanhol de cada frase | Sim |
| `extensao/uirapp/` | A pasta que o navegador carrega | Não, é gerada |
| `scripts/extensao.py` | Manifesto, permissões e pacote | Sim, e depois monta |
| `testes/whatsapp_falso.py` | O WhatsApp de mentira dos testes | Sim |
| `DESIGN.md` | O design system: cores, tipos, espaços, componentes e o porquê de cada um | Sim, e depois monta |
| `ui/componentes.css` | Componentes da interface | Sim |
| `ui/tokens.css` | Variáveis de cor, tipo e espaço | Não, sai do `DESIGN.md` |
| `prototipo/fonte/` | HTML das telas | Sim |
| `prototipo/*.html` | Telas montadas | Não, é gerada |
| `design-system/vitrine.html` | A vitrine do design system; abre com dois cliques | Não, é gerada |
| `marca/` | Logo, mascote e ícones em SVG e PNG | Não, sai do `scripts/marca.py` |
| `docs/imagens/` | Imagens do README | Não, saem dos scripts |

## Quando o WhatsApp Web muda

O Silêncio esconde tudo e só mostra o que reconhece pelos marcadores de `extensao/fonte/ancoras.json`. Para trocar ou acrescentar um marcador:

1. Reproduza a estrutura nova em `testes/whatsapp_falso.py`.
2. Rode `python scripts/testar.py` e veja o teste **falhar**.
3. Só então mude `ancoras.json`, monte e rode o teste de novo.

Confira o WhatsApp Web de verdade só pela estrutura da página (atributos e contagens), nunca lendo ou guardando o conteúdo das conversas.

## Antes de mandar código

1. Abra uma issue dizendo o que quer mudar e espere a conversa: o projeto ainda não tem licença aberta.
2. Mude a fonte, não o que é gerado (veja a tabela acima).
3. Rode `node --test testes/regras.test.mjs`, `python scripts/testar.py brave` e `python scripts/testar_idioma.py`. Mudou algo de segurança ou do Silêncio: rode também `python testes/defeitos_plantados.py`.
4. Frase nova na tela precisa de inglês e espanhol em `frases.js`.

## Dúvidas

Pergunte numa [issue](https://github.com/FFloriani/uirapp/issues). Falha de segurança não vai em issue: siga o [SECURITY.md](SECURITY.md).
