// Mapa da vizinhança em SVG, desenhado a partir das coordenadas em km.
// Não depende de imagem de satélite nem de internet: funciona sem sinal.

const S = 60; // px por km
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (ch) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[ch]));

export const COR = {
  alta: '#B4432C', media: '#D99A1E', baixa: '#C4B169', mancha: '#B98A2A',
  javali: '#5C3A2E', limpo: '#6E8F4A', estrada: '#B9A486', arroio: '#86B3C2',
};

export function corNota(n) {
  return n >= 65 ? COR.alta : n >= 45 ? COR.media : COR.baixa;
}

export function criarProjecao(base) {
  const v = base.vizinhanca;
  const H = v.altura_km;
  return {
    w: v.largura_km * S, h: H * S,
    X: (x) => +(x * S).toFixed(1),
    Y: (y) => +((H - y) * S).toFixed(1),
    pts: (lista) => lista.map(([x, y]) => `${(x * S).toFixed(1)},${((H - y) * S).toFixed(1)}`).join(' '),
    km: (px, py) => [px / S, H - py / S],
    deLatLon: (lat, lon) => [(lon - v.lon0) * v.km_lon, (lat - v.lat0) * v.km_lat],
    paraLatLon: (x, y) => [v.lat0 + y / v.km_lat, v.lon0 + x / v.km_lon],
    dentro: (x, y) => x >= 0 && y >= 0 && x <= v.largura_km && y <= v.altura_km,
  };
}

function centro(pts) {
  return pts.reduce(([x, y], [a, b]) => [x + a / pts.length, y + b / pts.length], [0, 0]);
}

const PRECISA_ROTULO = { 1: [2.2, 9.7], 2: [6.2, 10.4], 3: [10, 10.2], 4: [14.1, 10.2], 5: [2, 1.6], 6: [5.9, 0.5], 7: [9.6, 1.6], 8: [13.8, 1.6] };

function idadeDias(iso, hoje) {
  return Math.max(0, Math.round((new Date(hoje) - new Date(iso.slice(0, 10))) / 86400000));
}

// opcoes: { camada: 'tudo'|'annoni'|'javali', perfil, selecionado, quentes, marcador, clicavel, rotulos }
export function desenhar(base, dados, opcoes = {}) {
  const P = criarProjecao(base);
  const camada = opcoes.camada || 'tudo';
  const verAnnoni = camada !== 'javali', verJavali = camada !== 'annoni';
  const F = base.feicoes;
  const out = [];

  out.push(`<defs>
    <pattern id="limpo" width="10" height="10" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
      <rect width="10" height="10" fill="#D7E4C2"/><line x1="0" y1="0" x2="0" y2="10" stroke="#B9CF9A" stroke-width="4"/></pattern>
    <pattern id="quadricula" width="8" height="8" patternUnits="userSpaceOnUse" patternTransform="rotate(-45)">
      <rect width="8" height="8" fill="#F6E6BF"/><line x1="0" y1="0" x2="0" y2="8" stroke="#E7C778" stroke-width="3"/></pattern>
  </defs>`);
  out.push(`<rect width="${P.w}" height="${P.h}" fill="#E9EBDD"/>`);

  for (const p of base.propriedades) {
    const minha = opcoes.perfil != null && p.id === opcoes.perfil;
    out.push(`<polygon class="prop${minha ? ' minha' : ''}" points="${P.pts(p.km)}"><title>${esc(p.nome)}</title></polygon>`);
  }
  for (const f of F.filter((f) => f.tipo === 'campo_limpo')) {
    out.push(`<polygon class="limpo" points="${P.pts(f.km)}"><title>${esc(f.nome)}: campo nativo ainda limpo</title></polygon>`);
  }
  for (const f of F.filter((f) => f.tipo === 'arroio')) {
    out.push(`<polyline class="arroio" points="${P.pts(f.km)}"/>`);
  }
  for (const f of F.filter((f) => f.tipo === 'estrada')) {
    out.push(`<polyline class="estrada-borda" points="${P.pts(f.km)}"/><polyline class="estrada" points="${P.pts(f.km)}"><title>${esc(f.nome)}</title></polyline>`);
  }
  for (const f of F.filter((f) => f.tipo === 'corredor')) {
    out.push(`<polyline class="corredor" points="${P.pts(f.km)}"><title>${esc(f.nome)}</title></polyline>`);
  }
  for (const f of F.filter((f) => f.tipo === 'vetor')) {
    const [x, y] = [P.X(f.km[0]), P.Y(f.km[1])];
    out.push(f.subtipo === 'porteira'
      ? `<rect class="vetor" x="${x - 5}" y="${y - 5}" width="10" height="10"><title>${esc(f.nome)}</title></rect>`
      : `<circle class="vetor" cx="${x}" cy="${y}" r="7"><title>${esc(f.nome)}</title></circle>`);
  }

  // rótulos de fundo
  if (opcoes.rotulos !== false) {
    for (const p of base.propriedades) {
      const [cx, cy] = PRECISA_ROTULO[p.id] || centro(p.km);
      const minha = opcoes.perfil != null && p.id === opcoes.perfil;
      out.push(`<text class="rot-prop${minha ? ' minha' : ''}" x="${P.X(cx)}" y="${P.Y(cy)}" text-anchor="middle">${esc(p.nome)}</text>`);
    }
    const arroio = F.find((f) => f.tipo === 'arroio');
    if (arroio) out.push(`<text class="rot-arroio" x="${P.X(11.2)}" y="${P.Y(9.05)}" text-anchor="middle">${esc(arroio.nome)}</text>`);
    const geral = F.find((f) => f.nome === 'Estrada Geral');
    if (geral) out.push(`<text class="rot-estrada" x="${P.X(14.6)}" y="${P.Y(5.3)}" text-anchor="middle">${esc(geral.nome)}</text>`);
  }

  // annoni dos vizinhos, por quadrícula (sem o ponto exato)
  if (verAnnoni) {
    for (const c of dados?.celulas || []) {
      const [i, j] = c.celula;
      out.push(`<g class="celula"><rect x="${P.X(i)}" y="${P.Y(j + 1)}" width="${S}" height="${S}" fill="url(#quadricula)" stroke="#D99A1E" stroke-dasharray="5 4" stroke-width="1.5"><title>${c.n} foco(s) de annoni de vizinhos nesta quadrícula de 1 km</title></rect>
        <text x="${P.X(i + 0.5)}" y="${P.Y(j + 0.5) + 7}" text-anchor="middle" class="rot-celula">${c.n}</text></g>`);
    }
  }

  const exatos = dados?.exatos || [];
  // javali primeiro (fica por baixo do annoni)
  if (verJavali) {
    for (const o of exatos.filter((o) => o.tipo === 'javali')) {
      const [x, y] = [P.X(o.km[0]), P.Y(o.km[1])];
      const idade = idadeDias(o.observado_em, base.hoje);
      const op = idade <= 14 ? 1 : idade <= 30 ? 0.75 : 0.45;
      const sel = opcoes.selecionado === o.id ? ' sel' : '';
      const dano = o.subtipo === 'ataque_criacao' || o.subtipo === 'lavoura';
      const r = dano ? 10 : 6.5;
      out.push(`<g class="oc javali${sel}" data-oc="${o.id}" tabindex="${opcoes.clicavel ? 0 : -1}" role="button" opacity="${op}">
        <path d="M${x} ${y - r} L${x + r} ${y} L${x} ${y + r} L${x - r} ${y} Z" fill="${dano ? COR.alta : COR.javali}" stroke="#fff" stroke-width="2"/>
        ${dano ? `<path d="M${x - 4} ${y - 4} L${x + 4} ${y + 4} M${x + 4} ${y - 4} L${x - 4} ${y + 4}" stroke="#fff" stroke-width="2.2"/>` : ''}
        <title>Javali</title></g>`);
    }
  }
  if (verAnnoni) {
    const ann = exatos.filter((o) => o.tipo === 'annoni').sort((a, b) => (b.area_m2 || 0) - (a.area_m2 || 0));
    for (const o of ann) {
      const [x, y] = [P.X(o.km[0]), P.Y(o.km[1])];
      const sel = opcoes.selecionado === o.id ? ' sel' : '';
      const comum = `class="oc annoni${sel}" data-oc="${o.id}" tabindex="${opcoes.clicavel ? 0 : -1}" role="button"`;
      if (o.status === 'descartada') {
        out.push(`<g ${comum}><circle cx="${x}" cy="${y}" r="6" fill="#fff" stroke="#9AA090" stroke-width="2" stroke-dasharray="3 2"/></g>`);
      } else if (o.situacao === 'eliminado') {
        out.push(`<g ${comum}><circle cx="${x}" cy="${y}" r="8" fill="#fff" stroke="${COR.limpo}" stroke-width="2.5"/>
          <path d="M${x - 4} ${y} l3 3 l5 -6" fill="none" stroke="${COR.limpo}" stroke-width="2.5" stroke-linecap="round"/><title>Foco eliminado</title></g>`);
      } else if (o.classe === 'mancha estabelecida') {
        const r = Math.min(34, 10 + Math.sqrt(o.area_m2 || 0) / 4);
        out.push(`<g ${comum}><circle cx="${x}" cy="${y}" r="${r.toFixed(1)}" fill="${COR.mancha}" fill-opacity="0.42" stroke="${COR.mancha}" stroke-width="2"/><title>Mancha de annoni</title></g>`);
      } else {
        const r = o.area_m2 > 10 ? 10 : 8.5;
        const cor = corNota(o.nota || 0);
        out.push(`<g ${comum}><circle cx="${x}" cy="${y}" r="${r}" fill="${o.status === 'suspeita' ? '#fff' : cor}" stroke="${cor}" stroke-width="${o.status === 'suspeita' ? 3.5 : 2}" ${o.status === 'suspeita' ? 'stroke-dasharray="4 2.5"' : ''}/>
          ${o.status === 'suspeita' ? `<circle cx="${x}" cy="${y}" r="3" fill="${cor}"/>` : ''}<title>Foco de annoni</title></g>`);
      }
    }
  }

  for (const q of opcoes.quentes || []) {
    const [i, j] = q.celula;
    out.push(`<rect class="quente" x="${P.X(i)}" y="${P.Y(j + 1)}" width="${S}" height="${S}"><title>Quadrícula com mais sinais de javali</title></rect>`);
  }

  for (const d of base.dispositivos) {
    if (!verJavali) break;
    const [x, y] = [P.X(d.km[0]), P.Y(d.km[1])];
    if (d.tipo === 'armadilha') {
      const fechada = d.estado === 'fechada';
      out.push(`<g class="disp"><rect x="${x - 13}" y="${y - 13}" width="26" height="26" rx="5" fill="${fechada ? COR.alta : '#2F3A28'}" stroke="#fff" stroke-width="2.5"/>
        <path d="M${x - 7} ${y + 7} V${y - 6} M${x} ${y + 7} V${y - 6} M${x + 7} ${y + 7} V${y - 6} M${x - 9} ${y - 6} H${x + 9}" stroke="#fff" stroke-width="2"/>
        <title>${esc(d.nome)} (${fechada ? 'fechada' : 'aberta'})</title></g>`);
    } else {
      out.push(`<g class="disp"><circle cx="${x}" cy="${y}" r="11" fill="#2F3A28" stroke="#fff" stroke-width="2.5"/>
        <rect x="${x - 5.5}" y="${y - 4}" width="8" height="8" rx="1.5" fill="#fff"/><path d="M${x + 2.5} ${y} l4 -3 v6 z" fill="#fff"/>
        <title>${esc(d.nome)}</title></g>`);
    }
  }

  if (opcoes.marcador) {
    const [x, y] = [P.X(opcoes.marcador[0]), P.Y(opcoes.marcador[1])];
    out.push(`<g class="marcador"><path d="M${x} ${y} c-3 -10 -14 -16 -14 -27 a14 14 0 0 1 28 0 c0 11 -11 17 -14 27z" fill="#1E231B" stroke="#fff" stroke-width="2.5"/><circle cx="${x}" cy="${y - 27}" r="5" fill="#fff"/></g>`);
  }

  return `<svg class="mapa${opcoes.clicavel === 'marcar' ? ' marcar' : ''}" viewBox="0 0 ${P.w} ${P.h}" role="img" aria-label="Mapa da vizinhança">${out.join('')}</svg>`;
}

// Converte um toque no SVG para km.
export function pontoDoToque(svg, ev, base) {
  const pt = svg.createSVGPoint();
  pt.x = ev.clientX; pt.y = ev.clientY;
  const p = pt.matrixTransform(svg.getScreenCTM().inverse());
  return criarProjecao(base).km(p.x, p.y);
}
