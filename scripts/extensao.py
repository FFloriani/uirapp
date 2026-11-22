"""Monta a extensão a partir das fontes únicas. Quem chama é scripts/montar.py.

extensao/fonte + DESIGN.md + ui + marca -> extensao/uirapp/ (a pasta que o navegador carrega)
                                        -> extensao/uirapp-<versão>.zip (o pacote da loja)
Pacote reproduzível: mesmas fontes, mesmos bytes.
"""
import base64
import json
import re
import shutil
import urllib.parse
import zipfile
from pathlib import Path
from xml.etree import ElementTree

import marca

NOME = "Uirapp"
# a versão mora em extensao/fonte/nucleo.js, que a janela também mostra
VERSAO = re.search(r'VERSAO = "([\d.]+)"', (Path(__file__).resolve().parent.parent / "extensao/fonte/nucleo.js").read_text("utf-8")).group(1)
DESCRICAO = "Esconde conversas no WhatsApp Web com Alt+S, guarda respostas prontas e troca o tema. Sem servidor. Não é afiliado ao WhatsApp."
SITE = "https://web.whatsapp.com/*"
FONTE = "extensao/fonte"
SAIDA = "extensao/uirapp"
ZIP = f"extensao/uirapp-{VERSAO}.zip"
WOFF = "ui/fontes/sofia-sans-latin-wght-normal.woff2"
FAMILIA_NA_PAGINA = "Uirapp Sofia"


CONTEUDO = ("regras.js", "nucleo.js", "frases.js", "idioma.js", "pacote.js", "silencio.js", "aparencia.js", "conversa.js")
PAGINA = ("regras.js", "nucleo.js", "frases.js", "idioma.js", "deposito.js")
FONTES_JS = ("regras.js", "nucleo.js", "frases.js", "idioma.js", "deposito.js", "silencio.js", "aparencia.js", "conversa.js",
             "fundo.js", "popup.js", "ninho.js")


def manifesto():
    return {
        "manifest_version": 3,
        "name": NOME,
        "version": VERSAO,
        "description": DESCRICAO,
        "minimum_chrome_version": "120",
        # storage: ajustes. scripting: pôr o CSS que esconde com força de usuário. Só no WhatsApp Web.
        # contextMenus: "Compartilhar no WhatsApp". alarms e notifications: lembretes.
        "permissions": ["storage", "scripting", "contextMenus", "alarms", "notifications"],
        "host_permissions": [SITE],
        "background": {"service_worker": "fundo.js"},
        "content_scripts": [{
            "matches": [SITE],
            "css": ["silencio.css"],
            "js": list(CONTEUDO),
            "run_at": "document_start",
        }],
        "action": {
            "default_popup": "popup.html",
            "default_title": NOME,
            "default_icon": {str(t): f"icones/icone-{t}.png" for t in (16, 32)},
        },
        "icons": {str(t): f"icones/icone-{t}.png" for t in (16, 32, 48, 128)},
        "commands": {"alternar": {"suggested_key": {"default": "Alt+S"}, "description": "Esconder ou mostrar conversas"}},
        "content_security_policy": {
            "extension_pages": ("default-src 'none'; script-src 'self'; style-src 'self'; font-src 'self'; img-src 'self'; "
                                "connect-src 'none'; form-action 'none'; base-uri 'none'; frame-ancestors 'none'; object-src 'none'"),
        },
    }


def arvore(svg):
    def no(e):
        return [e.tag, dict(e.attrib), [no(f) for f in e]]

    return no(ElementTree.fromstring(svg))


def passaro_dormindo(d, plumagem):
    c = d["colors"]
    cabeca, corpo, bico = c["escarlate"], c["carvao"], c["bico"]
    if plumagem != "vermelha":
        cabeca, bico = c[f"plumagem-{plumagem}"], c[f"plumagem-{plumagem}-bico"]
        corpo = c.get(f"plumagem-{plumagem}-corpo", corpo)
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{marca.CAIXA_PASSARO}">'
           f'<path d="{marca.CORPO}" fill="{corpo}"/><path d="{marca.CABECA}" fill="{cabeca}"/>'
           f'{marca.olho("silencio")}<path d="{marca.BICO_FECHADO}" fill="{bico}"/></svg>')
    return "data:image/svg+xml," + urllib.parse.quote(svg, safe="")


def silencio_css(m, d, ancoras):
    t = m.le(f"{FONTE}/silencio.css")
    t = re.sub(r"/\*.*?\*/", "", t, flags=re.S)  # os exemplos do comentário não são marcador

    def token(achado):
        grupo, chave = achado.group(1).split(".", 1)
        if grupo == "passaro":
            return passaro_dormindo(d, chave)
        valor = d[grupo]
        for parte in chave.split("."):
            valor = valor[parte]
        return str(valor)

    t = re.sub(r"@(\w+)@", lambda a: ", ".join(ancoras[a.group(1)]), t)
    t = re.sub(r"\$([a-z]+\.[\w.-]+)\$", token, t)
    return f"/* {m.AVISO} */\n{t.strip()}\n"


def css_da_tela(m, d):
    """Os mesmos tokens e componentes, para dentro do shadow root."""
    comp = re.sub(r"@font-face\s*\{[^}]*\}", "", m.le("ui/componentes.css"))
    t = m.tokens_css(d) + comp + m.le(f"{FONTE}/tela.css")
    t = re.sub(r':root\[(data-[\w-]+="[\w-]+")\]', r":host([\1])", t)
    t = t.replace(":root:not([data-tema])", ":host(:not([data-tema]))").replace(":root {", ":host {")
    t = t.replace('"Sofia Sans"', f'"{FAMILIA_NA_PAGINA}"')
    t = re.sub(r"/\*.*?\*/", "", t, flags=re.S)
    if ":root" in t:
        raise ValueError("sobrou :root no CSS do shadow root")
    return t


def pacote_js(m, d, ancoras):
    folhas = re.search(r"<svg.*</svg>", m.galho(), re.S).group(0)
    arte = {
        "css": css_da_tela(m, d),
        "passaro": arvore(m.passaro()),
        "folhas": arvore(folhas),
        "familia": FAMILIA_NA_PAGINA,
        "fonte": base64.b64encode((m.RAIZ / WOFF).read_bytes()).decode(),
    }
    usadas = {"estrutura": ancoras["estrutura"], "reconhece": ancoras["reconhece"]}
    j = lambda v: json.dumps(v, ensure_ascii=False, separators=(",", ":"))
    return (f'// {m.AVISO}\n"use strict";\n\n'
            f"globalThis.UirappPacote = Object.freeze({{\n  ANCORAS: {j(usadas)},\n  ARTE: {j(arte)},\n}});\n")


def pagina(m, fonte, script, prefixo):
    t = m.expande(m.le(fonte), scripts=(*PAGINA, script))
    for de, para in ((f"{prefixo}marca/icones/", "icones/"), (f"{prefixo}ui/tokens.css", "tokens.css"), (f"{prefixo}ui/componentes.css", "componentes.css")):
        t = t.replace(de, para)
    if "../" in t:
        raise ValueError(f"caminho de fora do pacote em {fonte}")
    return t.replace("<!doctype html>", f"<!doctype html>\n<!-- {m.AVISO} -->", 1)


def arquivos(m, d):
    """Tudo o que vai no pacote: caminho -> bytes. Lista fechada, nada entra por engano."""
    ancoras = json.loads(m.le(f"{FONTE}/ancoras.json"))
    texto = {
        "manifest.json": json.dumps(manifesto(), ensure_ascii=False, indent=2) + "\n",
        "pacote.js": pacote_js(m, d, ancoras),
        "silencio.css": silencio_css(m, d, ancoras),
        "popup.html": pagina(m, "prototipo/fonte/popup.html", "popup.js", "../"),
        "ninho.html": pagina(m, f"{FONTE}/ninho.html", "ninho.js", "../../"),
        "ninho.css": m.le(f"{FONTE}/ninho.css"),
        "popup.css": m.le("prototipo/popup.css") + "\n/* a janela da extensão tem o tamanho do conteúdo */\nbody { width: var(--tam-popup); }\n",
        "tokens.css": m.tokens_css(d),
        "componentes.css": m.le("ui/componentes.css"),
    }
    for n in FONTES_JS:
        texto[n] = m.le(f"{FONTE}/{n}")
    saida = {n: t.encode("utf-8") for n, t in texto.items()}
    copias = {
        "fontes/sofia-sans-latin-wght-normal.woff2": WOFF,
        "fontes/OFL-sofia-sans.txt": "ui/fontes/OFL-sofia-sans.txt",
        "icones/LICENSE-tabler.txt": "ui/icones/LICENSE-tabler.txt",
    }
    copias.update({f"icones/icone-{t}.png": f"marca/icones/icone-{t}.png" for t in (16, 32, 48, 128)})
    for destino, origem in copias.items():
        saida[destino] = (m.RAIZ / origem).read_bytes()
    return dict(sorted(saida.items()))


def monta(m, d):
    novos = arquivos(m, d)
    pasta = m.RAIZ / SAIDA
    # a pasta é gerada: some o que não faz parte, sem trocar a pasta que o navegador já carregou
    if pasta.is_dir():
        for f in pasta.rglob("*"):
            if f.is_file() and f.relative_to(pasta).as_posix() not in novos:
                f.unlink()
    for nome, dados in novos.items():
        f = pasta / nome
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_bytes(dados)
    with zipfile.ZipFile(m.RAIZ / ZIP, "w") as z:
        for nome, dados in novos.items():
            info = zipfile.ZipInfo(nome, (2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, dados)
    return sum(len(v) for v in novos.values())
