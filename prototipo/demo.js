// Só no protótipo: faz o papel do navegador, na memória, para a janela verdadeira rodar sem instalar.
// Não vai no pacote. O endereço escolhe o estado: popup.html#inicio?silencio=1
"use strict";

(() => {
  const raiz = document.documentElement;
  const [tela, busca = ""] = (raiz.dataset.inicio || location.hash.slice(1) || "inicio").split("?");
  const q = new URLSearchParams(busca);
  let problema = q.get("estado") || "";

  const dados = {
    ajustes: {
      consentido: tela !== "boas-vindas", visto: tela === "novidades" ? "" : "0.2.0",
      plumagem: q.get("plumagem") || "", tema: q.get("tema") || "",
    },
    silencio: q.get("silencio") === "1",
  };
  const ouvintes = [];
  const avisaMudanca = (mudou) => { for (const f of ouvintes) f(mudou, "local"); };

  globalThis.chrome = {
    storage: {
      onChanged: { addListener: (f) => ouvintes.push(f) },
      local: {
        async get() {
          return structuredClone(dados);
        },
        set(novo) {
          Object.assign(dados, structuredClone(novo));
          if (novo.silencio === false) problema = "";
          avisaMudanca(Object.fromEntries(Object.entries(novo).map(([k, v]) => [k, { newValue: structuredClone(v) }])));
          return Promise.resolve();
        },
        remove(chaves) {
          for (const k of chaves) delete dados[k];
          avisaMudanca(Object.fromEntries(chaves.map((k) => [k, {}])));
          return Promise.resolve();
        },
      },
    },
    tabs: {
      async query() {
        return problema === "fechado" ? [] : [{ id: 1, status: "complete", discarded: false, active: true }];
      },
      async sendMessage(id, pedido) {
        if (problema === "recarregar") throw new Error("sem resposta");
        if (pedido.uirapp === "estado") return { estado: problema || "ativo" };
        if (pedido.uirapp === "inserir") return { ok: true };
        return { ok: false, motivo: "sem" };
      },
      async create() {
        problema = "";
      },
      async reload() {
        problema = "";
      },
    },
    runtime: {
      async sendMessage() {
        return true;
      },
      getURL: (p) => p,
    },
  };

  const guardado = {
    respostas: q.has("vazio") ? [] : [
      { id: "a", nome: "Horário", atalho: "horario", texto: "{saudacao}! Atendemos de segunda a sábado, das 9h às 18h." },
      { id: "b", nome: "Entrega", atalho: "entrega", texto: "Entregamos em toda a cidade em até 2 dias úteis." },
      { id: "c", nome: "Agradecer", atalho: "", texto: "Obrigado pela preferência! Qualquer coisa, é só chamar." },
    ],
  };
  globalThis.UirappDemo = {
    deposito: {
      le: async () => globalThis.UirappRegras.dados(structuredClone(guardado)),
      grava: async (d) => {
        Object.assign(guardado, structuredClone(globalThis.UirappRegras.dados(d)));
        return globalThis.UirappRegras.dados(structuredClone(guardado));
      },
      apaga: async () => {
        guardado.respostas = [];
      },
    },
  };

  // aberto pela vitrine, não rouba o foco da página
  if (raiz.dataset.inicio) HTMLElement.prototype.focus = () => {};

  const espera = new MutationObserver(() => {
    if (!("pronto" in raiz.dataset)) return;
    espera.disconnect();
    if (!["inicio", "boas-vindas", "novidades"].includes(tela)) {
      const passos = { nova: ["respostas", "nova"], assinatura: ["respostas", "assinatura"] }[tela] ?? [tela];
      for (const p of passos) document.querySelector(`[data-tela]:not([hidden]) [data-ir="${CSS.escape(p)}"]`)?.click();
    }
    if (q.has("erro")) document.querySelector("#form-resposta").requestSubmit();
    if (q.has("apagar")) document.querySelector(".resposta-apagar")?.click();
    if (q.has("copiada")) {
      document.querySelector("#aviso-texto").textContent = "Resposta copiada";
      document.querySelector("#aviso").hidden = false;
    }
  });
  espera.observe(raiz, { attributes: true, attributeFilter: ["data-pronto"] });
})();
