"""Prova a IA no computador com o modelo de verdade: a extensão montada, num Chrome com o Gemini Nano já baixado.

Uso: python scripts/provar_ia.py PERFIL [--prints PASTA] [--imagem]
  PERFIL  pasta de um perfil de teste do Chrome que fica (não use o seu perfil de todo dia). Na primeira vez o
          Chrome baixa cerca de 4 GB nele; depois a prova roda sem internet.
Abre o Ninho, prepara a IA com um clique de verdade e roda resumir, sugerir, traduzir e reescrever numa conversa
de exemplo em português. Mostra o resultado e o tempo de cada um. Sai com 1 se algo falhar.
  --imagem  também refaz docs/imagens/readme-ia.png: a janela de verdade com o que o modelo respondeu.
"""
import json
import re
import shutil
import sys
import tempfile
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = Path(__file__).resolve().parent.parent
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

CONVERSA = [
    {"autor": "Juliana Costa", "texto": "Oi! Vocês fazem bolo de casamento para 120 pessoas?", "tipo": "texto", "de": ""},
    {"autor": "Loja", "texto": "Fazemos sim! Para quando seria?", "tipo": "texto", "de": "eu"},
    {"autor": "Juliana Costa", "texto": "Dia 14 de dezembro, num sábado. Queria massa branca com recheio de doce de leite e morango.", "tipo": "texto", "de": ""},
    {"autor": "Juliana Costa", "texto": "", "tipo": "foto", "de": ""},
    {"autor": "Juliana Costa", "texto": "Quanto fica mais ou menos? E vocês entregam em Pinhais?", "tipo": "texto", "de": ""},
    {"autor": "Loja", "texto": "Para 120 pessoas fica em torno de R$ 1.800. Vou confirmar a entrega.", "tipo": "texto", "de": "eu"},
    {"autor": "Juliana Costa", "texto": "Ótimo. Consigo fazer uma degustação antes? Pode ser na semana que vem, à tarde.", "tipo": "texto", "de": ""},
]
RASCUNHO = "oi juliana, a gente consegue sim fazer a degustacao na terça as 15h, pode ser? abraço"

RODA = """async ([conversa, rascunho]) => {
  const IA = globalThis.UirappIA, r = {}, tempo = {};
  const mede = async (nome, f) => { const t0 = performance.now(); try { r[nome] = await f(); } catch (e) { r[nome] = 'ERRO ' + e.name + ': ' + e.message; } tempo[nome] = Math.round(performance.now() - t0); };
  await mede('resumir', () => IA.resumir(conversa, 'pt'));
  await mede('sugerir', () => IA.sugerir(conversa, 'pt'));
  await mede('traduzirConversa', async () => (await IA.traduzirConversa(conversa, 'en')).map(m => m.traducao || m.texto));
  await mede('educado', () => IA.reescrever(rascunho, 'educado', 'pt'));
  await mede('curto', () => IA.reescrever(rascunho, 'curto', 'pt'));
  return { r, tempo };
}"""
# idioma novo pede o clique da pessoa, como o botão Traduzir da janela
CLIQUE_ESPANHOL = """([rascunho]) => { window._es = new Promise((fim) => addEventListener('click', () => {
  const t0 = performance.now();
  UirappIA.traduzirTexto(rascunho, 'es', 'pt').then((v) => fim([v, Math.round(performance.now() - t0)]), (e) => fim(['ERRO ' + e.name + ': ' + e.message, 0]));
}, { once: true })); }"""

falhas = []


def espera(pg, expressao, prazo):
    """wait_for_function usa eval, que a CSP da extensão proíbe: pergunta de fora, de tempos em tempos."""
    fim = time.time() + prazo
    while time.time() < fim:
        if pg.evaluate(expressao):
            return
        pg.wait_for_timeout(200)
    raise TimeoutError(expressao)


def ok(cond, oque):
    if not cond:
        falhas.append(oque)
        print("  FALHA", oque)


def conversa_em_portugues(html):
    """O WhatsApp de mentira dos testes, com uma conversa de verdade no lugar dos códigos."""
    textos = {
        0: ("Juliana Costa", "Oi! Vocês fazem bolo de casamento para 120 pessoas? Seria para 14 de dezembro."),
        2: ("Loja", "Fazemos sim! Massa branca com doce de leite e morango fica em torno de R$ 1.800."),
        3: ("Juliana Costa", "Ótimo! Consigo fazer uma degustação antes? Pode ser na semana que vem, à tarde."),
    }
    lados = iter(["message-in", "message-in", "message-out", "message-in"])
    html = re.sub(r"linha-msg message-(?:in|out)", lambda m: f"linha-msg {next(lados)}", html)
    for i, (autor, texto) in textos.items():
        html = re.sub(rf"MENSQa{i}(?: palavras)*", texto, html).replace(f"AUTORQa{i}", autor).replace(f"MENCQa{i}", "")
    return html.replace("NOMEQa99", "Juliana Costa").replace("CITAQa2", textos[0][1]).replace("MENSQarascunho", "")


def imagem(ctx, eid):
    """docs/imagens/readme-ia.png: a janela de verdade com o resumo e as sugestões que o modelo escreveu agora."""
    sys.path.insert(0, str(RAIZ / "testes"))
    sys.path.insert(0, str(RAIZ / "scripts"))
    import whatsapp_falso as falso
    from imagens_readme import FUNDO, cola_com_sombra, png
    from PIL import Image

    ctx.route("https://web.whatsapp.com/**", lambda rota: rota.fulfill(
        status=200, content_type="text/html; charset=utf-8", headers={"content-security-policy": falso.CSP},
        body=conversa_em_portugues(falso.pagina(v="a"))) if rota.request.url.rstrip("/").endswith("whatsapp.com") else rota.fulfill(status=204, body=""))
    ctx.route("https://*.whatsapp.net/**", lambda rota: rota.fulfill(status=200, content_type="image/png", body=falso.IMAGENS["foto"]))
    janela = ctx.new_page()
    janela.set_viewport_size({"width": 360, "height": 551})
    # a janela de verdade não tem barra de rolagem fixa; a aba aberta pelo teste tem
    ctx.new_cdp_session(janela).send("Emulation.setScrollbarsHidden", {"hidden": True})
    janela.goto(f"chrome-extension://{eid}/popup.html")
    janela.evaluate("v => chrome.storage.local.set({ ajustes: { consentido: true, visto: v, tema: 'dia' }, silencio: false })",
                    json.loads((RAIZ / "extensao/uirapp/manifest.json").read_text("utf-8"))["version"])
    wa = ctx.new_page()
    wa.goto("https://web.whatsapp.com/")
    wa.wait_for_timeout(1500)
    telas = []
    for acao in ("", "resumir", "sugerir"):
        janela.bring_to_front()
        janela.goto(f"chrome-extension://{eid}/popup.html")
        espera(janela, "'pronto' in document.documentElement.dataset", 15)
        janela.click('.menu [data-ir="ia"]')
        espera(janela, "!document.querySelector('#ia-acoes').hidden", 10)
        if acao:
            janela.click(f'[data-ia="{acao}"]')
            espera(janela, "document.querySelectorAll('#ia-lista .ia-item').length > 0 || document.querySelector('#aviso:not([hidden])')", 60)
            ok(janela.locator("#ia-lista .ia-item").count() > 0, f"a janela não mostrou o resultado de {acao}: {janela.text_content('#aviso-texto')}")
        janela.wait_for_timeout(400)
        telas.append(png(janela.screenshot(animations="disabled")))
    m = 40
    faixa = Image.new("RGB", (3 * telas[0].width + 4 * m, telas[0].height + 2 * m), FUNDO)
    for i, tela in enumerate(telas):
        cola_com_sombra(faixa, tela, (m + i * (tela.width + m), m))
    destino = RAIZ / "docs/imagens/readme-ia.png"
    faixa.save(destino, optimize=True)
    print("imagem:", destino.relative_to(RAIZ), faixa.size)


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    perfil = Path(sys.argv[1]).resolve()
    prints = Path(sys.argv[sys.argv.index("--prints") + 1]) if "--prints" in sys.argv else None
    base = Path(tempfile.mkdtemp(prefix="uirapp-provar-"))
    ext = base / "extensao"
    shutil.copytree(RAIZ / "extensao/uirapp", ext)
    try:
        with sync_playwright() as p:
            # o Playwright desliga o "OptimizationHints" (é por ele que o Chrome entrega o modelo), os testes de campo e
            # a atualização de componentes: com isso o modelo fica "unavailable" mesmo baixado. Tira só essas opções;
            # a lista exata de recursos desligados se lê no próprio Chrome, porque muda com a versão do Playwright.
            sonda = p.chromium.launch(executable_path=CHROME)
            pg0 = sonda.new_page()
            pg0.goto("chrome://version")
            desligados = next(a for a in pg0.inner_text("#command_line").split() if a.startswith("--disable-features=") and "OptimizationHints" in a)
            sonda.close()
            ctx = p.chromium.launch_persistent_context(
                str(perfil), executable_path=CHROME, headless=False, viewport={"width": 1180, "height": 760},
                ignore_default_args=["--disable-extensions", "--disable-component-update", "--disable-field-trial-config",
                                     "--disable-background-networking", desligados],
                args=["--enable-unsafe-extension-debugging", "--no-first-run", "--window-position=-1900,40"])
            eid = ctx.browser.new_browser_cdp_session().send("Extensions.loadUnpacked", {"path": str(ext)})["id"]
            pg = ctx.new_page()
            pg.goto(f"chrome-extension://{eid}/ninho.html#ia")
            espera(pg, "'pronto' in document.documentElement.dataset", 15)
            pg.wait_for_timeout(800)
            print("antes:", pg.text_content("#ia-situacao").strip(), "|", " · ".join(pg.eval_on_selector_all("#ia-partes li", "l => l.map(e => e.innerText.replace(/\\n/g, ': '))")))
            for volta in range(4):
                if pg.is_hidden("#ia-preparar"):
                    break
                pg.click("#ia-preparar")
                espera(pg, "!document.querySelector('#ia-preparar').disabled", 1800)
                pg.wait_for_timeout(500)
                print(f"clique {volta + 1}:", pg.text_content("#ia-situacao").strip())
            ok(pg.is_hidden("#ia-preparar"), "a IA não ficou pronta no Ninho")
            if prints:
                prints.mkdir(parents=True, exist_ok=True)
                pg.screenshot(path=str(prints / "ninho-ia-real.png"))
            saida = pg.evaluate(RODA, [CONVERSA, RASCUNHO])
            pg.evaluate(CLIQUE_ESPANHOL, [RASCUNHO])
            pg.mouse.click(600, 700)
            saida["r"]["paraEspanhol"], saida["tempo"]["paraEspanhol"] = pg.evaluate("window._es")
            print(json.dumps(saida, ensure_ascii=False, indent=1))
            r = saida["r"]
            for k, v in r.items():
                ok(v and not (isinstance(v, str) and v.startswith("ERRO")), f"{k}: {str(v)[:160]}")
            ok(isinstance(r["sugerir"], list) and len(r["sugerir"]) == 3, "não vieram 3 sugestões")
            ok(isinstance(r["resumir"], list) and len(r["resumir"]) >= 2, "resumo com menos de 2 pontos")
            if "--imagem" in sys.argv:
                imagem(ctx, eid)
            ctx.close()
    finally:
        time.sleep(1)
        shutil.rmtree(base, ignore_errors=True)
    print("0 falhas" if not falhas else f"{len(falhas)} falhas")
    sys.exit(1 if falhas else 0)


if __name__ == "__main__":
    main()
