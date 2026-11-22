"""Monta docs/imagens/instalar.png: o passo a passo com os botões marcados, tirado do Brave de verdade.

Uso: python scripts/imagem_instalar.py   (perfil descartável; não toca no navegador do dono)
"""
import io
import shutil
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright

sys.dont_write_bytecode = True
import montar  # noqa: E402

RAIZ = montar.RAIZ
EXT = RAIZ / montar.extensao.SAIDA
BRAVE = str(Path.home() / r"AppData\Local\BraveSoftware\Brave-Browser\Application\brave.exe")
TABLER = RAIZ / "ui/icones/puzzle.svg"


def captura():
    base = Path(tempfile.mkdtemp(prefix="uirapp-imagem-"))
    try:
        with sync_playwright() as p:
            ctx = p.chromium.launch_persistent_context(
                str(base / "perfil"), executable_path=BRAVE, headless=True, color_scheme="light", locale="pt-BR",
                viewport={"width": 1100, "height": 420}, ignore_default_args=["--disable-extensions"],
                args=[f"--disable-extensions-except={EXT}", f"--load-extension={EXT}", "--lang=pt-BR",
                      "--host-resolver-rules=MAP * ~NOTFOUND"])
            sw = ctx.service_workers or [ctx.wait_for_event("serviceworker")]
            quem = sw[0].url.split("/")[2]
            pg = ctx.pages[0]
            pg.goto("chrome://extensions/")
            pg.evaluate("chrome.developerPrivate.updateProfileConfiguration({inDeveloperMode: true})")
            pg.wait_for_timeout(3000)
            botoes = {k: pg.locator(s).first.bounding_box()
                      for k, s in (("modo", "#devMode"), ("carregar", "#loadUnpacked"))}
            tela = Image.open(io.BytesIO(pg.screenshot())).convert("RGB")
            janela = ctx.new_page()
            janela.set_viewport_size({"width": 360, "height": 560})
            janela.goto(f"chrome-extension://{quem}/popup.html")
            janela.wait_for_timeout(1000)
            botoes["permitir"] = janela.locator("#permitir").bounding_box()
            popup = Image.open(io.BytesIO(janela.screenshot())).convert("RGB")
            quebra = ctx.new_page()
            quebra.set_viewport_size({"width": 56, "height": 56})
            quebra.set_content(f"<body style='margin:4px'><style>svg{{width:48px;height:48px}}</style>{TABLER.read_text('utf-8')}</body>")
            peca = Image.open(io.BytesIO(quebra.screenshot())).convert("RGB")
            ctx.close()
        return tela, popup, peca, botoes
    finally:
        shutil.rmtree(base, ignore_errors=True)


def monta():
    d = montar.livro()
    cor = {k: v for k, v in d["colors"].items()}
    tela, popup, peca, b = captura()
    f = Image.new("RGB", (1600, 1120), cor["bg"])
    g = ImageDraw.Draw(f)
    fonte = lambda tam, forte=True: ImageFont.truetype(f"C:/Windows/Fonts/segoeui{'b' if forte else ''}.ttf", tam)

    def numero(x, y, n):
        g.ellipse((x - 22, y - 22, x + 22, y + 22), fill=cor["primary"])
        g.text((x, y), str(n), fill=cor["on-primary"], font=fonte(26), anchor="mm")

    def marca(caixa, ox, oy, n, esc=1.0, lado="esquerda"):
        x, y = ox + caixa["x"] * esc, oy + caixa["y"] * esc
        w, h = caixa["width"] * esc, caixa["height"] * esc
        g.rounded_rectangle((x - 7, y - 7, x + w + 7, y + h + 7), radius=12, outline=cor["escarlate"], width=5)
        if lado == "esquerda":
            numero(x - 34, y + h / 2, n)
        else:
            numero(x + w / 2, y + h + 34, n)

    icone = Image.open(RAIZ / "marca/icones/icone-128.png").convert("RGBA").resize((64, 64))
    f.paste(icone, (40, 30), icone)
    g.text((124, 62), "Instalar o Uirapp no Brave", fill=cor["text"], font=fonte(40), anchor="lm")

    f.paste(tela, (40, 130))
    g.rectangle((40, 130, 40 + tela.width, 130 + tela.height), outline=cor["line"], width=2)
    marca(b["modo"], 40, 130, 2, lado="abaixo")
    marca(b["carregar"], 40, 130, 3, lado="abaixo")

    f.paste(popup, (1200, 130))
    g.rectangle((1200, 130, 1560, 690), outline=cor["line"], width=2)
    marca(b["permitir"], 1200, 130, 6)

    passos = [
        (["Abra uma aba e digite:", "brave://extensions"]),
        (["Ligue o Modo do desenvolvedor, no alto à direita.", "Deixe ligado: se desligar, o Brave desliga o Uirapp."]),
        (["Clique em Carregar sem compactação."]),
        (["Escolha a pasta que você descompactou,", "a que tem o arquivo manifest.json dentro."]),
        (["Clique na peça de quebra-cabeça ao lado da barra de endereço", "e depois em Uirapp."]),
        (["Clique em Permitir e começar."]),
        (["Volte à aba do WhatsApp Web e aperte F5."]),
    ]
    y = 598
    for i, linhas in enumerate(passos, 1):
        numero(62, y + 16, i)
        g.text((104, y + 16), linhas[0], fill=cor["text"], font=fonte(26), anchor="lm")
        for j, extra in enumerate(linhas[1:], 1):
            g.text((104, y + 16 + 33 * j), extra, fill=cor["text-muted"], font=fonte(23, False), anchor="lm")
        if i == 5:
            f.paste(peca, (890, y - 8))
        y += 58 + 22 * (len(linhas) - 1)

    saida = RAIZ / "docs/imagens/instalar.png"
    saida.parent.mkdir(parents=True, exist_ok=True)
    f.save(saida)
    print("ok", saida)


if __name__ == "__main__":
    monta()
