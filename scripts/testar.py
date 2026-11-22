"""Testa a extensão de verdade, em Brave e Chrome com perfil descartável e um WhatsApp de mentira.

Uso: python scripts/testar.py [brave|chrome] [--parado] [--prints PASTA]
  --parado   espera os 5 minutos de verdade do "Ao ficar 5 min parado".
Nada sai para a internet, nada toca o navegador do dono. Sai com 1 se algo falhar.
"""
import base64
import io
import itertools
import json
import re
import shutil
import sys
import tempfile
import urllib.parse
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

sys.dont_write_bytecode = True
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "testes"))
import whatsapp_falso as falso  # noqa: E402

EXT = RAIZ / "extensao/uirapp"
NAVEGADORES = {
    "brave": str(Path.home() / r"AppData\Local\BraveSoftware\Brave-Browser\Application\brave.exe"),
    "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
}
WA = "https://web.whatsapp.com/"
LARG, ALT = 1280, 800
BOTAO = (LARG - 16 - 28, ALT - 88 - 28)
CATS = ("mensagens", "previas", "nomes", "fotos", "midia")

falhas, feitos = [], [0]


def ok(cond, oque):
    feitos[0] += 1
    if not cond:
        falhas.append(oque)
        print("  FALHA", oque, flush=True)


def estatico():
    man = json.loads((EXT / "manifest.json").read_text("utf-8"))
    ok(man["permissions"] == ["storage", "scripting", "contextMenus", "alarms", "notifications"], "permissão a mais")
    ok(man["host_permissions"] == ["https://web.whatsapp.com/*"], "site a mais")
    for chave in ("web_accessible_resources", "externally_connectable", "update_url", "optional_permissions", "declarative_net_request"):
        ok(chave not in man, f"manifesto com {chave}")
    ok(all("world" not in c for c in man["content_scripts"]), "script no mundo da página")
    ok("connect-src 'none'" in man["content_security_policy"]["extension_pages"], "páginas da extensão podem conectar")
    proibido = {
        "rede": r"\bfetch\(|XMLHttpRequest|WebSocket|sendBeacon|EventSource|RTCPeerConnection|new Image\(",
        "HTML com texto": r"innerHTML|outerHTML|insertAdjacentHTML|document\.write|parseFromString|setHTMLUnsafe",
        "código dinâmico": r"\beval\(|new Function|import\(|executeScript|registerContentScripts",
        "ponte com a página": r"postMessage|CustomEvent|dispatchEvent|onMessageExternal|onConnectExternal",
        "saída na desinstalação": r"setUninstallURL",
    }
    for f in EXT.glob("*.js"):
        t = re.sub(r'"fonte":"[^"]+"', "", f.read_text("utf-8"))
        for nome, rx in proibido.items():
            ok(not re.search(rx, t), f"{nome} em {f.name}")
    dentro = (EXT / "silencio.js").read_text("utf-8")
    for rx in (r"\.click\(", r"\.submit\(", r"requestSubmit", r"execCommand", r"\.value\s*=", r"indexedDB", r"document\.cookie", r"localStorage", r"innerText"):
        ok(not re.search(rx, dentro), f"age ou lê demais na conta: {rx}")
    conversa = (EXT / "conversa.js").read_text("utf-8")
    for rx in (r"[\"']Enter[\"']", r"\.submit\(", r"requestSubmit", r"compose-btn-send", r"innerText", r"localStorage", r"indexedDB", r"document\.cookie"):
        ok(not re.search(rx, conversa), f"a ajuda da conversa age ou lê demais: {rx}")
    ok(len(re.findall(r"\.click\(", conversa)) == 1 and "a.click(); // âncora nossa" in conversa, "a ajuda da conversa clica em algo da página")
    for f in ("aparencia.js", "silencio.js"):
        ok("execCommand" not in (EXT / f).read_text("utf-8"), f"{f} escreve na conversa")
    for f in EXT.rglob("*"):
        if f.suffix in (".js", ".css", ".html", ".json"):
            achou = set(re.findall(r"https?://[^\s\"'<>)`]+", f.read_text("utf-8")))
            fora = {u for u in achou if not u.startswith(("http://www.w3.org", "https://web.whatsapp.com/"))}
            ok(not fora, f"endereço de fora em {f.name}: {fora}")


def espera_pronta(pg, prazo=10000):
    """wait_for_function usa eval, que a CSP da extensão proíbe: pergunta de fora."""
    for _ in range(prazo // 50):
        if pg.evaluate("'pronto' in document.documentElement.dataset"):
            return
        pg.wait_for_timeout(50)
    raise TimeoutError("a janela não ficou pronta")


class Navegador:
    def __init__(self, p, nome):
        self.nome, self.pedidos, self.erros = nome, [], []
        self.base = Path(tempfile.mkdtemp(prefix="uirapp-teste-"))
        self.ext = self.base / "extensao"
        shutil.copytree(EXT, self.ext)
        padrao = self.base / "perfil" / "Default"
        padrao.mkdir(parents=True)
        (padrao / "Preferences").write_text(json.dumps({"extensions": {"ui": {"developer_mode": True}}}), "utf-8")
        args = ["--enable-unsafe-extension-debugging", "--no-first-run", "--no-default-browser-check",
                "--host-resolver-rules=MAP * ~NOTFOUND"]
        if nome == "brave":
            args += [f"--disable-extensions-except={self.ext}", f"--load-extension={self.ext}"]
        self.ctx = p.chromium.launch_persistent_context(
            str(self.base / "perfil"), executable_path=NAVEGADORES[nome], headless=True, color_scheme="light",
            viewport={"width": LARG, "height": ALT}, ignore_default_args=["--disable-extensions"], args=args)
        self.pagina = {"v": "a"}
        self.ctx.route("https://web.whatsapp.com/**", self._site)
        self.ctx.route("https://*.whatsapp.net/**", self._imagem)
        self.ctx.on("request", lambda r: self.pedidos.append(r.url))
        try:
            self._prepara()
        except Exception:
            self.fecha()
            raise

    def _prepara(self):
        nome = self.nome
        self.cdp = self.ctx.browser.new_browser_cdp_session()
        self.wa = self.ctx.pages[0]
        self.wa.on("pageerror", lambda e: self.erros.append(str(e)))
        self.wa.on("console", lambda m: self.erros.append(m.text) if m.type == "error" and "ERR_FAILED" not in m.text else None)
        self.antiga = False
        if nome == "chrome":
            self.abre()  # aba que já estava aberta antes de instalar
            self.antiga = True
            self.id = self.cdp.send("Extensions.loadUnpacked", {"path": str(self.ext)})["id"]
        else:
            sw = self.ctx.service_workers or [self.ctx.wait_for_event("serviceworker", timeout=15000)]
            self.id = urllib.parse.urlparse(sw[0].url).netloc
        # sem o Modo do desenvolvedor de verdade (o Preferences sozinho não segura), recarregar desliga a extensão
        ajuste = self.ctx.new_page()
        ajuste.goto("chrome://extensions/")
        ajuste.evaluate("chrome.developerPrivate.updateProfileConfiguration({inDeveloperMode: true})")
        ajuste.close()
        self.janela = self.ctx.new_page()
        self.janela.on("pageerror", lambda e: self.erros.append(str(e)))
        self.abre_janela()

    def _site(self, rota):
        if urllib.parse.urlparse(rota.request.url).path not in ("/", "/send"):
            return rota.fulfill(status=204, body="")
        rota.fulfill(status=200, content_type="text/html; charset=utf-8",
                     headers={"content-security-policy": falso.CSP}, body=falso.pagina(**self.pagina))

    def _imagem(self, rota):
        qual = "foto" if "foto" in rota.request.url else "midia"
        rota.fulfill(status=200, content_type="image/png", body=falso.IMAGENS[qual])

    def abre_janela(self):
        if self.janela.is_closed():  # "Abrir conversa" fecha a janela, como no navegador
            self.janela = self.ctx.new_page()
            self.janela.on("pageerror", lambda e: self.erros.append(str(e)))
        self.janela.set_viewport_size({"width": 360, "height": 560})
        self.janela.goto(f"chrome-extension://{self.id}/popup.html")
        espera_pronta(self.janela)

    def abre(self, **pagina):
        if pagina:
            self.pagina = pagina
        self.wa.bring_to_front()
        self.wa.goto(WA)
        self.wa.wait_for_timeout(500)

    def poe(self, **dado):
        self.janela.evaluate("d => chrome.storage.local.set(d)", dado)
        self.wa.wait_for_timeout(120)

    def ajustes(self, mostra=(), **resto):
        versao = json.loads((self.ext / "manifest.json").read_text("utf-8"))["version"]
        self.poe(ajustes={"consentido": True, "visto": versao, "esconder": {c: c not in mostra for c in CATS}, "tema": "dia", **resto})

    def guardado(self):
        return self.janela.evaluate("chrome.storage.local.get(null)")

    def marca(self):
        return self.wa.evaluate("document.documentElement.getAttribute('data-uirapp') || ''")

    def foto(self):
        self.wa.bring_to_front()
        self.wa.mouse.move(700, 3)
        self.wa.wait_for_timeout(450)
        return self.wa.screenshot(animations="disabled")

    def fecha(self):
        try:
            self.ctx.close()
        finally:
            shutil.rmtree(self.base, ignore_errors=True)


VE = """() => {
  const achou = new Set();
  const rx = new RegExp('(%s)', 'g');
  const opaco = e => { for (; e; e = e.parentElement) if (+getComputedStyle(e).opacity === 0) return false; return true };
  const visivel = (e, p) => getComputedStyle(e, p).visibility === 'visible' && opaco(e);
  const soma = t => { for (const m of String(t).matchAll(rx)) achou.add(m[1]) };
  const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  for (let n; (n = w.nextNode());) {
    const e = n.parentElement;
    if (e.closest('script,style,head') || !e.getClientRects().length || !visivel(e)) continue;
    soma(n.nodeValue);
  }
  for (const e of document.body.querySelectorAll('*')) {
    for (const p of ['::before', '::after']) { const s = getComputedStyle(e, p); if (s.content !== 'none' && visivel(e, p)) soma(s.content) }
    if (e.matches('input,textarea') && visivel(e)) soma(e.value);
    if (e.shadowRoot && visivel(e)) soma(e.shadowRoot.textContent);
    if (e.localName === 'iframe' && visivel(e)) soma(e.srcdoc);
  }
  return [...achou].sort();
}""" % "|".join(falso.CODIGOS)

DICAS = """() => {
  const achou = new Set();
  for (let x = 4; x < innerWidth; x += 12) for (let y = 4; y < innerHeight; y += 8) {
    const t = document.elementFromPoint(x, y)?.closest('[title]')?.getAttribute('title');
    const m = t && t.match(/^[A-Z]+Q/);
    if (m) achou.add(m[0]);
  }
  return [...achou].sort();
}"""


REAL = """() => {
  const ve = e => getComputedStyle(e).visibility === 'visible';
  const citas = [...document.querySelectorAll('#main .cita')];
  const fotos = [...document.querySelectorAll('#main [data-testid=group-chat-profile-picture]')];
  return {totalCitadas: citas.length, citadas: citas.filter(ve).length,
    rodape: ve(document.querySelector('#main footer')),
    sticky: fotos.every(e => getComputedStyle(e).position === 'sticky'),
    passaro: fotos.every(e => {
      const s = getComputedStyle(e, '::after');
      return s.content !== 'none' && s.visibility === 'visible' && s.backgroundImage !== 'none' && parseFloat(s.width) <= 28;
    })};
}"""


def cores(foto):
    n = {"foto": 0, "midia": 0, "emoji": 0}
    im = Image.open(io.BytesIO(foto)).convert("RGB")
    for q, (r, g, b) in im.getcolors(1 << 24):
        if r > 225 and b > 225 and g < 40:
            n["foto"] += q
        elif g > 225 and r < 40 and b < 40:
            n["midia"] += q
        elif g > 225 and b > 225 and r < 40:
            n["emoji"] += q
    return n


def nada_vaza(n, caso):
    t = n.wa.evaluate(VE)
    ok(not t, f"{n.nome} {caso}: texto à vista {t}")
    c = cores(n.foto())
    ok(c == {"foto": 0, "midia": 0, "emoji": 0}, f"{n.nome} {caso}: imagem à vista {c}")


def primeira_vez(n, prints):
    j, w = n.janela, n.wa
    n.abre_janela()
    ok(j.is_visible('[data-tela="boas-vindas"]'), f"{n.nome}: não começa nas boas-vindas")
    if prints:
        j.screenshot(path=str(prints / f"{n.nome}-boas-vindas.png"))
    if n.antiga:
        j.click('[data-tela="boas-vindas"] [data-ir="acesso"]')
        j.click('[data-tela="acesso"] [data-ir="inicio"]')
        ok(j.is_visible('[data-tela="boas-vindas"]'), f"{n.nome}: pulou o Permitir pelo Voltar")
    else:
        n.abre(v="a")
        ok(n.marca() == "aberto", f"{n.nome}: agiu antes do Permitir ({n.marca()})")
        ok(w.locator("uirapp-casa").count() == 0, f"{n.nome}: botão antes do Permitir")
        w.keyboard.press("Alt+KeyS")
        ok(n.marca() == "aberto" and "silencio" not in n.guardado(), f"{n.nome}: atalho antes do Permitir")
    j.bring_to_front()
    j.click("#permitir")
    ok(j.is_visible('[data-tela="inicio"]'), f"{n.nome}: Permitir não abre o início")
    if n.antiga:
        j.wait_for_timeout(1300)
        ok(j.text_content("#palco-titulo") == "Falta recarregar", f"{n.nome}: aba antiga não avisou")
        if prints:
            j.screenshot(path=str(prints / f"{n.nome}-recarregar.png"))
        j.click("#silencio")
        w.wait_for_timeout(1800)
        ok(w.locator("uirapp-casa").count() == 1, f"{n.nome}: Recarregar não ligou o Uirapp na aba antiga")
    w.wait_for_timeout(1300)
    ok(j.text_content("#palco-titulo") == "Conversas à vista", f"{n.nome}: janela não achou o WhatsApp")
    ok(n.marca() == "aberto" and w.locator("uirapp-casa").count() == 1, f"{n.nome}: sem botão depois do Permitir")


def gestos(n):
    j, w = n.janela, n.wa
    n.ajustes()
    n.poe(silencio=False)
    n.abre(v="a")
    w.mouse.click(*BOTAO)
    w.wait_for_timeout(200)
    ok(n.marca() == "cheio" and n.guardado()["silencio"] is True, f"{n.nome}: botão não escondeu")
    w.keyboard.press("Enter")
    ok(n.marca() == "cheio", f"{n.nome}: Enter logo depois do clique mostrou tudo")
    w.mouse.click(*BOTAO)
    w.wait_for_timeout(200)
    ok(n.marca() == "aberto", f"{n.nome}: botão não mostrou")

    for esperado in ("cheio", "aberto", "cheio"):
        w.wait_for_timeout(450)
        w.keyboard.press("Alt+KeyS")
        w.wait_for_timeout(350)
        ok(n.marca() == esperado, f"{n.nome}: Alt+S deu {n.marca()}, esperado {esperado}")

    antes = w.evaluate("[teclas, digitado, envios, cliques]")
    w.keyboard.type("texto que nao pode entrar")
    w.keyboard.press("Enter")
    w.mouse.click(200, 160)
    w.mouse.click(900, 770)
    ok(w.evaluate("[teclas, digitado, envios, cliques]") == antes, f"{n.nome}: escondido e a conta recebeu gesto")
    w.keyboard.press("Control+KeyA")
    sel = w.evaluate("getSelection().toString()")
    ok(not any(c in sel for c in falso.CODIGOS), f"{n.nome}: selecionar tudo pegou texto")
    ok(not w.evaluate("window.find('NOMEQ')"), f"{n.nome}: buscar na página achou nome")
    ok(not any(c in w.evaluate("document.body.innerText") for c in falso.CODIGOS), f"{n.nome}: innerText com conversa")
    ax = json.dumps(n.ctx.new_cdp_session(w).send("Accessibility.getFullAXTree")["nodes"])
    nomes_ax = {m for m in falso.CODIGOS if m in "".join(
        str(x.get("name", {}).get("value", "")) for x in json.loads(ax) if not x.get("ignored"))}
    ok(not nomes_ax, f"{n.nome}: leitor de tela lê {nomes_ax}")
    w.emulate_media(media="print")
    ok(not w.evaluate(VE), f"{n.nome}: impressão mostra conversa")
    w.emulate_media(media="screen")

    j.bring_to_front()
    j.wait_for_timeout(1200)
    ok(j.text_content("#palco-titulo") == "Conversas escondidas", f"{n.nome}: janela não acompanha")
    j.click("#silencio")
    w.wait_for_timeout(200)
    ok(n.marca() == "aberto", f"{n.nome}: janela não mostrou")
    j.wait_for_timeout(450)
    j.keyboard.press("Alt+KeyS")
    w.wait_for_timeout(350)
    ok(n.marca() == "cheio", f"{n.nome}: Alt+S na janela não escondeu")

    outra = n.ctx.new_page()
    outra.goto(WA)
    outra.wait_for_timeout(500)
    ok(outra.evaluate("document.documentElement.getAttribute('data-uirapp')") == "cheio", f"{n.nome}: 2ª aba nasceu aberta")
    n.poe(silencio=False)
    ok(outra.evaluate("document.documentElement.getAttribute('data-uirapp')") == "aberto", f"{n.nome}: 2ª aba não acompanha")
    outra.close()
    n.wa.bring_to_front()


def cena_cega(n, prints):
    n.ajustes()
    n.poe(silencio=True)
    casos = (dict(v="a", linhas=9, conversa=True), dict(v="b", linhas=3, conversa=True, escuro=False),
             dict(v="b", linhas=14, conversa=False, armadilhas=True))
    fotos = []
    for caso in casos:
        n.abre(**caso)
        nada_vaza(n, f"cheio {caso}")
        ok(not n.wa.evaluate(DICAS), f"{n.nome}: balão de dica no silêncio cheio")
        fotos.append(Image.open(io.BytesIO(n.foto())).convert("RGB").tobytes())
    ok(fotos[0] == fotos[1] == fotos[2], f"{n.nome}: o print muda com o conteúdo (algo vaza)")
    if not prints:
        return
    n.abre(v="a")
    for tema, plumagem in (("dia", "vermelha"), ("noite", "laranja"), ("dia", "lenda")):
        n.ajustes(tema=tema, plumagem=plumagem)
        (prints / f"{n.nome}-silencio-{tema}-{plumagem}.png").write_bytes(n.foto())
    n.ajustes()
    n.poe(silencio=False)
    (prints / f"{n.nome}-aberto.png").write_bytes(n.foto())
    n.poe(silencio=True)


def combinacoes(n, prints):
    n.poe(silencio=True)
    for escuro in (False, True):
        n.abre(v="a", linhas=9, escuro=escuro, armadilhas=True)
        for bits in itertools.product((False, True), repeat=5):
            mostra = {c for c, b in zip(CATS, bits) if b}
            n.ajustes(mostra)
            n.wa.wait_for_timeout(120)
            ok(n.marca().split()[0] == ("parcial" if mostra else "cheio"), f"{n.nome} {mostra}: modo {n.marca()}")
            espera = set()
            if "nomes" in mostra:
                espera |= {"NOMEQ", "AUTORQ", "MEMBROQ"}
                if "fotos" in mostra:
                    espera.add("INICQ")
            if "previas" in mostra:
                espera.add("PREVIAQ")
                if "nomes" in mostra:
                    espera |= {"REMETQ", "AVISOQ", "MENCQ"}
            if "mensagens" in mostra:
                espera.add("MENSQ")
                if "nomes" in mostra:
                    espera |= {"MENCQ", "CITAQ"}
            viu = set(n.wa.evaluate(VE))
            caso = f"{n.nome} escuro={escuro} mostra={sorted(mostra)}"
            ok(viu == espera, f"{caso}: viu {sorted(viu)}, devia {sorted(espera)}")
            foto = n.foto()
            c = cores(foto)
            foto_ok = "fotos" in mostra
            ok((c["foto"] > 0) == foto_ok, f"{caso}: fotos {c['foto']}")
            midia_ok = "midia" in mostra
            ok((c["midia"] > 0) == midia_ok, f"{caso}: mídia {c['midia']}")
            ok((c["emoji"] > 0) == ("mensagens" in mostra), f"{caso}: emoji da mensagem {c['emoji']}")
            r = n.wa.evaluate(REAL)
            ok(r["citadas"] == (r["totalCitadas"] if {"nomes", "mensagens"} <= mostra else 0), f"{caso}: respostas {r['citadas']} de {r['totalCitadas']}")
            if mostra:
                ok(r["rodape"], f"{caso}: rodapé fora do esqueleto")
                ok(r["sticky"], f"{caso}: foto do grupo perdeu o sticky")
                ok(r["passaro"] == ("fotos" not in mostra), f"{caso}: passarinho na foto do grupo")
            dicas = set(n.wa.evaluate(DICAS))
            podem = ({"NOMEQ", "MEMBROQ"} if "nomes" in mostra else set()) | ({"PREVIAQ"} if {"nomes", "previas"} <= mostra else set())
            if {"nomes", "fotos"} & mostra:
                podem.add("NOMEQ")
            ok(dicas <= podem, f"{caso}: balão de dica {sorted(dicas - podem)}")
            nome_curto = {("nomes",): "so-nomes", ("fotos", "mensagens", "midia", "previas"): "esconde-nomes"}.get(tuple(sorted(mostra)))
            if prints and nome_curto:
                (prints / f"{n.nome}-parcial-{nome_curto}-{'escuro' if escuro else 'claro'}.png").write_bytes(foto)

    n.ajustes(("previas",))
    vaos = n.wa.evaluate("""() => [...document.querySelectorAll('#pane-side [data-testid=last-msg-status] > span[dir]:last-child')]
      .map(e => Math.round(e.getBoundingClientRect().left - e.parentElement.getBoundingClientRect().left))""")
    ok(set(vaos) == {0}, f"{n.nome}: vão na prévia entrega o tamanho de quem mandou {set(vaos)}")
    n.ajustes(("mensagens",))
    n.abre(v="a", escuro=True)
    r = n.wa.evaluate("""() => { const s = getComputedStyle(document.querySelector('#main [data-pre-plain-text] > div > span.selectable-text'));
      return [s.color, s.backgroundColor] }""")
    ok(r[0] != r[1] and r[1] not in ("rgba(0, 0, 0, 0)", "transparent"), f"{n.nome}: mensagem sem fundo próprio {r}")
    n.abre(v="a", linhas=14)
    n.ajustes(("mensagens",))
    n.wa.mouse.click(340, 146)
    ok(n.wa.evaluate("cliques") == 1, f"{n.nome}: parcial não deixa abrir conversa")
    n.wa.mouse.move(340, 320)
    n.wa.mouse.wheel(0, 240)
    n.wa.wait_for_timeout(700)
    ok(n.wa.evaluate("document.querySelector('#pane-side').scrollTop") > 0, f"{n.nome}: parcial não rola a lista")


def ataques(n):
    w = n.wa
    n.ajustes()
    n.poe(silencio=True)
    n.abre(v="a", armadilhas=True)
    for acao in ("setAttribute('data-uirapp','aberto')", "removeAttribute('data-uirapp')", "setAttribute('data-uirapp','parcial ve-nomes')"):
        depois = w.evaluate(f"async () => {{ document.documentElement.{acao}; await Promise.resolve(); return document.documentElement.getAttribute('data-uirapp') }}")
        ok(depois == "cheio", f"{n.nome}: marca forjada ficou ({depois})")
    w.evaluate("document.querySelector('html > uirapp-casa').remove()")
    w.wait_for_timeout(100)
    ok(w.evaluate("!!document.querySelector('html > uirapp-casa')"), f"{n.nome}: casa removida não voltou")
    nada_vaza(n, "casa removida")
    ok(w.evaluate("document.querySelector('html > uirapp-casa').shadowRoot === null"), f"{n.nome}: página lê o shadow root")
    w.evaluate("""() => {
      const c = document.querySelector('html > uirapp-casa');
      c.dispatchEvent(new MouseEvent('click', {bubbles: true}));
      dispatchEvent(new KeyboardEvent('keydown', {code: 'KeyS', altKey: true, bubbles: true}));
      document.dispatchEvent(new KeyboardEvent('keydown', {code: 'KeyS', altKey: true, bubbles: true}));
    }""")
    w.wait_for_timeout(150)
    ok(n.marca() == "cheio", f"{n.nome}: evento falso mostrou a tela")
    visto = w.evaluate("""() => ({nucleo: typeof Uirapp, pacote: typeof UirappPacote,
      extensao: typeof globalThis.chrome?.storage, runtime: typeof globalThis.chrome?.runtime?.id})""")
    ok(set(visto.values()) == {"undefined"}, f"{n.nome}: página enxerga a extensão {visto}")
    ok(not w.evaluate(f"fetch('chrome-extension://{n.id}/pacote.js').then(() => true, () => false)"), f"{n.nome}: página baixa arquivo da extensão")

    forte = """() => {
      const s = document.createElement('style'); s.id = 'forte';
      s.textContent = '@layer nega{*{visibility:visible!important;opacity:1!important}} html body *{visibility:visible!important} body{opacity:1!important}';
      document.head.prepend(s);
      for (const e of [document.body, ...document.body.querySelectorAll('*')]) {
        e.style.setProperty('visibility', 'visible', 'important'); e.style.setProperty('opacity', '1', 'important');
      }
    }"""
    w.evaluate(forte)
    nada_vaza(n, "CSS forte do site")
    w.evaluate("document.querySelector('html > uirapp-casa').style.setProperty('display', 'none', 'important')")
    nada_vaza(n, "sem a cena, só o CSS")
    n.abre(v="a", armadilhas=True)
    n.ajustes(("midia",))
    w.evaluate(forte)
    ok(not w.evaluate(VE), f"{n.nome}: CSS forte furou o parcial: {w.evaluate(VE)}")
    ok(cores(n.foto())["foto"] == 0, f"{n.nome}: CSS forte mostrou foto no parcial")
    n.ajustes()
    n.abre(v="a")
    w.evaluate("() => { const d = document.createElement('dialog'); d.style.cssText = 'visibility:visible!important'; d.textContent = 'SOLTOQmodal'; document.body.append(d); d.showModal() }")
    nada_vaza(n, "diálogo na camada do topo")
    w.keyboard.press("Alt+KeyS")
    w.wait_for_timeout(250)
    ok(n.marca() == "aberto", f"{n.nome}: com diálogo aberto o atalho não responde")


def sem_flash(n):
    n.ajustes()
    n.poe(silencio=True)
    n.abre(v="a")
    s = n.ctx.new_cdp_session(n.wa)
    quadros = []

    def chegou(e):
        quadros.append(e["data"])
        try:
            s.send("Page.screencastFrameAck", {"sessionId": e["sessionId"]})
        except Exception:
            pass

    s.on("Page.screencastFrame", chegou)
    s.send("Page.startScreencast", {"format": "png", "everyNthFrame": 1})
    for _ in range(6):
        n.wa.reload()
        n.wa.wait_for_timeout(500)
        # o filme perde o que dura menos de um quadro: a própria página também confere a cada mudança
        piscou, amostras = n.wa.evaluate("[piscou, amostras]")
        ok(amostras > 0 and piscou == 0, f"{n.nome}: abriu antes de ler ({piscou} em {amostras} amostras)")
    s.send("Page.stopScreencast")
    n.wa.wait_for_timeout(300)
    maus = [c for c in (cores(base64.b64decode(q)) for q in quadros) if any(c.values())]
    ok(len(quadros) >= 6, f"{n.nome}: filmou só {len(quadros)} quadros")
    ok(not maus, f"{n.nome}: piscou conversa em {len(maus)} de {len(quadros)} quadros")
    print(f"  {n.nome}: {len(quadros)} quadros filmados em 6 recargas")

    n.ajustes(aoAbrir=True)
    n.poe(silencio=False)
    n.abre(v="a")
    ok(n.marca() == "cheio", f"{n.nome}: 'Ao abrir' não escondeu")

    n.ajustes(("mensagens",))
    n.poe(silencio=True)
    try:
        n.cdp.send("Target.getTargets")
        ps = n.ctx.new_cdp_session(n.janela)
        ps.send("ServiceWorker.enable")
        ps.send("ServiceWorker.stopAllWorkers")
    except Exception as e:
        print("  fundo não parou:", str(e)[:120])
    n.abre(v="a", armadilhas=True)
    n.wa.wait_for_timeout(1200)
    ok(n.marca().startswith("parcial"), f"{n.nome}: fundo dormindo não reforçou ({n.marca()})")
    ok("SOLTOQ" not in n.wa.evaluate(VE), f"{n.nome}: fundo dormindo, CSS fraco")


def falha_fechado(n, prints):
    w, j = n.wa, n.janela
    n.ajustes()
    n.poe(silencio=True)
    n.abre(v="a")
    w.evaluate("document.querySelectorAll('[data-testid=cell-frame-title]').forEach(e => e.dataset.testid = 'nome-novo')")
    for _ in range(4):
        w.wait_for_timeout(1400)
        ok(not w.evaluate(VE), f"{n.nome}: vazou enquanto percebia a mudança")
    w.wait_for_timeout(1700)
    ok(n.marca() == "coberto", f"{n.nome}: WhatsApp mudou e não cobriu ({n.marca()})")
    nada_vaza(n, "alerta")
    if prints:
        (prints / f"{n.nome}-alerta.png").write_bytes(n.foto())
    j.bring_to_front()
    j.wait_for_timeout(1300)
    ok(j.text_content("#palco-titulo") == "O WhatsApp mudou", f"{n.nome}: janela não avisou a mudança")
    w.bring_to_front()
    w.keyboard.press("Enter")
    w.wait_for_timeout(300)
    ok(n.marca() == "aberto", f"{n.nome}: 'Descobrir a tela' não responde ao Enter")

    n.abre(v="a")
    n.ajustes(("mensagens",))
    n.poe(silencio=True)
    ok(n.marca().startswith("parcial"), f"{n.nome}: não entrou no parcial")
    w.evaluate("async () => { document.querySelector('#side').append('SOLTOQnovo'); await Promise.resolve() }")
    ok(n.marca() == "coberto", f"{n.nome}: texto no esqueleto não cobriu na hora")
    ok("SOLTOQ" not in w.evaluate(VE), f"{n.nome}: texto no esqueleto vazou")

    n.ajustes()
    n.abre(v="a", entrada=True)
    w.wait_for_timeout(8000)
    ok(n.marca() == "cheio", f"{n.nome}: tela de entrar virou alerta ({n.marca()})")
    nada_vaza(n, "tela de entrar")


def janela_real(n, prints):
    j, w = n.janela, n.wa
    n.ajustes()
    n.poe(silencio=False)
    n.abre(v="a")
    n.abre_janela()
    j.bring_to_front()
    j.wait_for_timeout(400)
    if prints:
        j.screenshot(path=str(prints / f"{n.nome}-janela.png"))
    j.click('.menu [data-ir="privacidade"]')
    j.click('[data-esconde="nomes"]')
    j.click('[data-ajuste="parado"]')
    g = n.guardado()["ajustes"]
    ok(g["esconder"]["nomes"] is False and g["parado"] is True, f"{n.nome}: interruptor não gravou")
    ok(j.text_content("#valor-privacidade") == "4 de 5", f"{n.nome}: valor da linha errado")
    j.click('[data-tela="privacidade"] [data-ir="inicio"]')
    j.click('.menu [data-ir="plumagem"]')
    j.click('.plumagem:has([value="lenda"])')
    j.click('.segmento:has([value="noite"])')
    j.reload()
    espera_pronta(j)
    ok(j.evaluate("[document.documentElement.dataset.plumagem, document.documentElement.dataset.tema]") == ["lenda", "noite"],
       f"{n.nome}: plumagem ou tema não ficaram")
    ok(w.evaluate("[document.querySelector('html > uirapp-casa').dataset.plumagem, document.querySelector('html > uirapp-casa').dataset.tema]") == ["lenda", "noite"],
       f"{n.nome}: página não recebeu plumagem ou tema")

    j.click('.menu [data-ir="respostas"]')
    ok(j.is_visible("#respostas-vazio"), f"{n.nome}: nasceu com resposta de exemplo")
    j.click('[data-tela="respostas"] [data-ir="nova"]')
    texto = "<img src=x onerror=alert(1)> RESPOSTA-SEGREDO"
    j.fill("#r-nome", "Teste")
    j.fill("#r-texto", texto)
    j.click('#form-resposta [type="submit"]')
    j.wait_for_timeout(400)
    ok(j.locator("#lista-respostas li").count() == 1 and not j.locator("#lista-respostas img").count(), f"{n.nome}: resposta não salvou como texto")
    # cópia de mentira: não mexe na área de transferência do Windows
    j.evaluate("navigator.clipboard.writeText = async t => { globalThis.copiado = t }")
    j.click(".resposta-copiar")
    ok(j.evaluate("copiado") == texto, f"{n.nome}: não copiou")
    ok("RESPOSTA-SEGREDO" not in json.dumps(n.guardado()), f"{n.nome}: resposta ficou onde o script do site alcança")
    ok("RESPOSTA-SEGREDO" not in w.evaluate("JSON.stringify({...localStorage}) + document.documentElement.outerHTML"), f"{n.nome}: resposta chegou à página")
    j.reload()
    espera_pronta(j)
    ok(j.text_content("#valor-respostas") == "1", f"{n.nome}: resposta não ficou")
    ok(not j.evaluate("fetch('https://example.com/').then(() => true, () => false)"), f"{n.nome}: a extensão consegue conectar")

    g = n.guardado()
    ok(set(g) <= {"ajustes", "silencio", "tecla"}, f"{n.nome}: guardou além do prometido {list(g)}")
    ok(not any(c in json.dumps(g) for c in falso.CODIGOS), f"{n.nome}: guardou conversa")

    for escondido in (True, False):
        n.ajustes()
        n.poe(silencio=escondido)
        n.abre_janela()
        j.click('.menu [data-ir="acesso"]')
        j.click("#apagar-tudo")
        j.click("#dialogo-apagar")
        j.wait_for_timeout(300)
        g = n.guardado()
        ok(j.is_visible('[data-tela="boas-vindas"]'), f"{n.nome}: apagar não volta ao começo")
        ok("ajustes" not in g and j.evaluate("localStorage.length") == 0, f"{n.nome}: apagar deixou dado {g}")
        ok(n.marca() == ("cheio" if escondido else "aberto"), f"{n.nome}: apagar {'descobriu a tela' if escondido else 'deixou estado'}")
        if escondido:
            w.bring_to_front()
            w.mouse.click(*BOTAO)
            w.wait_for_timeout(250)
            ok(n.marca() == "aberto", f"{n.nome}: sem dados, não dá para mostrar de volta")
        else:
            ok(w.locator("uirapp-casa").count() == 0, f"{n.nome}: botão ficou depois de apagar")


def abre_popup_em(n, tela):
    n.abre_janela()
    j = n.janela
    n.janela.bring_to_front()
    if tela != "inicio":
        j.click(f'.menu [data-ir="{tela}"]')
    return j


def campo_whatsapp(n):
    return n.wa.evaluate("document.querySelector('[data-testid=conversation-compose-box-input]').textContent")


def funcoes(n, prints):
    j, w = n.janela, n.wa
    n.ajustes()
    n.poe(silencio=False)
    n.abre(v="a")

    # respostas com atalho, variáveis e assinatura
    j = abre_popup_em(n, "respostas")
    j.click('[data-tela="respostas"] [data-ir="nova"]')
    j.fill("#r-nome", "Horário")
    j.fill("#r-atalho", "/Hora")
    j.fill("#r-texto", "{saudacao}, {primeiro_nome}! Abrimos às 9h. {assinatura}")
    j.click('#form-resposta [type="submit"]')
    j.wait_for_timeout(400)
    ok("Horário · /hora" in j.text_content("#lista-respostas"), f"{n.nome}: atalho não aparece na lista")
    j.click('[data-tela="respostas"] [data-ir="nova"]')
    j.fill("#r-nome", "Outra")
    j.fill("#r-atalho", "hora")
    j.fill("#r-texto", "x")
    j.click('#form-resposta [type="submit"]')
    ok(j.is_visible("#e-atalho"), f"{n.nome}: aceitou atalho repetido")
    j.click('[data-tela="nova"] [data-ir="respostas"]')
    j.click('[data-tela="respostas"] [data-ir="assinatura"]')
    j.fill("#a-assinatura", "Equipe Loja")
    j.press("#a-assinatura", "Tab")
    for campo, valor in (("#a-chave", "loja@exemplo.com"), ("#a-recebedor", "Loja da Ana"), ("#a-cidade", "Curitiba")):
        j.fill(campo, valor)
        j.press(campo, "Tab")
    a = n.guardado()["ajustes"]
    ok(a["assinatura"] == "Equipe Loja" and a["pix"]["cidade"] == "Curitiba", f"{n.nome}: assinatura ou Pix não gravou")
    ok("pronto" in j.text_content("#pix-estado"), f"{n.nome}: Pix completo não avisou")

    # /atalho + Tab dentro da conversa
    w.bring_to_front()
    w.click('[data-testid="conversation-compose-box-input"]')
    w.keyboard.press("End")
    w.keyboard.type(" /hora")
    w.keyboard.press("Tab")
    w.wait_for_timeout(300)
    texto = campo_whatsapp(n)
    ok("/hora" not in texto and "NOMEQa99! Abrimos às 9h. Equipe Loja" in texto and texto.startswith("MENSQarascunho"),
       f"{n.nome}: /atalho não virou a resposta: {texto[:120]!r}")
    w.keyboard.type(" /nada")
    w.keyboard.press("Tab")
    ok("/nada" in campo_whatsapp(n), f"{n.nome}: atalho que não existe mexeu no texto")
    ok(w.evaluate("envios") == 0, f"{n.nome}: a resposta foi enviada sozinha")

    # pôr na conversa pela janela, e no silêncio vira cópia
    j = abre_popup_em(n, "respostas")
    antes = campo_whatsapp(n)
    j.click(".resposta-usar")
    w.wait_for_timeout(300)
    ok(campo_whatsapp(n).count("Abrimos às 9h") == antes.count("Abrimos às 9h") + 1, f"{n.nome}: 'Pôr na conversa' não pôs")
    ok(w.evaluate("envios") == 0, f"{n.nome}: 'Pôr na conversa' enviou")
    n.poe(silencio=True)
    j.evaluate("navigator.clipboard.writeText = async t => { globalThis.copiado = t }")
    antes = campo_whatsapp(n)
    j.click(".resposta-usar")
    j.wait_for_timeout(300)
    ok(campo_whatsapp(n) == antes and "Abrimos às 9h" in (j.evaluate("globalThis.copiado ?? ''")), f"{n.nome}: no silêncio escreveu na conversa")
    n.poe(silencio=False)

    # exportar
    n.abre(v="a")
    j = abre_popup_em(n, "exportar")
    j.click('.segmento:has([value="txt"])')
    j.wait_for_timeout(400)
    with j.expect_download() as d:
        j.click('#form-exportar [type="submit"]')
    txt = Path(d.value.path()).read_text("utf-8")
    ok("MENSQa0" in txt and "AUTORQa0" in txt and "(figurinha)" in txt and "CITAQa2" not in txt.split("MENSQa2")[0][-40:],
       f"{n.nome}: exportar texto veio errado: {txt[:160]!r}")
    j.click('.segmento:has([value="csv"])')
    j.wait_for_timeout(400)
    with j.expect_download() as d:
        j.click('#form-exportar [type="submit"]')
    csv = Path(d.value.path()).read_text("utf-8")
    ok(csv.startswith("\ufeff") and "MENSQa3" in csv, f"{n.nome}: planilha veio errada")
    j.click('.segmento:has([value="html"])')
    j.fill("#x-senha", "curta")
    j.click('#form-exportar [type="submit"]')
    ok(j.is_visible("#e-senha"), f"{n.nome}: aceitou senha curta")
    j.fill("#x-senha", "senha-boa-123")
    j.wait_for_timeout(400)
    with j.expect_download() as d:
        j.click('#form-exportar [type="submit"]')
    caminho = Path(d.value.path())
    pagina = caminho.read_text("utf-8")
    ok("MENSQ" not in pagina and "AUTORQ" not in pagina, f"{n.nome}: exportação com senha deixou texto à vista")
    final = caminho.with_suffix(".html")
    caminho.replace(final)
    pg = n.ctx.new_page()
    pg.goto(final.as_uri())
    pg.fill("input", "senha-errada")
    pg.click("button")
    pg.wait_for_timeout(2500)
    ok("Senha errada" in pg.text_content("output"), f"{n.nome}: senha errada não avisou")
    pg.fill("input", "senha-boa-123")
    pg.click("button")
    pg.wait_for_timeout(2500)
    ok("MENSQa0" in pg.text_content("main") and not pg.locator("main img, main script").count(), f"{n.nome}: senha certa não abriu")
    pg.close()

    # baixar a foto ou o vídeo aberto
    w.evaluate("""async () => { const c = document.createElement('canvas'); c.width = c.height = 300; c.getContext('2d').fillRect(0, 0, 300, 300);
      const b = await new Promise(r => c.toBlob(r)); const i = document.createElement('img'); i.src = URL.createObjectURL(b);
      i.width = i.height = 300; i.style.cssText = 'position:fixed;left:600px;top:100px;z-index:9'; document.body.append(i); await i.decode(); }""")
    j = abre_popup_em(n, "inicio")
    # o arquivo é da página do WhatsApp: o download sai por lá
    with w.expect_download() as d:
        j.click("#baixar")
    ok(d.value.suggested_filename.startswith("uirapp-") and Path(d.value.path()).stat().st_size > 100, f"{n.nome}: não baixou a mídia aberta")

    # conversar sem salvar o número
    j = abre_popup_em(n, "conversar")
    j.fill("#c-numero", "123")
    j.click('#form-conversar [type="submit"]')
    ok(j.is_visible("#e-numero"), f"{n.nome}: aceitou número torto")
    j.fill("#c-numero", "(11) 91234-5678")
    j.fill("#c-texto", "Olá & tchau")
    try:
        j.click('#form-conversar [type="submit"]')
    except Exception:
        pass
    w.wait_for_timeout(1200)
    url = urllib.parse.urlparse(w.url)
    q = urllib.parse.parse_qs(url.query)
    ok(url.path == "/send" and q.get("phone") == ["5511912345678"] and q.get("text") == ["Olá & tchau"], f"{n.nome}: conversa abriu em {w.url}")

    # botão direito: compartilhar
    sw = [s for s in n.ctx.service_workers if n.id in s.url]
    if sw:
        sw[-1].evaluate("""chrome.contextMenus.onClicked.dispatch({menuItemId: 'compartilhar', selectionText: 'trecho lido', pageUrl: 'https://exemplo.test/x'}, {url: 'https://exemplo.test/x'})""")
        w.wait_for_timeout(1200)
        q = urllib.parse.parse_qs(urllib.parse.urlparse(w.url).query)
        ok(q.get("text") == ["trecho lido\nhttps://exemplo.test/x"] and "phone" not in q, f"{n.nome}: compartilhar abriu {w.url}")
    else:
        print(f"  {n.nome}: fundo dormindo, compartilhar não testado")

    # aparência: tema, faixas, barra e letra
    n.abre(v="a")
    j = abre_popup_em(n, "aparencia")
    j.click('.tema:has([value="igarape"])')
    for o in ("filtros", "faixas", "status", "ligacoes", "desenhos"):
        j.click(f'label.linha:has([data-oculta="{o}"])')
    j.click('.segmento:has([name="letra"][value="125"])')
    w.wait_for_timeout(300)
    vis = w.evaluate("""() => { const d = s => getComputedStyle(document.querySelector(s)).display;
      const nav = t => [...document.querySelectorAll('button[data-navbar-item]')].find(b => b.querySelector('title').textContent === t);
      return {lado: getComputedStyle(document.querySelector('#side')).backgroundColor, filtros: d('[data-testid=chat_list_filters_row]'),
        faixa: d('[data-testid=chat_list_notifications_banner]'), status: getComputedStyle(nav('wds-ic-status')).display,
        canais: getComputedStyle(nav('wds-ic-channels')).display, ligacoes: getComputedStyle(nav('ic-call')).display,
        zoom: getComputedStyle(document.querySelector('#app')).zoom} }""")
    ok(vis == {"lado": "rgb(15, 42, 46)", "filtros": "none", "faixa": "none", "status": "none", "canais": "block", "ligacoes": "none", "zoom": "1.25"},
       f"{n.nome}: aparência no WhatsApp veio {vis}")
    if prints:
        (prints / f"{n.nome}-tema-igarape.png").write_bytes(n.foto())
        j.screenshot(path=str(prints / f"{n.nome}-janela-aparencia.png"))
    n.ajustes()

    # junto com o silêncio: som, título e passarinho
    n.ajustes(som=True, titulo=True, passaro="esquerda")
    n.abre(v="a")
    w.bring_to_front()
    w.mouse.click(16 + 48 + 28, ALT - 88 - 28)
    w.wait_for_timeout(500)
    mudo = j.evaluate("chrome.tabs.query({url: 'https://web.whatsapp.com/*'}).then(t => t.map(x => x.mutedInfo.muted))")
    ok(n.marca() == "cheio" and w.title() == "WhatsApp" and all(mudo), f"{n.nome}: silêncio sem som e título: {n.marca()} {w.title()!r} {mudo}")
    w.keyboard.press("Alt+KeyS")
    w.wait_for_timeout(500)
    mudo = j.evaluate("chrome.tabs.query({url: 'https://web.whatsapp.com/*'}).then(t => t.map(x => x.mutedInfo.muted))")
    ok(n.marca() == "aberto" and w.title() == "(3) WhatsApp" and not any(mudo), f"{n.nome}: som ou título não voltaram: {w.title()!r} {mudo}")
    n.ajustes(passaro="oculto")
    ok(not w.evaluate(f"document.elementFromPoint({BOTAO[0]}, {BOTAO[1]})?.localName === 'uirapp-casa'"), f"{n.nome}: passarinho à vista com 'Só no silêncio'")
    n.ajustes(aoSair=True)
    outra = n.ctx.new_page()
    outra.bring_to_front()
    outra.wait_for_timeout(700)
    escondeu = w.evaluate("document.visibilityState") == "hidden"
    if escondeu:
        ok(n.marca() == "cheio", f"{n.nome}: 'Ao sair da aba' não escondeu")
    else:
        print(f"  {n.nome}: sem tela, a aba não fica escondida: 'Ao sair da aba' não testado")
    outra.close()
    n.ajustes()
    n.poe(silencio=False)

    # idioma
    n.ajustes(idioma="en")
    j = abre_popup_em(n, "inicio")
    ok(j.text_content("#silencio-texto") == "Hide chats" and j.text_content('.menu [data-ir="respostas"] .linha-texto') == "Quick replies"
       and j.get_attribute("#busca", "placeholder") == "Search", f"{n.nome}: inglês não entrou")
    n.ajustes(idioma="es")
    j = abre_popup_em(n, "inicio")
    ok(j.text_content("#silencio-texto") == "Ocultar chats", f"{n.nome}: espanhol não entrou")
    n.ajustes()
    j = abre_popup_em(n, "inicio")
    ok(j.text_content("#silencio-texto") == "Esconder conversas", f"{n.nome}: português não voltou")


def ninho(n, prints):
    w = n.wa
    n.ajustes()
    n.poe(silencio=False)
    n.abre(v="a")
    pg = n.ctx.new_page()
    pg.set_viewport_size({"width": 1440, "height": 900})
    pg.on("pageerror", lambda e: n.erros.append(str(e)))
    pg.goto(f"chrome-extension://{n.id}/ninho.html#atendimento")
    espera_pronta(pg)
    le = lambda: pg.evaluate("UirappDeposito.le()")

    # ficha
    pg.click("#nova-ficha")
    pg.click("#fi-da-conversa")
    ok(pg.input_value("#fi-nome") == "NOMEQa99", f"{n.nome}: nome da conversa aberta não veio")
    pg.fill("#fi-telefone", "11 3456-7890")
    pg.fill("#fi-valor", "1.250,50")
    pg.fill("#fi-etiquetas", "vip, retorno, vip")
    pg.fill("#fi-nota", "<b>nota</b>")
    pg.click('#form-ficha [type="submit"]')
    f = le()["fichas"]
    ok(len(f) == 1 and f[0]["telefone"] == "551134567890" and f[0]["valor"] == 125050 and f[0]["etiquetas"] == ["vip", "retorno"],
       f"{n.nome}: ficha gravou {f}")
    ok(pg.locator(".ficha b").count() == 0 and "R$ 1.250,50" in pg.text_content('.coluna[data-etapa="novo"]').replace(" ", " "), f"{n.nome}: ficha mal mostrada")
    pg.locator('.coluna[data-etapa="novo"] .ficha').drag_to(pg.locator('.coluna[data-etapa="proposta"]'))
    pg.wait_for_timeout(300)
    ok(le()["fichas"][0]["etapa"] == "proposta", f"{n.nome}: arrastar a ficha não mudou a etapa")
    pg.select_option("#f-etiqueta", "vip")
    ok(pg.locator(".ficha").count() == 1, f"{n.nome}: filtro por etiqueta escondeu a ficha")
    pg.fill("#f-busca", "ninguém")
    ok(pg.locator(".ficha").count() == 0, f"{n.nome}: busca não filtrou")
    pg.fill("#f-busca", "")
    pg.select_option("#f-etiqueta", "")

    # lembrete: o formulário recusa o passado; o alarme vira aviso e o aviso abre a conversa
    pg.click(".ficha-abrir")
    pg.click("#fi-lembrar")
    ok(pg.input_value("#le-titulo").endswith("NOMEQa99") and pg.input_value("#le-telefone") == "551134567890", f"{n.nome}: lembrete da ficha não veio preenchido")
    pg.fill("#le-quando", "2020-01-01T10:00")
    pg.click('#form-lembrete [type="submit"]')
    ok(pg.is_visible("#e-le-quando"), f"{n.nome}: aceitou lembrete no passado")
    pg.click("#le-fechar")
    pg.evaluate("""async () => { const d = await UirappDeposito.le();
      d.lembretes.push({id: 'teste-1', titulo: 'Ligar para a Ana', quando: Date.now() + 4000, texto: 'Oi, tudo bem?', telefone: '5511912345678'});
      await UirappDeposito.grava(d); await chrome.runtime.sendMessage({uirapp: 'lembretes'}); }""")
    alarmes = pg.evaluate("chrome.alarms.getAll().then(a => a.map(x => x.name))")
    ok("lembrete:teste-1" in alarmes, f"{n.nome}: lembrete não virou alarme {alarmes}")
    pg.wait_for_timeout(6500)
    avisos = pg.evaluate("chrome.notifications.getAll().then(Object.keys)")
    ok("lembrete:teste-1" in avisos, f"{n.nome}: alarme não virou aviso {avisos}")
    sw = [s for s in n.ctx.service_workers if n.id in s.url]
    if sw:
        sw[-1].evaluate("chrome.notifications.onClicked.dispatch('lembrete:teste-1')")
        w.wait_for_timeout(1200)
        q = urllib.parse.parse_qs(urllib.parse.urlparse(w.url).query)
        ok(q.get("phone") == ["5511912345678"] and q.get("text") == ["Oi, tudo bem?"], f"{n.nome}: aviso abriu {w.url}")

    # temas
    pg.goto(f"chrome-extension://{n.id}/ninho.html#temas")
    espera_pronta(pg)
    pg.fill("#tm-nome", "Meu teste")
    pg.fill("#tm-fundo", "#204060")
    pg.fill("#tm-texto", "#30506f")
    pg.fill("#tm-acento", "#ffcc00")
    ok(pg.is_visible("#tm-ajuste"), f"{n.nome}: texto ilegível não foi ajustado")
    png = Path(n.base) / "fundo.png"
    Image.new("RGB", (40, 30), (255, 0, 255)).save(png)
    pg.set_input_files("#tm-imagem", str(png))
    pg.wait_for_timeout(500)
    pg.click('#form-tema [type="submit"]')
    pg.wait_for_timeout(400)
    a = n.guardado()["ajustes"]["aparencia"]
    ok(a["temaId"] == "meu-teste" and a["temaDados"]["imagem"].startswith("data:image/jpeg"), f"{n.nome}: tema do estúdio não ficou em uso")
    fundo = w.evaluate("getComputedStyle(document.querySelector('#main [data-testid=conversation-panel-body]')).backgroundImage")
    ok(fundo.startswith('url("data:image/jpeg'), f"{n.nome}: imagem do tema não foi para a conversa")
    with pg.expect_download() as d:
        pg.click(".tema-exportar")
    exportado = Path(d.value.path())
    pg.set_input_files("#tm-importar", str(exportado))
    pg.wait_for_timeout(400)
    ok(len(le()["temas"]) == 1, f"{n.nome}: importar o mesmo tema duplicou")
    torto = Path(n.base) / "torto.json"
    torto.write_text('{"uirapp":"tema","fundo":"red;}body{x","texto":"#000","acento":"#111"}', "utf-8")
    pg.set_input_files("#tm-importar", str(torto))
    pg.wait_for_timeout(300)
    ok("não é um tema" in pg.text_content("#aviso-texto"), f"{n.nome}: aceitou tema torto")
    if prints:
        pg.screenshot(path=str(prints / f"{n.nome}-ninho-temas.png"))

    # desenho
    pg.goto(f"chrome-extension://{n.id}/ninho.html#desenho")
    espera_pronta(pg)
    caixa = pg.locator("#tela-desenho").bounding_box()
    pg.mouse.move(caixa["x"] + 50, caixa["y"] + 50)
    pg.mouse.down()
    pg.mouse.move(caixa["x"] + 300, caixa["y"] + 200, steps=12)
    pg.mouse.up()
    with pg.expect_download() as d:
        pg.click("#d-baixar")
    im = Image.open(d.value.path()).convert("RGB")
    ok(im.size == (1200, 720) and im.getextrema() != ((255, 255), (255, 255), (255, 255)), f"{n.nome}: desenho saiu em branco")
    if prints:
        pg.screenshot(path=str(prints / f"{n.nome}-ninho-desenho.png"))

    # backup com senha e restauração
    pg.goto(f"chrome-extension://{n.id}/ninho.html#backup")
    espera_pronta(pg)
    pg.fill("#b-senha", "backup-forte-1")
    with pg.expect_download() as d:
        pg.click('#form-backup [type="submit"]')
    arquivo = Path(d.value.path())
    ok("NOMEQa99" not in arquivo.read_text("utf-8"), f"{n.nome}: backup com senha deixou texto à vista")
    antes = le()
    pg.evaluate("UirappDeposito.apaga()")
    pg.set_input_files("#b-arquivo", str(arquivo))
    pg.fill("#b-r-senha", "errada-123")
    pg.press("#b-r-senha", "Tab")
    pg.wait_for_timeout(2500)
    ok(pg.is_visible("#e-b-r") and pg.is_disabled("#b-restaurar"), f"{n.nome}: senha errada abriu o backup")
    pg.fill("#b-r-senha", "backup-forte-1")
    pg.press("#b-r-senha", "Tab")
    pg.wait_for_timeout(2500)
    # restaurar não pode dar o "Permitir": a instalação está sem ele e o arquivo tem
    pg.evaluate("chrome.storage.local.get('ajustes').then(g => chrome.storage.local.set({ajustes: {...g.ajustes, consentido: false}}))")
    pg.wait_for_timeout(200)
    pg.click("#b-restaurar")
    pg.click("#dialogo-apagar")
    pg.wait_for_timeout(500)
    depois = le()
    ok(depois["fichas"] == antes["fichas"] and depois["temas"] == antes["temas"] and len(depois["respostas"]) == len(antes["respostas"]),
       f"{n.nome}: restaurar não trouxe tudo de volta")
    ok(n.guardado()["ajustes"]["consentido"] is False, f"{n.nome}: restaurar deu o Permitir que a instalação não tinha")
    n.ajustes()

    if prints:
        for parte in ("atendimento", "lembretes"):
            pg.goto(f"chrome-extension://{n.id}/ninho.html#{parte}")
            espera_pronta(pg)
            pg.screenshot(path=str(prints / f"{n.nome}-ninho-{parte}.png"))
        pg.set_viewport_size({"width": 390, "height": 844})
        pg.goto(f"chrome-extension://{n.id}/ninho.html#atendimento")
        espera_pronta(pg)
        ok(pg.evaluate("document.documentElement.scrollWidth <= innerWidth"), f"{n.nome}: Ninho rola de lado no celular")
        pg.screenshot(path=str(prints / f"{n.nome}-ninho-390.png"))
    pg.evaluate("UirappDeposito.apaga()")
    pg.close()
    n.ajustes()


def loja(n):
    pg = n.ctx.new_page()
    pg.goto("chrome://extensions/")
    info = pg.evaluate("""async id => {
      const e = await chrome.developerPrivate.getExtensionInfo(id);
      return {manifesto: e.manifestErrors.map(x => x.message), rodando: e.runtimeErrors.map(x => x.message),
              avisos: e.permissions.simplePermissions.map(x => x.message), estado: e.state};
    }""", n.id)
    pg.close()
    ok(not info["manifesto"], f"{n.nome}: manifesto com aviso {info['manifesto']}")
    ok(not info["rodando"], f"{n.nome}: extensão deu erro {info['rodando']}")
    atalho = n.janela.evaluate("chrome.commands.getAll().then(c => c.find(x => x.name === 'alternar')?.shortcut)")
    ok(atalho == "Alt+S", f"{n.nome}: atalho veio {atalho!r}")
    print(f"  {n.nome}: avisos de instalação {info['avisos']}, atalho {atalho}")


def comando(n):
    n.ajustes()
    n.poe(silencio=False, tecla=0)
    n.abre(v="a")
    sw = [s for s in n.ctx.service_workers if n.id in s.url]
    if not sw:
        print(f"  {n.nome}: fundo dormindo, comando do navegador não testado")
        return
    try:
        sw[-1].evaluate("chrome.commands.onCommand.dispatch('alternar')")
    except Exception as e:
        print(f"  {n.nome}: comando do navegador não testado ({str(e)[:90]})")
        return
    n.wa.wait_for_timeout(400)
    ok(n.marca() == "cheio", f"{n.nome}: comando do navegador não escondeu")


def parado(n):
    n.ajustes(parado=True)
    n.poe(silencio=False)
    n.abre(v="a")
    n.wa.wait_for_timeout(280_000)
    ok(n.marca() == "aberto", f"{n.nome}: escondeu antes dos 5 minutos")
    n.wa.wait_for_timeout(25_000)
    ok(n.marca() == "cheio", f"{n.nome}: 5 minutos parado e não escondeu")


def orfa(n, prints):
    w = n.wa
    n.ajustes()
    n.poe(silencio=True)
    n.abre(v="a")
    n.janela.evaluate("setTimeout(() => chrome.runtime.reload(), 50)")
    w.wait_for_timeout(2500)
    ok(n.marca() == "coberto", f"{n.nome}: extensão recarregou e não cobriu ({n.marca()})")
    nada_vaza(n, "extensão recarregada")
    if prints:
        (prints / f"{n.nome}-parou.png").write_bytes(n.foto())
    w.keyboard.press("Enter")
    w.wait_for_timeout(2000)
    ok(n.marca() == "cheio", f"{n.nome}: 'Recarregar a página' não religou ({n.marca()})")


def roda(p, nome, prints, espera_parado):
    print(nome, flush=True)
    n = Navegador(p, nome)
    passos = [("primeira vez", lambda: primeira_vez(n, prints)), ("loja", lambda: loja(n)), ("gestos", lambda: gestos(n)),
              ("comando", lambda: comando(n)), ("cena cega", lambda: cena_cega(n, prints)),
              ("combinações", lambda: combinacoes(n, prints)), ("ataques", lambda: ataques(n)),
              ("sem flash", lambda: sem_flash(n)), ("falha fechado", lambda: falha_fechado(n, prints)),
              ("janela", lambda: janela_real(n, prints)), ("funções da 0.2", lambda: funcoes(n, prints)),
              ("ninho", lambda: ninho(n, prints))]
    if espera_parado:
        passos.append(("parado", lambda: parado(n)))
    passos.append(("órfã", lambda: orfa(n, prints)))
    try:
        for rotulo, passo in passos:
            print("  ·", rotulo, flush=True)
            try:
                passo()
            except Exception as e:
                ok(False, f"{nome} {rotulo}: {type(e).__name__} {str(e)[:500]}")
        permitido = ("https://web.whatsapp.com/", "https://pps.whatsapp.net/", "https://media.whatsapp.net/",
                     f"chrome-extension://{n.id}/", "chrome://", "brave://", "data:", "about:", "blob:",
                     "chrome-extension://invalid/", "file:///")  # é o que o navegador devolve à página que tenta ler a extensão
        fora = sorted({u for u in n.pedidos if not u.startswith(permitido) and u != "https://example.com/"})
        ok(not fora, f"{nome}: pedido para fora {fora[:6]}")
        erros = [e for e in n.erros if "Content Security Policy" not in e and "chrome-extension://" not in e]
        ok(not erros, f"{nome}: erro no console {sorted(set(erros))[:5]}")
    finally:
        n.fecha()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    argv = sys.argv[1:]
    pasta = None
    if "--prints" in argv:
        i = argv.index("--prints")
        pasta = Path(argv[i + 1])
        pasta.mkdir(parents=True, exist_ok=True)
        del argv[i:i + 2]
    quais = [a for a in argv if a in NAVEGADORES] or list(NAVEGADORES)
    estatico()
    with sync_playwright() as pw:
        for qual in quais:
            roda(pw, qual, pasta, "--parado" in argv)
    print(f"{feitos[0]} conferências, {len(falhas)} falhas")
    for f in falhas[:80]:
        print(" -", f)
    sys.exit(1 if falhas else 0)
