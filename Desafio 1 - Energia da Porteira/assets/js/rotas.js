/* Camada 2 — Rotas e payback.
 * Para cada resíduo disponível, monta as rotas viáveis (vender, briquete,
 * secagem própria, biodigestor) com investimento, R$/ano, atores (quem opera,
 * quem compra) e payback. Desenha as barras ordenadas da mais rápida para a
 * mais lenta, com a faixa pessimista–provável–otimista.
 *
 * calcularRotas(inv, p) aceita um conjunto de parâmetros (p); por padrão usa P.
 * Passar um conjunto no extremo das faixas (dados.js) gera os cenários. */

'use strict';

function rota(nome, residuo, tipo, net, invest, meta, atores) {
  const payback = invest <= 0 ? 0 : (net > 0 ? invest / net : Infinity);
  return {
    nome, residuo, tipo, valor_anual: net, investimento: invest, payback,
    meta: meta.slice(), atores,
    alerta: net <= 0 ? 'não se paga com estes preços' : null,
  };
}

function calcularRotas(inv, p = P) {
  const r = [];

  if (inv.palha_t > 0) {
    const netV = inv.palha_t * p.preco_palha - inv.palha_t * p.custo_venda;
    r.push(rota('Vender palha enfardada', 'Palha', 'receita', netV, p.inv_enfardadeira,
      [`${ton(inv.palha_t)} de palha/ano × ${brl(p.preco_palha)}/t`],
      { opera: 'produtor (enfarda e carrega)', compra: 'indústria, cama de aviário, forrageiras' }));

    const prodB = inv.palha_t * p.rend_briquete;
    const netB = prodB * p.preco_briquete - prodB * p.custo_briquete;
    r.push(rota('Briquete de palha', 'Palha', 'receita', netB, p.inv_briquetadeira,
      [`${ton(prodB)} de briquete/ano × ${brl(p.preco_briquete)}/t`],
      { opera: 'produtor ou cooperativa', compra: 'indústria, cerâmicas, termelétricas' }));
  }

  if (inv.casca_t > 0) {
    const netVC = inv.casca_t * p.preco_casca - inv.casca_t * p.custo_venda;
    r.push(rota('Vender a casca', 'Casca', 'receita', netVC, 0,
      [`${ton(inv.casca_t)} de casca/ano × ${brl(p.preco_casca)}/t`, 'casca já fica no engenho'],
      { opera: 'engenho', compra: 'cerâmicas e termelétricas a casca' }));

    const prodBC = inv.casca_t * p.rend_briquete;
    const netBC = prodBC * p.preco_briquete - prodBC * p.custo_briquete;
    r.push(rota('Briquete de casca', 'Casca', 'receita', netBC, p.inv_briquetadeira,
      [`${ton(prodBC)} de briquete/ano × ${brl(p.preco_briquete)}/t`],
      { opera: 'engenho ou cooperativa', compra: 'indústria e termelétricas' }));
  }

  if (inv.grao_t > 0 && (inv.casca_t > 0 || inv.palha_t > 0)) {
    const demanda_kwh = inv.grao_t * p.secagem_t_grao;
    const economia = demanda_kwh * p.energia_termica;
    const fonte = inv.casca_t > 0
      ? { nome: 'casca', pci: p.pci_casca, disp: inv.casca_t }
      : { nome: 'palha', pci: p.pci_palha, disp: inv.palha_t };
    const biomassa_usada_t = demanda_kwh / (fonte.pci * 1000);
    const net = economia - biomassa_usada_t * p.custo_secagem;
    const fracUso = fonte.disp > 0 ? Math.min(biomassa_usada_t / fonte.disp, 1) : 0;
    r.push(rota('Queima para secagem própria', cap(fonte.nome), 'economia', net, p.inv_secador,
      [`seca ${ton(inv.grao_t)} de grão/ano`, `usa só ~${pct(fracUso)} da ${fonte.nome}`],
      { opera: 'o próprio produtor/engenho', compra: 'uso interno (substitui lenha/GLP no secador)' }));
  }

  if (inv.esterco_t > 0) {
    const economia = inv.biogas_kwh_el * p.tarifa;
    const net = economia * (1 - p.custo_biodig_frac);
    r.push(rota('Biodigestor (biogás → energia)', 'Esterco', 'economia', net, p.inv_biodigestor,
      [`${n0(inv.biogas_m3)} m³ de biogás/ano`, `${n0(inv.biogas_kwh_el)} kWh elétricos/ano`],
      { opera: 'produtor/pecuarista', compra: 'uso interno (abate a conta de luz da propriedade)' }));
  }

  return r;
}

/* Texto curto de um payback: imediato / não se paga / "X,X anos". */
function textoPayback(pb) {
  if (pb === 0) return 'imediato';
  if (!isFinite(pb)) return 'não se paga';
  return fmtPay.format(pb) + ' anos';
}

function renderRotas(rotas) {
  const cont = el('rotas');
  if (!rotas.length) {
    cont.innerHTML = '<p class="ep-nota">Preencha o inventário (área de arroz ou cabeças de gado) para ver as rotas.</p>';
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

    // faixa pessimista–provável–otimista (feature 3)
    let faixa = '';
    if (x.payback_otim !== undefined && x.payback_pess !== undefined) {
      faixa = `<div class="ep-faixa-pb" aria-hidden="true">` +
        `<span>otimista <b>${textoPayback(x.payback_otim)}</b></span>` +
        `<span>provável <b>${textoPayback(x.payback)}</b></span>` +
        `<span>pessimista <b>${textoPayback(x.payback_pess)}</b></span></div>`;
    }

    const atores = x.atores
      ? `<p class="ep-atores"><b>Opera:</b> ${x.atores.opera} · <b>Compra:</b> ${x.atores.compra}</p>`
      : '';

    return `<article class="ep-rota ${rec && x === rec ? 'rec' : ''}">
      <header><h4>${x.nome}</h4><span class="pay">${payTxt}</span></header>
      <div class="ep-barra" aria-hidden="true"><i style="width:${w}%"></i></div>
      <div class="meta">${meta.join('')}</div>
      ${faixa}
      ${atores}
    </article>`;
  }).join('');
}
