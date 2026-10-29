/*
 * Painel do tempo — lê dados/tempo.json e preenche o painel.
 *
 * O arquivo é atualizado fora do navegador (manualmente ou por uma rotina
 * que consulte o INMET). Se faltar, estiver incompleto ou antigo, o painel
 * mostra "Dados temporariamente indisponíveis" e nunca inventa valores.
 */
(function () {
  "use strict";

  var ARQUIVO = "dados/tempo.json";
  var VALIDADE_HORAS = 6; // depois disso os dados são considerados desatualizados

  var NIVEIS = [
    { id: "emergencia", nome: "Emergência", ate: 11.99 },
    { id: "alerta", nome: "Alerta", ate: 20.99 },
    { id: "atencao", nome: "Atenção", ate: 30 },
    { id: "acompanhar", nome: "Acompanhar", ate: Infinity }
  ];

  var TIPOS_UMIDADE = {
    observada: "Umidade relativa observada",
    prevista: "Umidade relativa prevista",
    minima_prevista: "Menor umidade prevista para hoje"
  };

  function $(id) { return document.getElementById(id); }

  function nivelDaUmidade(valor) {
    for (var i = 0; i < NIVEIS.length; i++) {
      if (valor <= NIVEIS[i].ate) return NIVEIS[i];
    }
  }

  function formatarDataHora(data) {
    return data.toLocaleString("pt-BR", {
      timeZone: "America/Sao_Paulo",
      day: "2-digit", month: "2-digit", year: "numeric",
      hour: "2-digit", minute: "2-digit"
    }) + " (horário de Brasília)";
  }

  function formatarDia(iso) {
    var d = new Date(iso + "T12:00:00-03:00");
    return d.toLocaleDateString("pt-BR", {
      timeZone: "America/Sao_Paulo", weekday: "short", day: "2-digit", month: "2-digit"
    });
  }

  function dadosValidos(d) {
    if (!d || !d.atualizado_em || !d.umidade || typeof d.umidade.valor !== "number") return false;
    var atualizado = new Date(d.atualizado_em);
    if (isNaN(atualizado)) return false;
    var idadeHoras = (Date.now() - atualizado.getTime()) / 36e5;
    return idadeHoras >= -1 && idadeHoras <= VALIDADE_HORAS;
  }

  function mostrar(d) {
    var nivel = nivelDaUmidade(d.umidade.valor);

    $("painel-umidade").textContent = Math.round(d.umidade.valor);
    $("painel-umidade-tipo").textContent =
      TIPOS_UMIDADE[d.umidade.tipo] || "Umidade relativa do ar";
    $("painel-nivel").textContent = "Faixa do quadro: " + nivel.nome;
    $("painel-estacao").textContent = d.estacao || "Não informada";
    $("painel-atualizado").textContent = formatarDataHora(new Date(d.atualizado_em));

    var lista = $("painel-dias");
    lista.textContent = "";
    (d.previsao || []).slice(0, 4).forEach(function (dia) {
      var li = document.createElement("li");
      var temp = [];
      if (typeof dia.temp_min === "number") temp.push("mín. " + Math.round(dia.temp_min) + "°C");
      if (typeof dia.temp_max === "number") temp.push("máx. " + Math.round(dia.temp_max) + "°C");
      li.innerHTML = '<span class="dia"></span><span class="cond"></span><span class="temp"></span>';
      li.querySelector(".dia").textContent = formatarDia(dia.data);
      li.querySelector(".cond").textContent = dia.condicao || "";
      li.querySelector(".temp").textContent = temp.join(" · ");
      lista.appendChild(li);
    });
    lista.hidden = !lista.children.length;

    var atual = document.querySelector('.nivel[data-nivel="' + nivel.id + '"]');
    if (atual) atual.classList.add("atual");

    $("painel-indisponivel").hidden = true;
    $("painel-dados").hidden = false;
  }

  if (!window.fetch) return;

  fetch(ARQUIVO, { cache: "no-cache" })
    .then(function (r) { return r.ok ? r.json() : null; })
    .then(function (d) { if (dadosValidos(d)) mostrar(d); })
    .catch(function () { /* mantém a mensagem de indisponibilidade */ });
})();
