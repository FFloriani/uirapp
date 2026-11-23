"""Planta um defeito por vez numa cópia da extensão e exige que scripts/testar.py pegue. Não toca no projeto.

Uso: python testes/defeitos_plantados.py [pedaço do nome]
"""
import re, sys, shutil, tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(RAIZ / "scripts"))
import testar
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8", errors="replace")


class Pegou(BaseException):
    pass


def ok(cond, oque):
    if not cond:
        raise Pegou(oque)


testar.ok = ok
gestos, cega, comb, ataq, flash, falha, janela = (
    lambda n: testar.gestos(n), lambda n: testar.cena_cega(n, None), lambda n: testar.combinacoes(n, None),
    lambda n: testar.ataques(n), lambda n: testar.sem_flash(n), lambda n: testar.falha_fechado(n, None),
    lambda n: testar.janela_real(n, None))
funcoes, ninho = (lambda n: testar.funcoes(n, None)), (lambda n: testar.ninho(n, None))
ia, estatico = (lambda n: testar.ia(n, None)), (lambda n: testar.estatico())

DEFEITOS = [
    ("CSS sem origem USER", "fundo.js", 'origin: "USER"', 'origin: "AUTHOR"', ataq),
    ("pseudo-elemento a vista", "silencio.css", "*::before,", "i::before,", comb),
    ("balao de dica na previa", "silencio.css", "pointer-events: none !important;\n  }", "}", comb),
    ("midia nao volta a esconder", "silencio.css", "html[data-uirapp~=\"parcial\"]:not([data-uirapp~=\"ve-midia\"])", "html[data-nunca]", comb),
    ("marca forjada nao volta", "silencio.js", "new MutationObserver(assinaMarca)", "new MutationObserver(() => {})", ataq),
    ("tecla passa no silencio", "silencio.js", "    e.stopImmediatePropagation();\n    const doNavegador", "    const doNavegador", gestos),
    ("pisca antes de ler", "silencio.js", "  let marca = null;", '  let marca = "aberto"; document.documentElement.setAttribute("data-uirapp", "aberto");', flash),
    ("sem CSS antes da pintura", "manifest.json", '"css": [', '"nada": [', flash),
    ("Enter depois do clique", "silencio.js", "if (e.detail > 0) botao.blur();", "", gestos),
    ("cena depende do conteudo", "silencio.js", "Math.floor((innerHeight - 88) / 76)", "document.querySelectorAll(A.celula).length", cega),
    ("esqueleto com texto passa", "silencio.js", "return estruturaLimpa() ?", "return true ?", falha),
    ("apagar descobre a tela", "popup.js", 'escondido ? ["ajustes", "tecla"] :', 'false ? ["ajustes", "tecla"] :', janela),
    ("evento falso aceito", "nucleo.js", "e.isTrusted && ", "", ataq),
    ("resposta enviada sozinha", "conversa.js", 'return document.execCommand("insertText", false, texto);',
     'const ok = document.execCommand("insertText", false, texto); ed.dispatchEvent(new KeyboardEvent("keydown", { key: "Enter", bubbles: true })); return ok;', funcoes),
    ("backup mexe no Permitir", "ninho.js", "consentido: ajustes.consentido, ", "", ninho),
    ("lembrete no passado", "ninho.js", "!(ms > Date.now())", "false", ninho),
    ("atalho troca sem resposta", "conversa.js", "if (texto) poeNoCampo(R.preenche(texto, contexto()), m[1].length + 1);",
     'poeNoCampo(texto ? R.preenche(texto, contexto()) : "", m[1].length + 1);', funcoes),
    ("tema sem conferir cor", "aparencia.js", "let t = ap.temaDados ? R.cssTema(ap.temaDados) : \"\";",
     "let t = ap.temaDados ? R.cssTema(ap.temaDados) + 'body{visibility:visible!important}#side{background:#ff00ff!important}' : \"\";", funcoes),
    ("IA le a conversa escondida", "conversa.js", 'case "exportar":\n          if (silencio) return responde({ ok: false, motivo: "silencio" }), false;\n',
     'case "exportar":\n', ia),
    ("portugues direto para a IA", "ia.js", 'const pivo = async (l) => (DO_MODELO.includes(l) ? l : "en");', "const pivo = async (l) => l;", ia),
    ("texto entra antes do rascunho", "conversa.js", "const noCampo = sel.rangeCount > 0 && ed.contains(sel.anchorNode);\n    ed.focus();",
     "ed.focus();\n    const noCampo = sel.rangeCount > 0 && ed.contains(sel.anchorNode);", ia),
    ("resultado da IA vira HTML", "popup.js", 'li.querySelector(".ia-texto").textContent = item.texto;', 'li.querySelector(".ia-texto").innerHTML = item.texto;', estatico),
]

if len(sys.argv) > 1:
    DEFEITOS = [d for d in DEFEITOS if any(a in d[0] for a in sys.argv[1:])]
base = Path(tempfile.mkdtemp(prefix="uirapp-planta-"))
pegos = 0
try:
    with sync_playwright() as p:
        for i, (nome, arq, de, para, passo) in enumerate(DEFEITOS):
            ext = base / f"d{i}"
            shutil.copytree(RAIZ / "extensao/uirapp", ext)
            f = ext / arq
            t = f.read_text("utf-8")
            if de not in t:
                print(f"NAO APLICOU  {nome}", flush=True)
                continue
            f.write_text(t.replace(de, para), "utf-8")
            testar.EXT = ext
            n = testar.Navegador(p, "brave")
            try:
                n.ajustes()
                n.poe(silencio=False)
                passo(n)
                print(f"ESCAPOU      {nome}", flush=True)
            except Pegou as e:
                pegos += 1
                print(f"pego         {nome}  <- {str(e)[:130]}", flush=True)
            except Exception as e:
                print(f"ERRO         {nome}  <- {type(e).__name__} {str(e)[:130]}", flush=True)
            finally:
                n.fecha()
finally:
    shutil.rmtree(base, ignore_errors=True)
print(f"{pegos} de {len(DEFEITOS)} pegos")
sys.exit(0 if pegos == len(DEFEITOS) else 1)
