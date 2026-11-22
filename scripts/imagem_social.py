"""Imagem de compartilhamento do repositório (social preview do GitHub, 1280x640).

Uso: python scripts/imagem_social.py   (precisa do Google Chrome; roda depois de scripts/imagens_readme.py)
Gera docs/imagens/social-preview.png.
"""
import base64
from pathlib import Path

from playwright.sync_api import sync_playwright

RAIZ = Path(__file__).resolve().parent.parent
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
SAIDA = RAIZ / "docs/imagens/social-preview.png"


def dado(caminho, tipo):
    return f"data:{tipo};base64,{base64.b64encode((RAIZ / caminho).read_bytes()).decode()}"


PAGINA = f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><style>
@font-face {{ font-family: "Sofia Sans"; src: url("{dado('ui/fontes/sofia-sans-latin-wght-normal.woff2', 'font/woff2')}"); font-weight: 1 1000; }}
* {{ margin: 0; box-sizing: border-box; }}
body {{ width: 1280px; height: 640px; overflow: hidden; background: #BCDDE8; font-family: "Sofia Sans", sans-serif; color: #1E1E24; position: relative; }}
.galho {{ position: absolute; left: 0; right: 0; bottom: 0; height: 22px; background: #75523F; }}
.texto {{ position: absolute; left: 72px; top: 96px; width: 470px; }}
.texto img {{ width: 300px; display: block; }}
h1 {{ font-size: 46px; line-height: 1.12; font-weight: 800; margin-top: 44px; letter-spacing: -0.5px; }}
p {{ font-size: 25px; line-height: 1.35; margin-top: 22px; color: #2C3A42; font-weight: 500; }}
.tela {{ position: absolute; right: 48px; top: 100px; width: 640px; border-radius: 14px; box-shadow: 0 18px 48px rgba(16, 52, 66, .28); }}
</style></head><body>
<div class="texto">
  <img src="{dado('marca/logo-horizontal.svg', 'image/svg+xml')}" alt="">
  <h1>Suas conversas no WhatsApp Web, escondidas com Alt+S.</h1>
  <p>Respostas prontas, temas e atendimento. Grátis, sem conta e sem servidor.</p>
</div>
<img class="tela" src="{dado('docs/imagens/readme-inicio.png', 'image/png')}" alt="">
<div class="galho"></div>
</body></html>"""

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CHROME)
    pg = b.new_page(viewport={"width": 1280, "height": 640})
    pg.set_content(PAGINA)
    pg.wait_for_timeout(500)
    pg.screenshot(path=str(SAIDA))
    b.close()
print(SAIDA.relative_to(RAIZ), f"{SAIDA.stat().st_size // 1024} KB")
