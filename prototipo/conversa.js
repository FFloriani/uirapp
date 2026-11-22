// Como o Uirapp aparece dentro de uma conversa. Protótipo, sem rede.
"use strict";

(() => {
  const raiz = document.documentElement;
  const [inicio, busca = ""] = (raiz.dataset.inicio || location.hash.slice(1) || "aberta").split("?");
  const q = new URLSearchParams(busca);
  const botao = document.querySelector("#flutuante");
  const cobertura = document.querySelector("#cobertura");
  const tela = document.querySelector("#mensageiro");

  function silencio(ligado) {
    tela.classList.toggle("silencio", ligado);
    botao.setAttribute("aria-pressed", String(ligado));
    botao.dataset.humor = ligado ? "silencio" : "acordado";
    const acao = ligado ? "Mostrar conversas" : "Esconder conversas";
    botao.setAttribute("aria-label", acao);
    botao.title = `${acao} (Alt+S)`;
  }

  function cobre(ligada) {
    cobertura.hidden = !ligada;
    botao.hidden = ligada;
    tela.inert = ligada;
    if (ligada && !raiz.dataset.inicio) document.querySelector("#descobrir").focus();
  }

  botao.addEventListener("click", () => silencio(!tela.classList.contains("silencio")));
  document.querySelector("#descobrir").addEventListener("click", () => {
    cobre(false);
    silencio(false);
    botao.focus();
  });
  document.addEventListener("keydown", (e) => {
    if (e.altKey && e.code === "KeyS" && cobertura.hidden) {
      e.preventDefault();
      silencio(!tela.classList.contains("silencio"));
    }
  });

  for (const chave of ["tema", "plumagem"]) if (q.get(chave)) raiz.dataset[chave] = q.get(chave);
  silencio(inicio === "silencio" || inicio === "cobertura");
  cobre(inicio === "cobertura");
})();
