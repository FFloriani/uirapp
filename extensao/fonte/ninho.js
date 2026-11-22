// O Ninho: atendimento, lembretes, estúdio de temas, desenho e backup. Tudo local; nada sai do computador.
// Texto que a pessoa digita entra sempre por textContent.
"use strict";

(() => {
  const U = globalThis.Uirapp;
  const R = globalThis.UirappRegras;
  const D = globalThis.UirappDeposito;
  const T = (s) => globalThis.UirappIdioma?.t(s) ?? s;
  const $ = (s) => document.querySelector(s);
  const $$ = (s) => document.querySelectorAll(s);
  const PARTES = ["atendimento", "lembretes", "temas", "desenho", "backup"];

  let ajustes = U.ajustes();
  let dados = R.dados();
  let fichaAberta = null;
  let lembreteAberto = null;
  let aoApagar = null;
  let relogio = 0;

  function avisa(texto) {
    $("#aviso-texto").textContent = T(texto);
    $("#aviso").hidden = false;
    clearTimeout(relogio);
    relogio = setTimeout(() => { $("#aviso").hidden = true; }, 2600);
  }

  async function guarda(novo, lembretes = false) {
    try {
      dados = await D.grava(novo);
    } catch {
      avisa("Não deu para salvar. Tente de novo.");
      return false;
    }
    if (lembretes) await chrome.runtime.sendMessage({ uirapp: "lembretes" }).catch(() => {});
    pinta();
    return true;
  }

  async function guardaAjustes(muda) {
    muda(ajustes);
    ajustes = U.ajustes(ajustes);
    await chrome.storage.local.set({ ajustes });
  }

  function confirma(titulo, acao) {
    $("#dialogo-titulo").textContent = T(titulo);
    aoApagar = acao;
    $("#dialogo").showModal();
    $("#dialogo-manter").focus();
  }

  const erro = (campo, aviso, falta) => {
    $(campo).setAttribute("aria-invalid", String(falta));
    $(aviso).hidden = !falta;
    return falta;
  };
  const reais = (c) => (c / 100).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
  const quando = (ms) => new Date(ms).toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" });
  const paraCampoData = (ms) => {
    const d = new Date(ms - new Date(ms).getTimezoneOffset() * 60000);
    return d.toISOString().slice(0, 16);
  };
  function baixa(nome, conteudo, tipo) {
    const url = URL.createObjectURL(conteudo instanceof Blob ? conteudo : new Blob([conteudo], { type: tipo }));
    const a = document.createElement("a");
    a.href = url;
    a.download = nome;
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 60000);
  }

  // ---------- navegação
  function mostra(parte, foca = true) {
    const qual = PARTES.includes(parte) ? parte : "atendimento";
    for (const p of PARTES) $(`#${p}`).hidden = p !== qual;
    for (const a of $$("[data-aba]")) {
      if (a.dataset.aba === qual) a.setAttribute("aria-current", "page");
      else a.removeAttribute("aria-current");
    }
    if (foca) $(`#t-${qual}`).focus({ preventScroll: true });
    if (qual === "desenho") preparaDesenho();
  }
  addEventListener("hashchange", () => mostra(location.hash.slice(1)));

  // ---------- atendimento
  function pintaQuadro() {
    const busca = R.atalho($("#f-busca").value).replace(/-/g, " ");
    const etiqueta = $("#f-etiqueta").value;
    const todas = [...new Set(dados.fichas.flatMap((f) => f.etiquetas))].sort((a, b) => a.localeCompare(b));
    const sel = $("#f-etiqueta");
    sel.replaceChildren(new Option(T("Todas as etiquetas"), ""), ...todas.map((e) => new Option(e, e)));
    sel.value = todas.includes(etiqueta) ? etiqueta : "";
    const passa = (f) => (!sel.value || f.etiquetas.includes(sel.value))
      && (!busca || R.atalho(`${f.nome} ${f.telefone} ${f.nota} ${f.etiquetas.join(" ")}`).replace(/-/g, " ").includes(busca));

    const quadro = $("#quadro");
    quadro.replaceChildren();
    for (const etapa of dados.etapas) {
      const col = $("#molde-coluna").content.firstElementChild.cloneNode(true);
      const fichas = dados.fichas.filter((f) => f.etapa === etapa.id && passa(f)).sort((a, b) => b.atualizada - a.atualizada);
      col.dataset.etapa = etapa.id;
      col.querySelector(".coluna-nome").textContent = etapa.nome;
      const total = fichas.reduce((s, f) => s + (f.valor ?? 0), 0);
      col.querySelector(".coluna-conta").textContent = total ? `${fichas.length} · ${reais(total)}` : String(fichas.length);
      const ul = col.querySelector(".coluna-fichas");
      ul.setAttribute("aria-label", etapa.nome);
      for (const f of fichas) {
        const li = $("#molde-ficha").content.firstElementChild.cloneNode(true);
        li.dataset.id = f.id;
        li.querySelector(".ficha-nome").textContent = f.nome;
        li.querySelector(".ficha-valor").textContent = f.valor ? reais(f.valor) : "";
        li.querySelector(".ficha-nota").textContent = f.nota;
        const et = li.querySelector(".ficha-etiquetas");
        for (const e of f.etiquetas) {
          const s = document.createElement("span");
          s.className = "etiqueta";
          s.textContent = e;
          et.append(s);
        }
        li.querySelector(".ficha-abrir").addEventListener("click", () => abreFicha(f));
        li.addEventListener("dragstart", (ev) => {
          ev.dataTransfer.setData("text/x-uirapp-ficha", f.id);
          li.classList.add("arrastando");
        });
        li.addEventListener("dragend", () => li.classList.remove("arrastando"));
        ul.append(li);
      }
      col.addEventListener("dragover", (ev) => {
        if (!ev.dataTransfer.types.includes("text/x-uirapp-ficha")) return;
        ev.preventDefault();
        col.classList.add("solta");
      });
      col.addEventListener("dragleave", () => col.classList.remove("solta"));
      col.addEventListener("drop", (ev) => {
        ev.preventDefault();
        col.classList.remove("solta");
        const id = ev.dataTransfer.getData("text/x-uirapp-ficha");
        const f = dados.fichas.find((x) => x.id === id);
        if (f && f.etapa !== etapa.id) guarda({ ...dados, fichas: dados.fichas.map((x) => (x.id === id ? { ...x, etapa: etapa.id, atualizada: Date.now() } : x)) });
      });
      quadro.append(col);
    }
    $("#quadro-vazio").hidden = Boolean(dados.fichas.length);
  }

  function abreFicha(f) {
    fichaAberta = f ?? null;
    const sel = $("#fi-etapa");
    sel.replaceChildren(...dados.etapas.map((e) => new Option(e.nome, e.id)));
    $("#fi-nome").value = f?.nome ?? "";
    $("#fi-telefone").value = f?.telefone ?? "";
    sel.value = f?.etapa ?? dados.etapas[0].id;
    $("#fi-valor").value = f?.valor ? (f.valor / 100).toFixed(2).replace(".", ",") : "";
    $("#fi-etiquetas").value = f?.etiquetas.join(", ") ?? "";
    $("#fi-nota").value = f?.nota ?? "";
    $("#fi-apagar").hidden = !f;
    for (const [c, e] of [["#fi-nome", "#e-fi-nome"], ["#fi-telefone", "#e-fi-tel"], ["#fi-valor", "#e-fi-valor"]]) erro(c, e, false);
    $("#d-ficha").showModal();
    $("#fi-nome").focus();
  }

  function fichaDoFormulario() {
    const nome = $("#fi-nome").value.trim();
    const telCru = $("#fi-telefone").value.trim();
    const tel = telCru ? R.telefone(telCru) : "";
    const valorCru = $("#fi-valor").value.trim();
    const valor = valorCru ? R.centavos(valorCru) : null;
    const faltas = [erro("#fi-nome", "#e-fi-nome", !nome), erro("#fi-telefone", "#e-fi-tel", tel === null), erro("#fi-valor", "#e-fi-valor", valor === null && Boolean(valorCru))];
    if (faltas.some(Boolean)) {
      $(faltas[0] ? "#fi-nome" : faltas[1] ? "#fi-telefone" : "#fi-valor").focus();
      return null;
    }
    const agora = Date.now();
    return {
      id: fichaAberta?.id ?? R.novoId(), nome, telefone: tel ?? "", etapa: $("#fi-etapa").value, valor,
      etiquetas: $("#fi-etiquetas").value.split(",").map((e) => e.trim()).filter(Boolean),
      nota: $("#fi-nota").value.trim(), criada: fichaAberta?.criada || agora, atualizada: agora,
    };
  }

  $("#form-ficha").addEventListener("submit", async (e) => {
    e.preventDefault();
    const f = fichaDoFormulario();
    if (!f) return;
    const fichas = fichaAberta ? dados.fichas.map((x) => (x.id === f.id ? f : x)) : [...dados.fichas, f];
    if (await guarda({ ...dados, fichas })) {
      $("#d-ficha").close();
      avisa("Ficha salva");
    }
  });
  $("#fi-fechar").addEventListener("click", () => $("#d-ficha").close());
  $("#fi-apagar").addEventListener("click", () => confirma("Apagar ficha?", async () => {
    if (await guarda({ ...dados, fichas: dados.fichas.filter((x) => x.id !== fichaAberta.id), lembretes: dados.lembretes.filter((l) => l.fichaId !== fichaAberta.id) }, true)) {
      $("#d-ficha").close();
      avisa("Ficha apagada");
    }
  }));
  $("#fi-conversar").addEventListener("click", async () => {
    const tel = R.telefone($("#fi-telefone").value);
    if (erro("#fi-telefone", "#e-fi-tel", !tel)) return $("#fi-telefone").focus();
    await chrome.runtime.sendMessage({ uirapp: "abrir", url: R.linkConversa(tel) });
  });
  $("#fi-lembrar").addEventListener("click", () => {
    const f = fichaDoFormulario();
    if (!f) return;
    $("#d-ficha").close();
    abreLembrete(null, { titulo: `${T("Retornar")}: ${f.nome}`, telefone: f.telefone, fichaId: fichaAberta?.id ?? "" });
  });
  $("#fi-da-conversa").addEventListener("click", async () => {
    const abas = await chrome.tabs.query({ url: `${U.WHATSAPP}*` });
    let r = null;
    try {
      if (abas[0]) r = await chrome.tabs.sendMessage(abas[0].id, { uirapp: "conversa" }, { frameId: 0 });
    } catch {
      r = null;
    }
    if (r?.nome) $("#fi-nome").value = r.nome;
    else avisa(r?.aberta ? "Mostre as conversas primeiro." : "Abra uma conversa no WhatsApp Web.");
  });
  $("#nova-ficha").addEventListener("click", () => abreFicha(null));
  $("#f-busca").addEventListener("input", pintaQuadro);
  $("#f-etiqueta").addEventListener("change", pintaQuadro);

  function linhaEtapa(e) {
    const li = document.createElement("li");
    const campo = document.createElement("input");
    campo.className = "entrada";
    campo.maxLength = 30;
    campo.value = e.nome;
    campo.dataset.id = e.id;
    campo.setAttribute("aria-label", T("Nome da etapa"));
    const tira = document.createElement("button");
    tira.type = "button";
    tira.className = "botao botao-discreto";
    tira.textContent = T("Tirar");
    tira.addEventListener("click", () => {
      if ($("#lista-etapas").children.length > 1) li.remove();
    });
    li.append(campo, tira);
    return li;
  }
  $("#editar-etapas").addEventListener("click", () => {
    $("#lista-etapas").replaceChildren(...dados.etapas.map(linhaEtapa));
    $("#d-etapas").showModal();
  });
  $("#mais-etapa").addEventListener("click", () => {
    if ($("#lista-etapas").children.length < 12) $("#lista-etapas").append(linhaEtapa({ id: "", nome: "" }));
  });
  $("#et-fechar").addEventListener("click", () => $("#d-etapas").close());
  $("#form-etapas").addEventListener("submit", async (e) => {
    e.preventDefault();
    const etapas = [...$$("#lista-etapas input")].filter((c) => c.value.trim())
      .map((c) => ({ id: c.dataset.id || R.atalho(c.value) || R.novoId(), nome: c.value.trim() }));
    if (!etapas.length) return;
    // ficha de etapa que saiu vai para a primeira
    const ids = new Set(etapas.map((x) => x.id));
    const fichas = dados.fichas.map((f) => (ids.has(f.etapa) ? f : { ...f, etapa: etapas[0].id }));
    if (await guarda({ ...dados, etapas, fichas })) $("#d-etapas").close();
  });

  // ---------- lembretes
  function pintaLembretes() {
    const ul = $("#lista-lembretes");
    ul.replaceChildren();
    const agora = Date.now();
    const ordem = [...dados.lembretes].sort((a, b) => a.feito - b.feito || a.quando - b.quando);
    for (const l of ordem) {
      const li = $("#molde-lembrete").content.firstElementChild.cloneNode(true);
      li.classList.toggle("feito", l.feito);
      li.classList.toggle("atrasado", !l.feito && l.quando < agora);
      li.querySelector(".lembrete-quando").textContent = quando(l.quando);
      li.querySelector(".lembrete-titulo").textContent = l.titulo;
      const feito = li.querySelector(".lembrete-feito");
      feito.textContent = T(l.feito ? "Refazer" : "Feito");
      feito.addEventListener("click", () => guarda({ ...dados, lembretes: dados.lembretes.map((x) => (x.id === l.id ? { ...x, feito: !x.feito } : x)) }, true));
      const editar = li.querySelector(".lembrete-editar");
      editar.setAttribute("aria-label", `${T("Abrir")} ${l.titulo}`);
      editar.addEventListener("click", () => abreLembrete(l));
      ul.append(li);
    }
    $("#lembretes-vazio").hidden = Boolean(dados.lembretes.length);
  }

  function abreLembrete(l, base = {}) {
    lembreteAberto = l;
    const v = l ?? { titulo: "", quando: Date.now() + 3600000, texto: "", telefone: "", fichaId: "", ...base };
    $("#le-titulo").value = v.titulo;
    $("#le-quando").value = paraCampoData(v.quando);
    $("#le-telefone").value = v.telefone;
    $("#le-texto").value = v.texto;
    $("#le-ficha").replaceChildren(new Option(T("Nenhuma"), ""), ...dados.fichas.map((f) => new Option(f.nome, f.id)));
    $("#le-ficha").value = v.fichaId;
    for (const [c, e] of [["#le-titulo", "#e-le-titulo"], ["#le-quando", "#e-le-quando"], ["#le-telefone", "#e-le-tel"]]) erro(c, e, false);
    if (!$("#lembretes").hidden || !$("#atendimento").hidden) $("#d-lembrete").showModal();
    $("#le-titulo").focus();
  }

  $("#form-lembrete").addEventListener("submit", async (e) => {
    e.preventDefault();
    const titulo = $("#le-titulo").value.trim();
    const ms = new Date($("#le-quando").value).getTime();
    const telCru = $("#le-telefone").value.trim();
    const tel = telCru ? R.telefone(telCru) : "";
    const faltas = [erro("#le-titulo", "#e-le-titulo", !titulo), erro("#le-quando", "#e-le-quando", !(ms > Date.now())), erro("#le-telefone", "#e-le-tel", tel === null)];
    if (faltas.some(Boolean)) return;
    const l = { id: lembreteAberto?.id ?? R.novoId(), titulo, quando: ms, texto: $("#le-texto").value.trim(), telefone: tel ?? "", fichaId: $("#le-ficha").value, feito: false };
    const lembretes = lembreteAberto ? dados.lembretes.map((x) => (x.id === l.id ? l : x)) : [...dados.lembretes, l];
    if (await guarda({ ...dados, lembretes }, true)) {
      $("#d-lembrete").close();
      avisa("Lembrete salvo");
    }
  });
  $("#le-fechar").addEventListener("click", () => $("#d-lembrete").close());
  $("#novo-lembrete").addEventListener("click", () => abreLembrete(null));

  // ---------- estúdio de temas
  let imagemTema = "";
  function temaDoEstudio() {
    return R.tema({ id: R.atalho($("#tm-nome").value) || "meu-tema", nome: $("#tm-nome").value, fundo: $("#tm-fundo").value, texto: $("#tm-texto").value, acento: $("#tm-acento").value, imagem: imagemTema });
  }
  function pintaPrevia() {
    const t = temaDoEstudio();
    const p = t && R.paleta(t);
    if (!p) return;
    const previa = $("#previa");
    previa.style.setProperty("background", p.fundo);
    previa.style.setProperty("color", p.texto);
    for (const [i, el] of [...$$(".previa-lista i")].entries()) el.style.setProperty("background", i === 0 ? p.recebida : p.elevado);
    const conversa = $(".previa-conversa");
    conversa.style.setProperty("background-image", imagemTema ? `url("${imagemTema}")` : "none");
    $(".balao-recebido").style.setProperty("background", p.recebida);
    $(".balao-enviado").style.setProperty("background", p.enviada);
    $(".previa-escrever").style.setProperty("background", p.elevado);
    $(".previa-escrever").style.setProperty("color", p.apoio);
    $("#tm-ajuste").hidden = p.texto.toUpperCase() === t.texto.toUpperCase();
    $("#tm-sem-imagem").hidden = !imagemTema;
  }
  for (const id of ["#tm-fundo", "#tm-texto", "#tm-acento"]) $(id).addEventListener("input", pintaPrevia);

  $("#tm-imagem").addEventListener("change", async () => {
    const f = $("#tm-imagem").files[0];
    if (!f) return;
    try {
      const bmp = await createImageBitmap(f);
      const escala = Math.min(1, 1600 / Math.max(bmp.width, bmp.height));
      const tela = document.createElement("canvas");
      tela.width = Math.round(bmp.width * escala);
      tela.height = Math.round(bmp.height * escala);
      tela.getContext("2d").drawImage(bmp, 0, 0, tela.width, tela.height);
      imagemTema = R.imagem(tela.toDataURL("image/jpeg", 0.82));
      pintaPrevia();
    } catch {
      avisa("Não deu para abrir essa imagem.");
    }
  });
  $("#tm-sem-imagem").addEventListener("click", () => {
    imagemTema = "";
    $("#tm-imagem").value = "";
    pintaPrevia();
  });

  async function usaTema(t) {
    await guardaAjustes((a) => {
      a.aparencia.temaId = t.id;
      a.aparencia.temaDados = t;
    });
    avisa("Tema no WhatsApp");
  }

  $("#form-tema").addEventListener("submit", async (e) => {
    e.preventDefault();
    if (erro("#tm-nome", "#e-tm-nome", !$("#tm-nome").value.trim())) return $("#tm-nome").focus();
    const t = temaDoEstudio();
    // nome repetido troca o tema antigo; os prontos não se apagam
    const id = R.TEMAS.some((x) => x.id === t.id) ? `${t.id}-meu` : t.id;
    const novo = { ...t, id };
    if (await guarda({ ...dados, temas: [...dados.temas.filter((x) => x.id !== id), novo] })) await usaTema(novo);
  });

  function pintaTemas() {
    const ul = $("#meus-temas");
    ul.replaceChildren();
    for (const t of dados.temas) {
      const li = $("#molde-meu-tema").content.firstElementChild.cloneNode(true);
      const p = R.paleta(t);
      li.querySelector(".tema-amostra").style.setProperty("background", p.fundo);
      const [a, b, c] = li.querySelectorAll(".tema-amostra i");
      a.style.setProperty("background", p.recebida);
      b.style.setProperty("background", p.acento);
      c.style.setProperty("background", p.enviada);
      li.querySelector(".meu-tema-nome").textContent = t.nome;
      li.querySelector(".tema-usar").addEventListener("click", () => usaTema(t));
      li.querySelector(".tema-exportar").addEventListener("click", () => {
        baixa(`tema-${t.id}.json`, JSON.stringify({ uirapp: "tema", versao: 1, ...t }, null, 1), "application/json");
      });
      const apagar = li.querySelector(".tema-apagar");
      apagar.setAttribute("aria-label", `${T("Apagar")} ${t.nome}`);
      apagar.addEventListener("click", () => confirma("Apagar tema?", async () => {
        await guarda({ ...dados, temas: dados.temas.filter((x) => x.id !== t.id) });
        if (ajustes.aparencia.temaId === t.id) await guardaAjustes((x) => { x.aparencia.temaId = ""; x.aparencia.temaDados = null; });
      }));
      ul.append(li);
    }
    $("#temas-vazio").hidden = Boolean(dados.temas.length);
  }

  $("#tm-importar").addEventListener("change", async () => {
    const f = $("#tm-importar").files[0];
    $("#tm-importar").value = "";
    if (!f || f.size > 5_000_000) return avisa("Esse arquivo não é um tema.");
    let t = null;
    try {
      const j = JSON.parse(await f.text());
      if (j?.uirapp === "tema") t = R.tema(j);
    } catch {
      t = null;
    }
    if (!t) return avisa("Esse arquivo não é um tema.");
    const novo = R.TEMAS.some((x) => x.id === t.id) ? { ...t, id: `${t.id}-meu` } : t;
    if (await guarda({ ...dados, temas: [...dados.temas.filter((x) => x.id !== novo.id), novo] })) avisa("Tema importado");
  });

  // ---------- desenho
  const tracos = [];
  let desenhoPronto = false;
  function preparaDesenho() {
    if (desenhoPronto) return;
    desenhoPronto = true;
    const tela = $("#tela-desenho");
    const ctx = tela.getContext("2d");
    const limpa = () => {
      ctx.fillStyle = "#FFFFFF";
      ctx.fillRect(0, 0, tela.width, tela.height);
    };
    const redesenha = () => {
      limpa();
      for (const t of tracos) {
        ctx.strokeStyle = t.cor;
        ctx.lineWidth = t.traco;
        ctx.lineCap = "round";
        ctx.lineJoin = "round";
        ctx.beginPath();
        t.pontos.forEach(([x, y], i) => (i ? ctx.lineTo(x, y) : ctx.moveTo(x, y)));
        if (t.pontos.length === 1) ctx.lineTo(t.pontos[0][0] + 0.1, t.pontos[0][1]);
        ctx.stroke();
      }
    };
    for (const s of $$(".pincel-cor")) s.style.setProperty("background", s.dataset.cor);
    limpa();
    let atual = null;
    const ponto = (e) => {
      const r = tela.getBoundingClientRect();
      return [(e.clientX - r.left) * (tela.width / r.width), (e.clientY - r.top) * (tela.height / r.height)];
    };
    tela.addEventListener("pointerdown", (e) => {
      tela.setPointerCapture(e.pointerId);
      atual = { cor: $('[name="cor"]:checked').value, traco: Number($("#d-traco").value) * (tela.width / tela.getBoundingClientRect().width), pontos: [ponto(e)] };
      tracos.push(atual);
      redesenha();
    });
    tela.addEventListener("pointermove", (e) => {
      if (!atual) return;
      atual.pontos.push(ponto(e));
      redesenha();
    });
    for (const fim of ["pointerup", "pointercancel"]) tela.addEventListener(fim, () => { atual = null; });
    $("#d-desfazer").addEventListener("click", () => {
      tracos.pop();
      redesenha();
    });
    $("#d-limpar").addEventListener("click", () => {
      tracos.length = 0;
      redesenha();
    });
    const png = () => new Promise((ok) => tela.toBlob(ok, "image/png"));
    $("#d-baixar").addEventListener("click", async () => baixa("desenho-uirapp.png", await png()));
    $("#d-copiar").addEventListener("click", async () => {
      try {
        await navigator.clipboard.write([new ClipboardItem({ "image/png": png() })]);
        avisa("Desenho copiado. Cole na conversa.");
      } catch {
        avisa("Não deu para copiar. Use Baixar.");
      }
    });
  }

  // ---------- backup
  $("#form-backup").addEventListener("submit", async (e) => {
    e.preventDefault();
    const senha = $("#b-senha").value;
    if (erro("#b-senha", "#e-b-senha", Boolean(senha) && senha.length < 8)) return $("#b-senha").focus();
    const texto = R.paraBackup(ajustes, dados);
    const conteudo = senha ? JSON.stringify(await R.tranca(texto, senha)) : texto;
    baixa(`uirapp-backup-${new Date().toISOString().slice(0, 10)}.json`, conteudo, "application/json");
    $("#b-senha").value = "";
    avisa("Backup baixado");
  });

  let paraRestaurar = null;
  async function leArquivo() {
    paraRestaurar = null;
    $("#b-restaurar").disabled = true;
    $("#b-resumo").textContent = "";
    const f = $("#b-arquivo").files[0];
    if (!f) return;
    if (f.size > 30_000_000) return void ($("#b-resumo").textContent = T("Esse arquivo não é um backup do Uirapp."));
    let b = R.backup(await f.text());
    if (b?.trancado) {
      $("#campo-r-senha").hidden = false;
      const senha = $("#b-r-senha").value;
      if (!senha) return void $("#b-r-senha").focus();
      try {
        b = R.backup(await R.destranca(b.trancado, senha));
        erro("#b-r-senha", "#e-b-r", false);
      } catch {
        erro("#b-r-senha", "#e-b-r", true);
        return;
      }
    }
    if (!b || b.trancado) return void ($("#b-resumo").textContent = T("Esse arquivo não é um backup do Uirapp."));
    paraRestaurar = b;
    $("#b-resumo").textContent = `${b.dados.respostas.length} ${T("respostas")}, ${b.dados.fichas.length} ${T("fichas")}, ${b.dados.lembretes.length} ${T("lembretes")}, ${b.dados.temas.length} ${T("temas")}.`;
    $("#b-restaurar").disabled = false;
  }
  $("#b-arquivo").addEventListener("change", () => {
    $("#b-r-senha").value = "";
    $("#campo-r-senha").hidden = true;
    leArquivo();
  });
  $("#b-r-senha").addEventListener("change", leArquivo);
  $("#form-restaurar").addEventListener("submit", (e) => {
    e.preventDefault();
    if (!paraRestaurar) return;
    confirma("Trocar tudo pelo backup?", async () => {
      // o "Permitir" é desta instalação: não vem de arquivo
      const novos = U.ajustes({ ...paraRestaurar.ajustes, consentido: ajustes.consentido, visto: ajustes.visto });
      await chrome.storage.local.set({ ajustes: novos });
      ajustes = novos;
      if (await guarda(paraRestaurar.dados, true)) avisa("Backup restaurado");
    });
  });

  // ---------- comum
  $("#dialogo-manter").addEventListener("click", () => $("#dialogo").close());
  $("#dialogo-apagar").addEventListener("click", () => {
    $("#dialogo").close();
    aoApagar?.();
  });

  function pinta() {
    pintaQuadro();
    pintaLembretes();
    pintaTemas();
    pintaPrevia();
    document.documentElement.dataset.plumagem = ajustes.plumagem;
    if (ajustes.tema) document.documentElement.dataset.tema = ajustes.tema;
    else delete document.documentElement.dataset.tema;
    globalThis.UirappIdioma?.aplica(ajustes.idioma);
  }

  chrome.storage.onChanged.addListener((m, onde) => {
    if (onde !== "local" || !m.ajustes) return;
    ajustes = U.ajustes(m.ajustes.newValue);
    pinta();
  });

  (async () => {
    try {
      ajustes = U.ajustes((await chrome.storage.local.get("ajustes")).ajustes);
      dados = await D.le();
    } catch {
      avisa("Não deu para ler seus dados.");
    }
    pinta();
    mostra(location.hash.slice(1), false);
    document.documentElement.dataset.pronto = "";
  })();
})();
