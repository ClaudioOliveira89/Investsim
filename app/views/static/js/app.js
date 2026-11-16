/* InvestSim — comportamentos globais da interface (sem dependências externas).
 * Cada recurso é ativado por um atributo data-* no HTML, então o JavaScript
 * apenas melhora a página: sem ele, todos os formulários continuam funcionando
 * (validação final sempre no servidor). */
(function () {
  "use strict";

  /* ------------------------------------------------------------ validação no navegador */
  function mensagemDoCampo(campo) {
    const v = campo.validity;
    const rotulo = campo.closest(".campo")?.querySelector(".campo__rotulo");
    const nome = rotulo ? rotulo.textContent.replace("*", "").trim() : "Este campo";
    if (v.valueMissing) {
      return campo.tagName === "SELECT" || campo.type === "radio"
        ? `Selecione: ${nome.toLowerCase()}.`
        : "Campo obrigatório.";
    }
    if (v.typeMismatch && campo.type === "email") return "E-mail inválido.";
    if (v.tooShort) return `Use ao menos ${campo.minLength} caracteres.`;
    if (v.rangeUnderflow) return `O valor mínimo é ${campo.min}.`;
    if (v.rangeOverflow) return `O valor máximo é ${campo.max}.`;
    if (v.stepMismatch) return "Valor fora do intervalo permitido.";
    if (v.badInput) return "Valor inválido.";
    if (v.customError) return campo.validationMessage;
    return "";
  }

  function validacoesPersonalizadas(campo) {
    campo.setCustomValidity("");
    if (campo.tagName === "SELECT" && campo.required && campo.value === "0") {
      campo.setCustomValidity("Selecione uma opção.");
    }
    if (campo.type === "file" && campo.hasAttribute("data-previa-imagens")) {
      campo.setCustomValidity(problemaNasImagens(campo.files));
    }
  }

  function problemaNasImagens(arquivos) {
    const lista = Array.from(arquivos || []);
    if (lista.length > 3) return "Envie no máximo 3 imagens.";
    for (const arquivo of lista) {
      if (!arquivo.type.startsWith("image/")) return `“${arquivo.name}” não é uma imagem.`;
      if (arquivo.size > 2 * 1024 * 1024) return `“${arquivo.name}” passa de 2 MB.`;
    }
    return "";
  }

  function mostrarErro(campo, mensagem) {
    const caixa = campo.closest(".campo");
    if (!caixa) return;
    let erro = caixa.querySelector(".campo__erro[data-js]");
    const erroServidor = caixa.querySelector(".campo__erro:not([data-js])");
    if (!mensagem) {
      erro?.remove();
      if (!erroServidor) caixa.classList.remove("campo--erro");
      campo.setAttribute("aria-invalid", erroServidor ? "true" : "false");
      return;
    }
    erroServidor?.remove();
    if (!erro) {
      erro = document.createElement("p");
      erro.className = "campo__erro";
      erro.dataset.js = "";
      erro.id = `${campo.id || campo.name}-erro-js`;
      caixa.appendChild(erro);
      const descritos = (campo.getAttribute("aria-describedby") || "").split(" ").filter(Boolean);
      if (!descritos.includes(erro.id)) descritos.unshift(erro.id);
      campo.setAttribute("aria-describedby", descritos.join(" "));
    }
    erro.textContent = mensagem;
    caixa.classList.add("campo--erro");
    campo.setAttribute("aria-invalid", "true");
  }

  function validarCampo(campo) {
    validacoesPersonalizadas(campo);
    const valido = campo.checkValidity();
    mostrarErro(campo, valido ? "" : mensagemDoCampo(campo));
    return valido;
  }

  function ativarValidacao(form) {
    const campos = () =>
      Array.from(form.elements).filter(
        (c) => c.willValidate && !c.disabled && c.type !== "hidden" && c.type !== "submit"
      );

    form.addEventListener("blur", (e) => {
      if (e.target.willValidate && e.target.value) validarCampo(e.target);
    }, true);
    form.addEventListener("input", (e) => {
      if (e.target.closest(".campo--erro")) validarCampo(e.target);
    });
    form.addEventListener("change", (e) => {
      if (e.target.tagName === "SELECT" || e.target.type === "radio") validarCampo(e.target);
    });

    form.addEventListener("submit", (e) => {
      if (form.dataset.enviando) {
        e.preventDefault(); // já está enviando: ignora o segundo clique
        return;
      }
      const invalidos = campos().filter((c) => !validarCampo(c));
      if (invalidos.length) {
        e.preventDefault();
        e.stopImmediatePropagation();
        invalidos[0].focus();
        return;
      }
      travarEnvio(form, e.submitter);
    });
  }

  /* Evita envio duplicado (duplo clique) mostrando que a ação está em andamento */
  function travarEnvio(form, botao) {
    if (form.dataset.enviando) return;
    form.dataset.enviando = "1";
    const alvo = botao || form.querySelector('[type="submit"]');
    if (alvo) {
      if (alvo.name) {
        const espelho = document.createElement("input");
        espelho.type = "hidden";
        espelho.name = alvo.name;
        espelho.value = alvo.value;
        form.appendChild(espelho);
      }
      setTimeout(() => {
        alvo.disabled = true;
        alvo.classList.add("carregando");
      }, 0);
    }
  }

  /* ------------------------------------------------------------ confirmação com modal */
  function ativarConfirmacoes() {
    const modal = document.getElementById("modal-confirmacao");
    document.addEventListener("submit", (e) => {
      const form = e.target;
      if (!form.matches("[data-confirmar]") || form.dataset.confirmado) return;
      e.preventDefault();
      const texto = form.dataset.confirmar;
      if (!modal || typeof modal.showModal !== "function") {
        if (window.confirm(texto)) enviarConfirmado(form);
        return;
      }
      modal.querySelector("[data-modal-texto]").textContent = texto;
      modal.returnValue = "";
      modal.showModal();
      modal.addEventListener("close", function aoFechar() {
        modal.removeEventListener("close", aoFechar);
        if (modal.returnValue === "confirmar") enviarConfirmado(form);
      });
    });
  }

  function enviarConfirmado(form) {
    form.dataset.confirmado = "1";
    travarEnvio(form);
    form.submit();
  }

  /* ------------------------------------------------------------ pequenos comportamentos */
  function ativarAlertas() {
    document.addEventListener("click", (e) => {
      const botao = e.target.closest("[data-fechar-alerta]");
      if (botao) botao.closest("[data-alerta]").remove();
    });
    document.querySelectorAll(".alerta--sucesso[data-alerta], .alerta--info[data-alerta]").forEach((alerta) => {
      setTimeout(() => alerta.remove(), 7000);
    });
  }

  function ativarMenu() {
    const botao = document.querySelector("[data-alternar-menu]");
    const menu = document.getElementById("menu-lateral");
    if (!botao || !menu) return;
    botao.addEventListener("click", () => {
      const aberto = menu.classList.toggle("aberto");
      botao.setAttribute("aria-expanded", String(aberto));
    });
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && menu.classList.contains("aberto")) {
        menu.classList.remove("aberto");
        botao.setAttribute("aria-expanded", "false");
        botao.focus();
      }
    });
  }

  function ativarLinhasClicaveis() {
    document.addEventListener("click", (e) => {
      const linha = e.target.closest("tr[data-href]");
      if (!linha || e.target.closest("a, button, input, form")) return;
      window.location.href = linha.dataset.href;
    });
  }

  function ativarBuscaAtivos() {
    const campo = document.querySelector("[data-busca-ativos]");
    const tabela = document.querySelector("[data-tabela-ativos]");
    const contador = document.querySelector("[data-contagem-ativos]");
    const vazio = document.querySelector("[data-busca-vazia]");
    if (!campo || !tabela || !contador || !vazio) return;

    const linhas = Array.from(tabela.querySelectorAll("tbody tr[data-filtro-ativo]"));
    const normalizar = (valor) => valor.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLocaleLowerCase("pt-BR");
    const filtrar = () => {
      const termo = normalizar(campo.value.trim());
      let visiveis = 0;
      linhas.forEach((linha) => {
        const corresponde = normalizar(linha.dataset.filtroAtivo || "").includes(termo);
        linha.hidden = !corresponde;
        if (corresponde) visiveis += 1;
      });
      contador.textContent = String(visiveis);
      vazio.hidden = visiveis !== 0;
    };

    campo.addEventListener("input", filtrar);
    document.addEventListener("keydown", (evento) => {
      const alvo = evento.target;
      if (evento.key === "/" && !alvo.matches("input, textarea, select, [contenteditable='true']")) {
        evento.preventDefault();
        campo.focus();
      }
      if (evento.key === "Escape" && document.activeElement === campo) {
        campo.value = "";
        filtrar();
        campo.blur();
      }
    });
  }

  function ativarTema() {
    document.querySelectorAll("[data-alternar-tema]").forEach((botao) =>
      botao.addEventListener("click", () => {
        const novo = document.documentElement.dataset.tema === "claro" ? "escuro" : "claro";
        document.documentElement.dataset.tema = novo;
        try { localStorage.setItem("tema", novo); } catch (e) { /* navegação privada */ }
        document.dispatchEvent(new CustomEvent("tema-alterado", { detail: novo }));
      })
    );
  }

  function ativarSimulacao() {
    // Página do ativo: "Simular compra" leva ao formulário da carteira escolhida.
    document.querySelectorAll("form[data-simular]").forEach((form) =>
      form.addEventListener("submit", (e) => {
        e.preventDefault();
        const destino = form.querySelector("[data-carteira-destino]");
        if (destino && destino.value) window.location.href = destino.value;
      })
    );
  }

  function ativarSugestoesCarteira() {
    document.querySelectorAll("form[data-sugestoes-carteira]").forEach((form) => {
      const nome = form.querySelector("#nome");
      const descricao = form.querySelector("#descricao");
      form.querySelectorAll("[data-nome-carteira]").forEach((botao) =>
        botao.addEventListener("click", () => {
          nome.value = botao.dataset.nomeCarteira;
          if (descricao) descricao.value = botao.dataset.descricaoCarteira || "";
          nome.dispatchEvent(new Event("input", { bubbles: true }));
          if (descricao) descricao.dispatchEvent(new Event("input", { bubbles: true }));
          form.querySelectorAll("[data-nome-carteira]").forEach((opcao) =>
            opcao.setAttribute("aria-pressed", String(opcao === botao))
          );
        })
      );
    });
  }

  function ativarDiversos() {
    document.querySelectorAll("[data-enviar-ao-mudar]").forEach((campo) =>
      campo.addEventListener("change", () => campo.form.submit())
    );
    document.querySelectorAll("[data-imprimir]").forEach((b) => b.addEventListener("click", () => window.print()));
    document.querySelectorAll("[data-voltar]").forEach((b) =>
      b.addEventListener("click", () => (history.length > 1 ? history.back() : (location.href = "/")))
    );
    document.querySelectorAll("[data-copiar]").forEach((b) =>
      b.addEventListener("click", async () => {
        try {
          await navigator.clipboard.writeText(b.dataset.copiar);
          b.textContent = "Link copiado!";
        } catch {
          b.textContent = "Copie manualmente";
        }
      })
    );
  }

  function ativarPreviaImagens() {
    document.querySelectorAll("[data-previa-imagens]").forEach((campo) => {
      const destino = document.querySelector("[data-previas]");
      campo.addEventListener("change", () => {
        destino.innerHTML = "";
        Array.from(campo.files || []).forEach((arquivo) => {
          if (!arquivo.type.startsWith("image/")) return;
          const img = document.createElement("img");
          img.alt = `Prévia de ${arquivo.name}`;
          img.src = URL.createObjectURL(arquivo);
          destino.appendChild(img);
        });
        validarCampo(campo);
      });
    });
  }

  /* Ao voltar pelo histórico (cache do navegador), destrava formulários já enviados */
  window.addEventListener("pageshow", (e) => {
    if (!e.persisted) return;
    document.querySelectorAll("form[data-enviando]").forEach((form) => {
      delete form.dataset.enviando;
      form.querySelectorAll("button[disabled].carregando").forEach((b) => {
        b.disabled = false;
        b.classList.remove("carregando");
      });
    });
  });

  /* ------------------------------------------------------------ inicialização */
  document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll("form[data-validar]").forEach(ativarValidacao);
    ativarConfirmacoes();
    ativarAlertas();
    ativarMenu();
    ativarLinhasClicaveis();
    ativarBuscaAtivos();
    ativarDiversos();
    ativarPreviaImagens();
    ativarTema();
    ativarSimulacao();
    ativarSugestoesCarteira();
  });

  // Exposto para os outros scripts e para os testes E2E.
  window.InvestSim = { mostrarErro, validarCampo };
})();
