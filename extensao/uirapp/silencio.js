// O Uirapp dentro do WhatsApp Web, no mundo isolado da extensão.
//
// Só lê a estrutura da tela e aplica estilo. Não lê texto de conversa para guardar, não clica, não escreve e não
// envia nada no WhatsApp. Na dúvida, fecha: o erro é sempre mais escondido que o normal.
"use strict";

(() => {
  if (window.top !== window) return;

  const U = globalThis.Uirapp;
  const T = (s) => globalThis.UirappIdioma?.t(s) ?? s;
  const { ANCORAS, ARTE } = globalThis.UirappPacote;
  const A = ANCORAS.reconhece;
  const ESTRUTURA = ANCORAS.estrutura.join(",");
  const DEMORA_CARREGAR = 15000;
  const DEMORA_MUDOU = 5000;
  const raiz = document.documentElement;
  const nasceu = Date.now();

  let ajustes = U.ajustes();
  let escondido = false;
  let lido = false;
  let quebrou = false;
  let reforcado = false; // sem o CSS de origem USER, o site poderia vencer o parcial: fica cheio
  let modo = "espera"; // espera | fora | aberto | cheio | parcial | alerta | parou
  let marca = null; // o valor que data-uirapp tem que ter; null = fechado
  let estranhoDesde = 0;
  let atividade = Date.now();
  let ultimaTecla = 0;
  let desenho = "";
  let tela = null;
  let vigiaPagina = null;
  let mutei = false;
  let tituloOriginal = null;
  let vigiaTitulo = null;

  const viva = () => {
    try {
      return Boolean(chrome.runtime?.id);
    } catch {
      return false;
    }
  };

  function guarda(dado) {
    try {
      chrome.storage.local.set(dado).catch(() => {});
    } catch {
      // extensão recarregada: o batimento cobre a tela se ela estava escondida
    }
  }

  // ---------- desenho: tudo nasce por createElement, nada por texto HTML
  function el(tipo, classe, ...filhos) {
    const e = document.createElement(tipo);
    if (classe) e.className = classe;
    e.append(...filhos);
    return e;
  }

  function arte([tipo, atributos, filhos]) {
    const svg = document.createElementNS("http://www.w3.org/2000/svg", tipo);
    for (const [k, v] of Object.entries(atributos)) svg.setAttribute(k, v);
    for (const f of filhos) svg.append(arte(f));
    return svg;
  }

  function galho() {
    const g = el("span", "galho", arte(ARTE.folhas));
    g.setAttribute("aria-hidden", "true");
    return g;
  }

  function montaTela() {
    const casa = document.createElement("uirapp-casa");
    for (const [p, v] of Object.entries({
      all: "initial", position: "fixed", inset: "0", "z-index": "2147483647", display: "block",
      visibility: "visible", opacity: "1", "pointer-events": "none",
    })) casa.style.setProperty(p, v, "important");

    const sombra = casa.attachShadow({ mode: "closed" });
    const folha = new CSSStyleSheet();
    folha.replaceSync(ARTE.css);
    sombra.adoptedStyleSheets = [folha];

    const cena = el("div", "cena");
    cena.setAttribute("aria-hidden", "true");

    const botao = el("button", "flutuante", arte(ARTE.passaro));
    botao.type = "button";
    botao.addEventListener("click", (e) => {
      if (!e.isTrusted) return;
      // sem isto, o próximo Enter de quem estava digitando mostraria tudo de novo
      if (e.detail > 0) botao.blur();
      alterna();
    });

    const titulo = el("h2", "");
    titulo.id = "cobertura-titulo";
    const acao = el("button", "botao");
    acao.type = "button";
    acao.addEventListener("click", (e) => {
      if (!e.isTrusted) return;
      if (modo === "parou") location.reload();
      else muda(false);
    });
    const apoio = el("p", "", "Cobri a tela inteira.");
    apoio.className = "cobertura-apoio";
    const cobertura = el("div", "cobertura", el("div", "vazio-poleiro", arte(ARTE.passaro), galho()), titulo, apoio, acao);
    cobertura.dataset.humor = "alerta";
    cobertura.setAttribute("role", "alertdialog");
    cobertura.setAttribute("aria-labelledby", titulo.id);

    sombra.append(el("div", "casa", cena, botao, cobertura));
    for (const tipo of ["pointerdown", "pointerup", "mousedown", "mouseup", "click", "dblclick", "contextmenu"]) {
      casa.addEventListener(tipo, (e) => e.stopPropagation());
    }
    return { casa, cena, botao, cobertura, titulo, acao, apoio, fonte: false };
  }

  function carregaFonte() {
    if (tela.fonte) return;
    tela.fonte = true;
    try {
      const bytes = Uint8Array.from(atob(ARTE.fonte), (c) => c.charCodeAt(0));
      const fonte = new FontFace(ARTE.familia, bytes, { weight: "1 1000" });
      document.fonts.add(fonte);
      fonte.load().catch(() => {});
    } catch {
      // sem a fonte fica a do sistema
    }
  }

  // A cena é igual para qualquer conversa: usa só a divisão dos painéis, nunca tamanho ou número de conteúdo.
  function desenhaCena() {
    const lado = document.querySelector(A.lado)?.getBoundingClientRect();
    const temLado = lado && lado.width > 100 && lado.width < innerWidth * 0.9;
    const trilho = Math.round(temLado ? lado.left : innerWidth > 720 ? 64 : 0);
    const largura = Math.round(temLado ? lado.width : innerWidth > 720 ? Math.max(280, innerWidth * 0.3) : innerWidth);
    const linhas = Math.min(40, Math.max(1, Math.floor((innerHeight - 88) / 76)));
    const chave = `${trilho} ${largura} ${linhas}`;
    if (chave === desenho) return;
    desenho = chave;

    const foto = () => el("span", "cena-foto", arte(ARTE.passaro));
    const lista = el("div", "cena-lista", el("div", "cena-busca"));
    for (let i = 0; i < linhas; i++) {
      lista.append(el("div", "cena-linha", foto(),
        el("div", "cena-textos", el("i", "cena-tarja cena-nome"), el("i", "cena-tarja cena-previa"))));
    }
    const baloes = el("div", "cena-baloes");
    for (const meu of [false, false, true, false, true]) baloes.append(el("i", `cena-tarja cena-balao${meu ? " meu" : ""}`));
    const conversa = el("div", "cena-conversa",
      el("div", "cena-topo", foto(), el("i", "cena-tarja cena-nome")), baloes, el("div", "cena-escrever"));

    tela.cena.style.setProperty("grid-template-columns", `${trilho}px ${largura}px minmax(0, 1fr)`);
    tela.cena.replaceChildren(el("div", "cena-trilho"), lista, conversa);
  }

  function pintaTela(novo) {
    if (novo === "espera" || novo === "fora") {
      tela?.casa.remove();
      return;
    }
    if (!document.body) return;
    tela ??= montaTela();
    if (tela.casa.parentNode !== raiz) raiz.append(tela.casa);

    const { casa, cena, botao, cobertura, titulo, acao, apoio } = tela;
    casa.setAttribute("data-plumagem", ajustes.plumagem);
    if (ajustes.tema) casa.setAttribute("data-tema", ajustes.tema);
    else casa.removeAttribute("data-tema");

    const coberto = novo === "alerta" || novo === "parou";
    if (novo === "cheio") desenhaCena();
    cena.hidden = novo !== "cheio";
    // "sem passarinho" vale só com as conversas à vista: escondido, ele é o caminho de volta
    botao.hidden = coberto || (novo === "aberto" && ajustes.passaro === "oculto");
    botao.dataset.lado = ajustes.passaro === "esquerda" ? "esquerda" : "direita";

    const oculto = novo !== "aberto";
    globalThis.UirappIdioma?.aplica(ajustes.idioma, null);
    const verbo = T(oculto ? "Mostrar conversas" : "Esconder conversas");
    botao.dataset.humor = oculto ? "silencio" : "acordado";
    botao.setAttribute("aria-pressed", String(oculto));
    botao.setAttribute("aria-label", verbo);
    botao.title = `${verbo} (Alt+S)`;

    const apareceu = coberto && (cobertura.hidden || modo !== novo);
    cobertura.hidden = !coberto;
    if (!coberto) return;
    titulo.textContent = T(novo === "parou" ? "O Uirapp parou" : "O WhatsApp mudou");
    acao.textContent = T(novo === "parou" ? "Recarregar a página" : "Descobrir a tela");
    apoio.textContent = T("Cobri a tela inteira.");
    if (apareceu) {
      carregaFonte();
      acao.focus({ preventScroll: true });
    }
  }

  // ---------- o que está na tela
  function estruturaLimpa() {
    for (const e of document.querySelectorAll(ESTRUTURA)) {
      if (e.hasAttribute("title")) return false;
      for (const n of e.childNodes) if (n.nodeType === Node.TEXT_NODE && n.nodeValue.trim()) return false;
    }
    return true;
  }

  function reconhece() {
    if (document.querySelector(A.lista)) {
      const temCelula = document.querySelector(A.celula);
      if (temCelula && !document.querySelector(A.titulo)) return "estranho";
      const linha = document.querySelector(A.linha);
      if (!temCelula && linha?.childElementCount) return "estranho";
      if (document.querySelector(A.conversa) && !document.querySelector(A.mensagens)) return "estranho";
      return "pronto";
    }
    if (document.querySelector(A.entrada)) return "entrada";
    if (document.querySelector(A.carregando) || Date.now() - nasceu < DEMORA_CARREGAR) return "carregando";
    return "estranho";
  }

  function decide() {
    if (quebrou) return "parou";
    if (!viva()) return !lido || escondido ? "parou" : "fora";
    if (!lido) return "espera";
    if (!escondido) return ajustes.consentido ? "aberto" : "fora";

    const achou = reconhece();
    const tudo = U.CATEGORIAS.every((c) => ajustes.esconder[c]);
    if (achou === "pronto") {
      estranhoDesde = 0;
      if (tudo || !reforcado) return "cheio";
      return estruturaLimpa() ? "parcial" : "alerta";
    }
    if (achou !== "estranho") {
      estranhoDesde = 0;
      return "cheio";
    }
    estranhoDesde ||= Date.now();
    return Date.now() - estranhoDesde >= DEMORA_MUDOU ? "alerta" : "cheio";
  }

  function marcaDe(novo) {
    if (novo === "espera") return null;
    if (novo === "fora" || novo === "aberto") return "aberto";
    if (novo === "cheio") return "cheio";
    if (novo !== "parcial") return "coberto";
    const ve = U.CATEGORIAS.filter((c) => !ajustes.esconder[c]).map((c) => `ve-${c}`);
    return ["parcial", ajustes.plumagem, ...ve].join(" ");
  }

  function assinaMarca() {
    if (marca === null) {
      if (raiz.hasAttribute("data-uirapp")) raiz.removeAttribute("data-uirapp");
    } else if (raiz.getAttribute("data-uirapp") !== marca) {
      raiz.setAttribute("data-uirapp", marca);
    }
  }

  function largaOQueEstavaAberto() {
    const foco = document.activeElement;
    if (foco && foco !== document.body && foco !== tela?.casa) foco.blur?.();
    getSelection()?.removeAllRanges();
    if (document.pictureInPictureElement) document.exitPictureInPicture().catch(() => {});
    if (document.fullscreenElement) document.exitFullscreen().catch(() => {});
  }

  // o que acompanha o silêncio, conforme os ajustes: som da aba e título neutro
  function acompanha(fechado) {
    const quer = fechado && ajustes.som;
    if (quer !== mutei) {
      mutei = quer;
      try {
        chrome.runtime.sendMessage({ uirapp: "som", mudo: quer }).catch(() => {});
      } catch {
        // extensão recarregada
      }
    }
    const neutro = fechado && ajustes.titulo;
    if (neutro && tituloOriginal === null) {
      tituloOriginal = document.title;
      document.title = "WhatsApp";
      vigiaTitulo = new MutationObserver(() => {
        if (document.title !== "WhatsApp") {
          tituloOriginal = document.title;
          document.title = "WhatsApp";
        }
      });
      if (document.head) vigiaTitulo.observe(document.head, { childList: true, subtree: true, characterData: true });
    } else if (!neutro && tituloOriginal !== null) {
      vigiaTitulo?.disconnect();
      document.title = tituloOriginal;
      tituloOriginal = null;
    }
  }

  function aplica() {
    try {
      const antes = modo;
      const novo = decide();
      marca = marcaDe(novo);
      const abrindo = novo === "fora" || novo === "aberto";
      // ao abrir, desenha e depois solta; ao fechar, fecha e depois desenha
      if (!abrindo) assinaMarca();
      pintaTela(novo);
      if (abrindo) assinaMarca();
      modo = novo;

      const estavaAberto = antes === "fora" || antes === "aberto";
      if (estavaAberto && !abrindo) largaOQueEstavaAberto();
      acompanha(!abrindo && novo !== "espera");
      vigiaPagina ??= new MutationObserver(aplica);
      vigiaPagina.disconnect();
      if (novo === "parcial") {
        vigiaPagina.observe(document.body, {
          childList: true, subtree: true, characterData: true, attributes: true, attributeFilter: ["title"],
        });
      }
    } catch {
      quebrou = true;
      modo = "parou";
      marca = "coberto";
      assinaMarca();
      try {
        pintaTela("parou");
      } catch {
        // sem tela própria, o CSS já deixou tudo fechado
      }
    }
  }

  // ---------- gestos
  function muda(novo, porTecla = false) {
    if (novo === escondido) return;
    escondido = novo;
    estranhoDesde = 0;
    atividade = Date.now();
    const dado = { silencio: novo };
    if (porTecla) {
      ultimaTecla = Date.now();
      dado.tecla = ultimaTecla;
    }
    guarda(dado);
    aplica();
  }

  function alterna(porTecla = false) {
    if (!lido || modo === "parou") return;
    if (!ajustes.consentido && !escondido) return;
    if (porTecla && Date.now() - ultimaTecla < U.TECLA_MS) return;
    muda(!escondido, porTecla);
  }

  const tudoFechado = () => modo === "espera" || modo === "cheio" || modo === "alerta" || modo === "parou";

  addEventListener("keydown", (e) => {
    if (U.ehAtalho(e) && (ajustes.consentido || escondido)) {
      e.preventDefault();
      e.stopImmediatePropagation();
      if (!e.repeat) alterna(true);
      return;
    }
    if (!tudoFechado()) {
      if (e.isTrusted) atividade = Date.now();
      return;
    }
    // com tudo escondido, tecla não chega ao WhatsApp: nada digita nem envia às cegas
    e.stopImmediatePropagation();
    const doNavegador = e.ctrlKey || e.metaKey || e.altKey || e.key === "Tab" || /^F\d+$/.test(e.key);
    const noUirapp = tela && e.target === tela.casa;
    if (!doNavegador && !noUirapp) e.preventDefault();
  }, true);

  for (const tipo of ["keypress", "keyup", "beforeinput"]) {
    addEventListener(tipo, (e) => {
      if (tudoFechado()) e.stopImmediatePropagation();
    }, true);
  }
  for (const tipo of ["copy", "cut", "paste", "drop", "dragover", "dragstart"]) {
    addEventListener(tipo, (e) => {
      if (!tudoFechado()) return;
      e.preventDefault();
      e.stopImmediatePropagation();
    }, true);
  }
  for (const tipo of ["pointermove", "pointerdown", "wheel"]) {
    addEventListener(tipo, (e) => {
      if (e.isTrusted) atividade = Date.now();
    }, { capture: true, passive: true });
  }
  addEventListener("resize", () => {
    if (modo === "cheio") aplica();
  });

  function bate() {
    const longe = document.visibilityState === "hidden" && ajustes.aoSair;
    const parado = ajustes.parado && Date.now() - atividade >= ajustes.paradoMin * 60000;
    if (viva() && lido && !escondido && ajustes.consentido && (parado || longe)) {
      muda(true);
    } else {
      aplica();
    }
  }
  setInterval(bate, 1000);
  document.addEventListener("visibilitychange", bate);

  // se alguém tirar ou trocar a marca ou a casa, volta antes da próxima pintura
  new MutationObserver(assinaMarca).observe(raiz, { attributes: true, attributeFilter: ["data-uirapp"] });
  new MutationObserver(() => {
    if (document.body && modo !== "espera" && modo !== "fora" && tela?.casa.parentNode !== raiz) aplica();
  }).observe(raiz, { childList: true });

  // ---------- extensão
  async function reforca(tentativas = 3) {
    try {
      if ((await chrome.runtime.sendMessage({ uirapp: "reforca" })) === true) {
        reforcado = true;
        aplica();
        return;
      }
    } catch {
      // o fundo ainda acordando: tenta de novo
    }
    if (tentativas > 1) {
      await new Promise((r) => setTimeout(r, 300));
      return reforca(tentativas - 1);
    }
    aplica();
  }

  try {
    chrome.runtime.onMessage.addListener((pedido, de, responde) => {
      if (de.id === chrome.runtime.id && pedido?.uirapp === "estado") {
        responde({ estado: modo === "alerta" || modo === "parou" ? modo : "ativo" });
      }
      return false;
    });

    chrome.storage.onChanged.addListener((mudou, onde) => {
      if (onde !== "local" || !lido) return;
      if (mudou.ajustes) ajustes = U.ajustes(mudou.ajustes.newValue);
      if (mudou.tecla) ultimaTecla = Number(mudou.tecla.newValue) || 0;
      if (mudou.silencio) {
        const novo = U.silencio(mudou.silencio.newValue);
        if (novo !== escondido) {
          atividade = Date.now();
          estranhoDesde = 0;
        }
        escondido = novo;
      }
      aplica();
    });

    reforca();
    chrome.storage.local.get(["ajustes", "silencio", "tecla"]).then((g) => {
      ajustes = U.ajustes(g.ajustes);
      escondido = U.silencio(g.silencio);
      ultimaTecla = Number(g.tecla) || 0;
      lido = true;
      if (ajustes.consentido && ajustes.aoAbrir && !escondido) {
        escondido = true;
        guarda({ silencio: true });
      }
      aplica();
    }, () => {
      quebrou = true;
      aplica();
    });
  } catch {
    quebrou = true;
    aplica();
  }
})();
