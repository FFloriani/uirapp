// Fundo da extensão: reforça o CSS do Silêncio, atende o atalho, lembra, compartilha e acha uma resposta pelo atalho.
// Não abre conexão, não registra nada e não envia mensagem: tudo que vai para o WhatsApp a pessoa envia.
"use strict";

importScripts("regras.js", "nucleo.js", "deposito.js");

const U = globalThis.Uirapp;
const R = globalThis.UirappRegras;
const D = globalThis.UirappDeposito;
const doWhatsApp = (de) => de.id === chrome.runtime.id && de.tab && de.frameId === 0 && de.url?.startsWith(U.WHATSAPP);
const daExtensao = (de) => de.id === chrome.runtime.id && de.url?.startsWith(`chrome-extension://${chrome.runtime.id}/`);

// ---------- abre ou reaproveita a aba do WhatsApp
async function abreWhatsApp(url = U.WHATSAPP) {
  const [aba] = await chrome.tabs.query({ url: `${U.WHATSAPP}*` });
  if (aba) {
    await chrome.tabs.update(aba.id, { url, active: true });
    await chrome.windows.update(aba.windowId, { focused: true }).catch(() => {});
  } else {
    await chrome.tabs.create({ url });
  }
}

// ---------- lembretes: alarme do navegador e aviso do sistema
async function agendaLembretes() {
  const { lembretes } = await D.le();
  const todos = await chrome.alarms.getAll();
  await Promise.all(todos.filter((a) => a.name.startsWith("lembrete:")).map((a) => chrome.alarms.clear(a.name)));
  const agora = Date.now();
  for (const l of lembretes) {
    if (!l.feito && l.quando > agora) await chrome.alarms.create(`lembrete:${l.id}`, { when: l.quando });
  }
}

chrome.alarms.onAlarm.addListener(async (alarme) => {
  if (!alarme.name.startsWith("lembrete:")) return;
  const id = alarme.name.slice(9);
  const { lembretes } = await D.le();
  const l = lembretes.find((x) => x.id === id && !x.feito);
  if (!l) return;
  chrome.notifications.create(`lembrete:${id}`, {
    type: "basic", iconUrl: "icones/icone-128.png", title: l.titulo, message: l.texto ? "A mensagem está pronta para você enviar." : "Hora do lembrete.",
    priority: 2, requireInteraction: true,
  });
});

chrome.notifications.onClicked.addListener(async (nota) => {
  if (!nota.startsWith("lembrete:")) return;
  chrome.notifications.clear(nota);
  const { lembretes } = await D.le();
  const l = lembretes.find((x) => x.id === nota.slice(9));
  if (l?.telefone || l?.texto) await abreWhatsApp(R.linkConversa(l.telefone || null, l.texto));
  else await chrome.tabs.create({ url: chrome.runtime.getURL("ninho.html#lembretes") });
});

// ---------- botão direito: compartilhar no WhatsApp
function criaMenus() {
  chrome.contextMenus.removeAll(() => {
    chrome.contextMenus.create({ id: "compartilhar", title: "Compartilhar no WhatsApp", contexts: ["page", "selection", "link", "image"] });
  });
}

chrome.contextMenus.onClicked.addListener(async (info, aba) => {
  if (info.menuItemId !== "compartilhar") return;
  const g = await chrome.storage.local.get("ajustes");
  if (!U.ajustes(g.ajustes).consentido) return;
  const texto = (info.selectionText ? `${info.selectionText}\n` : "") + (info.linkUrl || info.srcUrl || info.pageUrl || aba?.url || "");
  if (texto.trim()) await abreWhatsApp(R.linkConversa(null, texto.trim().slice(0, 4000)));
});

chrome.runtime.onInstalled.addListener(() => {
  criaMenus();
  agendaLembretes().catch(() => {});
});
chrome.runtime.onStartup.addListener(() => agendaLembretes().catch(() => {}));

// ---------- mensagens
chrome.runtime.onMessage.addListener((pedido, de, responde) => {
  const tipo = pedido?.uirapp;
  if (doWhatsApp(de) && tipo === "reforca") {
    chrome.scripting
      .insertCSS({ target: { tabId: de.tab.id, documentIds: [de.documentId] }, files: ["silencio.css"], origin: "USER" })
      .then(() => responde(true), () => responde(false));
    return true;
  }
  if (doWhatsApp(de) && tipo === "som") {
    chrome.tabs.update(de.tab.id, { muted: pedido.mudo === true }).then(() => responde(true), () => responde(false));
    return true;
  }
  if (doWhatsApp(de) && tipo === "atalho") {
    // devolve só a resposta daquele atalho exato, nunca a lista
    const pedido_ = R.atalho(pedido.atalho);
    D.le().then((d) => responde(pedido_ ? d.respostas.find((r) => r.atalho === pedido_)?.texto ?? null : null), () => responde(null));
    return true;
  }
  if (daExtensao(de) && tipo === "lembretes") {
    agendaLembretes().then(() => responde(true), () => responde(false));
    return true;
  }
  if (daExtensao(de) && tipo === "abrir") {
    abreWhatsApp(typeof pedido.url === "string" && pedido.url.startsWith(U.WHATSAPP) ? pedido.url : U.WHATSAPP)
      .then(() => responde(true), () => responde(false));
    return true;
  }
  return false;
});

chrome.commands.onCommand.addListener(async (comando) => {
  if (comando !== "alternar") return;
  const g = await chrome.storage.local.get(["ajustes", "silencio", "tecla"]);
  const escondido = U.silencio(g.silencio);
  if (!U.ajustes(g.ajustes).consentido && !escondido) return;
  if (Math.abs(Date.now() - (Number(g.tecla) || 0)) < U.TECLA_MS) return; // a página já tratou esta tecla
  await chrome.storage.local.set({ silencio: !escondido, tecla: Date.now() });
});
