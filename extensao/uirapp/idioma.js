// Idiomas do Uirapp. O português é a fonte; inglês e espanhol traduzem frase a frase.
// scripts/testar_idioma.py confere que toda frase das telas tem tradução.
"use strict";

globalThis.UirappIdioma = (() => {
  const EN_ES = globalThis.UirappFrases ?? {};
  let atual = "pt";
  const originais = new WeakMap();
  const ATRIBUTOS = ["aria-label", "placeholder", "title"];

  function resolve(pedido) {
    if (pedido === "pt" || pedido === "en" || pedido === "es") return pedido;
    const nav = (globalThis.navigator?.language ?? "pt").slice(0, 2).toLowerCase();
    return nav === "en" || nav === "es" ? nav : "pt";
  }

  function t(frase) {
    if (atual === "pt" || typeof frase !== "string") return frase;
    return EN_ES[frase]?.[atual === "en" ? 0 : 1] ?? frase;
  }

  function aplica(pedido, raiz = globalThis.document?.body) {
    atual = resolve(pedido);
    if (!raiz) return atual;
    document.documentElement.lang = { pt: "pt-BR", en: "en", es: "es" }[atual];
    const andador = document.createTreeWalker(raiz, NodeFilter.SHOW_TEXT | NodeFilter.SHOW_ELEMENT);
    for (let no = andador.currentNode; no; no = andador.nextNode()) {
      if (no.nodeType === Node.TEXT_NODE) {
        const p = no.parentElement;
        if (!no.nodeValue.trim() || p?.closest("script, style, textarea, [data-sem-traducao]")) continue;
        if (!originais.has(no)) originais.set(no, no.nodeValue);
        const pt = originais.get(no);
        const nucleo = pt.trim();
        const novo = pt.replace(nucleo, t(nucleo));
        if (no.nodeValue !== novo) no.nodeValue = novo;
        continue;
      }
      for (const a of ATRIBUTOS) {
        if (!no.hasAttribute(a)) continue;
        const guarda = `data-pt-${a}`;
        if (!no.hasAttribute(guarda)) no.setAttribute(guarda, no.getAttribute(a));
        no.setAttribute(a, t(no.getAttribute(guarda)));
      }
    }
    return atual;
  }

  return Object.freeze({ t, aplica, resolve, agora: () => atual, frases: () => Object.keys(EN_ES) });
})();
