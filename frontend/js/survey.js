/* Espectro 24 — survey.js
   Micro-pesquisa do A/B: "Qual formato te ajudou mais a decidir?"
   - voto salvo em localStorage por filme (chave espectro24:voto:<slug>);
   - sem backend, sem analytics, sem cookies de terceiros;
   - após votar: agradecimento + botão que COPIA o feedback em texto simples
     (filme, escolha, comentário, data) para a pessoa mandar por mensagem.
   Exposto como window.mountSurvey(container, film). */
(function () {
  "use strict";

  var KEY_PREFIX = "espectro24:voto:";

  var DIC = {
    pt: {
      "survey.pergunta": "Qual formato te ajudou mais a decidir?",
      "survey.opcao_resumo": "O resumo em texto",
      "survey.opcao_detalhe": "Os temas detalhados",
      "survey.comentario_rotulo": "Comentário opcional",
      "survey.comentario_placeholder": "Comentário (opcional)",
      "survey.enviar": "Enviar",
      "survey.obrigado": "Obrigado pelo voto! Você escolheu {escolha}.",
      "survey.comentario_registrado": "Comentário registrado.",
      "survey.copiar": "Copiar meu feedback",
      "survey.copiado": "Copiado!",
      "survey.copiar_manual": "Selecione e copie manualmente",
      "survey.copia_titulo": "Espectro 24 — feedback A/B",
      "survey.copia_filme": "Filme",
      "survey.copia_formato": "Formato que ajudou mais",
      "survey.copia_comentario": "Comentário",
      "survey.copia_nenhum": "(nenhum)",
      "survey.copia_data": "Data",
    },
    en: {
      "survey.pergunta": "Which format helped you decide the most?",
      "survey.opcao_resumo": "The text summary",
      "survey.opcao_detalhe": "The detailed themes",
      "survey.comentario_rotulo": "Optional comment",
      "survey.comentario_placeholder": "Comment (optional)",
      "survey.enviar": "Submit",
      "survey.obrigado": "Thanks for voting! You chose {escolha}.",
      "survey.comentario_registrado": "Comment recorded.",
      "survey.copiar": "Copy my feedback",
      "survey.copiado": "Copied!",
      "survey.copiar_manual": "Select and copy it manually",
      "survey.copia_titulo": "Espectro 24 — A/B feedback",
      "survey.copia_filme": "Film",
      "survey.copia_formato": "Format that helped most",
      "survey.copia_comentario": "Comment",
      "survey.copia_nenhum": "(none)",
      "survey.copia_data": "Date",
    },
  };
  if (globalThis.I18N) globalThis.I18N.registrar(DIC);
  function T(chave, vars) {
    if (globalThis.I18N) return globalThis.I18N.t(chave, vars);
    var v = DIC.pt[chave];
    return String(v == null ? chave : v).replace(/\{(\w+)\}/g, function (m, k) {
      return vars && vars[k] != null ? String(vars[k]) : m;
    });
  }

  // Rótulo de uma escolha no idioma atual; null para valor desconhecido.
  function rotuloDa(valor) {
    return (valor === "resumo" || valor === "detalhe") ? T("survey.opcao_" + valor) : null;
  }

  window.mountSurvey = function (container, film) {
    var slug = film.slug;
    var titulo = (film.ficha && film.ficha.titulo) || slug;
    var storeKey = KEY_PREFIX + slug;

    var section = document.createElement("section");
    section.className = "survey";
    section.setAttribute("aria-labelledby", "surveyQ");

    var form = document.createElement("form");
    form.innerHTML =
      '<p class="survey__q serif" id="surveyQ">' + esc(T("survey.pergunta")) + "</p>" +
      '<div class="survey__options" role="radiogroup" aria-labelledby="surveyQ">' +
        opt(slug, "resumo") + opt(slug, "detalhe") +
      "</div>" +
      '<label class="visually-hidden" for="surveyComment">' + esc(T("survey.comentario_rotulo")) + "</label>" +
      '<textarea id="surveyComment" placeholder="' + esc(T("survey.comentario_placeholder")) + '"></textarea>' +
      '<button class="btn" type="submit" disabled>' + esc(T("survey.enviar")) + "</button>";

    var thanks = document.createElement("div");
    thanks.className = "survey__thanks";
    thanks.setAttribute("role", "status");
    thanks.setAttribute("aria-live", "polite");

    section.appendChild(form);
    section.appendChild(thanks);
    container.appendChild(section);

    var radios = form.querySelectorAll('input[type="radio"]');
    var comment = form.querySelector("#surveyComment");
    var submit = form.querySelector('button[type="submit"]');

    radios.forEach(function (r) {
      r.addEventListener("change", function () { submit.disabled = false; });
    });

    // já votou antes? mostra o estado de agradecimento direto.
    var saved = readVote(storeKey);
    if (saved) {
      form.style.display = "none";
      showThanks(saved);
    }

    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var chosen = form.querySelector('input[type="radio"]:checked');
      if (!chosen) return;
      var vote = {
        slug: slug,
        titulo: titulo,
        escolha: chosen.value,
        escolha_label: rotuloDa(chosen.value),
        comentario: comment.value.trim(),
        data: new Date().toISOString(),
      };
      writeVote(storeKey, vote);
      form.style.display = "none";
      showThanks(vote);
    });

    function showThanks(vote) {
      thanks.classList.add("is-visible");
      thanks.innerHTML =
        "<p>" + T("survey.obrigado", {
          escolha: '<span class="choice-echo">' + esc(rotuloDa(vote.escolha) || vote.escolha) + "</span>",
        }) +
        (vote.comentario ? " " + esc(T("survey.comentario_registrado")) : "") +
        "</p>" +
        '<div class="survey__actions">' +
        '<button class="btn btn--ghost" type="button" id="copyFeedback">' + esc(T("survey.copiar")) + "</button>" +
        '<span class="copy-status" id="copyStatus" role="status" aria-live="polite"></span>' +
        "</div>";

      var copyBtn = thanks.querySelector("#copyFeedback");
      var status = thanks.querySelector("#copyStatus");
      copyBtn.addEventListener("click", function () {
        var text = feedbackText(vote);
        copyToClipboard(text, function (ok) {
          status.textContent = ok ? T("survey.copiado") : T("survey.copiar_manual");
          status.classList.add("is-visible");
          if (ok) setTimeout(function () { status.classList.remove("is-visible"); }, 2500);
        });
      });
    }

    function opt(slug, val) {
      var id = "opt-" + slug + "-" + val;
      return (
        '<label class="survey__opt" for="' + id + '">' +
        '<input type="radio" id="' + id + '" name="fmt-' + esc(slug) + '" value="' + val + '">' +
        "<span>" + esc(rotuloDa(val)) + "</span></label>"
      );
    }
  };

  function feedbackText(v) {
    var d = new Date(v.data);
    var locale = globalThis.I18N && globalThis.I18N.idioma === "en" ? "en-US" : "pt-BR";
    var dataLegivel = isNaN(d) ? v.data : d.toLocaleString(locale);
    return (
      T("survey.copia_titulo") + "\n" +
      T("survey.copia_filme") + ": " + v.titulo + "\n" +
      T("survey.copia_formato") + ": " + (rotuloDa(v.escolha) || v.escolha_label || v.escolha) + "\n" +
      T("survey.copia_comentario") + ": " + (v.comentario || T("survey.copia_nenhum")) + "\n" +
      T("survey.copia_data") + ": " + dataLegivel
    );
  }

  function readVote(key) {
    try { return JSON.parse(localStorage.getItem(key) || "null"); }
    catch (e) { return null; }
  }
  function writeVote(key, vote) {
    try { localStorage.setItem(key, JSON.stringify(vote)); }
    catch (e) { /* localStorage indisponível: segue sem persistir */ }
  }

  function copyToClipboard(text, cb) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(
        function () { cb(true); },
        function () { cb(fallbackCopy(text)); }
      );
    } else {
      cb(fallbackCopy(text));
    }
  }
  function fallbackCopy(text) {
    try {
      var ta = document.createElement("textarea");
      ta.value = text;
      ta.style.position = "fixed";
      ta.style.opacity = "0";
      document.body.appendChild(ta);
      ta.select();
      var ok = document.execCommand("copy");
      document.body.removeChild(ta);
      return ok;
    } catch (e) { return false; }
  }

  function esc(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }
})();
