"""Gera a vitrine do design system. Tudo vem do DESIGN.md, da marca e dos protótipos."""
import base64
import html
import re

esc = html.escape


def contraste(a, b):
    def lum(h):
        c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
        c = [x / 12.92 if x <= .03928 else ((x + .055) / 1.055) ** 2.4 for x in c]
        return .2126 * c[0] + .7152 * c[1] + .0722 * c[2]

    x, y = sorted((lum(a), lum(b)), reverse=True)
    return (x + .05) / (y + .05)


def arquivo_img(m, caminho, classe="", alt="", largura=None):
    f = m.RAIZ / caminho
    tipo = "image/png" if f.suffix == ".png" else "image/svg+xml"
    tam = f' width="{largura}" height="{largura}"' if largura else ""
    return f'<img class="{classe}" alt="{esc(alt)}"{tam} src="data:{tipo};base64,{base64.b64encode(f.read_bytes()).decode()}">'


def quadro(m, pagina, inicio, classe, titulo):
    return (f'<iframe class="{classe}" title="{esc(titulo)}" sandbox="allow-scripts allow-forms" '
            f'srcdoc="{esc(m.solto(pagina, inicio))}"></iframe>')


def sec_marca(m):
    img = lambda n, c="logo": arquivo_img(m, f"marca/{n}.svg", c, n)
    ics = "".join(arquivo_img(m, f"marca/icones/icone-{t}.png", "", f"ícone {t} px", t) for t in (16, 32, 48, 128))
    return ('<div class="marcas">'
            f'<div class="marca-campo">{img("logo-horizontal")}</div>'
            f'<div class="marca-campo marca-escura">{img("logo-horizontal-escura")}</div>'
            f'<div class="marca-campo">{img("simbolo-mono-preto", "mono")}</div>'
            f'<div class="marca-campo marca-acao">{img("simbolo-mono-branco", "mono")}</div>'
            f'<div class="marca-campo marca-barra">{ics}</div>'
            f'<div class="marca-campo marca-barra-escura">{ics}</div></div>')


def sec_mascote(m):
    itens = (("Acordado", "conversas à vista", "acordado", "aberto"), ("Silêncio", "conversas escondidas", "silencio", "silencio"),
             ("Cantando", "deu certo", "cantando", "aberto"), ("Alerta", "algo mudou, cobriu tudo", "alerta", "alerta"))
    return '<div class="humores">' + "".join(
        f'<div class="humor"><div class="palco" data-estado="{ceu}" data-humor="{h}">{m.passaro()}{m.galho()}</div>'
        f"<p><b>{n}</b><span>{d}</span></p></div>" for n, d, h, ceu in itens) + "</div>"


def sec_cores(m, d, p):
    c = d["colors"]
    ceus = (("ceu-aberto", "on-ceu-aberto", "À vista"), ("ceu-silencio", "on-ceu-silencio", "Escondidas"),
            ("ceu-neblina", "on-ceu-aberto", "Fechado"), ("ceu-alerta", "on-warning", "Alerta"))
    r = '<div class="ceus">' + "".join(
        f'<div class="ceu" style="background:{c[f]};color:{c[t]}"><b>{n}</b><span>{f}</span><span>{c[f]}</span></div>'
        for f, t, n in ceus) + "</div>"
    am = lambda h: f'<span class="amostra" style="background:{h}"></span>{h}'
    tema = d["themes"]["noite"]
    r += '<h3>Interface</h3><div class="rola"><table><thead><tr><th>Token</th><th>Claro</th><th>Escuro</th><th>Papel</th></tr></thead><tbody>'
    for k in tema:
        r += f"<tr><td>{k}</td><td>{am(c[k])}</td><td>{am(m.resolve(d, tema[k]))}</td><td>{esc(p.get('colors.' + k, ''))}</td></tr>"
    r += '</tbody></table></div><h3>Marca, poleiro e plumagens</h3><div class="rola"><table class="estreita"><tbody>'
    for k, v in c.items():
        if k in ("escarlate", "carvao", "bico", "creme", "galho", "folha") or k.startswith("plumagem-"):
            r += f"<tr><td>{k}</td><td>{am(v)}</td><td>{esc(p.get('colors.' + k, ''))}</td></tr>"
    return r + "</tbody></table></div>"


def sec_tipos(d, p):
    frases = {"display": "Conversas escondidas", "title": "Respostas prontas", "label": "Esconder conversas",
              "body": "Atendemos de segunda a sábado, das 9h às 18h.", "small": "Cobri a tela inteira."}
    return "".join(
        f'<div class="tipo"><small>{k}, {t["fontSize"]}, peso {t["fontWeight"]}<br>{esc(p.get("typography." + k, ""))}</small>'
        f'<span style="font:var(--tipo-{k})">{frases[k]}</span></div>' for k, t in d["typography"].items())


def sec_medidas(d):
    e = "".join(f'<div class="regua"><span>{k} &nbsp; {v}</span><i style="width:calc({v} * 3)"></i></div>' for k, v in d["spacing"].items())
    r = "".join(f'<div class="raio"><i style="border-radius:{v}"></i><span>{k}, {v}</span></div>' for k, v in d["rounded"].items())
    return f'<div class="medidas"><div><h3>Espaços, em escala 3x</h3>{e}</div><div><h3>Cantos</h3><div class="raios">{r}</div></div></div>'


def painel(m, tema, titulo):
    ic, est = m.icone, lambda nome, corpo: f'<div class="estado">{corpo}<small>{nome}</small></div>'
    bot = lambda classe, txt, extra="": f'<button type="button" class="botao {classe}" {extra}>{txt}</button>'
    chave = lambda rot, extra: f'<input class="interruptor" type="checkbox" role="switch" aria-label="{rot}" {extra}>'
    campo = lambda nome, extra="", apos="": (
        f'<div class="campo"><label class="campo-rotulo" for="{tema}-{nome}">{nome}</label>'
        f'<input class="entrada" id="{tema}-{nome}" {extra}>{apos}</div>')
    erro = f'<p class="campo-erro">{ic("alert-triangle")}Dê um nome à resposta.</p>'
    return f'''<div class="painel tema-{tema}"><h3>{titulo}</h3>
<h4>Botão principal</h4><div class="estados">{est("normal", bot("", "Salvar"))}{est("mouse", bot("ex-mouse", "Salvar"))}{est("pressionado", bot("ex-aperto", "Salvar"))}{est("foco", bot("ex-foco", "Salvar"))}{est("desabilitado", bot("", "Salvar", "disabled"))}</div>
<h4>Discreto, perigo e atalho</h4><div class="estados">{est("discreto", bot("botao-discreto", "Manter"))}{est("mouse", bot("botao-discreto ex-mouse", "Manter"))}{est("perigo", bot("botao-perigo", "Apagar"))}{est("mouse", bot("botao-perigo ex-mouse", "Apagar"))}{est("tecla", '<span class="tecla">Alt+S</span>')}</div>
<h4>Interruptor</h4><div class="estados">{est("ligado", chave("ligado", "checked"))}{est("desligado", chave("desligado", ""))}{est("foco", chave("foco", 'checked style="outline:3px solid var(--primary);outline-offset:2px"'))}{est("desabilitado", chave("desabilitado", "checked disabled"))}</div>
<h4>Linha: normal, mouse, foco</h4><div class="linhas">
<button type="button" class="linha">{ic("eye")}<span class="linha-texto">Privacidade</span><span class="linha-valor">Tudo</span>{ic("chevron-right")}</button>
<button type="button" class="linha ex-mouse">{ic("palette")}<span class="linha-texto">Plumagem</span><span class="linha-valor">Laranja</span>{ic("chevron-right")}</button>
<button type="button" class="linha ex-foco">{ic("message")}<span class="linha-texto">Respostas prontas</span>{ic("chevron-right")}</button></div>
<h4>Campo</h4>{campo("Normal")}{campo("Foco", 'style="outline:2px solid var(--primary);border-color:var(--primary)" value="Horário"')}{campo("Erro", 'aria-invalid="true"', erro)}{campo("Desabilitado", 'disabled value="Entrega"')}
<h4>Seletor e plumagem</h4><div class="segmentos"><label class="segmento"><input type="radio" name="{tema}-t" checked><span>Sistema</span></label><label class="segmento"><input type="radio" name="{tema}-t"><span>Claro</span></label><label class="segmento"><input type="radio" name="{tema}-t"><span>Escuro</span></label></div><br>
<div class="plumagens">{"".join(f'<label class="plumagem"><input type="radio" name="{tema}-p" {"checked" if i == 0 else ""}><span class="plumagem-ceu">{m.passaro("plumagem-" + v)}</span><span class="plumagem-nome">{n}</span></label>' for i, (v, n) in enumerate((("vermelha", "Vermelha"), ("laranja", "Laranja"), ("lenda", "Da lenda"))))}</div>
<h4>Aviso passageiro e aviso fixo</h4><div class="aviso" data-humor="cantando">{m.passaro()}<span>Resposta copiada</span></div><br>
<p class="nota">{ic("alert-triangle")}O WhatsApp mudou. Cobri a tela inteira.</p>
<h4>Diálogo</h4><div class="dialogo"><h2>Apagar resposta?</h2><p>Não dá para desfazer.</p><div class="dialogo-acoes">{bot("botao-discreto", "Manter")}{bot("botao-perigo", "Apagar")}</div></div>
</div>'''


def sec_telas(m):
    lista = (("Primeira vez", "boas-vindas?tema=dia"), ("Conversas à vista", "inicio?tema=dia"),
             ("Conversas escondidas", "inicio?tema=dia&silencio=1"), ("O WhatsApp mudou", "inicio?tema=dia&estado=alerta"),
             ("WhatsApp fechado", "inicio?tema=dia&estado=fechado"), ("Privacidade", "privacidade?tema=dia"),
             ("Plumagem", "plumagem?tema=dia&plumagem=lenda"), ("Respostas prontas", "respostas?tema=dia"),
             ("Sem respostas", "respostas?tema=dia&vazio"), ("Criar resposta, com erro", "nova?tema=dia&erro"),
             ("O que o Uirapp acessa", "acesso?tema=dia"), ("Resposta copiada", "respostas?tema=dia&copiada"),
             ("À vista, escuro", "inicio?tema=noite"), ("Escondidas, escuro", "inicio?tema=noite&silencio=1&plumagem=laranja"),
             ("Plumagem, escuro", "plumagem?tema=noite"))
    return '<div class="telas">' + "".join(
        f'<figure class="tela-item">{quadro(m, "popup", i, "janela", n)}<figcaption>{n}</figcaption></figure>'
        for n, i in lista) + "</div>"


def sec_contraste(m, d):
    r = '<div class="rola"><table><thead><tr><th>Componente</th><th>Amostra</th><th>Contraste</th></tr></thead><tbody>'
    for k, v in d["components"].items():
        if "textColor" in v and "backgroundColor" in v:
            t, f = m.resolve(d, v["textColor"]), m.resolve(d, v["backgroundColor"])
            n = f"{contraste(t, f):.1f}".replace(".", ",")
            r += f'<tr><td>{k}</td><td><span class="par" style="color:{t};background:{f}">Esconder conversas</span></td><td>{n}</td></tr>'
    return r + "</tbody></table></div>"


def sec_regras(m):
    corpo = m.le("DESIGN.md").split("## Do's and Don'ts", 1)[1].strip().splitlines()
    linhas = [re.sub(r"`([^`]+)`", r"<code>\1</code>", esc(l[2:])) for l in corpo if l.startswith("- ")]
    col = lambda t, itens: f"<div><h3>{t}</h3><ul>" + "".join(f"<li>{i}</li>" for i in itens) + "</ul></div>"
    return ('<div class="faca">' + col("Fazer", [l for l in linhas if not l.startswith("Não")])
            + col("Não fazer", [l for l in linhas if l.startswith("Não")]) + "</div>")


def css_todo(m, d):
    fonte = base64.b64encode((m.RAIZ / "ui/fontes/sofia-sans-latin-wght-normal.woff2").read_bytes()).decode()
    css = m.le("ui/tokens.css") + m.le("ui/componentes.css").replace(
        "fontes/sofia-sans-latin-wght-normal.woff2", f"data:font/woff2;base64,{fonte}")
    css += ":root{" + "".join(f"--{k}:{v};" for k, v in d["colors"].items() if k.startswith("noite-")) + "}\n"
    tema = d["themes"]["noite"]
    css += ".tema-dia{" + "".join(f"--{k}:{d['colors'][k]};" for k in tema) + "}\n"
    css += ".tema-noite{" + "".join(f"--{k}:{m.resolve(d, v)};" for k, v in tema.items()) + "}\n"
    return css + m.le("design-system/vitrine.css")


def monta(m, d):
    p = m.papeis()
    partes = {
        "css": css_todo(m, d), "nome": m.nome(), "passaro": m.passaro(), "galho": m.galho(),
        "janela_principal": quadro(m, "popup", "inicio?tema=dia", "janela", "Uirapp funcionando"),
        "conversa": quadro(m, "conversa", "silencio?tema=dia", "conversa-quadro", "Uirapp dentro de uma conversa"),
        "marca": sec_marca(m), "mascote": sec_mascote(m), "cores": sec_cores(m, d, p), "tipos": sec_tipos(d, p),
        "medidas": sec_medidas(d),
        "componentes": f'<div class="paineis">{painel(m, "dia", "Claro")}{painel(m, "noite", "Escuro")}</div>',
        "telas": sec_telas(m), "contraste": sec_contraste(m, d), "regras": sec_regras(m),
    }
    t = re.sub(r"\{\{(\w+)\}\}", lambda x: partes[x.group(1)], m.le("design-system/fonte.html"))
    return t.replace("<!doctype html>", f"<!doctype html>\n<!-- {m.AVISO} -->", 1)
