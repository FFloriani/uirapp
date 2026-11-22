// Onde moram respostas, fichas, lembretes e temas: IndexedDB da própria extensão.
// O script que roda dentro do WhatsApp não tem acesso a este banco; só a janela, o Ninho e o fundo.
"use strict";

globalThis.UirappDeposito = globalThis.UirappDemo?.deposito ?? (() => {
  const R = globalThis.UirappRegras;
  let banco = null;

  function abre() {
    banco ??= new Promise((ok, falha) => {
      const pedido = indexedDB.open("uirapp", 1);
      pedido.onupgradeneeded = () => pedido.result.createObjectStore("dados");
      pedido.onsuccess = () => ok(pedido.result);
      pedido.onerror = () => falha(pedido.error);
    });
    return banco;
  }

  async function passo(modo, faz) {
    const db = await abre();
    return new Promise((ok, falha) => {
      const t = db.transaction("dados", modo);
      const r = faz(t.objectStore("dados"));
      t.oncomplete = () => ok(r?.result);
      t.onerror = () => falha(t.error);
      t.onabort = () => falha(t.error);
    });
  }

  // a 0.1 guardava as respostas no localStorage da janela: leva uma vez para cá
  async function trazDaVersaoAntiga(d) {
    if (typeof localStorage === "undefined") return d;
    const velhas = localStorage.getItem("respostas");
    if (!velhas) return d;
    try {
      const lista = JSON.parse(velhas);
      d = R.dados({ ...d, respostas: [...d.respostas, ...(Array.isArray(lista) ? lista : [])] });
      await grava(d);
      localStorage.removeItem("respostas");
    } catch {
      // resposta torta fica onde estava
    }
    return d;
  }

  async function le() {
    const d = R.dados(await passo("readonly", (s) => s.get("tudo")) ?? {});
    return trazDaVersaoAntiga(d);
  }

  async function grava(d) {
    const limpo = R.dados(d);
    await passo("readwrite", (s) => s.put(limpo, "tudo"));
    return limpo;
  }

  async function apaga() {
    await passo("readwrite", (s) => s.clear());
    if (typeof localStorage !== "undefined") localStorage.clear();
  }

  return Object.freeze({ le, grava, apaga });
})();
