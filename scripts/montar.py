"""Monta tokens, protótipos e vitrine a partir das fontes únicas.

Uso: python scripts/montar.py
DESIGN.md -> ui/tokens.css
extensao/fonte + tudo acima -> extensao/uirapp/ e o zip (scripts/extensao.py)
marca.py + ui/icones -> <!--@...--> em prototipo/fonte/*.html -> prototipo/*.html
tudo -> design-system/vitrine.html (um arquivo só, abre sem servidor)
"""
import base64
import html
import json
import re
import sys
from pathlib import Path

import yaml

sys.dont_write_bytecode = True
import extensao  # noqa: E402
import marca  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
AVISO = "GERADO por scripts/montar.py. Não edite aqui."


def le(p):
    return (RAIZ / p).read_text("utf-8")


def grava(p, t):
    f = RAIZ / p
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(t, encoding="utf-8", newline="\n")


def livro():
    return yaml.safe_load(le("DESIGN.md").split("---", 2)[1])


def resolve(d, v):
    m = re.fullmatch(r"\{([\w.-]+)\}", str(v))
    if not m:
        return v
    grupo, chave = m.group(1).split(".", 1)
    return resolve(d, d[grupo][chave])


def papeis():
    """Comentário de cada linha do YAML: é o papel do token."""
    out, grupo = {}, None
    for l in le("DESIGN.md").split("---", 2)[1].splitlines():
        if l and not l.startswith(" "):
            grupo = l.split(":")[0]
        m = re.match(r'  "?([\w-]+)"?:.*\s#\s(.+)$', l)
        if m:
            out[f"{grupo}.{m.group(1)}"] = m.group(2).strip()
    return out


def tokens_css(d):
    r = [f"  --{k}: {v};" for k, v in d["colors"].items() if not k.startswith("noite-")]
    for grupo, pref in (("spacing", "espaco"), ("rounded", "raio"), ("sizes", "tam"), ("motion", "tempo")):
        r += [f"  --{pref}-{k}: {v};" for k, v in d[grupo].items()]
    for k, t in d["typography"].items():
        r.append(f'  --tipo-{k}: {t["fontWeight"]} {t["fontSize"]}/{t["lineHeight"]} "{t["fontFamily"]}", system-ui, sans-serif;')
    noite = "\n".join(f"  --{k}: {resolve(d, v)};" for k, v in d["themes"]["noite"].items())
    dia = "\n".join(r)
    return (f"/* {AVISO} Fonte: DESIGN.md */\n:root {{\n  color-scheme: light;\n{dia}\n}}\n"
            f':root[data-tema="noite"] {{\n  color-scheme: dark;\n{noite}\n}}\n'
            f"@media (prefers-color-scheme: dark) {{\n:root:not([data-tema]) {{\n  color-scheme: dark;\n{noite}\n}}\n}}\n")


# --- desenhos embutidos ------------------------------------------------------
def passaro(classe=""):
    """Um SVG com os quatro estados; o CSS mostra um e pinta a plumagem."""
    olhos = "".join(f'<g class="olho olho-{e}">{marca.olho(e)}</g>' for e in ("acordado", "silencio", "cantando", "alerta"))
    return (f'<svg class="passaro {classe}" viewBox="{marca.CAIXA_PASSARO}" aria-hidden="true" focusable="false">'
            f'<path class="p-corpo" d="{marca.CORPO}"/><path class="p-cabeca" d="{marca.CABECA}"/>{olhos}'
            f'<path class="p-bico bico-fechado" d="{marca.BICO_FECHADO}"/>'
            f'<path class="p-bico bico-aberto" d="{marca.BICO_ABERTO}"/></svg>')


def nome():
    return ('<svg class="nome" viewBox="546 388 914 278" role="img" aria-label="Uirapp">'
            f'{marca.nome("currentColor")}</svg>')


def galho():
    return ('<span class="galho" aria-hidden="true"><svg class="folhas" viewBox="0 0 64 34" focusable="false">'
            '<path d="M22 32C8 32 1 22 2 8C16 8 25 17 22 32Z"/><path d="M30 33C29 15 41 3 60 3C61 22 49 33 30 33Z"/>'
            '</svg></span>')


def icone(n):
    s = le(f"ui/icones/{n}.svg")
    miolo = re.search(r"<svg[^>]*>(.*)</svg>", s, re.S).group(1)
    miolo = re.sub(r'<path stroke="none" d="M0 0h24v24H0z" fill="none"\s*/>', "", miolo)
    tipo = "cheio" if 'fill="currentColor"' in s else "traco"
    return f'<svg class="icone icone-{tipo}" viewBox="0 0 24 24" aria-hidden="true" focusable="false">{" ".join(miolo.split())}</svg>'


SCRIPTS_DEMO = ("demo.js", *(f"../extensao/fonte/{n}" for n in ("regras.js", "nucleo.js", "frases.js", "idioma.js", "deposito.js", "ia.js", "popup.js")))


def expande(t, scripts=SCRIPTS_DEMO):
    def troca(m):
        if m.group(1) == "scripts":
            return "\n".join(f'<script src="{s}" defer></script>' for s in scripts)
        que, _, arg = m.group(1).partition(":")
        if que == "passaro":
            return passaro(arg)
        if que == "nome":
            return nome()
        if que == "galho":
            return galho()
        if que == "icone":
            return icone(arg)
        raise ValueError(m.group(0))

    return re.sub(r"<!--@([\w:-]+)-->", troca, t)


def solto(pagina, inicio=""):
    """Protótipo num arquivo só, para a vitrine."""
    fonte = base64.b64encode((RAIZ / "ui/fontes/sofia-sans-latin-wght-normal.woff2").read_bytes()).decode()
    css = le("ui/tokens.css") + le("ui/componentes.css").replace(
        "fontes/sofia-sans-latin-wght-normal.woff2", f"data:font/woff2;base64,{fonte}")
    css += le(f"prototipo/{pagina}.css") if (RAIZ / f"prototipo/{pagina}.css").exists() else ""
    t = re.sub(r"<meta http-equiv=[^>]+>", "", le(f"prototipo/{pagina}.html"))
    t = re.sub(r'<link rel="(?:stylesheet|icon)"[^>]+>\s*', "", t)
    srcs = re.findall(r'<script src="([^"]+)"', t)
    t = re.sub(r'<script src="[^"]+"[^>]*></script>', "", t)
    js = "".join(f"<script>{(RAIZ / 'prototipo' / s).read_text('utf-8')}</script>" for s in srcs)
    t = t.replace("</head>", f"<style>{css}</style></head>")
    t = t.replace("</body>", f"{js}</body>")
    if inicio:
        t = t.replace('<html lang="pt-BR"', f'<html lang="pt-BR" data-inicio="{html.escape(inicio)}"', 1)
    return t


# memória local do projeto (Rastro): rastro/no_painel.json diz que arquivo ganha cópia em que card do painel.
# Sem a pasta rastro/ (num clone do GitHub, por exemplo), não faz nada.
def publica():
    mapa = RAIZ / "rastro/no_painel.json"
    if not mapa.is_file():
        return
    for origem, card in json.loads(mapa.read_text("utf-8")).items():
        pasta = RAIZ / "rastro/painel" / card
        if pasta.is_dir() and (RAIZ / origem).is_file():
            (pasta / Path(origem).name).write_bytes((RAIZ / origem).read_bytes())


def monta():
    d = livro()
    grava("ui/tokens.css", tokens_css(d))
    for f in sorted((RAIZ / "prototipo/fonte").glob("*.html")):
        corpo = expande(f.read_text("utf-8"))
        grava(f"prototipo/{f.name}", corpo.replace("<!doctype html>", f"<!doctype html>\n<!-- {AVISO} -->", 1))
    if (RAIZ / "design-system/fonte.html").exists():
        import vitrine

        grava("design-system/vitrine.html", vitrine.monta(sys.modules[__name__], d))
    extensao.monta(sys.modules[__name__], d)
    publica()
    print("montado")


if __name__ == "__main__":
    monta()
