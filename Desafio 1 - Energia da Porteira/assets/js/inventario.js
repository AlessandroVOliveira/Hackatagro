/* Camada 1 — Inventário.
 * Das 5 perguntas às toneladas/ano de palha, casca e esterco e ao potencial
 * energético. Lê os coeficientes editáveis em P (parametros.js) e os dados
 * técnicos em COEFICIENTES (dados.js). */

'use strict';

function lerInventario() {
  const area = num('area_arroz');
  const prod = num('produtividade');
  const cabecas = num('cabecas');
  const manejo = el('manejo').value;
  const temEngenho = el('engenho').value === 'sim';

  const grao_t = area * prod;
  const casca_t = temEngenho ? grao_t * P.casca_fracao : 0;
  const palha_t = grao_t * P.palha_grao * P.palha_recolhivel;
  const fracManejo = COEFICIENTES.esterco.recolhivel[manejo].med;
  const esterco_t = (cabecas * P.esterco_kg * 365 * fracManejo) / 1000; // kg -> t

  const energia_casca_kwh = casca_t * 1000 * P.pci_casca;
  const energia_palha_kwh = palha_t * 1000 * P.pci_palha;
  const biogas_m3 = esterco_t * P.biogas_t;
  const biogas_kwh_el = biogas_m3 * P.biogas_kwh_el;

  return {
    area, prod, cabecas, manejo, temEngenho,
    grao_t, casca_t, palha_t, esterco_t,
    energia_casca_kwh, energia_palha_kwh, biogas_m3, biogas_kwh_el,
  };
}

function renderInventario(inv) {
  const cards = [
    { r: 'Palha recolhível',    v: inv.palha_t,   u: 't/ano' },
    { r: 'Casca',               v: inv.casca_t,   u: 't/ano' },
    { r: 'Esterco recolhível',  v: inv.esterco_t, u: 't/ano' },
    { r: 'Energia da biomassa', v: (inv.energia_palha_kwh + inv.energia_casca_kwh) / 1000, u: 'MWh/ano' },
    { r: 'Biogás',              v: inv.biogas_m3, u: 'm³/ano' },
  ];
  el('volumes').innerHTML = cards.map((c) => {
    const vazio = c.v <= 0.0001;
    const val = c.u === 'm³/ano' ? n0(c.v) : fmtT.format(c.v);
    return `<div class="${vazio ? 'vazio' : ''}"><small>${c.r}</small>` +
      `<strong>${vazio ? '—' : val}</strong> <span class="u">${vazio ? '' : c.u}</span></div>`;
  }).join('');
}

function renderTeto(inv) {
  const gasto = inv.area * P.energia_ha;
  const box = el('teto');
  if (gasto <= 0) { box.style.display = 'none'; return; }
  box.style.display = '';
  const v10 = 0.1 * gasto;
  box.innerHTML = `Sua conta de energia da irrigação é de cerca de <b>${brl(gasto)}/ano</b> ` +
    `(${n0(inv.area)} ha × ${brl(P.energia_ha)}/ha). Cada 10% de redução vale <b>${brl(v10)}/ano</b> — ` +
    `é o teto que um investimento em energia própria (biodigestor, geração compartilhada) precisa caber para se pagar.`;
}

function renderFicha(rotas) {
  const viaveis = rotas.filter((x) => x.valor_anual > 0);
  const valEl = el('ficha-valor'), frEl = el('ficha-frase');
  if (!viaveis.length) {
    valEl.textContent = 'R$ 0';
    frEl.innerHTML = rotas.length
      ? 'Com estes preços nenhuma rota se paga sozinha. Veja o <a href="#consorcio">consórcio</a> para somar com os vizinhos.'
      : 'Preencha o inventário (área de arroz ou cabeças de gado) para ver quanto seus resíduos valem.';
    return;
  }
  const melhor = viaveis.reduce((a, b) => (b.valor_anual > a.valor_anual ? b : a));
  const rec = viaveis.reduce((a, b) => (b.payback < a.payback ? b : a));
  valEl.innerHTML = brl(melhor.valor_anual) + `<small>na rota ${melhor.nome.toLowerCase()}</small>`;
  const pb = rec.investimento <= 0
    ? 'de forma imediata, sem investimento'
    : `com payback de ${fmtPay.format(rec.payback)} anos`;
  frEl.innerHTML = `A que se paga mais rápido é <b>${rec.nome.toLowerCase()}</b>, ${pb}. ` +
    `Compare o payback de cada rota abaixo.`;
}
