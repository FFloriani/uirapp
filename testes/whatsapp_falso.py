"""WhatsApp Web de mentira para testar o Silêncio. Estrutura vista em 22/11/2026, dados inventados, zero arte deles.

Cada segredo tem um código próprio, para o teste saber exatamente o que vazou.
Cada foto é magenta puro e cada mídia é verde puro, para achar vazamento no pixel.
"""
import base64
import io

from PIL import Image

FOTO, MIDIA, EMOJI = (255, 0, 255), (0, 255, 0), (0, 255, 255)
CODIGOS = ("NOMEQ", "REMETQ", "PREVIAQ", "MENSQ", "AUTORQ", "MENCQ", "CITAQ", "AVISOQ", "SOLTOQ", "MEMBROQ", "INICQ")
CSP = ("default-src 'self' blob:; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline' data: blob:; "
       "img-src 'self' data: blob: https://*.whatsapp.net; font-src 'self' data:; connect-src 'self'")


def png(cor):
    b = io.BytesIO()
    Image.new("RGB", (64, 64), cor).save(b, "PNG")
    return b.getvalue()


IMAGENS = {"foto": png(FOTO), "midia": png(MIDIA)}
DESENHO_EMOJI = "data:image/png;base64," + base64.b64encode(png(EMOJI)).decode()
VAZIA = "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"
F, M = "https://pps.whatsapp.net/foto.png", "https://media.whatsapp.net/midia.png"


def linha(i, v):
    extra = " da silva sauro" * (i % 3) if v == "a" else "x" * (i % 5)
    jeito = i % 4
    foto = (f'<img src="{F}" width="48" height="48">' if jeito == 0 else
            f'<svg width="48" height="48" viewBox="0 0 48 48"><image href="{F}" width="48" height="48"/><title>NOMEQ{v}{i}</title></svg>' if jeito == 1 else
            f'<div class="foto-fundo" style="background-image:url({F})"></div><div data-testid="profile-first-initial">INICQ{v}{i}</div>' if jeito == 2 else
            f'<img src="{F}" width="40" height="40" style="visibility:visible!important">')
    if i % 5 == 1:
        previa = f'<div class="aviso"><span>AVISOQ{v}{i} entrou</span></div>'
    elif i % 5 == 2:
        previa = (f'<div><span>REMETQ{v}{i}</span></div><span>: </span>'
                  f'<span dir="auto" class="p">PREVIAQ{v}{i}{extra}<span role="button">MENCQ{v}{i}</span></span>')
    elif i % 5 == 3:
        previa = f'<div data-testid="chat_list_last_msg_media_thumb" class="mini" style="background-image:url({M})"></div><span dir="auto" class="p">PREVIAQ{v}{i}</span>'
    else:
        previa = f'<span dir="auto" class="p">PREVIAQ{v}{i}{extra}</span>'
    return (f'<div role="row" class="linha" style="transform:translateY({i * 76}px)"><div role="gridcell"><div>'
            f'<div data-testid="cell-frame-container" class="celula" onclick="cliques++"><div class="caixa-foto"><div>{foto}</div></div>'
            f'<div class="corpo"><div class="cima"><div data-testid="cell-frame-title" class="titulo">'
            f'<span class="dir" dir="auto" title="NOMEQ{v}{i}{extra}">NOMEQ{v}{i}{extra}</span></div>'
            f'<div data-testid="cell-frame-primary-detail"><span data-testid="chat-list-timestamp">SOLTOQ1{i}h</span></div></div>'
            f'<div data-testid="cell-frame-secondary" class="baixo"><div>'
            f'<span data-testid="last-msg-status" class="status" title="PREVIAQ{v}{i}{extra}">{previa}</span></div></div></div>'
            f'</div></div></div></div>')


def citada(i, v):
    return (f'<div data-testid="quoted-message"><div role="button"><div><span data-testid="author">AUTORQ{v}{i}</span>'
            f'<div role="button"><span class="selectable-text copyable-text cita" data-testid="selectable-text">CITAQ{v}{i}</span></div></div></div></div>')


def balao(i, v):
    if i == 1:
        corpo = f'{citada(i, v)}<div data-testid="sticker-container"><button><img src="{M}" width="120" height="70" style="display:block"></button></div>'
    else:
        cita = citada(i, v) if i == 2 else ""
        corpo = (f'<div class="copyable-text" data-pre-plain-text="[10:0{i}, 22/11/2026] AUTORQ{v}{i}: ">{cita}<div>'
                 f'<span class="selectable-text copyable-text" data-testid="selectable-text"><span>MENSQ{v}{i}{" palavras" * (i + (v == "b") * 3)}</span> '
                 f'<img class="emoji selectable-text copyable-text" data-testid="selectable-text" src="{VAZIA}" width="20" height="20"> '
                 f'<span role="button">MENCQ{v}{i}</span></span><span><span><span>SOLTOQespaco</span></span></span></div></div>')
    foto = (f'<img src="{F}" width="28" height="28">' if i % 2 == 0 else
            f'<div><div><div data-testid="profile-first-initial">INICQ{v}{i}</div></div></div>')
    return (f'<div role="row"><div class="linha-msg"><div class="coluna-foto"><div role="button" data-testid="group-chat-profile-picture" class="foto-grupo">{foto}</div></div>'
            f'<div data-testid="msg-container" class="msg"><div class="balao"><span data-testid="author">AUTORQ{v}{i}</span>'
            f'{corpo}<div data-testid="msg-meta"><span><span>10:0{i}</span></span></div></div></div></div></div>')


CONVERSA = """<div id="main">
 <header data-testid="conversation-header" class="topo-conversa"><div data-testid="conversation-info-header" class="info">
  <div><div data-testid="conversation-header-avatar" class="caixa-foto"><img src="{F}" width="40" height="40"></div></div>
  <div data-testid="conversation-info-header-chat-title-name" class="titulo"><span data-testid="conversation-info-header-chat-title" title="NOMEQ{v}99">NOMEQ{v}99</span></div>
  <div data-testid="chat-subtitle"><span class="selectable-text copyable-text" data-testid="selectable-text" title="MEMBROQ{v}">MEMBROQ{v}</span></div></div></header>
 <div data-testid="conversation-panel-body" class="corpo-conversa"><div data-testid="conversation-panel-messages" class="mensagens" tabindex="0"><div><div><span>SOLTOQdia</span></div>{baloes}</div></div></div>
 <footer class="rodape"><div class="rodape-dentro"><div data-testid="compose-box" class="caixa-escrever">
  <div data-testid="conversation-compose-box-input" class="escrever" contenteditable="true">MENSQ{v}rascunho</div>
  <button data-testid="compose-btn-send" onclick="envios++">env</button></div></div></footer></div>"""

ENTRADA = """<div id="app"><div class="entrada"><h1>SOLTOQentrar</h1><div data-testid="link-device-qr-code"><canvas width="80" height="80"></canvas></div></div></div>"""

ESTILO = """
html,body{margin:0;height:100%} body{background:rgb(252,245,235);color:#111;font:16px sans-serif;overflow:hidden}
body.dark{background:rgb(38,37,36);color:#eee}
#app>.quadro{display:flex;height:100vh} .trilho{width:64px;flex:none}
#side{width:420px;flex:none;display:flex;flex-direction:column;position:relative;background:var(--WDS-surface-default,#fff);color:var(--WDS-content-default,#111)}.nav{display:block;width:48px;height:48px}.faixa{height:30px}
.busca{height:64px;flex:none} .filtros{height:44px;flex:none}
#pane-side{flex:1;overflow:auto;position:relative} [data-testid=chat-list]{position:relative;height:2000px}
.linha{position:absolute;left:0;right:0;height:76px;transition:all 2s} .celula{display:flex;height:76px}
.caixa-foto{width:76px;height:72px;flex:none;display:grid;place-items:center}
.foto-fundo{width:48px;height:48px;background-size:cover} .mini{display:inline-block;width:16px;height:16px;background-size:cover}
.corpo{flex:1;min-width:0;display:flex;flex-direction:column;justify-content:center}
.cima{display:flex;height:24px}.titulo{flex:1;min-width:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;animation:sempre 1s infinite}
@keyframes sempre{from,to{visibility:visible}}
.baixo{height:22px;white-space:nowrap;overflow:hidden} .status{display:flex;gap:3px} .p{overflow:hidden;text-overflow:ellipsis}
.teimoso{visibility:visible!important} .pseudo::before{content:"SOLTOQpseudo";visibility:visible!important}
#main{flex:1;min-width:0;display:flex;flex-direction:column}
.topo-conversa{height:64px;flex:none}.info{display:flex;align-items:center;gap:8px;height:64px}
.info .caixa-foto{width:48px;height:48px}.info .titulo{flex:none;width:260px}
.corpo-conversa{flex:1;min-height:0}.mensagens{height:100%;overflow:auto}
.msg{position:relative;padding:6px 40px}.balao{display:inline-block;background:#d9fdd3;color:#111;padding:6px}
.rodape{height:64px;flex:none}.rodape-dentro,.caixa-escrever{height:100%}.caixa-escrever{display:flex}.escrever{flex:1}
.linha-msg{display:flex}.coluna-foto{width:28px;flex:none}.foto-grupo{position:sticky;top:0;width:28px;height:28px}
.portal{position:fixed;left:500px;bottom:4px;z-index:2147483647}
"""

# Coisas que o site poderia ter e que já furaram esconder ingênuo
ARMADILHAS = """
<div class="portal"><p class="teimoso">SOLTOQclasse</p><p style="visibility:visible!important;opacity:1!important">SOLTOQinline</p>
<p class="pseudo"></p><input value="SOLTOQinput" style="visibility:visible!important"><iframe srcdoc="<body style='background:#0f0'>SOLTOQquadro" width="50" height="20" style="visibility:visible!important"></iframe>
<uirapp-casa style="visibility:visible!important">SOLTOQfalsa</uirapp-casa><div id="com-sombra"></div></div>
<div id="flutua" popover="manual" style="visibility:visible!important">SOLTOQpopover</div>
"""

ESPIAO = """
window.piscou=0; window.amostras=0;
const olha=()=>{ if(!document.body) return; amostras++;
  for(const e of [document.body, document.querySelector('[data-testid="cell-frame-title"]'), document.querySelector('.caixa-foto')])
    if(e && getComputedStyle(e).visibility==='visible' && +getComputedStyle(document.body).opacity>0) piscou++ };
const vigia=new MutationObserver(olha); vigia.observe(document.documentElement,{childList:true,subtree:true,attributes:true});
const quadro=()=>{olha(); if(performance.now()<1500) requestAnimationFrame(quadro); else vigia.disconnect()}; requestAnimationFrame(quadro);
window.cliques=0; window.envios=0; window.teclas=0; window.digitado=0;
addEventListener('keydown',e=>{teclas++; if(e.key==='Enter'&&e.target.closest&&e.target.closest('[data-testid=conversation-compose-box-input]'))envios++}); addEventListener('input',()=>digitado++,true);
"""


def pagina(v="a", linhas=9, conversa=True, escuro=False, armadilhas=False, entrada=False):
    if entrada:
        app = ENTRADA
    else:
        baloes = "".join(balao(i, v) for i in range(4))
        main = CONVERSA.format(F=F, v=v, baloes=baloes) if conversa else '<section data-testid="intro-panel">SOLTOQintro</section>'
        app = (f'<div id="app"><div class="quadro"><div class="trilho"><header data-testid="chatlist-header"><button data-navbar-item class="nav"><svg><title>wds-ic-chat-filled</title></svg></button><button data-navbar-item class="nav"><svg><title>wds-ic-status</title></svg></button><button data-navbar-item class="nav"><svg><title>wds-ic-channels</title></svg></button><button data-navbar-item class="nav"><svg><title>ic-call</title></svg></button></header></div><div id="side">'
               f'<div class="busca" data-testid="chat-list-search-container"><input role="textbox" value="SOLTOQbusca"></div>'
               f'<div class="filtros" data-testid="chat_list_filters_row"><span title="SOLTOQfiltro">SOLTOQfiltro</span></div>'
               f'<div data-testid="chat_list_notifications_banner" class="faixa">SOLTOQfaixa</div>'
               f'<div id="pane-side"><div><div data-testid="chat-list"><div role="grid">{"".join(linha(i, v) for i in range(linhas))}</div></div></div></div>'
               f'</div>{main}</div><div id="wa-popovers-bucket"></div></div>')
    extra = ARMADILHAS if armadilhas else ""
    js = "document.querySelector('#com-sombra').attachShadow({mode:'open'}).append('SOLTOQsombra');document.querySelector('#flutua').showPopover();" if armadilhas else ""
    return (f'<!doctype html><html id="whatsapp-web"><head><meta charset="utf-8"><title>(3) WhatsApp</title><style>{ESTILO}</style>'
            f'<style>img.emoji{{background-image:url({DESENHO_EMOJI});background-size:cover}}</style><script>{ESPIAO}</script></head><body class="{"dark" if escuro else ""}">{app}{extra}<script>{js}</script></body></html>')
