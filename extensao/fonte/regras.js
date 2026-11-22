// Regras puras do Uirapp: sem DOM, sem rede, sem armazenamento. Testadas em testes/regras.test.mjs.
"use strict";

globalThis.UirappRegras = (() => {
  // ---------- texto
  const corta = (v, max) => (typeof v === "string" ? v.trim().slice(0, max) : "");
  const semAcento = (v) => v.normalize("NFD").replace(/[̀-ͯ]/g, "");
  const novoId = () => (globalThis.crypto?.randomUUID?.() ?? `${Date.now()}-${Math.random()}`).slice(0, 40);
  const idLimpo = (v) => (typeof v === "string" && /^[A-Za-z0-9-]{1,40}$/.test(v) ? v : novoId());

  function atalho(v) {
    if (typeof v !== "string") return "";
    return semAcento(v).toLowerCase().replace(/^\s*\/+/, "").replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 24);
  }

  // ---------- telefone e link oficial de conversa
  function telefone(cru) {
    if (typeof cru !== "string") return null;
    const v = cru.trim();
    let d = v.replace(/\D/g, "");
    let internacional = v.startsWith("+");
    if (!internacional && d.startsWith("00")) {
      d = d.slice(2);
      internacional = true;
    }
    if (!internacional) {
      d = d.replace(/^0+/, "");
      if (d.length === 10 || d.length === 11) d = `55${d}`;
    }
    return d.length >= 8 && d.length <= 15 && /^[1-9]/.test(d) ? d : null;
  }

  function linkConversa(numero, texto = "") {
    const u = new URL("https://web.whatsapp.com/send");
    if (numero) u.searchParams.set("phone", numero);
    if (texto) u.searchParams.set("text", texto);
    return u.href;
  }

  // ---------- variáveis das respostas
  const DIAS = ["domingo", "segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado"];
  const dois = (n) => String(n).padStart(2, "0");

  function preenche(texto, ctx = {}) {
    const agora = ctx.agora instanceof Date ? ctx.agora : new Date();
    const h = agora.getHours();
    const nome = corta(ctx.nome, 80);
    const valores = {
      saudacao: h >= 5 && h < 12 ? "Bom dia" : h >= 12 && h < 18 ? "Boa tarde" : "Boa noite",
      data: `${dois(agora.getDate())}/${dois(agora.getMonth() + 1)}/${agora.getFullYear()}`,
      hora: `${dois(h)}:${dois(agora.getMinutes())}`,
      dia: DIAS[agora.getDay()],
      nome,
      primeiro_nome: nome.split(/\s+/)[0] || "",
      assinatura: corta(ctx.assinatura, 200),
      pix: corta(ctx.pix, 300),
    };
    // uma passada só: valor que contém {algo} não é expandido de novo
    return String(texto).replace(/\{([a-z_]+)\}/g, (inteiro, chave) => (valores[chave] ? valores[chave] : inteiro));
  }

  // ---------- dinheiro e Pix copia e cola (BR Code estático do Banco Central)
  function centavos(cru) {
    if (typeof cru !== "string" && typeof cru !== "number") return null;
    let v = String(cru).replace(/R\$|\s/g, "");
    if (!v || v.startsWith("-")) return null;
    if (v.includes(",")) v = v.replace(/\./g, "").replace(",", ".");
    else if (/^\d{1,3}(\.\d{3})+$/.test(v)) v = v.replace(/\./g, "");
    if (!/^\d{1,11}(\.\d{1,2})?$/.test(v)) return null;
    const [inteiro, fracao = ""] = v.split(".");
    return Number(inteiro) * 100 + Number(fracao.padEnd(2, "0"));
  }

  function crc16(texto) {
    let crc = 0xffff;
    for (const b of new TextEncoder().encode(texto)) {
      crc ^= b << 8;
      for (let i = 0; i < 8; i++) crc = crc & 0x8000 ? ((crc << 1) ^ 0x1021) & 0xffff : (crc << 1) & 0xffff;
    }
    return crc.toString(16).toUpperCase().padStart(4, "0");
  }

  const campo = (id, valor) => `${id}${String(valor.length).padStart(2, "0")}${valor}`;
  const ascii = (v, max) => semAcento(String(v)).replace(/[^\x20-\x7E]/g, "").trim().slice(0, max);

  function pix({ chave, nome, cidade, valor, descricao } = {}) {
    const k = corta(chave, 77);
    const n = ascii(nome ?? "", 25);
    const c = ascii(cidade ?? "", 15);
    if (!k || !n || !c) return null;
    let conta = campo("00", "br.gov.bcb.pix") + campo("01", k);
    const d = ascii(descricao ?? "", 99 - conta.length - 4);
    if (d) conta += campo("02", d);
    if (conta.length > 99) return null;
    let corpo = campo("00", "01") + campo("26", conta) + campo("52", "0000") + campo("53", "986");
    if (valor !== undefined && valor !== "") {
      const cent = centavos(valor);
      if (cent === null || cent === 0) return null;
      corpo += campo("54", (cent / 100).toFixed(2));
    }
    corpo += campo("58", "BR") + campo("59", n) + campo("60", c) + campo("62", campo("05", "***")) + "6304";
    return corpo + crc16(corpo);
  }

  // ---------- cores e temas
  const HEX = /^#([0-9a-f]{3}|[0-9a-f]{6})$/i;
  function rgb(hex) {
    let h = hex.slice(1);
    if (h.length === 3) h = [...h].map((x) => x + x).join("");
    return [0, 2, 4].map((i) => parseInt(h.slice(i, i + 2), 16));
  }
  const paraHex = (c) => `#${c.map((x) => Math.round(Math.min(255, Math.max(0, x))).toString(16).padStart(2, "0")).join("").toUpperCase()}`;
  const mistura = (a, b, t) => paraHex(rgb(a).map((x, i) => x + (rgb(b)[i] - x) * t));
  function luz(hex) {
    const [r, g, b] = rgb(hex).map((x) => {
      const v = x / 255;
      return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4;
    });
    return 0.2126 * r + 0.7152 * g + 0.0722 * b;
  }
  function contraste(a, b) {
    const [x, y] = [luz(a), luz(b)].sort((m, n) => n - m);
    return (x + 0.05) / (y + 0.05);
  }

  // empurra a cor para o preto ou o branco até ler bem sobre todos os fundos
  function legivel(cor, fundos, alvo = 4.6) {
    const pior = (c) => Math.min(...fundos.map((f) => contraste(c, f)));
    if (pior(cor) >= alvo) return cor;
    let melhor = null;
    for (const ponta of ["#000000", "#FFFFFF"]) {
      for (let t = 0.05; t <= 1.0001; t += 0.05) {
        const c = mistura(cor, ponta, t);
        if (pior(c) >= alvo) {
          if (!melhor || t < melhor.t) melhor = { c, t };
          break;
        }
      }
    }
    return melhor?.c ?? null;
  }

  function paleta(t) {
    const fundo = t.fundo;
    const escuro = luz(fundo) < 0.2;
    for (const passo of [1, 0.5, 0]) {
      const elevado = mistura(fundo, escuro ? "#FFFFFF" : "#000000", 0.05 * passo);
      const recebida = mistura(fundo, escuro ? "#FFFFFF" : "#000000", 0.09 * passo);
      const enviada = mistura(fundo, t.acento, 0.24 * passo);
      const fundos = [fundo, elevado, recebida, enviada];
      const texto = legivel(t.texto, fundos);
      if (!texto) continue;
      const apoio = legivel(mistura(texto, fundo, 0.28), fundos) ?? texto;
      const sobreAcento = contraste("#000000", t.acento) >= contraste("#FFFFFF", t.acento) ? "#000000" : "#FFFFFF";
      return { fundo, elevado, recebida, enviada, texto, apoio, acento: t.acento, sobreAcento, escuro };
    }
    return null;
  }

  const TEMAS = Object.freeze([
    { id: "manha", nome: "Manhã", fundo: "#F4F7F8", texto: "#1E1E24", acento: "#17627A" },
    { id: "noite", nome: "Noite", fundo: "#18242E", texto: "#EEF4F6", acento: "#8FCFE0" },
    { id: "igarape", nome: "Igarapé", fundo: "#0F2A2E", texto: "#E6F4F1", acento: "#4FD1B5" },
    { id: "acai", nome: "Açaí", fundo: "#241425", texto: "#F3E8F2", acento: "#C77DFF" },
    { id: "urucum", nome: "Urucum", fundo: "#FFF4EC", texto: "#2A1A12", acento: "#C2410C" },
    { id: "buriti", nome: "Buriti", fundo: "#FFF8E6", texto: "#2B2111", acento: "#B45309" },
    { id: "jenipapo", nome: "Jenipapo", fundo: "#10141F", texto: "#E8ECF7", acento: "#7AA2FF" },
    { id: "neblina", nome: "Neblina", fundo: "#E9EEF0", texto: "#1F2A30", acento: "#4A6B7C" },
    { id: "mata", nome: "Mata", fundo: "#102117", texto: "#E7F3EA", acento: "#6BCB77" },
    { id: "vitoria-regia", nome: "Vitória-régia", fundo: "#F1FAF3", texto: "#14301E", acento: "#2F855A" },
    { id: "arara", nome: "Arara", fundo: "#1B1020", texto: "#FBEFF0", acento: "#FF6B5B" },
    { id: "cacau", nome: "Cacau", fundo: "#2A1D17", texto: "#F6EDE6", acento: "#E0A56A" },
    { id: "contraste", nome: "Alto contraste", fundo: "#000000", texto: "#FFFFFF", acento: "#FFD400" },
    { id: "papel", nome: "Papel", fundo: "#FAFAF7", texto: "#111111", acento: "#5B5BD6" },
  ]);

  function imagem(url) {
    if (typeof url !== "string" || url.length > 4_200_000) return "";
    return /^data:image\/(png|jpeg|webp);base64,[A-Za-z0-9+/]+=*$/.test(url) ? url : "";
  }

  function tema(cru) {
    if (!cru || typeof cru !== "object") return null;
    const { fundo, texto, acento } = cru;
    if (![fundo, texto, acento].every((c) => typeof c === "string" && HEX.test(c))) return null;
    const norm = (c) => paraHex(rgb(c));
    return {
      id: atalho(cru.id) || "meu",
      nome: corta(cru.nome, 30) || "Meu tema",
      fundo: norm(fundo),
      texto: norm(texto),
      acento: norm(acento),
      imagem: imagem(cru.imagem),
    };
  }

  function cssTema(cru) {
    const t = tema(cru);
    const c = t && paleta(t);
    if (!c) return "";
    const v = {
      "--WDS-surface-default": c.fundo, "--WDS-background-wash-plain": c.fundo, "--WDS-background-wash-inset": c.fundo,
      "--app-background": c.fundo, "--WDS-surface-elevated-default": c.elevado, "--WDS-surface-emphasized": c.elevado,
      "--WDS-surface-elevated-emphasized": c.recebida, "--WDS-background-elevated-wash-plain": c.elevado,
      "--WDS-background-elevated-wash-inset": c.elevado, "--WDS-content-default": c.texto, "--WDS-content-deemphasized": c.apoio,
      "--WDS-content-action-default": c.texto, "--primary-strong": c.texto, "--primary-stronger": c.texto,
      "--WDS-accent": c.acento, "--WDS-content-action-emphasized": c.acento, "--WDS-content-on-accent": c.sobreAcento,
      "--WDS-systems-bubble-surface-incoming": c.recebida, "--WDS-systems-bubble-surface-outgoing": c.enviada,
      "--WDS-systems-bubble-content-deemphasized": c.apoio, "--bubble-meta": c.apoio, "--bubble-meta-icon": c.apoio,
      "--WDS-systems-chat-background-wallpaper": c.fundo, "--WDS-systems-chat-surface-composer": c.elevado,
      "--WDS-systems-chat-surface-tray": c.fundo,
    };
    const declara = Object.entries(v).map(([k, x]) => `${k}:${x} !important`).join(";");
    let css = `html,body,body.dark,#app{${declara};color-scheme:${c.escuro ? "dark" : "light"} !important}`
      + `body{background:${c.fundo} !important}`;
    if (t.imagem) {
      css += `#main [data-testid="conversation-panel-body"]{background:${c.fundo} url("${t.imagem}") center/cover no-repeat !important}`;
    }
    return css;
  }

  // ---------- exportar conversa
  function cabecalho(pre) {
    const m = typeof pre === "string" && /^\[([^,\]]+)(?:, ([^\]]+))?\] (.*): $/.exec(pre);
    return m ? { hora: m[1].trim(), data: (m[2] ?? "").trim(), autor: m[3].trim() } : null;
  }

  const linha = (m) => `[${m.data} ${m.hora}] ${m.autor}: ${m.texto || `(${m.tipo})`}`;
  const txt = (msgs) => `${msgs.map(linha).join("\n")}\n`;

  function celula(v) {
    let s = String(v ?? "");
    if (/^[=+\-@\t\r]/.test(s)) s = `'${s}`;
    return `"${s.replace(/"/g, '""')}"`;
  }
  const csv = (msgs) => `﻿${["data", "hora", "autor", "tipo", "texto"].map(celula).join(";")}\n`
    + msgs.map((m) => [m.data, m.hora, m.autor, m.tipo, m.texto].map(celula).join(";")).join("\n") + "\n";

  const escapa = (v) => String(v ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
  const ESTILO = "body{margin:0;font:15px/1.45 system-ui,sans-serif;background:#F4F7F8;color:#1E1E24}"
    + "main{max-width:760px;margin:0 auto;padding:24px 16px}h1{font-size:22px}"
    + "p{margin:0 0 10px;padding:8px 12px;background:#fff;border-radius:10px;white-space:pre-wrap;overflow-wrap:anywhere}"
    + "b{display:block;font-size:13px;color:#55616A}footer{margin-top:24px;font-size:13px;color:#55616A}"
    + "input,button{font:inherit;padding:8px 12px}";

  function html(titulo, msgs) {
    const corpo = msgs.map((m) => `<p><b>${escapa(`${m.data} ${m.hora} · ${m.autor}`)}</b>${escapa(m.texto || `(${m.tipo})`)}</p>`).join("");
    return `<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">`
      + `<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'">`
      + `<meta name="viewport" content="width=device-width,initial-scale=1"><title>${escapa(titulo)}</title><style>${ESTILO}</style></head>`
      + `<body><main><h1>${escapa(titulo)}</h1>${corpo}<footer>Exportado pelo Uirapp.</footer></main></body></html>`;
  }

  // página que se abre sozinha com a senha certa; o texto entra por textContent
  function htmlTrancado(titulo, caixa) {
    const js = `const c=${JSON.stringify(caixa).replace(/</g, "\\u003c")};`
      + "const b=s=>Uint8Array.from(atob(s),x=>x.charCodeAt(0));"
      + "document.querySelector('form').onsubmit=async e=>{e.preventDefault();const s=document.querySelector('input').value;"
      + "try{const k=await crypto.subtle.importKey('raw',new TextEncoder().encode(s),'PBKDF2',false,['deriveKey']);"
      + "const a=await crypto.subtle.deriveKey({name:'PBKDF2',salt:b(c.sal),iterations:c.voltas,hash:'SHA-256'},k,{name:'AES-GCM',length:256},false,['decrypt']);"
      + "const t=new TextDecoder().decode(await crypto.subtle.decrypt({name:'AES-GCM',iv:b(c.iv)},a,b(c.dado)));"
      + "const m=document.querySelector('main');m.replaceChildren();for(const l of JSON.parse(t)){const p=document.createElement('p');"
      + "const h=document.createElement('b');h.textContent=l.c;p.append(h,l.t);m.append(p)}}"
      + "catch{document.querySelector('output').textContent='Senha errada.'}}";
    return `<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">`
      + `<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'">`
      + `<meta name="viewport" content="width=device-width,initial-scale=1"><title>${escapa(titulo)}</title><style>${ESTILO}</style></head>`
      + `<body><main><h1>${escapa(titulo)}</h1><form><input type="password" aria-label="Senha" autofocus> <button>Abrir</button>`
      + ` <output></output></form></main><script>${js}<\/script></body></html>`; // <\/ deixa este arquivo seguro também quando embutido numa página
  }

  const paraTrancar = (msgs) => JSON.stringify(msgs.map((m) => ({ c: `${m.data} ${m.hora} · ${m.autor}`, t: m.texto || `(${m.tipo})` })));

  // ---------- senha (PBKDF2 + AES-GCM)
  const VOLTAS = 600000;
  function base64(bytes) {
    let s = "";
    for (let i = 0; i < bytes.length; i += 0x8000) s += String.fromCharCode(...bytes.subarray(i, i + 0x8000));
    return btoa(s);
  }
  const deBase64 = (s) => Uint8Array.from(atob(s), (x) => x.charCodeAt(0));

  async function chave(senha, sal, voltas, uso) {
    const base = await crypto.subtle.importKey("raw", new TextEncoder().encode(senha), "PBKDF2", false, ["deriveKey"]);
    return crypto.subtle.deriveKey({ name: "PBKDF2", salt: sal, iterations: voltas, hash: "SHA-256" }, base,
      { name: "AES-GCM", length: 256 }, false, [uso]);
  }

  async function tranca(texto, senha) {
    const sal = crypto.getRandomValues(new Uint8Array(16));
    const iv = crypto.getRandomValues(new Uint8Array(12));
    const k = await chave(senha, sal, VOLTAS, "encrypt");
    const dado = new Uint8Array(await crypto.subtle.encrypt({ name: "AES-GCM", iv }, k, new TextEncoder().encode(texto)));
    return { uirapp: "caixa", versao: 1, voltas: VOLTAS, sal: base64(sal), iv: base64(iv), dado: base64(dado) };
  }

  async function destranca(caixa, senha) {
    if (caixa?.uirapp !== "caixa" || caixa.versao !== 1 || !(caixa.voltas >= 100000 && caixa.voltas <= 5000000)) {
      throw new Error("caixa estranha");
    }
    const k = await chave(senha, deBase64(caixa.sal), caixa.voltas, "decrypt");
    return new TextDecoder().decode(await crypto.subtle.decrypt({ name: "AES-GCM", iv: deBase64(caixa.iv) }, k, deBase64(caixa.dado)));
  }

  // ---------- dados guardados (respostas, atendimento e lembretes)
  const ETAPAS = Object.freeze([
    { id: "novo", nome: "Novo" }, { id: "conversando", nome: "Conversando" },
    { id: "proposta", nome: "Proposta" }, { id: "fechado", nome: "Fechado" },
  ]);
  const lista = (v, max) => (Array.isArray(v) ? v.slice(0, max) : []);
  const numero = (v) => (Number.isFinite(v) && v > 0 ? Math.floor(v) : 0);

  function dados(cru = {}) {
    const d = cru && typeof cru === "object" ? cru : {};
    const usados = new Set();
    const respostas = lista(d.respostas, 500).filter((r) => typeof r?.nome === "string" && typeof r?.texto === "string" && r.nome.trim())
      .map((r) => {
        let a = atalho(r.atalho);
        if (usados.has(a)) a = "";
        if (a) usados.add(a);
        return { id: idLimpo(r.id), nome: corta(r.nome, 60), texto: corta(r.texto, 4000), atalho: a, pasta: corta(r.pasta, 30) };
      });
    let etapas = lista(d.etapas, 12).filter((e) => typeof e?.nome === "string" && e.nome.trim())
      .map((e) => ({ id: atalho(e.id) || novoId(), nome: corta(e.nome, 30) }));
    if (!etapas.length) etapas = ETAPAS.map((e) => ({ ...e }));
    const ids = new Set(etapas.map((e) => e.id));
    const fichas = lista(d.fichas, 5000).filter((f) => typeof f?.nome === "string" && f.nome.trim()).map((f) => ({
      id: idLimpo(f.id),
      nome: corta(f.nome, 80),
      telefone: telefone(typeof f.telefone === "string" ? f.telefone : "") ?? "",
      etapa: ids.has(f.etapa) ? f.etapa : etapas[0].id,
      etiquetas: [...new Set(lista(f.etiquetas, 12).filter((e) => typeof e === "string").map((e) => corta(e, 24)).filter(Boolean))],
      nota: corta(f.nota, 4000),
      valor: Number.isInteger(f.valor) && f.valor >= 0 ? f.valor : null,
      criada: numero(f.criada),
      atualizada: numero(f.atualizada),
    }));
    const lembretes = lista(d.lembretes, 500).filter((l) => typeof l?.titulo === "string" && l.titulo.trim() && numero(l.quando))
      .map((l) => ({
        id: idLimpo(l.id), titulo: corta(l.titulo, 80), quando: numero(l.quando), texto: corta(l.texto, 4000),
        telefone: telefone(typeof l.telefone === "string" ? l.telefone : "") ?? "", fichaId: typeof l.fichaId === "string" ? l.fichaId.slice(0, 40) : "",
        feito: l.feito === true,
      }));
    const temas = lista(d.temas, 30).map(tema).filter(Boolean);
    return { respostas, etapas, fichas, lembretes, temas };
  }

  function backup(texto) {
    let b;
    try {
      b = JSON.parse(texto);
    } catch {
      return null;
    }
    if (b?.uirapp === "caixa") return { trancado: b };
    if (b?.uirapp !== "backup" || b.versao !== 1 || typeof b.dados !== "object" || typeof b.ajustes !== "object") return null;
    return { ajustes: b.ajustes, dados: dados(b.dados) };
  }

  const paraBackup = (ajustes, d) => JSON.stringify({ uirapp: "backup", versao: 1, criado: new Date().toISOString(), ajustes, dados: dados(d) }, null, 1);

  return Object.freeze({
    atalho, telefone, linkConversa, preenche, centavos, crc16, pix, contraste, mistura, paleta, TEMAS, imagem, tema, cssTema,
    cabecalho, txt, csv, html, htmlTrancado, paraTrancar, escapa, tranca, destranca, ETAPAS, dados, backup, paraBackup, novoId,
  });
})();
