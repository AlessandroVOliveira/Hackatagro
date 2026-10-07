/* Camada 2 — Rotas e payback.
 * Para cada resíduo disponível, monta as rotas viáveis (vender, briquete,
 * secagem própria, biodigestor) com investimento, R$/ano e payback, e desenha
 * as barras ordenadas da mais rápida para a mais lenta. */

'use strict';

function rota(nome, residuo, tipo, net, invest, meta) {
  const payback = invest <= 0 ? 0 : (net > 0 ? invest / net : Infinity);
  return {
    nome, residuo, tipo, valor_anual: net, investimento: invest, payback,
    meta: meta.slice(),
    alerta: net <= 0 ? 'não se paga com estes preços' : null,
  };
}

function calcularRotas(inv) {
  const r = [];

  if (inv.palha_t > 0) {
    const netV = inv.palha_t * P.preco_palha - inv.palha_t * P.custo_venda;
    r.push(rota('Vender palha enfardada', 'Palha', 'receita', netV, P.inv_enfardadeira,
      [`${ton(inv.palha_t)} de palha/ano × ${brl(P.preco_palha)}/t`]));

    const prodB = inv.palha_t * P.rend_briquete;
    const netB = prodB * P.preco_briquete - prodB * P.custo_briquete;
    r.push(rota('Briquete de palha', 'Palha', 'receita', netB, P.inv_briquetadeira,
      [`${ton(prodB)} de briquete/ano × ${brl(P.preco_briquete)}/t`]));
  }

  if (inv.casca_t > 0) {
    const netVC = inv.casca_t * P.preco_casca - inv.casca_t * P.custo_venda;
    r.push(rota('Vender a casca', 'Casca', 'receita', netVC, 0,
      [`${ton(inv.casca_t)} de casca/ano × ${brl(P.preco_casca)}/t`, 'casca já fica no engenho']));

    const prodBC = inv.casca_t * P.rend_briquete;
    const netBC = prodBC * P.preco_briquete - prodBC * P.custo_briquete;
    r.push(rota('Briquete de casca', 'Casca', 'receita', netBC, P.inv_briquetadeira,
      [`${ton(prodBC)} de briquete/ano × ${brl(P.preco_briquete)}/t`]));
  }

  if (inv.grao_t > 0 && (inv.casca_t > 0 || inv.palha_t > 0)) {
    const demanda_kwh = inv.grao_t * P.secagem_t_grao;
    const economia = demanda_kwh * P.energia_termica;
    const fonte = inv.casca_t > 0
      ? { nome: 'casca', pci: P.pci_casca, disp: inv.casca_t }
      : { nome: 'palha', pci: P.pci_palha, disp: inv.palha_t };
    const biomassa_usada_t = demanda_kwh / (fonte.pci * 1000);
    const net = economia - biomassa_usada_t * P.custo_secagem;
    const fracUso = fonte.disp > 0 ? Math.min(biomassa_usada_t / fonte.disp, 1) : 0;
    r.push(rota('Queima para secagem própria', cap(fonte.nome), 'economia', net, P.inv_secador,
      [`seca ${ton(inv.grao_t)} de grão/ano`, `usa só ~${pct(fracUso)} da ${fonte.nome}`]));
  }

  if (inv.esterco_t > 0) {
    const economia = inv.biogas_kwh_el * P.tarifa;
    const net = economia * (1 - P.custo_biodig_frac);
    r.push(rota('Biodigestor (biogás → energia)', 'Esterco', 'economia', net, P.inv_biodigestor,
      [`${n0(inv.biogas_m3)} m³ de biogás/ano`, `${n0(inv.biogas_kwh_el)} kWh elétricos/ano`]));
  }

  return r;
}

function renderRotas(rotas) {
  const cont = el('rotas'), eixo = el('rotas-eixo');
  if (!rotas.length) {
    cont.innerHTML = '<p class="ep-nota">Preencha o inventário (área de arroz ou cabeças de gado) para ver as rotas.</p>';
    eixo.innerHTML = '';
    return;
  }
  const ordenadas = rotas.slice().sort((a, b) => a.payback - b.payback);
  const viaveis = rotas.filter((x) => x.valor_anual > 0 && isFinite(x.payback));
  const rec = viaveis.length ? viaveis.reduce((a, b) => (b.payback < a.payback ? b : a)) : null;
  const axisMax = Math.max(1, Math.ceil(Math.max(0.5, ...viaveis.map((x) => x.payback))));

  cont.innerHTML = ordenadas.map((x) => {
    let payTxt, w;
    if (x.valor_anual <= 0) { payTxt = 'não se paga'; w = 100; }
    else if (x.investimento <= 0) { payTxt = 'imediato'; w = 4; }
    else { payTxt = fmtPay.format(x.payback) + ' anos'; w = Math.min(100, Math.max(4, (x.payback / axisMax) * 100)); }

    const meta = [`<span>${brl(x.valor_anual)}/ano de ${x.tipo}</span>`];
    if (x.investimento > 0) meta.push(`<span>investe ${brl(x.investimento)}</span>`);
    x.meta.forEach((m) => meta.push(`<span>${m}</span>`));
    if (x.alerta) meta.push(`<span class="alerta">${x.alerta}</span>`);

    return `<article class="ep-rota ${rec && x === rec ? 'rec' : ''}">
      <header><h4>${x.nome}</h4><span class="pay">${payTxt}</span></header>
      <div class="ep-barra" aria-hidden="true"><i style="width:${w}%"></i></div>
      <div class="meta">${meta.join('')}</div>
    </article>`;
  }).join('');

  eixo.innerHTML = `<span>0</span><span>payback — menor é melhor</span><span>${axisMax} anos</span>`;
}
