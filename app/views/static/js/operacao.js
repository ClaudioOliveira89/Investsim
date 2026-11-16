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
  };
  let cotacao = null; // { preco, casas, data, data_pedida, ativo }
  let requisicao = null;

  const num = (nome) => {
    const v = parseFloat(String(campo(nome).value || "").replace(",", "."));
    return Number.isFinite(v) ? v : null;
  };
  const modo = () => (form.querySelector('[name="modo"]:checked') || {}).value || "VALOR";
  const dataBR = (iso) => iso.split("-").reverse().join("/");

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
    const preco = precoEfetivo();
    const taxas = num("taxas") || 0;
    ui.taxas.textContent = taxas ? moeda.format(taxas) : "—";
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
    ui.quantidade.textContent = quantidade.toLocaleString("pt-BR", { maximumFractionDigits: 8 });
    ui.total.textContent = moeda.format(venda ? bruto - taxas : bruto + taxas) + (venda ? " a receber" : "");
  }

  async function buscarCotacao() {
    const ativo = campo("ativo_id").value;
    const data = campo("data").value;
    cotacao = null;
    if (!Number(ativo) || !data) {
      ui.preco.textContent = "—";
      ui.info.textContent = "Escolha o ativo e a data.";
      atualizar();
      return;
    }
    const minha = (requisicao = Symbol());
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
      ui.info.textContent = corpo.data === corpo.data_pedida
        ? `Fechamento de ${dataBR(corpo.data)}`
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
  form.querySelectorAll('[name="tipo"]').forEach((r) => r.addEventListener("change", atualizar));
  ["valor", "quantidade", "preco", "taxas"].forEach((nome) => campo(nome).addEventListener("input", atualizar));
  campo("ativo_id").addEventListener("change", buscarCotacao);
  campo("data").addEventListener("change", buscarCotacao);

  alternarModo();
  buscarCotacao();
})();
