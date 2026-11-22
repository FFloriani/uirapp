// Tema e opções de tela dentro do WhatsApp. Só estilo e marcas de atributo; não lê conversa.
"use strict";

(() => {
  if (window.top !== window) return;
  const U = globalThis.Uirapp;
  const R = globalThis.UirappRegras;
  const folha = new CSSStyleSheet();
  const raiz = document.documentElement;
  let ap = U.ajustes().aparencia;

  // a barra lateral não tem marcador estável: o desenho do ícone diz quem é quem
  const ICONES = { status: /^wds-ic-status/, canais: /^wds-ic-channels/, comunidades: /^wds-ic-communities/, ligacoes: /^ic-call/ };

  function marcaBarra() {
    for (const b of document.querySelectorAll("header button[data-navbar-item]")) {
      const t = b.querySelector("svg > title")?.textContent.trim() ?? "";
      const qual = Object.keys(ICONES).find((k) => ICONES[k].test(t)) ?? "";
      if ((b.getAttribute("data-uirapp-barra") ?? "") !== qual) {
        if (qual) b.setAttribute("data-uirapp-barra", qual);
        else b.removeAttribute("data-uirapp-barra");
      }
    }
  }

  function css() {
    let t = ap.temaDados ? R.cssTema(ap.temaDados) : "";
    const some = [];
    if (ap.filtros) some.push('[data-testid="chat_list_filters_row"]');
    if (ap.faixas) {
      some.push('[data-testid="chat_list_notifications_banner"]', '[data-testid="chatlist_calling_activation_banner_wrapper"]',
        '[data-testid="chatlist_channels_migration_banner_wrapper"]', '[data-testid="chatlist-e2e-message"]',
        '[data-testid="intro_panel_v2_title_card"]', '[data-testid="download-native-client-button"]');
    }
    for (const k of Object.keys(ICONES)) if (ap[k]) some.push(`button[data-uirapp-barra="${k}"]`);
    if (some.length) t += `${some.join(",")}{display:none !important}`;
    if (ap.desenhos) t += "html,body,body.dark{--WDS-systems-chat-foreground-wallpaper:transparent !important}";
    if (ap.letra !== 100) t += `#app{zoom:${ap.letra / 100} !important}`;
    return t;
  }

  function aplica() {
    folha.replaceSync(css());
    if (!document.adoptedStyleSheets.includes(folha)) document.adoptedStyleSheets = [...document.adoptedStyleSheets, folha];
    marcaBarra();
  }

  let pendente = false;
  new MutationObserver(() => {
    if (pendente || !(ap.status || ap.canais || ap.comunidades || ap.ligacoes)) return;
    pendente = true;
    queueMicrotask(() => {
      pendente = false;
      marcaBarra();
    });
  }).observe(raiz, { childList: true, subtree: true });

  try {
    chrome.storage.local.get("ajustes").then((g) => {
      ap = U.ajustes(g.ajustes).aparencia;
      aplica();
    }, () => {});
    chrome.storage.onChanged.addListener((m, onde) => {
      if (onde !== "local" || !m.ajustes) return;
      ap = U.ajustes(m.ajustes.newValue).aparencia;
      aplica();
    });
  } catch {
    // extensão recarregada: a tela fica como estava
  }
})();
