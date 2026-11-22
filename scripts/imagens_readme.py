"""Imagens do README: a extensão de verdade num Brave descartável, com o WhatsApp de mentira e dados de exemplo.

Uso: python scripts/imagens_readme.py   (precisa do Brave instalado; nada sai para a internet)
Gera docs/imagens/readme-inicio.png, readme-janela.png e readme-ninho.png.
"""
import io
import sys
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter
from playwright.sync_api import sync_playwright

sys.dont_write_bytecode = True
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))
import testar  # noqa: E402

SAIDA = RAIZ / "docs/imagens"
FUNDO = "#E6EEF1"
DIA = 24 * 3600 * 1000

agora = int(time.time() * 1000)
EXEMPLO = {
    "respostas": [
        {"id": "r1", "nome": "Horário", "atalho": "horario",
         "texto": "{saudacao}! Atendemos de segunda a sábado, das 9h às 18h."},
        {"id": "r2", "nome": "Entrega", "atalho": "entrega",
         "texto": "Entregamos em toda a cidade em até 2 horas. A taxa depende do bairro."},
        {"id": "r3", "nome": "Agradecer", "atalho": "obrigado",
         "texto": "Obrigado pela preferência, {primeiro_nome}! Qualquer dúvida, é só chamar."},
    ],
    "fichas": [
        {"id": "f1", "nome": "Carla Mendes", "etapa": "novo", "etiquetas": ["bolo", "aniversário"], "criada": agora},
        {"id": "f2", "nome": "Rafael Lima", "etapa": "novo", "etiquetas": ["orçamento"], "criada": agora},
        {"id": "f3", "nome": "Juliana Costa", "etapa": "conversando", "etiquetas": ["casamento"], "valor": 180000, "criada": agora},
        {"id": "f4", "nome": "Pedro Alves", "etapa": "conversando", "etiquetas": ["retorno"], "criada": agora},
        {"id": "f5", "nome": "Mariana Rocha", "etapa": "proposta", "etiquetas": ["vip"], "valor": 45000, "criada": agora},
        {"id": "f6", "nome": "Bruno Martins", "etapa": "fechado", "etiquetas": ["entregue"], "valor": 32000, "criada": agora},
    ],
    "lembretes": [{"id": "l1", "titulo": "Confirmar o bolo da Juliana", "quando": agora + DIA, "fichaId": "f3"}],
}


def png(dados):
    return Image.open(io.BytesIO(dados)).convert("RGB")


def cantos(img, raio):
    mascara = Image.new("L", img.size, 0)
    ImageDraw.Draw(mascara).rounded_rectangle((0, 0, img.width - 1, img.height - 1), raio, fill=255)
    return img, mascara


def cola_com_sombra(fundo, img, xy, raio=12):
    img, mascara = cantos(img, raio)
    sombra = Image.new("RGBA", (img.width + 60, img.height + 60), (0, 0, 0, 0))
    ImageDraw.Draw(sombra).rounded_rectangle((30, 34, 30 + img.width, 34 + img.height), raio, fill=(20, 40, 50, 70))
    sombra = sombra.filter(ImageFilter.GaussianBlur(14))
    fundo.paste(sombra, (xy[0] - 30, xy[1] - 30), sombra)
    fundo.paste(img, xy, mascara)


def janela(n, tela):
    j = testar.abre_popup_em(n, tela)
    j.set_viewport_size({"width": 360, "height": 551})  # corta no fim de uma linha, não no meio
    j.wait_for_timeout(400)
    return png(j.screenshot(animations="disabled"))


def main():
    SAIDA.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        n = testar.Navegador(p, "brave")
        try:
            n.ajustes()
            n.janela.evaluate("d => UirappDeposito.grava(d)", EXEMPLO)
            n.poe(silencio=True)
            n.abre(v="a")
            n.wa.wait_for_timeout(800)
            whatsapp = png(n.foto())
            inicio = janela(n, "inicio")
            respostas = janela(n, "respostas")
            aparencia = janela(n, "aparencia")

            pg = n.ctx.new_page()
            pg.set_viewport_size({"width": 1180, "height": 530})
            pg.goto(f"chrome-extension://{n.id}/ninho.html#atendimento")
            testar.espera_pronta(pg)
            pg.wait_for_timeout(600)
            ninho = png(pg.screenshot(animations="disabled"))
        finally:
            n.fecha()

    # 1. o WhatsApp escondido com a janela do Uirapp aberta por cima, como no navegador
    capa = whatsapp.copy()
    cola_com_sombra(capa, inicio, (capa.width - inicio.width - 28, 14))
    capa.save(SAIDA / "readme-inicio.png", optimize=True)

    # 2. três telas da janela lado a lado
    m = 40
    faixa = Image.new("RGB", (3 * respostas.width + 4 * m, respostas.height + 2 * m), FUNDO)
    for i, tela in enumerate((inicio, respostas, aparencia)):
        cola_com_sombra(faixa, tela, (m + i * (tela.width + m), m))
    faixa.save(SAIDA / "readme-janela.png", optimize=True)

    # 3. o Ninho
    quadro = Image.new("RGB", (ninho.width + 2 * m, ninho.height + 2 * m), FUNDO)
    cola_com_sombra(quadro, ninho, (m, m), raio=10)
    quadro.save(SAIDA / "readme-ninho.png", optimize=True)
    for nome in ("readme-inicio.png", "readme-janela.png", "readme-ninho.png"):
        print(nome, Image.open(SAIDA / nome).size, f"{(SAIDA / nome).stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
