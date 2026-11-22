// Ajudas dentro da conversa, sempre por pedido da pessoa: pôr uma resposta no campo de escrever, trocar /atalho
// pela resposta, ler o nome da conversa aberta, exportar as mensagens carregadas e baixar a foto ou o vídeo aberto.
//
// Nunca envia: não aperta Enter, não clica em enviar. O texto fica no campo e quem manda é a pessoa.
"use strict";

(() => {
  if (window.top !== window) return;
  const U = globalThis.Uirapp;
  const R = globalThis.UirappRegras;
  const CAMPO = '#main [data-testid="conversation-compose-box-input"]';
  let ajustes = U.ajustes();

  const nomeDaConversa = () => document.querySelector('#main [data-testid="conversation-info-header-chat-title"]')?.textContent.trim().slice(0, 80) ?? "";
  const contexto = () => ({ nome: nomeDaConversa(), assinatura: ajustes.assinatura, pix: R.pix(ajustes.pix) ?? "" });

  function editavel() {
    const campo = document.querySelector(CAMPO);
    return campo?.isContentEditable ? campo : campo?.querySelector('[contenteditable="true"]') ?? null;
  }

  function poeNoCampo(texto, apagarAntes = 0) {
    const ed = editavel();
    if (!ed) return false;
    ed.focus();
    const sel = getSelection();
    if (!sel.rangeCount || !ed.contains(sel.anchorNode)) {
      sel.selectAllChildren(ed);
      sel.collapseToEnd();
    }
    for (let i = 0; i < apagarAntes; i++) sel.modify("extend", "backward", "character");
    // o editor do WhatsApp entende o insertText como se a pessoa tivesse digitado
    return document.execCommand("insertText", false, texto);
  }

  // /atalho + Tab vira a resposta, só se houver uma com esse atalho
  addEventListener("keydown", async (e) => {
    if (!e.isTrusted || e.key !== "Tab" || e.shiftKey || e.ctrlKey || e.altKey || e.metaKey || !ajustes.atalhos || !ajustes.consentido) return;
    const ed = editavel();
    const sel = getSelection();
    if (!ed || !sel.rangeCount || !sel.isCollapsed || !ed.contains(sel.anchorNode)) return;
    const no = sel.anchorNode;
    const antes = no.nodeType === Node.TEXT_NODE ? no.textContent.slice(0, sel.anchorOffset) : "";
    const m = /(?:^|\s)\/([a-z0-9-]{1,24})$/.exec(antes);
    if (!m) return;
    e.preventDefault();
    e.stopImmediatePropagation();
    let texto = null;
    try {
      texto = await chrome.runtime.sendMessage({ uirapp: "atalho", atalho: m[1] });
    } catch {
      return;
    }
    if (texto) poeNoCampo(R.preenche(texto, contexto()), m[1].length + 1);
  }, true);

  function mensagens() {
    const lista = [];
    for (const bloco of document.querySelectorAll('#main [data-testid="msg-container"]')) {
      const pre = bloco.querySelector("[data-pre-plain-text]");
      const cab = R.cabecalho(pre?.getAttribute("data-pre-plain-text"));
      const partes = [...(pre?.querySelectorAll(".selectable-text") ?? [])].filter((t) => !t.closest('[data-testid="quoted-message"]'));
      const texto = partes.map((t) => t.textContent).join("\n").trim();
      let tipo = "texto";
      if (bloco.querySelector('[data-testid="sticker-container"]')) tipo = "figurinha";
      else if (bloco.querySelector('[data-testid="audio-play"], [data-testid="ptt-status"]')) tipo = "áudio";
      else if (bloco.querySelector('[data-testid="msg-video"], video')) tipo = "vídeo";
      else if (bloco.querySelector('[data-testid="msgImage"], img[src^="blob:"]')) tipo = "foto";
      else if (bloco.querySelector('[data-testid="document-thumb-details"]')) tipo = "documento";
      if (!texto && tipo === "texto") continue;
      lista.push({ data: cab?.data ?? "", hora: cab?.hora ?? "", autor: cab?.autor ?? "", texto, tipo });
    }
    return lista;
  }

  function baixaAberta() {
    let melhor = null;
    for (const e of document.querySelectorAll('img[src^="blob:"], video[src^="blob:"], video > source[src^="blob:"]')) {
      const alvo = e.localName === "source" ? e.parentElement : e;
      const r = alvo.getBoundingClientRect();
      const area = r.width * r.height;
      if (area > 40000 && (!melhor || area > melhor.area)) melhor = { url: e.src, area, video: alvo.localName === "video" };
    }
    if (!melhor) return false;
    const a = document.createElement("a");
    a.href = melhor.url;
    a.download = `uirapp-${new Date().toISOString().slice(0, 19).replace(/[T:]/g, "-")}.${melhor.video ? "mp4" : "jpg"}`;
    a.click(); // âncora nossa, fora da página
    return true;
  }

  try {
    chrome.storage.local.get("ajustes").then((g) => { ajustes = U.ajustes(g.ajustes); }, () => {});
    chrome.storage.onChanged.addListener((m, onde) => {
      if (onde === "local" && m.ajustes) ajustes = U.ajustes(m.ajustes.newValue);
    });
    chrome.runtime.onMessage.addListener((pedido, de, responde) => {
      if (de.id !== chrome.runtime.id || de.tab) return false;
      const silencio = document.documentElement.getAttribute("data-uirapp") !== "aberto";
      switch (pedido?.uirapp) {
        case "inserir":
          if (silencio) return responde({ ok: false, motivo: "silencio" }), false;
          responde({ ok: typeof pedido.texto === "string" && poeNoCampo(R.preenche(pedido.texto.slice(0, 4000), contexto())) });
          return false;
        case "conversa":
          responde({ aberta: Boolean(document.querySelector("#main")), nome: silencio ? "" : nomeDaConversa() });
          return false;
        case "exportar":
          if (silencio) return responde({ ok: false, motivo: "silencio" }), false;
          responde({ ok: true, nome: nomeDaConversa(), mensagens: mensagens() });
          return false;
        case "baixar":
          if (silencio) return responde({ ok: false, motivo: "silencio" }), false;
          responde({ ok: baixaAberta() });
          return false;
        default:
          return false;
      }
    });
  } catch {
    // extensão recarregada
  }
})();
