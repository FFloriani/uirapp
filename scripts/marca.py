"""Fonte única da marca Uirapp: pássaro, letras, ícones e estados do mascote, tudo em vetor.

Uso: python scripts/marca.py
Gera marca/*.svg e marca/icones/*.png. Não edite os SVG à mão: mude aqui e rode de novo.
As coordenadas usam a grade das artes de 22/11/2026 (pássaro 1024x1024; nome 1536x1024).
"""
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
MARCA = RAIZ / "marca"

ESCARLATE, CARVAO, BICO, BRANCO, CREME = "#E63323", "#1E1E24", "#FF8A3D", "#FFFFFF", "#FFF3E8"

# --- pássaro -----------------------------------------------------------------
CABECA = ("M212 598C211 553 242 511 270 472C299 432 312 399 331 359C379 258 466 190 575 190"
          "C653 190 722 229 758 292L766 377C761 405 764 423 776 445C759 483 721 505 668 506"
          "C581 508 558 461 461 460C405 459 352 474 303 503C261 526 222 565 212 598Z")
# o corpo sobe um pouco por baixo da cabeça para não abrir fresta na divisa
CORPO = ("M212.5 594C222 560 261 520 303 497C352 468 405 453 461 454C558 455 581 502 668 500"
         "C721 499 757 477 773 441L776 445C794 480 803 517 803 557C803 714 664 829 497 829"
         "C441 829 389 817 344 792L213 856C198 862 188 849 195 835L254 722"
         "C226 688 212 647 212 604Z")
BICO_FECHADO = ("M758 292C795 292 836 305 853 321C858 326 855 331 848 335L772 376"
                "C758 382 737 384 725 372C714 361 716 346 722 333C731 314 743 301 758 292Z")
BICO_ABERTO = ("M758 292C795 283 832 279 859 283C867 285 867 292 860 296L788 340L847 370"
               "C854 375 852 382 843 383C810 388 763 390 734 379C716 372 711 352 722 333"
               "C731 314 743 301 758 292Z")


def olho(estado="acordado"):
    if estado == "silencio":  # olho fechado
        return f'<path d="M590 318Q636 372 682 318" fill="none" stroke="{CARVAO}" stroke-width="27" stroke-linecap="round"/>'
    if estado == "cantando":  # olho sorrindo
        return f'<path d="M590 342Q636 286 682 342" fill="none" stroke="{CARVAO}" stroke-width="27" stroke-linecap="round"/>'
    if estado == "alerta":    # olho arregalado
        return (f'<circle cx="636" cy="324" r="62" fill="{BRANCO}"/><circle cx="642" cy="324" r="35" fill="{CARVAO}"/>'
                f'<circle cx="653" cy="311" r="11" fill="{BRANCO}"/>')
    return f'<circle cx="636" cy="324" r="45.5" fill="{CARVAO}"/><circle cx="652" cy="307" r="14" fill="{BRANCO}"/>'


def passaro(estado="acordado"):
    bico = BICO_ABERTO if estado == "cantando" else BICO_FECHADO
    return (f'<path d="{CORPO}" fill="{CARVAO}"/><path d="{CABECA}" fill="{ESCARLATE}"/>'
            f'{olho(estado)}<path d="{bico}" fill="{BICO}"/>')


def passaro_mono(cor):
    """Uma cor só: olho e divisa do papo são vazados por máscara."""
    return (f'<mask id="vazado" maskUnits="userSpaceOnUse" x="0" y="0" width="1024" height="1024">'
            f'<path d="{CORPO}" fill="#fff"/><path d="{CABECA}" fill="#fff"/><path d="{BICO_FECHADO}" fill="#fff"/>'
            f'<circle cx="636" cy="324" r="45.5" fill="#000"/>'
            f'<path d="M205 602C222 562 261 523 303 500C352 471 405 456 461 457C558 458 581 505 668 503C721 502 759 480 782 438" '
            f'fill="none" stroke="#000" stroke-width="24"/></mask>'
            f'<rect width="1024" height="1024" fill="{cor}" mask="url(#vazado)"/>')


# --- nome ---------------------------------------------------------------------
def oval(cx, cy, rx, ry):
    return f"M{cx - rx} {cy}a{rx} {ry} 0 1 0 {2 * rx} 0a{rx} {ry} 0 1 0 {-2 * rx} 0Z"


LETRA_U = ("M552 428C552 415 562 406 575 406H581C594 406 603 415 603 428V520C603 543 616 555 636 555"
           "C656 555 669 543 669 520V428C669 415 678 406 691 406H699C712 406 721 415 721 428V517"
           "C721 570 686 602 636 602C586 602 552 570 552 517Z")
LETRA_R = ("M825 578V470C825 457 836 448 848 448C862 448 870 454 873 463C885 451 896 446 907 446"
           "C923 446 932 457 932 474C932 493 919 500 902 496C886 492 874 504 874 526V578"
           "C874 592 865 601 849 601C834 601 825 592 825 578Z")
LETRA_A = ("M1052 456C1056 451 1064 448 1075 448C1089 448 1099 457 1099 471V578C1099 592 1089 601 1075 601"
           "C1064 601 1055 596 1052 589C1041 598 1027 603 1009 603C969 603 937 568 937 524"
           "C937 480 970 446 1015 446C1030 446 1042 450 1052 456Z" + oval(1019, 523.5, 32, 36))
LETRA_P = ("M1125 636V470C1125 457 1134 448 1148 448C1159 448 1167 452 1172 460C1183 451 1197 446 1213 446"
           "C1251 446 1280 480 1280 524C1280 568 1250 603 1210 603C1195 603 1182 599 1172 591V636"
           "C1172 650 1163 659 1148 659C1134 659 1125 650 1125 636Z" + oval(1200, 522, 31, 35.5))


def nome(tinta=CARVAO, pingo=ESCARLATE):
    return (f'<g fill="{tinta}" fill-rule="evenodd"><path d="{LETRA_U}"/>'
            f'<rect x="748" y="456" width="50" height="144.5" rx="22"/><path d="{LETRA_R}"/><path d="{LETRA_A}"/>'
            f'<path d="{LETRA_P}"/><path d="{LETRA_P}" transform="translate(173.5 0)"/></g>'
            f'<circle cx="773.5" cy="419.5" r="25.5" fill="{pingo}"/>')


# posição do pássaro dentro da logo horizontal
NO_LOCKUP = "translate(-22.8 183.9) scale(.6182)"


def tile(tam=1024, ocupa=.76):
    esc = ocupa * tam / 666  # 666 = maior lado do pássaro
    tx, ty = tam / 2 - 524 * esc, tam / 2 - 524 * esc
    return (f'<rect width="{tam}" height="{tam}" rx="{tam * .22:g}" fill="{CREME}"/>'
            f'<g transform="translate({tx:.3f} {ty:.3f}) scale({esc:.5f})">{passaro()}</g>')


def icone16():
    """Desenho próprio para 16 px: poucas formas, olho e bico exagerados."""
    return (f'<rect width="16" height="16" rx="3" fill="{CREME}"/>'
            f'<path d="M2 8Q2.5 6 12 6.2Q14 8 13.5 10.5C12.8 14 8.5 14.8 5.2 13.4L1.2 15L2.6 11.6Q1.7 10 2 8Z" fill="{CARVAO}"/>'
            f'<path d="M2 8.4C3.8 6 4 1 8.5 1C10.8 1 12 2.6 12.2 4.4V7Q10.5 9 7.5 7.8Q4.5 6.8 2 8.4Z" fill="{ESCARLATE}"/>'
            f'<path d="M12 3.5L15.5 4.8L12 6.5Z" fill="{BICO}"/><rect x="9" y="3" width="2" height="2" rx=".6" fill="{CARVAO}"/>')


def svg(caixa, miolo, titulo="Uirapp"):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{caixa}" role="img" aria-label="{titulo}">'
            f'{miolo}</svg>\n')


CAIXA_PASSARO = "180 178 690 696"
CAIXA_LOCKUP = "84 290 1382 434"


def arquivos():
    a = {f"mascote-{e}.svg": svg(CAIXA_PASSARO, passaro(e), f"Uirapp, {e}")
         for e in ("acordado", "silencio", "cantando", "alerta")}
    a["simbolo.svg"] = svg(CAIXA_PASSARO, passaro())
    a["simbolo-mono-preto.svg"] = svg(CAIXA_PASSARO, passaro_mono(CARVAO))
    a["simbolo-mono-branco.svg"] = svg(CAIXA_PASSARO, passaro_mono(BRANCO))
    a["nome.svg"] = svg("546 388 914 278", nome())
    a["nome-claro.svg"] = svg("546 388 914 278", nome("#F6F4F0"))
    a["logo-horizontal.svg"] = svg(CAIXA_LOCKUP, f'<g transform="{NO_LOCKUP}">{passaro()}</g>' + nome())
    a["logo-horizontal-escura.svg"] = svg(
        "54 290 1416 440", f'<g transform="translate(62 298) scale({424 / 1024:.5f})">{tile()}</g>' + nome("#F6F4F0"))
    a["icone.svg"] = svg("0 0 1024 1024", tile())
    a["icone-32.svg"] = svg("0 0 1024 1024", tile(ocupa=.91))
    a["icone-16.svg"] = svg("0 0 16 16", icone16())
    return a


def exporta_png():
    from playwright.sync_api import sync_playwright

    fontes = {16: "icone-16", 32: "icone-32", 48: "icone", 128: "icone", 512: "icone", 1024: "icone"}
    with sync_playwright() as p:
        nav = p.chromium.launch(executable_path=r"C:\Program Files\Google\Chrome\Application\chrome.exe")
        for t, arq in fontes.items():
            pg = nav.new_page(viewport={"width": t, "height": t})
            s = (MARCA / f"{arq}.svg").read_text("utf-8")
            pg.set_content(f"<style>html,body{{margin:0;background:transparent}}svg{{display:block;width:{t}px;height:{t}px}}</style>{s}")
            pg.screenshot(path=str(MARCA / "icones" / f"icone-{t}.png"), omit_background=True)
            pg.close()
        nav.close()


if __name__ == "__main__":
    (MARCA / "icones").mkdir(parents=True, exist_ok=True)
    for n, s in arquivos().items():
        (MARCA / n).write_text(s, encoding="utf-8", newline="\n")
    exporta_png()
    print("marca gerada em", MARCA)
