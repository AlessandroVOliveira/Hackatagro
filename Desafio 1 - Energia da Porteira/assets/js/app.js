/* Energia da Porteira — orquestração.
 *
 * Junta as três camadas (inventario.js, rotas.js, consorcio.js): guarda os
 * parâmetros editáveis, monta o bloco de "premissas", aplica os perfis e liga
 * os eventos. Carregado por último, depois de formato.js, dados.js e das três
 * camadas.
 *
 * Nada aqui é previsão: são contas transparentes sobre coeficientes editáveis
 * (dados.js), refeitas a cada mudança de campo. */

'use strict';

/* ------------------------------------------------ parâmetros editáveis (P) */
/* Cada parâmetro mostra faixa/fonte e pode ser editado nas "premissas".
 * O cálculo usa sempre P[id]; começa no valor médio da literatura. */
const PARAMS = [
  // técnicas
  { id: 'casca_fracao',    g: 'tec', label: 'Casca por tonelada de arroz',      ref: COEFICIENTES.arroz.casca_fracao },
  { id: 'palha_grao',      g: 'tec', label: 'Palha por tonelada de grão',        ref: COEFICIENTES.arroz.palha_grao },
  { id: 'palha_recolhivel',g: 'tec', label: 'Fração da palha recolhível',        ref: COEFICIENTES.arroz.palha_recolhivel },
  { id: 'pci_casca',       g: 'tec', label: 'Energia da casca',                  ref: COEFICIENTES.energia.pci_casca },
  { id: 'pci_palha',       g: 'tec', label: 'Energia da palha',                  ref: COEFICIENTES.energia.pci_palha },
  { id: 'secagem_t_grao',  g: 'tec', label: 'Energia para secar o grão',         ref: COEFICIENTES.energia.secagem_por_t_grao },
  { id: 'esterco_kg',      g: 'tec', label: 'Esterco por cabeça/dia',            ref: COEFICIENTES.esterco.kg_cab_dia },
  { id: 'biogas_t',        g: 'tec', label: 'Biogás por t de esterco',           ref: COEFICIENTES.esterco.biogas_por_t },
  { id: 'biogas_kwh_el',   g: 'tec', label: 'Eletricidade por m³ de biogás',     ref: COEFICIENTES.esterco.biogas_kwh_m3_eletrico },
  // económicas
  { id: 'preco_casca',     g: 'eco', label: 'Preço da casca',                    ref: PRECOS.casca },
  { id: 'preco_palha',     g: 'eco', label: 'Preço da palha enfardada',          ref: PRECOS.palha },
  { id: 'preco_briquete',  g: 'eco', label: 'Preço do briquete',                 ref: PRECOS.briquete },
  { id: 'tarifa',          g: 'eco', label: 'Tarifa de energia elétrica',        ref: PRECOS.tarifa_energia },
  { id: 'energia_termica', g: 'eco', label: 'Custo do calor substituído',        ref: PRECOS.energia_termica },
  { id: 'energia_ha',      g: 'eco', label: 'Energia da irrigação',              ref: PRECOS.energia_irrigacao },
  { id: 'custo_venda',     g: 'eco', label: 'Custo de venda (manuseio/frete)',   ref: CUSTOS_OP.venda },
  { id: 'custo_briquete',  g: 'eco', label: 'Custo de briquetagem',              ref: CUSTOS_OP.briquete },
  { id: 'custo_secagem',   g: 'eco', label: 'Custo de operar o secador',         ref: CUSTOS_OP.secagem },
  { id: 'custo_biodig_frac',g:'eco', label: 'Operação do biodigestor',           ref: CUSTOS_OP.biodigestor_frac },
  { id: 'inv_enfardadeira',g: 'eco', label: 'Investimento: enfardadeira',        ref: INVESTIMENTOS.enfardadeira },
  { id: 'inv_briquetadeira',g:'eco', label: 'Investimento: briquetadeira',       ref: INVESTIMENTOS.briquetadeira },
  { id: 'inv_biodigestor', g: 'eco', label: 'Investimento: biodigestor',         ref: INVESTIMENTOS.biodigestor },
  { id: 'inv_secador',     g: 'eco', label: 'Investimento: secador',             ref: INVESTIMENTOS.secador },
  { id: 'rend_briquete',   g: 'eco', label: 'Rendimento do briquete',            ref: RENDIMENTOS.briquete },
];

const P = {};
PARAMS.forEach((p) => { P[p.id] = p.ref.med; });

const estado = { inv: null };

/* ------------------------------------------------------------- premissas */
function passo(med) {
  const a = Math.abs(med);
  if (a >= 10000) return 1000;
  if (a >= 1000) return 50;
  if (a >= 100) return 10;
  if (a >= 10) return 1;
  if (a >= 1) return 0.1;
  return 0.01;
}

function renderPremissas() {
  ['tec', 'eco'].forEach((g) => {
    const alvo = el(g === 'tec' ? 'premissas-tecnicas' : 'premissas-economicas');
    alvo.innerHTML = PARAMS.filter((p) => p.g === g).map((p) => `
      <div class="ep-param">
        <label for="prm_${p.id}">${p.label}</label>
        <input type="number" id="prm_${p.id}" data-pid="${p.id}" value="${p.ref.med}" step="${passo(p.ref.med)}" inputmode="decimal">
        <span class="faixa">faixa ${fmtT.format(p.ref.min)}–${fmtT.format(p.ref.max)} ${p.ref.unid}</span>
        <span class="fonte">${p.ref.fonte}</span>
      </div>`).join('');
  });
}

/* ----------------------------------------------------------------- fluxo */
function recalcTudo() {
  estado.inv = lerInventario();
  renderInventario(estado.inv);
  const rotas = calcularRotas(estado.inv);
  renderRotas(rotas);
  renderFicha(rotas);
  renderTeto(estado.inv);
  atualizarConsorcio();
}

const PRESETS = {
  orizicultor: { area_arroz: 300, produtividade: 8.5, cabecas: 0, manejo: 'extensivo', engenho: 'nao' },
  pecuarista:  { area_arroz: 0,   produtividade: 8.5, cabecas: 600, manejo: 'confinamento', engenho: 'nao' },
  engenho:     { area_arroz: 300, produtividade: 8.5, cabecas: 0, manejo: 'extensivo', engenho: 'sim' },
};

function marcarPerfil(nome) {
  document.querySelectorAll('.ep-perfil').forEach((b) => {
    b.setAttribute('aria-pressed', String(b.dataset.perfil === nome));
  });
}

function aplicarPreset(nome) {
  const d = PRESETS[nome];
  if (!d) return;
  Object.entries(d).forEach(([k, v]) => { el(k).value = v; });
  marcarPerfil(nome);
  recalcTudo();
}

function iniciar() {
  renderPremissas();
  initMapa();

  el('form-inventario').addEventListener('input', () => { marcarPerfil(null); recalcTudo(); });

  document.querySelectorAll('.ep-perfil').forEach((b) => {
    b.addEventListener('click', () => aplicarPreset(b.dataset.perfil));
  });

  const onParam = (e) => {
    const t = e.target;
    if (!t.dataset || !t.dataset.pid) return;
    const v = parseFloat(t.value);
    if (!isNaN(v)) P[t.dataset.pid] = v;
    recalcTudo();
  };
  el('premissas-tecnicas').addEventListener('input', onParam);
  el('premissas-economicas').addEventListener('input', onParam);

  el('raio').addEventListener('input', atualizarConsorcio);

  aplicarPreset('orizicultor');
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', iniciar);
} else {
  iniciar();
}
