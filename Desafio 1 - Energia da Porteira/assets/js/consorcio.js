/* Camada 3 — Consórcio de vizinhos.
 * Mapa Leaflet com as propriedades de Alegrete (dados.js). Soma o resíduo
 * dentro de um raio ao redor da propriedade do usuário e avisa quando o grupo
 * atinge a escala de uma rota compartilhada (Lei 14.300/2022). */

'use strict';

let mapa = null, marcadores = [], circuloRaio = null, marcadorUser = null;

function distKm(lat1, lng1, lat2, lng2) {
  const R = 6371, rad = (x) => (x * Math.PI) / 180;
  const dLat = rad(lat2 - lat1), dLng = rad(lng2 - lng1);
  const s = Math.sin(dLat / 2) ** 2 + Math.cos(rad(lat1)) * Math.cos(rad(lat2)) * Math.sin(dLng / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(s));
}

function initMapa() {
  if (typeof L === 'undefined') {
    el('mapa').innerHTML = '<p style="padding:1rem;color:var(--tinta-suave)">Mapa indisponível (sem internet). ' +
      'A soma do consórcio abaixo continua funcionando normalmente.</p>';
    return;
  }
  mapa = L.map('mapa', { scrollWheelZoom: false }).setView([ALEGRETE.lat, ALEGRETE.lng], 10);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 18, attribution: '© OpenStreetMap',
  }).addTo(mapa);

  circuloRaio = L.circle([ALEGRETE.lat, ALEGRETE.lng], {
    radius: ESCALA.raio_padrao_km * 1000, color: '#1E4D3A', weight: 1.5,
    fillColor: '#1E4D3A', fillOpacity: 0.06,
  }).addTo(mapa);

  PROPRIEDADES.forEach((p) => {
    const m = L.circleMarker([p.lat, p.lng], {
      radius: 7, weight: 1.5, color: '#58625B', fillColor: '#CFE0D3', fillOpacity: 0.9,
    }).addTo(mapa);
    m.bindPopup(`<b>${p.nome}</b><br>${p.tipo}<br>${n0(p.residuo_t_ano)} t de resíduo/ano`);
    marcadores.push({ p, m });
  });

  marcadorUser = L.circleMarker([ALEGRETE.lat, ALEGRETE.lng], {
    radius: 10, weight: 2, color: '#8a6418', fillColor: '#C8952B', fillOpacity: 0.95,
  }).addTo(mapa);
  marcadorUser.bindPopup('<b>Sua propriedade</b>');
}

function atualizarConsorcio() {
  const raio = num('raio');
  el('raio-val').textContent = raio + ' km';

  const inv = estado.inv;
  const userResiduo = inv ? inv.palha_t + inv.casca_t + inv.esterco_t : 0;

  let soma = userResiduo, dentro = 0;
  marcadores.forEach(({ p, m }) => {
    const d = distKm(ALEGRETE.lat, ALEGRETE.lng, p.lat, p.lng);
    const estaDentro = d <= raio;
    if (estaDentro) { soma += p.residuo_t_ano; dentro++; }
    if (m) m.setStyle(estaDentro
      ? { color: '#1E4D3A', fillColor: '#1E4D3A', fillOpacity: 0.85 }
      : { color: '#58625B', fillColor: '#CFE0D3', fillOpacity: 0.5 });
  });

  if (circuloRaio) circuloRaio.setRadius(raio * 1000);
  if (marcadorUser) marcadorUser.setPopupContent(`<b>Sua propriedade</b><br>${n0(userResiduo)} t de resíduo/ano`);

  renderEscala(soma, dentro);
}

function renderEscala(soma, dentro) {
  const meta = ESCALA.usina_t_ano;
  const frac = Math.min(soma / meta, 1);
  const atingiu = soma >= meta;
  const aviso = atingiu
    ? `<p class="aviso ok">✓ O grupo soma ${n0(soma)} t/ano e atinge a escala de uma usina ou briquetagem compartilhada (${n0(meta)} t/ano). Dá para acionar a rota coletiva.</p>`
    : `<p class="aviso">Faltam <b>${n0(meta - soma)} t/ano</b> para a escala de uma rota compartilhada (${n0(meta)} t/ano). Aumente o raio ou chame mais vizinhos.</p>`;

  el('escala').innerHTML = `
    <div class="linha"><span>${dentro} vizinho(s) no raio + sua propriedade</span><b>${n0(soma)} t/ano</b></div>
    <div class="trilho"><i class="${atingiu ? 'cheio' : ''}" style="width:${frac * 100}%"></i></div>
    <div class="linha" style="font-size:0.78rem;color:var(--tinta-suave)"><span>0</span><span>meta: ${n0(meta)} t/ano</span></div>
    ${aviso}
    <p class="ep-nota" style="margin-top:0.4rem">Uma propriedade sozinha já enche um caminhão para venda conjunta (${ESCALA.caminhao_t} t). O consórcio existe para chegar à escala da usina.</p>`;
}
