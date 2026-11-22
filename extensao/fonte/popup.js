// A janela do Uirapp. É o mesmo arquivo na extensão e no protótipo (lá, prototipo/demo.js faz o papel do navegador).
// Texto que a pessoa digita entra sempre por textContent.
"use strict";

(() => {
  const U = globalThis.Uirapp;
  const R = globalThis.UirappRegras;
  const D = globalThis.UirappDeposito;
  const T = (s) => globalThis.UirappIdioma?.t(s) ?? s;
  const raiz = document.documentElement;
  const $ = (s) => document.querySelector(s);
  const $$ = (s) => document.querySelectorAll(s);

  let ajustes = U.ajustes();
  let dados = R.dados();
  let escondido = false;
  let problema = ""; // "", alerta, parou, fechado ou recarregar
  let recarregaveis = [];
  let ultimaTecla = 0;
  let relogio = 0;
  let aoApagar = null;

  function avisa(texto) {
    $("#aviso-texto").textContent = T(texto);
    $("#aviso").hidden = false;
    clearTimeout(relogio);
    relogio = setTimeout(() => { $("#aviso").hidden = true; }, 2400);
  }

  async function guarda(dado) {
    try {
      await chrome.storage.local.set(dado);
    } catch {
      avisa("Não deu para salvar. Tente de novo.");
    }
  }

  async function guardaDados(novo) {
    try {
      dados = await D.grava(novo);
    } catch {
      avisa("Não deu para salvar. Tente de novo.");
      return false;
    }
    pintaRespostas();
    pintaTemas();
    return true;
  }

  // ---------- aba do WhatsApp
  async function abaWhatsApp() {
    const abas = await chrome.tabs.query({ url: `${U.WHATSAPP}*` });
    return abas.find((a) => a.active) ?? abas[0] ?? null;
  }

  async function pedeAoWhatsApp(pedido) {
    const aba = await abaWhatsApp();
    if (!aba) return { ok: false, motivo: "fechado" };
    try {
      return (await chrome.tabs.sendMessage(aba.id, pedido, { frameId: 0 })) ?? { ok: false, motivo: "recarregar" };
    } catch {
      return { ok: false, motivo: "recarregar" };
    }
  }

  const MOTIVOS = {
    fechado: "Abra o WhatsApp Web primeiro.",
    recarregar: "Recarregue o WhatsApp Web primeiro.",
    silencio: "Mostre as conversas primeiro.",
    sem: "Abra uma conversa primeiro.",
  };

  // ---------- pintura
  function pintaPalco() {
    let visual = escondido ? "silencio" : "aberto";
    let titulo = escondido ? "Conversas escondidas" : "Conversas à vista";
    let acao = escondido ? "Mostrar conversas" : "Esconder conversas";
    let apoio = "";
    if (problema === "alerta") {
      [visual, titulo, acao, apoio] = ["alerta", "O WhatsApp mudou", "Descobrir a tela", "Cobri a tela inteira."];
    } else if (problema === "parou") {
      [visual, titulo, acao, apoio] = ["alerta", "O Uirapp parou", "Recarregar o WhatsApp Web", "Cobri a tela inteira."];
    } else if (problema === "fechado") {
      [visual, titulo, acao] = ["fechado", "WhatsApp Web fechado", "Abrir o WhatsApp Web"];
    } else if (problema === "recarregar") {
      [visual, titulo, acao] = ["fechado", "Falta recarregar", "Recarregar o WhatsApp Web"];
    }
    const palco = $("#palco");
    palco.dataset.estado = visual;
    palco.dataset.humor = visual === "silencio" ? "silencio" : visual === "alerta" ? "alerta" : "acordado";
    $("#palco-titulo").textContent = T(titulo);
    $("#palco-apoio").textContent = T(apoio);
    $("#palco-apoio").hidden = !apoio;
    $("#silencio-texto").textContent = T(acao);
    $("#silencio-tecla").hidden = Boolean(problema);
  }

  function marca(nome, valor) {
    for (const r of $$(`[name="${nome}"]`)) r.checked = String(r.value) === String(valor);
  }

  function pintaAjustes() {
    for (const c of $$("[data-esconde]")) c.checked = ajustes.esconder[c.dataset.esconde];
    for (const c of $$("[data-ajuste]")) c.checked = ajustes[c.dataset.ajuste];
    for (const c of $$("[data-oculta]")) c.checked = ajustes.aparencia[c.dataset.oculta];
    marca("plumagem", ajustes.plumagem);
    marca("tema", ajustes.tema);
    marca("paradoMin", ajustes.paradoMin);
    marca("passaro", ajustes.passaro);
    marca("letra", ajustes.aparencia.letra);
    marca("idioma", ajustes.idioma);
    marca("tema-whatsapp", ajustes.aparencia.temaId);
    $("#minutos").hidden = !ajustes.parado;
    raiz.dataset.plumagem = ajustes.plumagem;
    if (ajustes.tema) raiz.dataset.tema = ajustes.tema;
    else delete raiz.dataset.tema;
    for (const e of $$("[data-texto]")) if (document.activeElement !== e) e.value = ajustes[e.dataset.texto];
    for (const e of $$("[data-pix]")) if (document.activeElement !== e) e.value = ajustes.pix[e.dataset.pix];
    const pix = R.pix(ajustes.pix);
    $("#pix-estado").textContent = T(pix ? "Pix pronto para usar em {pix}." : "Preencha os três para usar {pix}.");
    const ligadas = U.CATEGORIAS.filter((c) => ajustes.esconder[c]).length;
    $("#valor-privacidade").textContent = ligadas === U.CATEGORIAS.length ? T("Tudo") : `${ligadas} ${T("de")} ${U.CATEGORIAS.length}`;
    $("#valor-plumagem").textContent = T(U.PLUMAGENS[ajustes.plumagem]);
    const tema = [...R.TEMAS, ...dados.temas].find((t) => t.id === ajustes.aparencia.temaId);
    $("#valor-aparencia").textContent = tema ? T(tema.nome) : "";
    for (const b of $$("[data-favorito]")) b.setAttribute("aria-pressed", String(ajustes.favoritos.includes(b.dataset.favorito)));
    ordenaMenu();
    globalThis.UirappIdioma?.aplica(ajustes.idioma);
  }

  // favoritos sobem para o começo, na ordem em que foram marcados
  function ordenaMenu() {
    const menu = $("#menu");
    const linhas = [...menu.children];
    const peso = (l) => {
      const i = ajustes.favoritos.indexOf(l.dataset.ir);
      return i === -1 ? 100 + linhas.indexOf(l) : i;
    };
    const ordem = [...linhas].sort((a, b) => peso(a) - peso(b));
    if (ordem.some((l, i) => l !== menu.children[i])) menu.append(...ordem);
    for (const l of linhas) l.classList.toggle("favorita", ajustes.favoritos.includes(l.dataset.ir));
  }

  function confirma(titulo, acao) {
    $("#dialogo-titulo").textContent = T(titulo);
    aoApagar = acao;
    $("#dialogo").showModal();
    $("#dialogo-manter").focus();
  }

  async function usaNaConversa(texto) {
    const r = await pedeAoWhatsApp({ uirapp: "inserir", texto });
    if (r.ok) return avisa("Resposta na conversa");
    // sem conversa aberta, a resposta vai para a área de transferência
    try {
      await navigator.clipboard.writeText(R.preenche(texto, { assinatura: ajustes.assinatura, pix: R.pix(ajustes.pix) ?? "" }));
      avisa(r.motivo === "silencio" ? "Copiei. Mostre as conversas e cole." : "Copiei. Cole na conversa.");
    } catch {
      avisa(MOTIVOS[r.motivo] ?? MOTIVOS.sem);
    }
  }

  function pintaRespostas() {
    const lista = $("#lista-respostas");
    lista.replaceChildren();
    for (const r of dados.respostas) {
      const li = $("#molde-resposta").content.firstElementChild.cloneNode(true);
      li.querySelector(".resposta-nome").textContent = r.atalho ? `${r.nome} · /${r.atalho}` : r.nome;
      li.querySelector(".linha-apoio").textContent = r.texto;
      li.querySelector(".resposta-copiar").addEventListener("click", async () => {
        try {
          await navigator.clipboard.writeText(R.preenche(r.texto, { assinatura: ajustes.assinatura, pix: R.pix(ajustes.pix) ?? "" }));
          avisa("Resposta copiada");
        } catch {
          avisa("Não deu para copiar. Tente de novo.");
        }
      });
      const usar = li.querySelector(".resposta-usar");
      usar.setAttribute("aria-label", `${T("Pôr na conversa")}: ${r.nome}`);
      usar.title = T("Pôr na conversa");
      usar.addEventListener("click", () => usaNaConversa(r.texto));
      const apagar = li.querySelector(".resposta-apagar");
      apagar.setAttribute("aria-label", `${T("Apagar")} ${r.nome}`);
      apagar.addEventListener("click", () => confirma("Apagar resposta?", async () => {
        if (await guardaDados({ ...dados, respostas: dados.respostas.filter((x) => x.id !== r.id) })) avisa("Resposta apagada");
      }));
      lista.append(li);
    }
    lista.hidden = !dados.respostas.length;
    $("#respostas-vazio").hidden = Boolean(dados.respostas.length);
    $("#valor-respostas").textContent = dados.respostas.length ? String(dados.respostas.length) : "";
  }

  function pintaTemas() {
    const caixa = $("#temas");
    caixa.replaceChildren();
    const opcoes = [{ id: "", nome: "Do WhatsApp" }, ...R.TEMAS, ...dados.temas];
    for (const t of opcoes) {
      const el = $("#molde-tema").content.firstElementChild.cloneNode(true);
      const input = el.querySelector("input");
      input.value = t.id;
      input.checked = t.id === ajustes.aparencia.temaId;
      el.querySelector(".tema-nome").textContent = T(t.nome);
      const p = t.fundo ? R.paleta(t) : null;
      const [a, b, c] = el.querySelectorAll(".tema-amostra i");
      const amostra = el.querySelector(".tema-amostra");
      if (p) {
        amostra.style.setProperty("background", p.fundo);
        a.style.setProperty("background", p.recebida);
        b.style.setProperty("background", p.acento);
        c.style.setProperty("background", p.enviada);
      } else {
        amostra.classList.add("tema-original");
      }
      input.addEventListener("change", () => ajusta((x) => {
        x.aparencia.temaId = t.id;
        x.aparencia.temaDados = t.fundo ? R.tema(t) : null;
      }));
      caixa.append(el);
    }
  }

  function vai(nome, foca = true) {
    // nada funciona antes do "Permitir": de qualquer tela, voltar cai nas boas-vindas
    const pedida = !ajustes.consentido && nome === "inicio" ? "boas-vindas" : nome;
    const destino = $(`[data-tela="${CSS.escape(pedida)}"]`);
    if (!destino) return;
    for (const t of $$(".tela")) t.hidden = t !== destino;
    if (!foca) return;
    const alvo = destino.querySelector("h2[tabindex]") || destino.querySelector("button");
    alvo?.focus({ preventScroll: true });
  }

  // ---------- WhatsApp Web
  async function confereWhatsApp() {
    let novo = "";
    let velhas = [];
    try {
      const abas = await chrome.tabs.query({ url: `${U.WHATSAPP}*` });
      const vistas = await Promise.all(abas.map(async (aba) => {
        if (aba.discarded) return { aba, estado: "dorme" };
        try {
          const r = await chrome.tabs.sendMessage(aba.id, { uirapp: "estado" }, { frameId: 0 });
          if (r?.estado) return { aba, estado: r.estado };
        } catch {
          // aba aberta antes de instalar, ou ainda carregando
        }
        return { aba, estado: aba.status === "loading" ? "ativo" : "velha" };
      }));
      const tem = (estado) => vistas.some((v) => v.estado === estado);
      // aba sem o Uirapp vem primeiro: dizer "escondidas" com ela aberta seria mentira
      if (!vistas.length) novo = "fechado";
      else if (tem("velha")) novo = "recarregar";
      else if (tem("parou")) novo = "parou";
      else if (tem("alerta")) novo = "alerta";
      else if (!tem("ativo")) novo = "recarregar";
      const pede = novo === "parou" ? ["parou"] : ["velha", "dorme"];
      velhas = vistas.filter((v) => pede.includes(v.estado)).map((v) => v.aba.id);
    } catch {
      novo = "recarregar";
    }
    recarregaveis = velhas;
    if (novo !== problema) {
      problema = novo;
      pintaPalco();
    }
  }

  function muda(novo, porTecla = false) {
    escondido = novo;
    const dado = { silencio: novo };
    if (porTecla) {
      ultimaTecla = Date.now();
      dado.tecla = ultimaTecla;
    }
    guarda(dado);
    pintaPalco();
  }

  async function acaoPrincipal() {
    if (problema === "fechado") {
      await chrome.tabs.create({ url: U.WHATSAPP });
      window.close();
    } else if (problema === "recarregar" || problema === "parou") {
      await Promise.all(recarregaveis.map((id) => chrome.tabs.reload(id)));
      setTimeout(confereWhatsApp, 700);
    } else if (problema === "alerta") {
      problema = "";
      muda(false);
    } else {
      muda(!escondido);
    }
  }

  function atalho(e) {
    if (!U.ehAtalho(e) || $("#dialogo").open) return;
    e.preventDefault();
    if (e.repeat || Date.now() - ultimaTecla < U.TECLA_MS) return;
    if (!ajustes.consentido && !escondido) return;
    if (problema === "alerta") problema = "";
    muda(!escondido, true);
  }

  function erroDe(campo, erro, falta) {
    $(campo).setAttribute("aria-invalid", String(falta));
    $(erro).hidden = !falta;
    return falta;
  }

  function validaResposta() {
    const atalho_ = R.atalho($("#r-atalho").value);
    const faltas = [
      ["#r-nome", "#e-nome", !$("#r-nome").value.trim()],
      ["#r-atalho", "#e-atalho", Boolean(atalho_) && dados.respostas.some((r) => r.atalho === atalho_)],
      ["#r-texto", "#e-texto", !$("#r-texto").value.trim()],
    ].filter(([c, e, f]) => erroDe(c, e, f));
    if (faltas.length) $(faltas[0][0]).focus();
    return !faltas.length;
  }

  function ajusta(muda_) {
    muda_(ajustes);
    ajustes = U.ajustes(ajustes);
    pintaAjustes();
    guarda({ ajustes });
  }

  function baixa(nome, conteudo, tipo) {
    const url = URL.createObjectURL(new Blob([conteudo], { type: tipo }));
    const a = document.createElement("a");
    a.href = url;
    a.download = nome;
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 60000);
  }

  // ---------- gestos
  for (const b of $$("[data-ir]")) b.addEventListener("click", () => vai(b.dataset.ir));
  for (const b of $$("[data-ninho]")) {
    b.addEventListener("click", () => chrome.tabs.create({ url: chrome.runtime.getURL(`ninho.html#${b.dataset.ninho}`) }));
  }
  $("#abrir-ninho").addEventListener("click", () => chrome.tabs.create({ url: chrome.runtime.getURL("ninho.html") }));
  $("#silencio").addEventListener("click", () => acaoPrincipal().catch(() => avisa("Não deu. Tente de novo.")));
  document.addEventListener("keydown", atalho);

  $("#busca").addEventListener("input", () => {
    const q = R.atalho($("#busca").value).replace(/-/g, " ");
    let algum = false;
    for (const l of $("#menu").children) {
      const onde = R.atalho(`${l.textContent} ${l.dataset.busca ?? ""}`).replace(/-/g, " ");
      const ve = !q || q.split(" ").every((p) => onde.includes(p));
      l.hidden = !ve;
      algum ||= ve;
    }
    $("#busca-vazia").hidden = algum;
  });

  for (const b of $$("[data-favorito]")) {
    b.addEventListener("click", () => ajusta((a) => {
      const f = b.dataset.favorito;
      a.favoritos = a.favoritos.includes(f) ? a.favoritos.filter((x) => x !== f) : [...a.favoritos, f];
    }));
  }

  $("#permitir").addEventListener("click", () => {
    ajusta((a) => {
      a.consentido = true;
      a.visto = U.VERSAO;
    });
    vai("inicio");
  });
  $("#entendi").addEventListener("click", () => {
    ajusta((a) => { a.visto = U.VERSAO; });
    vai("inicio");
  });
  for (const c of $$("[data-esconde]")) c.addEventListener("change", () => ajusta((a) => { a.esconder[c.dataset.esconde] = c.checked; }));
  for (const c of $$("[data-ajuste]")) c.addEventListener("change", () => ajusta((a) => { a[c.dataset.ajuste] = c.checked; }));
  for (const c of $$("[data-oculta]")) c.addEventListener("change", () => ajusta((a) => { a.aparencia[c.dataset.oculta] = c.checked; }));
  for (const [nome, aplica] of [
    ["plumagem", (a, v) => { a.plumagem = v; }], ["tema", (a, v) => { a.tema = v; }],
    ["paradoMin", (a, v) => { a.paradoMin = Number(v); }], ["passaro", (a, v) => { a.passaro = v; }],
    ["letra", (a, v) => { a.aparencia.letra = Number(v); }], ["idioma", (a, v) => { a.idioma = v; }],
  ]) {
    for (const r of $$(`[name="${nome}"]`)) r.addEventListener("change", () => ajusta((a) => aplica(a, r.value)));
  }
  for (const e of $$("[data-texto]")) e.addEventListener("change", () => ajusta((a) => { a[e.dataset.texto] = e.value; }));
  for (const e of $$("[data-pix]")) e.addEventListener("change", () => ajusta((a) => { a.pix[e.dataset.pix] = e.value; }));

  for (const b of $$("[data-variavel]")) {
    b.addEventListener("click", () => {
      const campo = $("#r-texto");
      const [i, f] = [campo.selectionStart, campo.selectionEnd];
      campo.setRangeText(b.dataset.variavel, i, f, "end");
      campo.focus();
    });
  }

  // o envio de formulário fica bloqueado pela CSP; aqui só se usa o evento
  $("#form-resposta").addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!validaResposta()) return;
    const nova = { id: R.novoId(), nome: $("#r-nome").value.trim(), atalho: $("#r-atalho").value, texto: $("#r-texto").value.trim() };
    if (!(await guardaDados({ ...dados, respostas: [...dados.respostas, nova] }))) return;
    e.target.reset();
    vai("respostas");
    avisa("Resposta salva");
  });

  $("#form-conversar").addEventListener("submit", async (e) => {
    e.preventDefault();
    const numero = R.telefone($("#c-numero").value);
    if (erroDe("#c-numero", "#e-numero", !numero)) return $("#c-numero").focus();
    await chrome.runtime.sendMessage({ uirapp: "abrir", url: R.linkConversa(numero, $("#c-texto").value.trim()) });
    window.close();
  });

  const senhaPede = () => { $("#campo-senha").hidden = $('[name="formato"]:checked').value !== "html"; };
  for (const r of $$('[name="formato"]')) r.addEventListener("change", senhaPede);
  $("#form-exportar").addEventListener("submit", async (e) => {
    e.preventDefault();
    const formato = $('[name="formato"]:checked').value;
    const senha = formato === "html" ? $("#x-senha").value : "";
    if (erroDe("#x-senha", "#e-senha", Boolean(senha) && senha.length < 8)) return $("#x-senha").focus();
    const r = await pedeAoWhatsApp({ uirapp: "exportar" });
    if (!r.ok) return avisa(MOTIVOS[r.motivo] ?? MOTIVOS.sem);
    if (!r.mensagens.length) return avisa(MOTIVOS.sem);
    const titulo = r.nome || T("Conversa");
    const nome = `${R.atalho(titulo) || "conversa"}-${new Date().toISOString().slice(0, 10)}`;
    if (formato === "txt") baixa(`${nome}.txt`, R.txt(r.mensagens), "text/plain;charset=utf-8");
    else if (formato === "csv") baixa(`${nome}.csv`, R.csv(r.mensagens), "text/csv;charset=utf-8");
    else if (senha) baixa(`${nome}.html`, R.htmlTrancado(titulo, await R.tranca(R.paraTrancar(r.mensagens), senha)), "text/html;charset=utf-8");
    else baixa(`${nome}.html`, R.html(titulo, r.mensagens), "text/html;charset=utf-8");
    $("#x-senha").value = "";
    avisa(`${r.mensagens.length} ${T("mensagens exportadas")}`);
  });

  $("#baixar").addEventListener("click", async () => {
    const r = await pedeAoWhatsApp({ uirapp: "baixar" });
    avisa(r.ok ? "Baixando" : MOTIVOS[r.motivo] ?? "Abra a foto ou o vídeo primeiro.");
  });

  $("#apagar-tudo").addEventListener("click", () => confirma("Apagar dados do Uirapp?", async () => {
    try {
      await D.apaga();
      // escondido continua escondido: apagar dados não pode descobrir a tela
      await chrome.storage.local.remove(escondido ? ["ajustes", "tecla"] : ["ajustes", "tecla", "silencio"]);
      await chrome.runtime.sendMessage({ uirapp: "lembretes" }).catch(() => {});
    } catch {
      avisa("Não deu para apagar. Tente de novo.");
      return;
    }
    ajustes = U.ajustes();
    dados = R.dados();
    pintaAjustes();
    pintaRespostas();
    pintaTemas();
    vai("boas-vindas");
    avisa("Dados apagados");
  }));
  $("#dialogo-manter").addEventListener("click", () => $("#dialogo").close());
  $("#dialogo-apagar").addEventListener("click", () => {
    $("#dialogo").close();
    aoApagar?.();
  });

  chrome.storage.onChanged.addListener((mudou, onde) => {
    if (onde !== "local") return;
    if (mudou.ajustes) {
      ajustes = U.ajustes(mudou.ajustes.newValue);
      pintaAjustes();
    }
    if (mudou.tecla) ultimaTecla = Number(mudou.tecla.newValue) || 0;
    if (mudou.silencio) escondido = U.silencio(mudou.silencio.newValue);
    pintaPalco();
  });

  async function comeca() {
    try {
      const g = await chrome.storage.local.get(["ajustes", "silencio", "tecla"]);
      ajustes = U.ajustes(g.ajustes);
      escondido = U.silencio(g.silencio);
      ultimaTecla = Number(g.tecla) || 0;
    } catch {
      avisa("Não deu para ler os ajustes.");
    }
    try {
      dados = await D.le();
    } catch {
      avisa("Não deu para ler suas respostas.");
    }
    pintaTemas();
    pintaAjustes();
    pintaRespostas();
    senhaPede();
    await confereWhatsApp();
    pintaPalco();
    vai(ajustes.consentido && ajustes.visto !== U.VERSAO ? "novidades" : "inicio", false);
    raiz.dataset.pronto = "";
    setInterval(confereWhatsApp, 1000);
  }

  comeca();
})();
