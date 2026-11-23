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
          const d = structuredClone(dados);
          // "já viu as novidades" acompanha a versão do pacote, para o protótipo não parar nas novidades a cada versão
          if (tela !== "novidades" && d.ajustes?.visto) d.ajustes.visto = globalThis.Uirapp?.VERSAO ?? d.ajustes.visto;
          return d;
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
        if (pedido.uirapp === "inserir" || pedido.uirapp === "trocar") return { ok: true };
        if (pedido.uirapp === "rascunho") return { ok: true, texto: "oi juliana, a gente consegue fazer a degustacao na terça as 15h, pode ser?" };
        if (pedido.uirapp === "exportar") {
          return { ok: true, nome: "Juliana Costa", mensagens: [
            { autor: "Juliana Costa", texto: "Oi! Vocês fazem bolo de casamento para 120 pessoas?", tipo: "texto", de: "" },
            { autor: "Loja", texto: "Fazemos sim! Para quando seria?", tipo: "texto", de: "eu" },
            { autor: "Juliana Costa", texto: "Dia 14 de dezembro. Massa branca com doce de leite e morango.", tipo: "texto", de: "" },
            { autor: "Juliana Costa", texto: "Hi! Do you deliver to Pinhais too?", tipo: "texto", de: "" },
            { autor: "Loja", texto: "Fica em torno de R$ 1.800. Vou confirmar a entrega.", tipo: "texto", de: "eu" },
            { autor: "Juliana Costa", texto: "Consigo fazer uma degustação antes?", tipo: "texto", de: "" },
          ] };
        }
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

  // IA de mentira: a tela da IA roda sem o modelo de verdade. ?ia=sem ou ?ia=baixar (padrão: pronta)
  const modoIA = q.get("ia") || "pronta";
  if (modoIA === "sem") {
    for (const n of ["LanguageModel", "Summarizer", "LanguageDetector", "Translator"]) globalThis[n] = undefined;
  } else {
    const disp = async () => (modoIA === "baixar" ? "downloadable" : "available");
    const pausa = () => new Promise((fim) => setTimeout(fim, 200));
    const fala = (op) => (op?.expectedInputs?.[0]?.languages?.[0] ?? "en") !== "pt";
    const respostas = {
      replies: ["Claro! Terça às 15h funciona para a degustação?", "Posso sim. Confirmo a entrega em Pinhais até amanhã.", "Ótimo! Vou separar as amostras de doce de leite e morango."],
      message: "Oi, Juliana! Conseguimos fazer a degustação na terça, às 15h. Pode ser para você?",
    };
    globalThis.LanguageModel = {
      availability: async (op) => (fala(op) ? disp() : "unavailable"),
      create: async () => ({ prompt: async () => (await pausa(), JSON.stringify(respostas)), destroy() {} }),
    };
    globalThis.Summarizer = {
      availability: disp,
      create: async () => ({
        summarize: async () => (await pausa(), "* Bolo de casamento para 120 pessoas, no dia 14 de dezembro\n* Preço em torno de R$ 1.800; falta confirmar a entrega em Pinhais\n* A cliente quer uma degustação na semana que vem, à tarde"),
        destroy() {},
      }),
    };
    globalThis.LanguageDetector = { availability: disp, create: async () => ({ detect: async (t) => [{ detectedLanguage: /\b(the|you|do|is)\b/i.test(t) ? "en" : "pt", confidence: 0.99 }] }) };
    const traducoes = { "Hi! Do you deliver to Pinhais too?": "Oi! Vocês também entregam em Pinhais?" };
    globalThis.Translator = { availability: disp, create: async () => ({ translate: async (t) => traducoes[t] ?? t }) };
  }

  // aberto pela vitrine, não rouba o foco da página
  if (raiz.dataset.inicio) HTMLElement.prototype.focus = () => {};

  const espera = new MutationObserver(() => {
    if (!("pronto" in raiz.dataset)) return;
    espera.disconnect();
    if (!["inicio", "boas-vindas", "novidades"].includes(tela)) {
      const passos = { nova: ["respostas", "nova"], assinatura: ["respostas", "assinatura"] }[tela] ?? [tela];
      for (const p of passos) document.querySelector(`[data-tela]:not([hidden]) [data-ir="${CSS.escape(p)}"]`)?.click();
    }
    if (q.has("acao")) setTimeout(() => document.querySelector(`[data-ia="${CSS.escape(q.get("acao"))}"]`)?.click(), 150);
    if (q.has("erro")) document.querySelector("#form-resposta").requestSubmit();
    if (q.has("apagar")) document.querySelector(".resposta-apagar")?.click();
    if (q.has("copiada")) {
      document.querySelector("#aviso-texto").textContent = "Resposta copiada";
      document.querySelector("#aviso").hidden = false;
    }
  });
  espera.observe(raiz, { attributes: true, attributeFilter: ["data-pronto"] });
})();
