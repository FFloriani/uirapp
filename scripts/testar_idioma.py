"""Confere que toda frase das telas do Uirapp tem inglês e espanhol em extensao/fonte/frases.js.

Uso: python scripts/testar_idioma.py [--lista]   (--lista mostra as frases que faltam, uma por linha)
"""
import html.parser
import json
import re
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
EXT = RAIZ / "extensao/uirapp"
# não se traduz: marca, tecla, sigla, exemplo de número e o que é igual nos três idiomas
IGUAIS = {"Uirapp", "Alt+S", "PT", "EN", "ES", "Pix", "R$ 0,00", "/horario", "(11) 91234-5678", "Ninho", "Auto"}


class Frases(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.achadas, self.pilha = set(), []

    def handle_starttag(self, tag, attrs):
        if tag not in ("br", "img", "input", "meta", "link", "path", "circle", "source"):
            self.pilha.append(tag)
        for nome, valor in attrs:
            if nome in ("aria-label", "placeholder", "title") and valor:
                self.achadas.add(valor.strip())

    def handle_endtag(self, tag):
        if tag in self.pilha:
            while self.pilha and self.pilha.pop() != tag:
                pass

    def handle_data(self, data):
        if self.pilha and self.pilha[-1] in ("script", "style", "title", "svg", "textarea"):
            return
        if "svg" in self.pilha:
            return
        if data.strip():
            self.achadas.add(data.strip())


def frases_das_telas():
    achadas = set()
    for pagina in ("popup.html", "ninho.html"):
        p = Frases()
        p.feed((EXT / pagina).read_text("utf-8"))
        achadas |= p.achadas
    for js in ("popup.js", "ninho.js", "silencio.js"):
        t = (EXT / js).read_text("utf-8")
        achadas |= set(re.findall(r'\bT\("([^"\n]+)"\)', t))
        for linha in t.splitlines():
            if re.search(r"\b(avisa|confirma|T)\(|MOTIVOS|\[visual, titulo|titulo\.textContent|acao\.textContent|const verbo", linha):
                achadas |= {s for s in re.findall(r'"([^"\n]{3,})"', linha) if re.match(r"[A-ZÀ-Ú]", s) and " " in s}
    achadas |= set(re.findall(r'nome: "([^"]+)"', (EXT / "regras.js").read_text("utf-8")))
    achadas |= set(re.findall(r'"([A-ZÀ-Ú][^"]+)"', re.search(r"PLUMAGENS = Object\.freeze\(\{([^}]+)\}", (EXT / "nucleo.js").read_text("utf-8")).group(1)))
    return {a for a in achadas if a not in IGUAIS and not re.fullmatch(r"[\d\s:+/.,()-]+", a) and not a.startswith("{")}


def dicionario():
    codigo = "const fs=require('fs');globalThis.Object=Object;eval(fs.readFileSync(process.argv[1],'utf8'));" \
             "process.stdout.write(JSON.stringify(globalThis.UirappFrases))"
    saida = subprocess.run(["node", "-e", codigo, str(RAIZ / "extensao/fonte/frases.js")], capture_output=True, text=True, encoding="utf-8")
    if saida.returncode:
        raise SystemExit(saida.stderr)
    return json.loads(saida.stdout)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    frases = frases_das_telas()
    d = dicionario()
    faltam = sorted(f for f in frases if f not in d)
    tortas = sorted(k for k, v in d.items() if not (isinstance(v, list) and len(v) == 2 and all(isinstance(x, str) and x.strip() for x in v)))
    variaveis = sorted(k for k, v in d.items() if isinstance(v, list) and any(set(re.findall(r"\{\w+\}", x)) != set(re.findall(r"\{\w+\}", k)) for x in v))
    if "--lista" in sys.argv:
        print("\n".join(faltam))
        sys.exit(0)
    print(f"{len(frases)} frases nas telas, {len(d)} no dicionário, faltam {len(faltam)}, tortas {len(tortas)}, variável trocada {len(variaveis)}")
    for f in (faltam + tortas + variaveis)[:40]:
        print(" -", f)
    sys.exit(1 if faltam or tortas or variaveis else 0)
