// IA no computador: a IA que o Google Chrome traz (Gemini Nano e o tradutor), rodando neste computador.
// O navegador baixa o modelo uma vez; depois tudo roda sem internet e nada da conversa sai daqui.
// O modelo não fala português (no Chrome 157 fala en, es, ja, de e fr): o português vai e volta pelo tradutor.
// Só roda nas páginas da extensão (janela e Ninho), sempre por um clique da pessoa.
"use strict";

globalThis.UirappIA = (() => {
  const R = globalThis.UirappRegras;
  const tem = (n) => typeof globalThis[n]?.create === "function";
  const base = (l) => String(l || "").toLowerCase().split(/[-_]/)[0];
  const CONTEXTO = 'A WhatsApp chat. Lines that start with "Me:" were written by the user.';
  const SUGERIR = 'You help the user, called "Me", reply in a WhatsApp chat. Write short, friendly, natural messages in the same tone '
    + "as Me. Never invent prices, dates, links or facts that are not in the chat; when something is unknown, say Me will check.";
  const JEITOS = Object.freeze({
    educado: "Rewrite this WhatsApp message to be more polite and warm. Keep every fact, keep it short.",
    curto: "Rewrite this WhatsApp message to be shorter and direct. Keep every fact.",
  });
  const UMA = { type: "object", properties: { message: { type: "string" } }, required: ["message"] };
  const TRES = { type: "object", properties: { replies: { type: "array", items: { type: "string" }, minItems: 3, maxItems: 3 } }, required: ["replies"] };

  // ---------- o que este navegador tem
  // idiomas do modelo, pela página do Prompt API (developer.chrome.com/docs/ai/prompt-api, 21/10/2026). Perguntar ao
  // Chrome por um idioma fora da lista funciona, mas enche o console de erro; quando a lista crescer, muda aqui.
  const DO_MODELO = Object.freeze(["en", "es", "ja", "de", "fr"]);
  // o idioma em que o modelo trabalha: o da pessoa, se ele falar; senão, inglês
  const pivo = async (l) => (DO_MODELO.includes(l) ? l : "en");

  // geral: "sem" (navegador sem IA), "baixar", "baixando" ou "pronta"; partes: cada peça que falta
  async function estado(idioma) {
    if (!["LanguageModel", "Summarizer", "Translator", "LanguageDetector"].every(tem)) return { geral: "sem", partes: {} };
    const p = await pivo(idioma);
    const partes = {
      modelo: await LanguageModel.availability({ expectedInputs: [{ type: "text", languages: [p] }], expectedOutputs: [{ type: "text", languages: [p] }] }),
      resumo: await Summarizer.availability({ expectedInputLanguages: [p], outputLanguage: p }),
      detector: await LanguageDetector.availability(),
    };
    if (p !== idioma) {
      partes.ida = await Translator.availability({ sourceLanguage: idioma, targetLanguage: p });
      partes.volta = await Translator.availability({ sourceLanguage: p, targetLanguage: idioma });
    }
    const v = Object.values(partes);
    const geral = v.includes("unavailable") ? "sem" : v.includes("downloading") ? "baixando" : v.includes("downloadable") ? "baixar" : "pronta";
    return { geral, partes };
  }

  // ---------- peças, criadas uma vez por página
  const pecas = new Map();
  function peca(chave, cria) {
    if (!pecas.has(chave)) pecas.set(chave, cria().catch((e) => { pecas.delete(chave); throw e; }));
    return pecas.get(chave);
  }
  const tradutor = (de, para) => peca(`t:${de}>${para}`, () => Translator.create({ sourceLanguage: de, targetLanguage: para }));
  const detector = () => peca("detector", () => LanguageDetector.create());

  // baixa e prepara tudo o que falta. Precisa de um clique: chame direto do clique, antes de qualquer espera.
  // aoAndar recebe (parte, "ok" | "erro" | número de 0 a 1 do download)
  function prepara(idioma, aoAndar = () => {}) {
    const monitor = (parte) => (m) => m.addEventListener("downloadprogress", (e) => aoAndar(parte, e.loaded));
    const passo = (parte, cria) => cria().then((s) => { aoAndar(parte, "ok"); return s; }, (e) => { aoAndar(parte, "erro"); throw e; });
    // começa agora, enquanto vale o clique. Resumo depois do modelo (é o mesmo modelo) e tradutores um depois do
    // outro: pedidos juntos para a mesma peça o Chrome recusa. Se o clique vencer no meio, o próximo clique termina.
    const modelo = pivo(idioma);
    const tarefas = [
      passo("modelo", async () => (await LanguageModel.create({ monitor: monitor("modelo") })).destroy())
        .then(() => passo("resumo", async () => (await Summarizer.create({ monitor: monitor("resumo") })).destroy())),
      passo("detector", () => detector()),
      modelo.then(async (p) => {
        if (p === idioma) return;
        await passo("ida", () => tradutor(idioma, p));
        await passo("volta", () => tradutor(p, idioma));
      }),
    ];
    return Promise.allSettled(tarefas).then((r) => r.every((x) => x.status === "fulfilled"));
  }

  // ---------- idioma e tradução
  async function idiomaDe(texto, padrao) {
    if (!texto || texto.length < 3) return padrao;
    const [melhor] = await (await detector()).detect(texto);
    const l = base(melhor?.detectedLanguage);
    return melhor && melhor.confidence >= 0.6 && l && l !== "und" ? l : padrao;
  }

  async function traduz(texto, de, para) {
    if (!texto || de === para) return texto;
    return (await tradutor(de, para)).translate(texto);
  }

  // cada mensagem no idioma em que o modelo trabalha
  async function noIdioma(mensagens, para, padrao) {
    const fora = [];
    for (const m of mensagens) {
      const texto = m.texto ? await traduz(m.texto, await idiomaDe(m.texto, padrao), para) : "";
      fora.push({ ...m, texto });
    }
    return fora;
  }

  const ultimas = (mensagens, n) => (Array.isArray(mensagens) ? mensagens.slice(-n) : []);
  const comEsquema = async (sessao, pedido, esquema) => JSON.parse(await sessao.prompt(pedido, { responseConstraint: esquema }));

  // ---------- o que a pessoa pede
  async function resumir(mensagens, idioma) {
    const p = await pivo(idioma);
    const conversa = R.iaConversa(await noIdioma(ultimas(mensagens, 40), p, idioma), 6000);
    if (!conversa) return [];
    const s = await Summarizer.create({ type: "key-points", format: "plain-text", length: "short", sharedContext: CONTEXTO, expectedInputLanguages: [p], outputLanguage: p });
    try {
      const pontos = R.iaRespostas(await s.summarize(conversa), 6);
      return Promise.all(pontos.map((t) => traduz(t, p, idioma)));
    } finally {
      s.destroy();
    }
  }

  async function traduzirConversa(mensagens, idioma) {
    const fora = [];
    for (const m of ultimas(mensagens, 20)) {
      if (!m.texto) continue;
      const de = await idiomaDe(m.texto, idioma);
      fora.push({ autor: m.de === "eu" ? "" : m.autor, de: m.de, texto: m.texto, traducao: de === idioma ? "" : await traduz(m.texto, de, idioma) });
    }
    return fora;
  }

  async function sugerir(mensagens, idioma) {
    const lista = ultimas(mensagens, 30);
    const deles = [...lista].reverse().find((m) => m.de !== "eu" && m.texto);
    const resposta = deles ? await idiomaDe(deles.texto, idioma) : idioma; // responde no idioma de quem escreveu
    const p = await pivo(resposta);
    const conversa = R.iaConversa(await noIdioma(lista, p, idioma), 4000);
    if (!conversa) return [];
    const s = await LanguageModel.create({ initialPrompts: [{ role: "system", content: SUGERIR }],
      expectedInputs: [{ type: "text", languages: [p] }], expectedOutputs: [{ type: "text", languages: [p] }] });
    try {
      const saida = await s.prompt(`Chat:\n${conversa}\n\nWrite 3 different reply options that Me could send next.`, { responseConstraint: TRES });
      return Promise.all(R.iaRespostas(saida).map((t) => traduz(t, p, resposta)));
    } finally {
      s.destroy();
    }
  }

  async function reescrever(texto, jeito, idioma) {
    const de = await idiomaDe(texto, idioma);
    const p = await pivo(de);
    const s = await LanguageModel.create({ expectedInputs: [{ type: "text", languages: [p] }], expectedOutputs: [{ type: "text", languages: [p] }] });
    try {
      const r = await comEsquema(s, `${JEITOS[jeito] ?? JEITOS.educado}\n\nMessage:\n${await traduz(texto, de, p)}`, UMA);
      return traduz(String(r?.message ?? "").trim(), p, de);
    } finally {
      s.destroy();
    }
  }

  async function traduzirTexto(texto, para, idioma) {
    return traduz(texto, await idiomaDe(texto, idioma), para);
  }

  // o que dizer quando dá errado
  function motivo(e) {
    if (e?.name === "NotAllowedError") return "tocar";
    if (e?.name === "NotSupportedError") return "idioma";
    if (e?.name === "QuotaExceededError") return "grande";
    return "falhou";
  }

  return Object.freeze({ estado, prepara, resumir, traduzirConversa, sugerir, reescrever, traduzirTexto, motivo, tem });
})();
