// O que a janela, o Ninho, o fundo e a tela dentro do WhatsApp têm em comum.
"use strict";

globalThis.Uirapp = (() => {
  const CATEGORIAS = Object.freeze(["mensagens", "previas", "nomes", "fotos", "midia"]);
  const PLUMAGENS = Object.freeze({ vermelha: "Vermelha", laranja: "Laranja", lenda: "Da lenda" });
  const OCULTAVEIS = Object.freeze(["filtros", "faixas", "status", "canais", "comunidades", "ligacoes", "desenhos"]);
  const PARADO = Object.freeze([1, 5, 10, 30]);
  const LETRA = Object.freeze([90, 100, 110, 125]);
  const IDIOMAS = Object.freeze({ auto: "Do navegador", pt: "Português", en: "English", es: "Español" });
  const VERSAO = "0.3.0";

  const texto = (v, max) => (typeof v === "string" ? v.trim().slice(0, max) : "");
  const umDe = (v, lista, padrao) => (lista.includes(v) ? v : padrao);

  // valor torto vira o lado mais fechado: só um false explícito deixa de esconder
  function ajustes(cru) {
    const a = cru && typeof cru === "object" ? cru : {};
    const e = a.esconder && typeof a.esconder === "object" ? a.esconder : {};
    const ap = a.aparencia && typeof a.aparencia === "object" ? a.aparencia : {};
    const px = a.pix && typeof a.pix === "object" ? a.pix : {};
    const tema = globalThis.UirappRegras?.tema(ap.temaDados) ?? null;
    return {
      consentido: a.consentido === true,
      esconder: Object.fromEntries(CATEGORIAS.map((c) => [c, e[c] !== false])),
      parado: a.parado === true,
      paradoMin: umDe(a.paradoMin, PARADO, 5),
      aoAbrir: a.aoAbrir === true,
      aoSair: a.aoSair === true,
      som: a.som === true,
      titulo: a.titulo === true,
      plumagem: Object.hasOwn(PLUMAGENS, a.plumagem) ? a.plumagem : "vermelha",
      tema: a.tema === "dia" || a.tema === "noite" ? a.tema : "",
      passaro: umDe(a.passaro, ["direita", "esquerda", "oculto"], "direita"),
      aparencia: {
        ...Object.fromEntries(OCULTAVEIS.map((o) => [o, ap[o] === true])),
        letra: umDe(ap.letra, LETRA, 100),
        temaId: tema ? texto(ap.temaId, 40) || tema.id : "",
        temaDados: tema,
      },
      atalhos: a.atalhos !== false,
      assinatura: texto(a.assinatura, 200),
      pix: { chave: texto(px.chave, 77), nome: texto(px.nome, 25), cidade: texto(px.cidade, 15) },
      idioma: Object.hasOwn(IDIOMAS, a.idioma) ? a.idioma : "auto",
      favoritos: Array.isArray(a.favoritos) ? [...new Set(a.favoritos.filter((f) => typeof f === "string" && /^[a-z-]{1,30}$/.test(f)))].slice(0, 8) : [],
      visto: texto(a.visto, 20),
    };
  }

  return Object.freeze({
    CATEGORIAS, PLUMAGENS, OCULTAVEIS, PARADO, LETRA, IDIOMAS, VERSAO,
    WHATSAPP: "https://web.whatsapp.com/",
    TECLA_MS: 400,
    ajustes,
    silencio: (v) => v !== undefined && v !== false,
    ehAtalho: (e) => e.isTrusted && e.altKey && !e.ctrlKey && !e.metaKey && !e.shiftKey && e.code === "KeyS",
  });
})();
