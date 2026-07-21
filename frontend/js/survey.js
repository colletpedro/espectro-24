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
  var OPCOES = {
    resumo: "O resumo em texto",
    detalhe: "Os temas detalhados",
  };

  window.mountSurvey = function (container, film) {
    var slug = film.slug;
    var titulo = (film.ficha && film.ficha.titulo) || slug;
    var storeKey = KEY_PREFIX + slug;

    var section = document.createElement("section");
    section.className = "survey";
    section.setAttribute("aria-labelledby", "surveyQ");

    var form = document.createElement("form");
    form.innerHTML =
      '<p class="survey__q serif" id="surveyQ">Qual formato te ajudou mais a decidir?</p>' +
      '<div class="survey__options" role="radiogroup" aria-labelledby="surveyQ">' +
        opt(slug, "resumo") + opt(slug, "detalhe") +
      "</div>" +
      '<label class="visually-hidden" for="surveyComment">Comentário opcional</label>' +
      '<textarea id="surveyComment" placeholder="Comentário (opcional)"></textarea>' +
      '<button class="btn" type="submit" disabled>Enviar</button>';

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
        escolha_label: OPCOES[chosen.value],
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
        "<p>Obrigado pelo voto! Você escolheu " +
        '<span class="choice-echo">' + esc(OPCOES[vote.escolha] || vote.escolha) + "</span>." +
        (vote.comentario ? " Comentário registrado." : "") +
        "</p>" +
        '<div class="survey__actions">' +
        '<button class="btn btn--ghost" type="button" id="copyFeedback">Copiar meu feedback</button>' +
        '<span class="copy-status" id="copyStatus" role="status" aria-live="polite"></span>' +
        "</div>";

      var copyBtn = thanks.querySelector("#copyFeedback");
      var status = thanks.querySelector("#copyStatus");
      copyBtn.addEventListener("click", function () {
        var text = feedbackText(vote);
        copyToClipboard(text, function (ok) {
          status.textContent = ok ? "Copiado!" : "Selecione e copie manualmente";
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
        "<span>" + esc(OPCOES[val]) + "</span></label>"
      );
    }
  };

  function feedbackText(v) {
    var d = new Date(v.data);
    var dataLegivel = isNaN(d) ? v.data : d.toLocaleString("pt-BR");
    return (
      "Espectro 24 — feedback A/B\n" +
      "Filme: " + v.titulo + "\n" +
      "Formato que ajudou mais: " + (v.escolha_label || v.escolha) + "\n" +
      "Comentário: " + (v.comentario || "(nenhum)") + "\n" +
      "Data: " + dataLegivel
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
