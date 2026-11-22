// Uso: node --test testes/regras.test.mjs
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";
import vm from "node:vm";

vm.runInThisContext(readFileSync(new URL("../extensao/fonte/regras.js", import.meta.url), "utf8"));
const R = globalThis.UirappRegras;

test("telefone: Brasil sem DDI ganha 55, internacional fica", () => {
  assert.equal(R.telefone("(11) 91234-5678"), "5511912345678");
  assert.equal(R.telefone("11 3456-7890"), "551134567890");
  assert.equal(R.telefone("+1 (415) 555-2671"), "14155552671");
  assert.equal(R.telefone("0044 20 7946 0958"), "442079460958");
  assert.equal(R.telefone("011 91234-5678"), "5511912345678");
  assert.equal(R.telefone("55 11 91234-5678"), "5511912345678");
});

test("telefone torto é recusado", () => {
  for (const v of ["", "123", "abc", "1234567890123456789", "+12"]) assert.equal(R.telefone(v), null, v);
});

test("link de conversa escapa o texto", () => {
  const u = new URL(R.linkConversa("5511912345678", "oi & tchau #1\nlinha"));
  assert.equal(u.origin + u.pathname, "https://web.whatsapp.com/send");
  assert.equal(u.searchParams.get("phone"), "5511912345678");
  assert.equal(u.searchParams.get("text"), "oi & tchau #1\nlinha");
  assert.equal(new URL(R.linkConversa(null, "só texto")).searchParams.has("phone"), false);
});

test("variáveis: preenche, não encadeia e deixa a desconhecida", () => {
  const agora = new Date(2026, 10, 22, 9, 5);
  const r = R.preenche("{saudacao}, {primeiro_nome}! {data} {hora} {dia} {nada} {assinatura}",
    { agora, nome: "Ana Souza", assinatura: "{nome}" });
  assert.equal(r, "Bom dia, Ana! 22/11/2026 09:05 domingo {nada} {nome}");
  assert.equal(R.preenche("{saudacao}", { agora: new Date(2026, 1, 1, 3) }), "Boa noite");
  assert.equal(R.preenche("{saudacao}", { agora: new Date(2026, 1, 1, 12) }), "Boa tarde");
  assert.equal(R.preenche("Olá, {nome}", {}), "Olá, {nome}", "sem valor, a lacuna fica à vista");
});

test("atalho da resposta", () => {
  assert.equal(R.atalho("/Horário de Loja!"), "horario-de-loja");
  assert.equal(R.atalho("  "), "");
});

test("CRC do padrão", () => {
  assert.equal(R.crc16("123456789"), "29B1");
});

test("Pix bate com o exemplo do manual do Banco Central", () => {
  assert.equal(
    R.pix({ chave: "123e4567-e12b-12d1-a456-426655440000", nome: "Fulano de Tal", cidade: "BRASILIA" }),
    "00020126580014br.gov.bcb.pix0136123e4567-e12b-12d1-a456-4266554400005204000053039865802BR5913Fulano de Tal6008BRASILIA62070503***63041D3D",
  );
});

test("Pix com valor e acento, e recusa sem dado", () => {
  const p = R.pix({ chave: "loja@exemplo.com", nome: "João da Padaria", cidade: "São Paulo", valor: "1.234,5" });
  assert.match(p, /54071234\.50/);
  assert.match(p, /5915Joao da Padaria6009Sao Paulo/);
  assert.equal(p.slice(-4), R.crc16(p.slice(0, -4)));
  assert.equal(R.pix({ chave: "", nome: "A", cidade: "B" }), null);
  assert.equal(R.pix({ chave: "a@b.co", nome: "A", cidade: "B", valor: "abc" }), null);
});

test("valor em real", () => {
  assert.equal(R.centavos("R$ 1.138,50"), 113850);
  assert.equal(R.centavos("10"), 1000);
  assert.equal(R.centavos("1,999"), null);
  assert.equal(R.centavos("-3"), null);
});

test("todo tema pronto tem contraste de 4,5 nos textos", () => {
  assert.ok(R.TEMAS.length >= 12);
  assert.equal(new Set(R.TEMAS.map((t) => t.id)).size, R.TEMAS.length);
  for (const t of R.TEMAS) {
    const c = R.paleta(t);
    for (const fundo of ["fundo", "elevado", "recebida", "enviada"]) {
      assert.ok(R.contraste(c.texto, c[fundo]) >= 4.5, `${t.id}: texto em ${fundo}`);
      assert.ok(R.contraste(c.apoio, c[fundo]) >= 4.5, `${t.id}: apoio em ${fundo}`);
    }
    assert.ok(R.contraste(c.sobreAcento, c.acento) >= 4.5, `${t.id}: sobre acento`);
  }
});

test("tema montado pela pessoa nunca fica ilegível", () => {
  for (const base of [["#777777", "#787878", "#777777"], ["#FFFFFF", "#FFFF00", "#FF00FF"], ["#000000", "#000011", "#000022"]]) {
    const c = R.paleta({ fundo: base[0], texto: base[1], acento: base[2] });
    for (const fundo of ["fundo", "elevado", "recebida", "enviada"]) assert.ok(R.contraste(c.texto, c[fundo]) >= 4.5, base.join());
  }
});

test("tema importado não injeta CSS", () => {
  assert.equal(R.tema({ fundo: "red;}body{background:url(https://x)", texto: "#000000", acento: "#111111" }), null);
  const css = R.cssTema({ id: "x", nome: "}body{display:none", fundo: "#102030", texto: "#FFFFFF", acento: "#33AA88" });
  assert.ok(!/display:none|url\(|https:/.test(css));
  assert.equal(R.cssTema({ fundo: "#12" }), "");
  assert.equal(R.imagem("data:image/svg+xml,<svg/>"), "");
  assert.equal(R.imagem("https://x/y.png"), "");
  assert.equal(R.imagem('data:image/png;base64,AA");}body{'), "");
});

test("cabeçalho da mensagem", () => {
  assert.deepEqual(R.cabecalho("[10:05, 22/11/2026] Ana: "), { hora: "10:05", data: "22/11/2026", autor: "Ana" });
  assert.deepEqual(R.cabecalho("[10:05 PM, 11/22/2026] A: B: "), { hora: "10:05 PM", data: "11/22/2026", autor: "A: B" });
  assert.deepEqual(R.cabecalho("[10:05] Ana: "), { hora: "10:05", data: "", autor: "Ana" });
  assert.equal(R.cabecalho("torto"), null);
});

const MSG = [
  { data: "22/11/2026", hora: "10:05", autor: "=HYPERLINK(\"x\")", texto: "<script>alert(1)</script>", tipo: "texto" },
  { data: "22/11/2026", hora: "10:06", autor: "Bia", texto: "", tipo: "foto" },
];

test("exportar CSV neutraliza fórmula", () => {
  const csv = R.csv(MSG);
  assert.ok(csv.includes('"\'=HYPERLINK(""x"")"'));
  assert.ok(!/(^|;)"[=+\-@]/m.test(csv.replace(/^﻿/, "")));
});

test("exportar texto marca a mídia", () => {
  assert.match(R.txt(MSG), /\[22\/11\/2026 10:06\] Bia: \(foto\)/);
});

test("exportar HTML escapa tudo e não chama a rede", () => {
  const h = R.html("<img src=x onerror=1>", MSG);
  assert.ok(!h.includes("<script>alert") && !h.includes("<img"));
  assert.match(h, /default-src 'none'/);
  assert.ok(!/https?:\/\//.test(h));
});

test("senha: abre com a certa, recusa a errada e mexida", async () => {
  const caixa = await R.tranca("segredo à vista", "senha-boa");
  assert.ok(!JSON.stringify(caixa).includes("segredo"));
  assert.equal(await R.destranca(caixa, "senha-boa"), "segredo à vista");
  await assert.rejects(R.destranca(caixa, "senha-ruim"));
  const mexida = { ...caixa, dado: (caixa.dado[0] === "A" ? "B" : "A") + caixa.dado.slice(1) };
  await assert.rejects(R.destranca(mexida, "senha-boa"));
  await assert.rejects(R.destranca({ ...caixa, voltas: 1 }, "senha-boa"));
});

test("dados importados entram limpos", () => {
  const d = R.dados({
    respostas: [
      { id: "a", nome: "Horário", texto: "oi", atalho: "/hora" },
      { id: "b", nome: "Repetido", texto: "oi", atalho: "hora" },
      { nome: 1, texto: "x" },
    ],
    fichas: [
      { id: "f", nome: "Ana", etapa: "nao-existe", telefone: "11 91234-5678", etiquetas: ["vip", "vip", 4] },
      { nome: "" },
    ],
    lembretes: [{ id: "l", titulo: "Ligar", quando: 1764000000000 }, { titulo: "sem hora" }],
    lixo: "fora",
    ["__proto__"]: { poluiu: true },
  });
  assert.deepEqual(d.respostas.map((r) => r.atalho), ["hora", ""]);
  assert.equal(d.fichas.length, 1);
  assert.equal(d.fichas[0].etapa, d.etapas[0].id);
  assert.equal(d.fichas[0].telefone, "5511912345678");
  assert.deepEqual(d.fichas[0].etiquetas, ["vip"]);
  assert.equal(d.lembretes.length, 1);
  assert.ok(!("lixo" in d) && !("poluiu" in d) && !("poluiu" in {}));
});

test("backup que não é do Uirapp é recusado", () => {
  assert.equal(R.backup("{}"), null);
  assert.equal(R.backup("não é json"), null);
  assert.ok(R.backup(JSON.stringify({ uirapp: "backup", versao: 1, dados: {}, ajustes: {} })));
});
