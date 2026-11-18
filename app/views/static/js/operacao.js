/* Formulário de operação: busca a cotação do dia na API e mostra quantidade e total estimados.
 * É só uma prévia — o servidor recalcula tudo ao salvar. */
(function () {
  "use strict";
  const form = document.querySelector("form[data-operacao]");
  if (!form) return;

  const $ = (seletor) => form.querySelector(seletor);
  const campo = (nome) => form.querySelector(`[name="${nome}"]`);
  const moeda = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });
  const ui = {
    rotulo: $("[data-cotacao-rotulo]"), preco: $("[data-cotacao-preco]"), info: $("[data-cotacao-info]"),
    quantidade: $("[data-resumo-quantidade]"), taxas: $("[data-resumo-taxas]"), total: $("[data-resumo-total]"),
    informado: $("[data-resumo-informado]"), sobra: $("[data-resumo-sobra]"), nota: $("[data-resumo-nota]"),
  };
  const linhasValor = form.querySelectorAll("[data-linha-valor]");
  const mostrarSobra = (visivel) => {
    [ui.informado, ui.sobra, ui.nota, ...linhasValor].forEach((el) => { el.hidden = !visivel; });
  };
  let cotacao = null; // { preco, casas, data, data_pedida, ativo }
  let requisicao = null;

  const num = (nome) => {
    const v = parseFloat(String(campo(nome).value || "").replace(",", "."));
    return Number.isFinite(v) ? v : null;
  };
  const modo = () => (form.querySelector('[name="modo"]:checked') || {}).value || "VALOR";
  const dataBR = (iso) => iso.split("-").reverse().join("/");
  const dataFutura = () => campo("data").value && campo("data").value > form.dataset.hoje;

  function alternarModo() {
    form.querySelectorAll("[data-campo-modo]").forEach((input) => {
      const ativo = input.dataset.campoModo === modo();
      input.closest(".campo").hidden = !ativo;
      input.disabled = !ativo;
    });
    atualizar();
  }

  function precoEfetivo() {
    return num("preco") || (cotacao && cotacao.preco) || null;
  }

  function atualizar() {
    if (dataFutura()) {
      const manual = num("preco");
      ui.rotulo.textContent = "Preço projetado";
      ui.preco.textContent = manual ? moeda.format(manual) : "Informe o preço manual";
      ui.info.textContent = "Não há cotação futura. Informe o preço projetado manualmente.";
    }
    const preco = precoEfetivo();
    const taxas = num("taxas") || 0;
    ui.taxas.textContent = taxas ? moeda.format(taxas) : "—";
    mostrarSobra(false);
    if (!preco) {
      ui.quantidade.textContent = "—";
      ui.total.textContent = "—";
      return;
    }
    const casas = cotacao ? cotacao.casas : 0;
    let quantidade = null;
    if (modo() === "VALOR") {
      const valor = num("valor");
      if (valor) quantidade = Math.floor((valor / preco) * 10 ** casas + 1e-9) / 10 ** casas;
    } else {
      quantidade = num("quantidade");
    }
    if (!quantidade) {
      ui.quantidade.textContent = modo() === "VALOR" && num("valor") ? "valor insuficiente para 1 unidade" : "—";
      ui.total.textContent = "—";
      return;
    }
    const venda = (form.querySelector('[name="tipo"]:checked') || {}).value === "VENDA";
    const bruto = quantidade * preco;
    if (modo() === "VALOR") {
      const informado = num("valor");
      ui.informado.textContent = moeda.format(informado);
      ui.sobra.textContent = moeda.format(Math.max(0, informado - bruto));
      mostrarSobra(true);
    }
    ui.quantidade.textContent = quantidade.toLocaleString("pt-BR", { maximumFractionDigits: 8 });
    ui.total.textContent = moeda.format(venda ? bruto - taxas : bruto + taxas) + (venda ? " a receber" : "");
  }

  async function buscarCotacao() {
    const ativo = campo("ativo_id").value;
    const data = campo("data").value;
    cotacao = null;
    if (dataFutura()) {
      const precoManual = form.querySelector("details");
      if (precoManual) precoManual.open = true;
      atualizar();
      return;
    }
    if (!Number(ativo) || !data) {
      ui.preco.textContent = "—";
      ui.rotulo.textContent = "Cotação";
      ui.info.textContent = "Escolha o ativo e a data.";
      atualizar();
      return;
    }
    const minha = (requisicao = Symbol());
    ui.rotulo.textContent = "Cotação";
    ui.preco.textContent = "…";
    ui.info.textContent = "Buscando a cotação do dia";
    ui.info.classList.add("carregando");
    try {
      const resposta = await fetch(`${form.dataset.urlCotacao}?ativo_id=${ativo}&data=${data}`, { headers: { Accept: "application/json" } });
      if (minha !== requisicao) return;
      const corpo = await resposta.json().catch(() => ({}));
      if (resposta.status === 401) throw new Error("Sua sessão expirou. Recarregue a página e entre de novo.");
      if (!resposta.ok) throw new Error(corpo.erro || "Cotação indisponível. Informe o preço manualmente.");
      cotacao = corpo;
      ui.rotulo.textContent = `${corpo.ativo} · fechamento`;
      ui.preco.textContent = moeda.format(corpo.preco);
      const venda = (form.querySelector('[name="tipo"]:checked') || {}).value === "VENDA";
      const uso = venda ? "Preço de venda = fechamento de" : "Fechamento de";
      ui.info.textContent = corpo.data === corpo.data_pedida
        ? `${uso} ${dataBR(corpo.data)}`
        : `Sem pregão em ${dataBR(corpo.data_pedida)}: usando ${dataBR(corpo.data)}`;
    } catch (erro) {
      ui.preco.textContent = "—";
      ui.info.textContent = erro.message;
    } finally {
      if (minha === requisicao) ui.info.classList.remove("carregando");
      atualizar();
    }
  }

  form.querySelectorAll('[name="modo"]').forEach((r) => r.addEventListener("change", alternarModo));
  form.querySelectorAll('[name="tipo"]').forEach((r) => r.addEventListener("change", buscarCotacao));

  /* Atalhos de data: úteis quando o seletor nativo do navegador é ruim (ex.: Firefox) e para
   * registrar compras retroativas sem digitar a data inteira. */
  const dataInput = campo("data");
  const iso = (d) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
  function definirData(d) {
    dataInput.value = iso(d);
    dataInput.dispatchEvent(new Event("input", { bubbles: true }));
    dataInput.dispatchEvent(new Event("change", { bubbles: true }));
  }
  form.querySelectorAll("[data-meses-atras], [data-dias-atras]").forEach((botao) => {
    botao.addEventListener("click", () => {
      const d = new Date(`${form.dataset.hoje}T12:00:00`);
      if (botao.dataset.mesesAtras) d.setMonth(d.getMonth() - Number(botao.dataset.mesesAtras));
      definirData(d);
    });
  });
  const abrir = form.querySelector("[data-abrir-calendario]");
  if (abrir) {
    abrir.addEventListener("click", () => {
      if (typeof dataInput.showPicker === "function") {
        try { dataInput.showPicker(); return; } catch (e) { /* cai no foco simples */ }
      }
      dataInput.focus();
    });
  }
  ["valor", "quantidade", "preco", "taxas"].forEach((nome) => campo(nome).addEventListener("input", atualizar));
  campo("ativo_id").addEventListener("change", buscarCotacao);
  campo("data").addEventListener("change", buscarCotacao);

  alternarModo();
  buscarCotacao();
})();
