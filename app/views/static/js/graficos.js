/* Gráficos com Chart.js (biblioteca local em /static/vendor, licença MIT).
 *  - #grafico-carteira : rentabilidade acumulada (ou patrimônio) da carteira × CDI
 *  - #grafico-alocacao : rosca com a alocação por classe
 *  - #grafico-ativo    : histórico de preços do ativo, com períodos (consulta /api)
 * As cores vêm das variáveis CSS, então os gráficos acompanham o tema claro/escuro. */
(function () {
  "use strict";
  if (typeof window.Chart === "undefined") return;

  const css = (nome) => getComputedStyle(document.documentElement).getPropertyValue(nome).trim();
  const moeda = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });
  const numero = (casas) => new Intl.NumberFormat("pt-BR", { minimumFractionDigits: casas, maximumFractionDigits: casas });
  const impressao = !!document.querySelector("[data-relatorio-impressao]");
  const graficos = [];

  function cores() {
    return impressao
      ? { texto: "#334155", grade: "#e2e8f0", carteira: "#0d9488", cdi: "#b7791f", fundo: "#ffffff" }
      : { texto: css("--texto-suave"), grade: css("--borda"), carteira: css("--primaria"), cdi: css("--cdi"), fundo: css("--superficie") };
  }

  function dataBR(iso) {
    const [a, m, d] = iso.split("-");
    return `${d}/${m}/${a}`;
  }

  function opcoesBase(formatarY) {
    const c = cores();
    return {
      responsive: true,
      maintainAspectRatio: false,
      animation: impressao ? false : { duration: 350 },
      interaction: { mode: "index", intersect: false },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: c.fundo, titleColor: c.texto, bodyColor: c.texto, borderColor: c.grade, borderWidth: 1,
          padding: 10, callbacks: {
            title: (itens) => (itens.length ? dataBR(itens[0].label) : ""),
            label: (ctx) => ` ${ctx.dataset.label}: ${formatarY(ctx.parsed.y)}`,
          },
        },
      },
      scales: {
        x: {
          ticks: { color: c.texto, maxTicksLimit: 7, maxRotation: 0, callback(valor) { return dataBR(this.getLabelForValue(valor)).slice(3); } },
          grid: { display: false }, border: { color: c.grade },
        },
        y: { ticks: { color: c.texto, callback: (v) => formatarY(v) }, grid: { color: c.grade }, border: { display: false } },
      },
    };
  }

  /* ------------------------------------------------------------ carteira × CDI */
  function graficoCarteira() {
    const canvas = document.getElementById("grafico-carteira");
    const fonte = document.getElementById("dados-grafico");
    if (!canvas || !fonte) return;
    const dados = JSON.parse(fonte.textContent);
    const pct = (v) => `${numero(1).format(v)}%`;
    const c = cores();

    const series = {
      rentabilidade: {
        formatar: pct,
        conjuntos: [
          { label: "Carteira", data: dados.carteira, borderColor: c.carteira, backgroundColor: c.carteira + "22", fill: "origin" },
          { label: "CDI", data: dados.cdi, borderColor: c.cdi, borderDash: [6, 5] },
        ],
      },
      patrimonio: {
        formatar: (v) => moeda.format(v),
        conjuntos: [
          { label: "Patrimônio", data: dados.patrimonio, borderColor: c.carteira, backgroundColor: c.carteira + "22", fill: "origin" },
          { label: "Se estivesse no CDI", data: dados.espelho, borderColor: c.cdi, borderDash: [6, 5] },
          { label: "Investido líquido", data: dados.investido, borderColor: c.texto, borderWidth: 1.2, stepped: true },
        ],
      },
    };

    const criar = (modo) => {
      const s = series[modo];
      return new Chart(canvas, {
        type: "line",
        data: {
          labels: dados.datas,
          datasets: s.conjuntos.map((d) => ({ pointRadius: 0, borderWidth: 2, tension: 0.15, fill: false, ...d })),
        },
        options: opcoesBase(s.formatar),
      });
    };

    let grafico = criar("rentabilidade");
    graficos.push(() => grafico);
    const legenda = document.querySelector("[data-legenda-grafico]");
    document.querySelectorAll("[data-grafico-modo]").forEach((botao) => {
      botao.addEventListener("click", () => {
        const modo = botao.dataset.graficoModo;
        document.querySelectorAll("[data-grafico-modo]").forEach((b) => b.setAttribute("aria-pressed", String(b === botao)));
        grafico.destroy();
        grafico = criar(modo);
        if (legenda) {
          legenda.innerHTML = "";
          series[modo].conjuntos.forEach((d) => {
            const item = document.createElement("span");
            const cor = document.createElement("i");
            cor.style.background = d.borderColor;
            item.append(cor, d.label);
            legenda.append(item);
          });
        }
      });
    });
  }

  /* ------------------------------------------------------------ alocação */
  function graficoAlocacao() {
    const canvas = document.getElementById("grafico-alocacao");
    const fonte = document.getElementById("dados-alocacao");
    if (!canvas || !fonte) return;
    const alocacao = JSON.parse(fonte.textContent);
    const nomes = { ACAO: "Ações e BDRs", FII: "FIIs", ETF: "ETFs", CRIPTO: "Cripto", CAIXA: "Proventos em caixa" };
    const paleta = { ACAO: "#60a5fa", FII: "#a78bfa", ETF: css("--primaria"), CRIPTO: css("--cdi"), CAIXA: "#94a3b8" };
    const chaves = Object.keys(alocacao).sort((a, b) => alocacao[b] - alocacao[a]);
    const total = chaves.reduce((s, k) => s + alocacao[k], 0);
    const grafico = new Chart(canvas, {
      type: "doughnut",
      data: {
        labels: chaves.map((k) => nomes[k] || k),
        datasets: [{ data: chaves.map((k) => alocacao[k]), backgroundColor: chaves.map((k) => paleta[k] || "#64748b"), borderColor: css("--superficie"), borderWidth: 2 }],
      },
      options: {
        responsive: true, maintainAspectRatio: false, cutout: "62%",
        plugins: {
          legend: { position: "right", labels: { color: css("--texto-suave"), boxWidth: 10, boxHeight: 10 } },
          tooltip: { callbacks: { label: (ctx) => ` ${ctx.label}: ${moeda.format(ctx.parsed)} (${numero(1).format((ctx.parsed / total) * 100)}%)` } },
        },
      },
    });
    graficos.push(() => grafico);
  }

  /* ------------------------------------------------------------ histórico do ativo */
  function graficoAtivo() {
    const canvas = document.getElementById("grafico-ativo");
    if (!canvas) return;
    const status = document.querySelector("[data-grafico-status]");
    let grafico = null;

    const ROTULOS = { "1m": "1 mês", "6m": "6 meses", "1a": "12 meses", "2a": "2 anos", "5a": "5 anos" };
    function atualizarCards(est, periodo) {
      if (!est) return;
      const pct = (v) => (v == null ? "—" : `${v >= 0 ? "+" : ""}${numero(2).format(v)}%`);
      const valores = { variacao: pct(est.variacao), minimo: moeda.format(est.minimo), maximo: moeda.format(est.maximo), proventos: moeda.format(est.proventos) };
      Object.entries(valores).forEach(([chave, texto]) => {
        const el = document.querySelector(`[data-kpi="${chave}"]`);
        if (el) el.textContent = texto;
      });
      const variacaoEl = document.querySelector('[data-kpi="variacao"]');
      if (variacaoEl) {
        variacaoEl.classList.remove("positivo", "negativo");
        if (est.variacao != null) variacaoEl.classList.add(est.variacao >= 0 ? "positivo" : "negativo");
      }
      document.querySelectorAll("[data-kpi-rotulo]").forEach((el) => { el.textContent = `${el.dataset.kpiRotulo} ${ROTULOS[periodo]}`; });
      const nota = document.querySelector('[data-kpi-nota="proventos"]');
      if (nota) nota.textContent = est.dividend_yield != null ? `Dividend yield: ${numero(2).format(est.dividend_yield)}%` : "por cota";
    }

    async function carregar(periodo) {
      status.textContent = "Carregando…";
      try {
        const resposta = await fetch(`${canvas.dataset.url}?periodo=${periodo}`, { headers: { Accept: "application/json" } });
        const corpo = await resposta.json();
        if (resposta.status === 401) throw new Error("Sua sessão expirou. Recarregue a página.");
        if (!resposta.ok) throw new Error(corpo.erro || "Não foi possível carregar o histórico.");
        const pontos = corpo.pontos || [];
        if (!pontos.length) throw new Error("Sem cotações no período.");
        const subiu = pontos[pontos.length - 1].valor >= pontos[0].valor;
        const cor = subiu ? css("--positivo") : css("--negativo");
        if (grafico) grafico.destroy();
        grafico = new Chart(canvas, {
          type: "line",
          data: {
            labels: pontos.map((p) => p.data),
            datasets: [{ label: "Fechamento", data: pontos.map((p) => p.valor), borderColor: cor, backgroundColor: cor + "1f", fill: "origin", pointRadius: 0, borderWidth: 2, tension: 0.1 }],
          },
          options: opcoesBase((v) => moeda.format(v)),
        });
        atualizarCards(corpo.estatisticas, periodo);
        const variacao = (pontos[pontos.length - 1].valor / pontos[0].valor - 1) * 100;
        status.textContent = `Variação no período: ${variacao >= 0 ? "+" : ""}${numero(2).format(variacao)}%` +
          (corpo.avisos && corpo.avisos.length ? ` · ${corpo.avisos.join(" ")}` : "");
      } catch (erro) {
        status.textContent = erro.message;
      }
    }

    document.querySelectorAll("[data-periodo]").forEach((botao) => {
      botao.addEventListener("click", () => {
        document.querySelectorAll("[data-periodo]").forEach((b) => b.setAttribute("aria-pressed", String(b === botao)));
        carregar(botao.dataset.periodo);
      });
    });
    carregar("1a");
  }

  graficoCarteira();
  graficoAlocacao();
  graficoAtivo();

  // Ao trocar o tema, redesenha com as novas cores (recarregar é o jeito mais simples e confiável).
  document.addEventListener("tema-alterado", () => {
    if (graficos.length) window.location.reload();
  });
})();
