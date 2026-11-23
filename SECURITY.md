# Segurança

## Como reportar uma falha

Não abra issue pública. Use o botão **Report a vulnerability** na aba [Security](https://github.com/FFloriani/uirapp/security/advisories/new) deste repositório: a conversa fica privada até a correção sair.

Conte a versão do Uirapp, o navegador e os passos para reproduzir. Não mande dados de conversas reais.

## Versões que recebem correção

| Versão | Recebe correção |
|---|---|
| 0.3.x | Sim |
| 0.2.x e anteriores | Não |

## Regras que o código segue

Cada regra tem checagem em `scripts/testar.py`, e `testes/defeitos_plantados.py` planta 22 defeitos para provar que o teste os pega.

1. **Sem servidor, telemetria ou código remoto.** As páginas da extensão têm `connect-src 'none'`, e o teste falha se qualquer pedido sair da extensão.
2. **Não mexe na página do WhatsApp.** Não troca cabeçalho de rede e não roda script no mundo da página; só lê a tela e aplica estilo.
3. **Nenhuma ponte com a página.** O WhatsApp Web não alcança os dados da extensão.
4. **Dado de fora entra só como texto.** Nada que vem da página, de um tema ou de um backup importado vira HTML.
5. **Nunca age na conta.** O Uirapp não envia, publica, entra, segue nem apaga nada. Ele escreve no campo da conversa quando você pede; quem envia é você.
6. **Guarda só o que você criou.** Ajustes, respostas, fichas, lembretes e temas, no banco da própria extensão. A conversa só é lida quando você clica em exportar, em usar uma resposta ou numa ação da IA, e não é guardada.
7. **Falha fechado.** Se não reconhecer a tela, cobre a página inteira e avisa, em vez de deixar algo à vista.
8. **IA só no computador.** A IA no computador usa a IA que o Google Chrome traz, que roda neste computador. O Uirapp não baixa nem chama modelo nenhum: quem baixa o modelo é o Chrome, e a conversa não vai a servidor.

## O que o Silêncio não protege

As notificações do computador, quem olha a tela antes de você apertar Alt+S e o que aparecer depois de desligar ou remover a extensão. O Silêncio protege a tela contra olhares, não contra quem tem acesso ao seu computador.
