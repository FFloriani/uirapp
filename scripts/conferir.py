"""Confere o design system no navegador de verdade. Sai com 1 se algo falhar.

Uso: python scripts/conferir.py [pasta-para-prints]
"""
import functools
import http.server
import re
import sys
import threading
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.dont_write_bytecode = True
import montar  # noqa: E402
from vitrine import contraste  # noqa: E402

RAIZ = montar.RAIZ
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
falhas, feitos = [], [0]


def ok(cond, oque):
    feitos[0] += 1
    if not cond:
        falhas.append(oque)


def estatico():
    d = montar.livro()
    ok(montar.tokens_css(d) == montar.le("ui/tokens.css"), "tokens.css velho: rode montar.py")
    for nome, dados in montar.extensao.arquivos(montar, d).items():
        f = RAIZ / montar.extensao.SAIDA / nome
        ok(f.is_file() and f.read_bytes() == dados, f"extensão velha ({nome}): rode montar.py")
    for f in (RAIZ / "prototipo/fonte").glob("*.html"):
        novo = montar.expande(f.read_text("utf-8")).replace("<!doctype html>", f"<!doctype html>\n<!-- {montar.AVISO} -->", 1)
        ok(novo == montar.le(f"prototipo/{f.name}"), f"{f.name} velho: rode montar.py")

    for k, v in d["components"].items():
        if "textColor" in v and "backgroundColor" in v:
            n = contraste(montar.resolve(d, v["textColor"]), montar.resolve(d, v["backgroundColor"]))
            ok(n >= 4.5, f"contraste de texto {k}: {n:.2f}")
    c = d["colors"]
    for pref in ("", "noite-"):
        for a, b in (("control", "bg"), ("control", "surface"), ("primary", "bg"), ("primary", "surface"), ("danger", "surface")):
            n = contraste(c[pref + a], c[pref + b])
            ok(n >= 3, f"contraste de controle {pref}{a} x {pref}{b}: {n:.2f}")
    for ceu in ("ceu-aberto", "ceu-silencio", "ceu-neblina", "ceu-alerta"):
        ok(contraste(c["carvao"], c[ceu]) >= 3, f"corpo do pássaro some em {ceu}")

    definidas = set(re.findall(r"(--[\w-]+)\s*:", montar.le("ui/tokens.css") + montar.le("ui/componentes.css")))
    for f in ("ui/componentes.css", "prototipo/popup.css", "prototipo/conversa.css", "extensao/fonte/tela.css"):
        css = re.sub(r"/\*.*?\*/", "", montar.le(f), flags=re.S)
        ok(not re.search(r"#[0-9a-fA-F]{3,8}\b(?=[^{}]*[;}])", css), f"cor solta em {f}")
        for v in set(re.findall(r"var\((--[\w-]+)", css)):
            ok(v in definidas, f"variável {v} não existe ({f})")
    proibido = (r"innerHTML|outerHTML|insertAdjacentHTML|document\.write|\beval\(|new Function|\bfetch\(|XMLHttpRequest"
                r"|WebSocket|sendBeacon|EventSource")
    feitos_js = ["prototipo/demo.js", "prototipo/conversa.js"] + [p.relative_to(RAIZ).as_posix() for p in (RAIZ / "extensao/fonte").glob("*.js")]
    for f in feitos_js:
        ok(not re.search(proibido, montar.le(f)), f"API proibida em {f}")
    for f in ("prototipo/popup.html", "prototipo/conversa.html", "ui/componentes.css", "prototipo/demo.js", "prototipo/conversa.js"):
        ok(not re.search(r"https?://(?!www\.w3\.org)", montar.le(f)), f"endereço externo em {f}")


AUDITA = r"""() => {
  const out = [];
  const num = (s) => {
    const m = s.match(/rgba?\(([^)]+)\)/); if (!m) return null;
    const p = m[1].split(/[ ,/]+/).map(Number); return p.length > 3 && p[3] === 0 ? null : p.slice(0, 3);
  };
  const lum = (c) => { const [r, g, b] = c.map(x => { x /= 255; return x <= .03928 ? x / 12.92 : ((x + .055) / 1.055) ** 2.4 });
    return .2126 * r + .7152 * g + .0722 * b };
  const fundo = (e) => { for (; e; e = e.parentElement) { const c = num(getComputedStyle(e).backgroundColor); if (c) return c }
    return num(getComputedStyle(document.documentElement).backgroundColor) || [255, 255, 255] };
  const visivel = (e) => { const r = e.getBoundingClientRect(); return r.width > 1 && r.height > 1 && getComputedStyle(e).visibility !== "hidden" };
  const modal = document.querySelector("dialog[open]") || document.querySelector(".cobertura:not([hidden])");
  const raiz = modal || document.body;
  const w = document.createTreeWalker(raiz, NodeFilter.SHOW_TEXT);
  for (let n; (n = w.nextNode());) {
    const e = n.parentElement;
    if (!n.textContent.trim() || e.closest("template,script,style,svg,[hidden],dialog:not([open])") || !visivel(e) || e.closest(":disabled")) continue;
    const tinta = num(getComputedStyle(e).color); if (!tinta) continue;
    const a = lum(tinta), b = lum(fundo(e));
    const r = (Math.max(a, b) + .05) / (Math.min(a, b) + .05);
    if (r < 4.5) out.push("contraste " + r.toFixed(2) + ": " + n.textContent.trim().slice(0, 30));
    const s = getComputedStyle(e);
    if (s.display !== "inline" && e.scrollWidth > e.clientWidth + 1 && s.textOverflow !== "ellipsis" && !e.matches(".conteudo"))
      out.push("texto estourou: " + n.textContent.trim().slice(0, 30));
  }
  for (const e of raiz.querySelectorAll("button, label.linha, label.segmento, label.plumagem, input.entrada, textarea")) {
    if (!visivel(e) || e.closest("[hidden],dialog:not([open])")) continue;
    const r = e.getBoundingClientRect();
    if (r.width < 43.5 || r.height < 43.5) out.push("alvo pequeno: " + (e.textContent.trim().slice(0, 25) || e.id));
    const nome = e.textContent.trim() || e.getAttribute("aria-label") || (e.labels && e.labels.length);
    if (!nome) out.push("sem nome acessível: " + (e.id || e.className));
  }
  if (document.documentElement.scrollWidth > innerWidth) out.push("rolagem lateral");
  if (!document.fonts.check('16px "Sofia Sans"')) out.push("fonte não carregou");
  return [...new Set(out)];
}"""

TELAS = ["inicio", "inicio?silencio=1", "inicio?estado=alerta", "inicio?estado=fechado", "inicio?estado=recarregar",
         "inicio?estado=parou", "aparencia", "conversar", "exportar", "assinatura", "novidades", "privacidade", "plumagem",
         "respostas", "respostas?vazio", "respostas?copiada", "nova", "nova?erro", "acesso", "respostas?apagar", "boas-vindas"]


def espera(pg, expressao, prazo=8000):
    """wait_for_function usa eval ao repetir, que a CSP das telas proíbe: pergunta de fora."""
    for _ in range(prazo // 50):
        if pg.evaluate(expressao):
            return True
        pg.wait_for_timeout(50)
    return False


def navegador(prints):
    class Quieto(http.server.SimpleHTTPRequestHandler):
        protocol_version = "HTTP/1.1"  # reaproveita a conexão; em 1.0 cada arquivo gastava um socket do PC

        def log_message(self, *a):
            pass

    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Quieto, directory=str(RAIZ)))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_port}/"
    ruido, fora = [], []
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=CHROME)

        def pagina(larg, alt, esquema="light", **extra):
            ctx = b.new_context(viewport={"width": larg, "height": alt}, color_scheme=esquema, **extra)
            pg = ctx.new_page()
            pg.on("console", lambda m: ruido.append(m.text) if m.type in ("error", "warning") else None)
            pg.on("pageerror", lambda e: ruido.append(str(e)))
            pg.on("request", lambda r: fora.append(r.url) if not r.url.startswith((base, "data:", "about:")) and not r.url.startswith("file:") else None)
            return pg

        def abre(pg, caminho):
            pg.goto("about:blank")
            pg.goto(base + "prototipo/" + caminho)
            if caminho.startswith("popup"):
                ok(espera(pg, "'pronto' in document.documentElement.dataset"), f"{caminho}: a janela não ficou pronta")
            pg.evaluate("document.fonts.ready.then(() => true)")

        # toda tela x tema x plumagem x largura
        for esquema in ("light", "dark"):
            for larg, alt in ((360, 560), (390, 844)):
                pg = pagina(larg, alt, esquema, reduced_motion="reduce")
                for tela in TELAS:
                    for pl in ("vermelha", "laranja", "lenda"):
                        abre(pg, f"popup.html#{tela}{'&' if '?' in tela else '?'}plumagem={pl}")
                        achados = pg.evaluate(AUDITA)
                        ok(not achados, f"{tela} {pl} {esquema} {larg}: {achados}")
                        if tela == "plumagem":
                            fill = "es => new Set(es.map(e => getComputedStyle(e).fill)).size"
                            ok(pg.eval_on_selector_all(".plumagem .p-cabeca", fill) == 3, f"amostras iguais com {pl} escolhida")
                pg.context.close()
            for larg, alt in ((1440, 900), (800, 600), (390, 844)):
                pg = pagina(larg, alt, esquema, reduced_motion="reduce")
                for tela in ("aberta", "silencio", "cobertura"):
                    abre(pg, f"conversa.html#{tela}")
                    achados = pg.evaluate(AUDITA)
                    ok(not achados, f"conversa {tela} {esquema} {larg}: {achados}")
                pg.context.close()

        # tema escolhido vence o do sistema
        for esquema, tema, esperado in (("dark", "dia", "rgb(244, 247, 248)"), ("light", "noite", "rgb(24, 36, 46)")):
            pg = pagina(360, 560, esquema)
            abre(pg, f"popup.html#inicio?tema={tema}")
            ok(pg.evaluate("getComputedStyle(document.documentElement).backgroundColor") == esperado, f"tema {tema} não venceu")
            pg.context.close()

        # fluxo inteiro só com teclado
        pg = pagina(360, 560, reduced_motion="reduce", permissions=["clipboard-read", "clipboard-write"])
        abre(pg, "popup.html#inicio")
        titulo = lambda: pg.text_content("#palco-titulo")
        pg.keyboard.press("Tab")
        ok(pg.evaluate("document.activeElement.id") == "silencio", "1º Tab não cai na ação principal")
        ok(pg.evaluate("getComputedStyle(document.activeElement).outlineStyle") == "solid", "foco não aparece")
        pg.keyboard.press("Enter")
        ok(titulo() == "Conversas escondidas", "Enter não escondeu")
        ok(pg.get_attribute("#palco", "data-humor") == "silencio", "olho não fechou")
        ok(pg.evaluate("getComputedStyle(document.querySelector('#palco')).transitionDuration").split(",")[0].strip() == "0s",
           "movimento reduzido ignorado")
        pg.keyboard.press("Alt+KeyS")
        ok(titulo() == "Conversas à vista", "Alt+S não mostrou")
        for _ in range(3):
            pg.keyboard.press("Tab")
        pg.keyboard.press("Enter")
        ok(pg.is_visible('[data-tela="respostas"]'), "Tab até Respostas falhou")
        ok(pg.evaluate("document.activeElement.id") == "t-respostas", "foco não foi para o título")
        pg.focus('[data-tela="respostas"] .rodape button')
        pg.keyboard.press("Enter")
        pg.focus('#form-resposta [type="submit"]')
        pg.keyboard.press("Enter")
        ok(pg.is_visible("#e-nome") and pg.evaluate("document.activeElement.id") == "r-nome", "erro do campo não apareceu com foco")
        marca_texto = "<b>não vira negrito</b>"
        pg.keyboard.type(marca_texto)
        pg.keyboard.press("Tab")
        ok(pg.evaluate("document.activeElement.id") == "r-atalho", "depois do nome não vem o atalho")
        pg.keyboard.press("Tab")
        pg.keyboard.type(marca_texto)
        pg.keyboard.press("Tab")
        pg.keyboard.press("Enter")
        ok("{saudacao}" in pg.input_value("#r-texto"), "botão de variável não põe no texto")
        pg.fill("#r-texto", marca_texto)
        pg.focus('#form-resposta [type="submit"]')
        pg.keyboard.press("Enter")
        ok(pg.locator("#lista-respostas li").count() == 4, "resposta não salvou")
        ok(pg.locator("#lista-respostas b").count() == 0, "texto digitado virou HTML")
        ok(pg.locator("#lista-respostas li").last.inner_text().count(marca_texto) == 2, "texto digitado mudou")
        pg.locator(".resposta-copiar").last.focus()
        pg.keyboard.press("Enter")
        ok(espera(pg, "document.querySelector('#aviso-texto').textContent === 'Resposta copiada'"), "cópia não avisou")
        ok(pg.evaluate("navigator.clipboard.readText()") == marca_texto, "não copiou")
        pg.locator(".resposta-apagar").last.focus()
        pg.keyboard.press("Enter")
        ok(pg.evaluate("document.activeElement.id") == "dialogo-manter", "apagar não começa em Manter")
        pg.keyboard.press("Tab")
        pg.keyboard.press("Enter")
        ok(pg.locator("#lista-respostas li").count() == 3, "não apagou")
        abre(pg, "popup.html#plumagem")
        pg.focus('[name="plumagem"][value="vermelha"]')
        pg.keyboard.press("ArrowRight")
        ok(pg.get_attribute("html", "data-plumagem") == "laranja", "seta não troca plumagem")
        pg.context.close()

        # silêncio esconde de verdade
        pg = pagina(1100, 700, reduced_motion="reduce")
        abre(pg, "conversa.html#aberta")
        pg.click("#flutuante")
        texto = pg.inner_text("#mensageiro")
        for segredo in ("Marina", "Fechado", "R$", "Oficina", "pão", "comprovante", "MP", "42"):
            ok(segredo not in texto, f"silêncio deixou ler: {segredo}")
        pg.keyboard.press("Control+A")
        ok("Marina" not in pg.evaluate("getSelection().toString()"), "silêncio deixou selecionar")
        larg = set(pg.eval_on_selector_all(".lista .contato-nome", "es => es.map(e => Math.round(e.getBoundingClientRect().width))"))
        ok(len(larg) == 1, f"tarja entrega o tamanho do nome: {larg}")
        ok(pg.evaluate("[...document.querySelectorAll('.silencio [data-tarja=linha]')].every(e => getComputedStyle(e).textOverflow === 'clip')"),
           "reticências escapam da tarja")
        ok(pg.evaluate("[...document.querySelectorAll('.silencio .foto > .passaro')].every(e => getComputedStyle(e).display === 'block')"),
           "foto não virou pássaro")
        abre(pg, "conversa.html#cobertura")
        ok(pg.evaluate("document.querySelector('#mensageiro').inert"), "cobertura deixa usar o que está atrás")
        ok(pg.evaluate("document.elementFromPoint(20, 20).closest('.cobertura') !== null"), "cobertura não cobre")
        pg.context.close()

        # vitrine abre sozinha, sem servidor
        for larg, alt in ((1440, 900), (390, 844)):
            pg = pagina(larg, alt, reduced_motion="reduce")
            pg.goto((RAIZ / "design-system/vitrine.html").as_uri())
            pg.wait_for_timeout(2500)
            ok(pg.evaluate("document.documentElement.scrollWidth <= innerWidth"), f"vitrine rola de lado em {larg}")
            ok(pg.evaluate("scrollY") == 0, f"vitrine abre rolada em {larg}")
            if larg == 1440:
                quadros = pg.locator("iframe")
                for i in range(quadros.count()):
                    quadros.nth(i).scroll_into_view_if_needed()
                    dentro = pg.frame_locator("iframe").nth(i).locator("main").inner_text()
                    ok(len(dentro.strip()) > 5 or i == 1, f"quadro {i} da vitrine vazio")
                    if prints:
                        pg.wait_for_timeout(250)
                        quadros.nth(i).screenshot(path=str(prints / f"quadro-{i:02d}.png"))
                jan = pg.frame_locator("iframe").first
                jan.locator("#silencio").click()
                ok(jan.locator("#palco-titulo").text_content() == "Conversas escondidas", "janela da vitrine não funciona")
            if prints:
                if larg == 1440:
                    jan.locator("#silencio").click()
                    pg.mouse.move(5, 5)
                pg.evaluate("scrollTo(0, 0)")
                pg.wait_for_timeout(300)
                pg.screenshot(path=str(prints / f"vitrine-{larg}.png"), full_page=True)
                pg.screenshot(path=str(prints / f"vitrine-{larg}-topo.png"))
            pg.context.close()
        b.close()
    srv.shutdown()
    ok(not ruido, f"console: {sorted(set(ruido))[:6]}")
    ok(not fora, f"rede externa: {sorted(set(fora))[:6]}")


if __name__ == "__main__":
    pasta = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    if pasta:
        pasta.mkdir(parents=True, exist_ok=True)
    estatico()
    navegador(pasta)
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print(f"{feitos[0]} conferências, {len(falhas)} falhas")
    for f in falhas[:50]:
        print(" -", f)
    sys.exit(1 if falhas else 0)
