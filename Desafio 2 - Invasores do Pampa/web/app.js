// Ronda do Pampa: vigilância de vizinhança contra o capim-annoni e o javali.
// Registros ficam numa fila no celular (IndexedDB) e sobem quando houver sinal.

import { desenhar, pontoDoToque, criarProjecao, corNota, COR } from '/web/mapa.js';

const $ = (s, el = document) => el.querySelector(s);
const tela = $('#tela');
const estado = {
  base: null, perfil: lembrado('perfil') ?? '6', camada: 'tudo', selecionado: null,
  mapa: null, resumo: null, prioridades: null, javali: null, avisos: [], movimentos: [], antigo: false,
  reg: { tipo: null, subtipo: null, km: null, onde: null, foto: null, animais: '', prejuizo: '', obs: '' },
  resultados: [],
};

// ------------------------------------------------------------------ formatos
const nf = (v, c = 0) => Number(v).toLocaleString('pt-BR', { minimumFractionDigits: c, maximumFractionDigits: c });
const brl = (v, c = 0) => (v == null ? '–' : 'R$ ' + nf(v, c));
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (ch) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[ch]));
const lerNumero = (s) => {
  s = String(s ?? '').trim().replace(/[R$\s]/g, '');
  if (!s) return null;
  if (s.includes(',')) s = s.replace(/\./g, '').replace(',', '.');
  else if (/^\d{1,3}(\.\d{3})+$/.test(s)) s = s.replace(/\./g, '');
  const n = Number(s);
  return Number.isFinite(n) ? n : null;
};
const novoId = () => (crypto.randomUUID ? crypto.randomUUID()
  : 'id-' + Date.now().toString(36) + '-' + Math.random().toString(36).slice(2, 10));
const hojeIso = () => estado.base?.hoje || new Date().toISOString().slice(0, 10);
const dataBr = (iso) => iso ? iso.slice(0, 10).split('-').reverse().slice(0, 2).join('/') : '';
function haQuanto(iso) {
  const d = Math.round((new Date(hojeIso()) - new Date(iso.slice(0, 10))) / 86400000);
  return d <= 0 ? 'hoje' : d === 1 ? 'ontem' : `há ${d} dias`;
}
function periodo(iso) {
  const h = Number(iso.slice(11, 13));
  return h < 6 ? 'de madrugada' : h < 12 ? 'de manhã' : h < 18 ? 'de tarde' : 'à noite';
}

const JAVALI = {
  rastro: 'Rastro', fucada: 'Campo fuçado', avistamento: 'Vi o bando', lavoura: 'Lavoura estragada', ataque_criacao: 'Atacou criação',
};
const ANNONI = {
  touceira: ['Uma touceira', 'Planta sozinha', 1],
  foco: ['Foco pequeno', 'Algumas touceiras, até uns 10 m²', 10],
  mancha: ['Mancha', 'Mais de 100 m², já tomou o lugar', 500],
};

// ------------------------------------------------------------------ guardar no celular
function lembrar(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch { /* sem espaço */ } }
function lembrado(k) { try { return JSON.parse(localStorage.getItem(k)); } catch { return null; } }

const BANCO = 'ronda-do-pampa';
let conexao;
function banco() {
  conexao ??= new Promise((ok, erro) => {
    const r = indexedDB.open(BANCO, 1);
    r.onupgradeneeded = () => r.result.createObjectStore('fila', { keyPath: 'id' });
    r.onsuccess = () => ok(r.result);
    r.onerror = () => erro(r.error);
  });
  return conexao;
}
async function fila(modo, fn) {
  const db = await banco();
  return new Promise((ok, erro) => {
    const tx = db.transaction('fila', modo);
    const req = fn(tx.objectStore('fila'));
    tx.oncomplete = () => ok(req?.result);
    tx.onerror = () => erro(tx.error);
  });
}
const filaTodos = () => fila('readonly', (s) => s.getAll());
const filaPor = (item) => fila('readwrite', (s) => s.put(item));
const filaTirar = (id) => fila('readwrite', (s) => s.delete(id));

// ------------------------------------------------------------------ servidor
async function api(caminho, opcoes) {
  const r = await fetch(caminho, opcoes);
  if (!r.ok) {
    let detalhe;
    try { detalhe = (await r.json()).detail; } catch { /* vazio */ }
    const e = new Error(typeof detalhe === 'string' ? detalhe : `O servidor respondeu ${r.status}.`);
    e.status = r.status;
    throw e;
  }
  return r.json();
}
const postJson = (url, corpo) => api(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(corpo) });

const perfilId = () => (estado.perfil === 'sindicato' ? null : Number(estado.perfil));
const comPerfil = (url) => `${url}${url.includes('?') ? '&' : '?'}perfil=${encodeURIComponent(estado.perfil)}`;

async function buscar(chave, url, porPerfil = true) {
  const k = porPerfil ? `${chave}:${estado.perfil}` : chave;
  try {
    const d = await api(porPerfil ? comPerfil(url) : url);
    lembrar(k, d);
    estado.antigo = false;
    return d;
  } catch {
    estado.antigo = true;
    return lembrado(k);
  }
}

async function carregarTudo() {
  estado.base = await buscar('base', '/api/base', false);
  [estado.mapa, estado.resumo] = await Promise.all([buscar('mapa', '/api/mapa'), buscar('resumo', '/api/resumo')]);
}

const nomeProp = (id) => estado.base?.propriedades.find((p) => p.id === id)?.nome || '';

// ------------------------------------------------------------------ avisos rápidos e sinal
function avisar(texto) {
  document.querySelector('.toast')?.remove();
  const t = Object.assign(document.createElement('div'), { className: 'toast', role: 'status', textContent: texto });
  document.body.append(t);
  setTimeout(() => t.remove(), 4200);
}

async function atualizarSinal() {
  const itens = await filaTodos();
  const n = itens.filter((i) => i.estado === 'aguardando').length;
  const el = $('#sinal');
  el.className = 'sinal' + (!navigator.onLine ? ' off' : n ? ' fila' : '');
  el.textContent = !navigator.onLine ? (n ? `Sem sinal: ${n} na fila` : 'Sem sinal') : (n ? `Enviando ${n}…` : 'Com sinal');
  $('#nav-fila').innerHTML = n ? `<span class="contador">${n}</span>` : '';
  const av = estado.resumo?.avisos_nao_lidos || 0;
  $('#nav-avisos').innerHTML = av ? `<span class="contador">${av}</span>` : '';
}

let processando = false;
async function processarFila() {
  if (processando || !navigator.onLine) return atualizarSinal();
  processando = true;
  let enviou = false;
  try {
    for (const it of await filaTodos()) {
      if (it.estado !== 'aguardando') continue;
      const fd = new FormData();
      fd.append('dados', JSON.stringify(it.dados));
      if (it.foto) fd.append('foto', it.foto, `${it.id}.jpg`);
      try {
        const r = await api('/api/ocorrencias', { method: 'POST', body: fd });
        await filaTirar(it.id);
        estado.resultados.unshift({ ...r, quando: new Date().toISOString() });
        avisar(r.avisados ? `Registrado. ${r.avisados} ${r.avisados === 1 ? 'vizinho avisado' : 'vizinhos avisados'}.` : 'Registrado.');
        enviou = true;
      } catch (e) {
        if (e.status && e.status < 500) { it.estado = 'erro'; it.erro = e.message; await filaPor(it); enviou = true; }
      }
    }
  } finally {
    processando = false;
  }
  if (enviou) {
    await carregarTudo();
    if (['registrar', 'mapa'].includes(rota().nome)) render(false);
  }
  await atualizarSinal();
}

async function comprimir(arquivo) {
  try {
    const img = await createImageBitmap(arquivo);
    const k = Math.min(1, 1400 / Math.max(img.width, img.height));
    const c = Object.assign(document.createElement('canvas'), { width: Math.round(img.width * k), height: Math.round(img.height * k) });
    c.getContext('2d').drawImage(img, 0, 0, c.width, c.height);
    return await new Promise((ok) => c.toBlob(ok, 'image/jpeg', 0.72));
  } catch {
    return arquivo;
  }
}

// ------------------------------------------------------------------ peças comuns
function kpi(rotulo, valor, sub, cls = '') {
  return `<div class="kpi"><small>${rotulo}</small><strong class="num ${cls}">${valor}</strong><small>${sub}</small></div>`;
}

function avisoAntigo() {
  return estado.antigo ? '<p class="aviso-suave">Sem sinal: mostrando o que foi guardado da última vez.</p>' : '';
}

function bannerEpoca() {
  if (!estado.base?.epoca_sementes) return '';
  return `<div class="banner"><b>Época de sementes (outubro a maio).</b> Cada planta de annoni solta até ${nf(estado.base.parametros.sementes_planta_ano)} sementes por ano, e elas duram mais de 20 anos no solo. Elimine os focos pequenos antes do espigamento.</div>`;
}

function textoOcorrencia(o) {
  if (o.tipo === 'annoni') {
    const cls = o.classe || (o.situacao === 'eliminado' ? 'foco eliminado' : 'foco de annoni');
    return `${cls[0].toUpperCase()}${cls.slice(1)}${o.area_m2 ? `, ${nf(o.area_m2)} m²` : ''}`;
  }
  const extra = o.subtipo === 'ataque_criacao' && o.animais ? ` (${o.animais} animais)` : o.subtipo === 'avistamento' && o.animais ? ` (bando de ${o.animais})` : '';
  return `${JAVALI[o.subtipo] || 'Javali'}${extra}`;
}

function detalhe(o) {
  if (!o) return '<p class="suave dica-mapa">Toque num ponto do mapa para ver o registro.</p>';
  const tags = [];
  if (o.tipo === 'annoni') {
    if (o.status === 'suspeita') tags.push('<span class="tag suspeita">a confirmar</span>');
    if (o.status === 'descartada') tags.push('<span class="tag">descartado</span>');
    if (o.situacao === 'eliminado') tags.push(`<span class="tag ok">eliminado em ${dataBr(o.eliminado_em)}</span>`);
  }
  if (o.propria) tags.push('<span class="tag">na sua propriedade</span>');
  const sugestao = o.triagem_ia ? `<p class="ia">Sugestão automática: ${o.triagem_ia.parece_annoni === 'sim' ? 'parece annoni' : o.triagem_ia.parece_annoni === 'nao' ? 'não parece annoni' : 'incerto'}. ${esc(o.triagem_ia.explicacao)}</p>` : '';
  return `<div class="detalhe">
    <div class="det-topo"><span class="pino ${o.tipo}"></span><div><b>${esc(textoOcorrencia(o))}</b><br>
    <small>${haQuanto(o.observado_em)}${o.tipo === 'javali' ? `, ${periodo(o.observado_em)}` : ''}${estado.perfil === 'sindicato' && o.propriedade_id ? `, ${esc(nomeProp(o.propriedade_id))}` : ''}</small></div></div>
    ${tags.length ? `<p class="tags">${tags.join(' ')}</p>` : ''}
    ${o.nota != null ? `<p>Nota de prioridade <b class="num grande" style="color:${corNota(o.nota)}">${o.nota}</b> de 100. <a href="#prioridades">Ver a lista da semana</a></p>` : ''}
    ${o.prejuizo ? `<p>Prejuízo estimado: <b>${brl(o.prejuizo)}</b></p>` : ''}
    ${o.obs ? `<p class="obs">“${esc(o.obs)}”</p>` : ''}
    ${o.foto ? `<img class="foto" src="/fotos/${esc(o.foto)}" alt="Foto do registro">` : ''}
    ${sugestao}
  </div>`;
}

function legenda(camada) {
  const a = camada !== 'javali', j = camada !== 'annoni';
  return `<ul class="legenda">
    ${a ? `<li><i class="lg foco" style="background:${COR.alta}"></i>Foco de annoni (cor = prioridade)</li>
    <li><i class="lg foco suspeita"></i>A confirmar</li>
    <li><i class="lg mancha"></i>Mancha estabelecida</li>
    <li><i class="lg elim"></i>Eliminado</li>
    <li><i class="lg quad"></i>Annoni de vizinho (só a quadrícula de 1 km)</li>` : ''}
    ${j ? `<li><i class="lg javali"></i>Sinal de javali</li><li><i class="lg dano"></i>Dano de javali</li><li><i class="lg disp"></i>Armadilha / câmera</li>` : ''}
    <li><i class="lg limpo"></i>Campo nativo limpo</li>
    <li><i class="lg vetor"></i>Porteira, mangueira</li>
  </ul>`;
}

// ------------------------------------------------------------------ tela: mapa
function renderMapa() {
  const { base, mapa: m, resumo: r } = estado;
  if (!base || !m) { tela.innerHTML = '<p class="vazio">Sem sinal e sem dados guardados. Abra o app com sinal uma vez.</p>'; return; }
  const sel = m.exatos.find((o) => o.id === estado.selecionado);
  const pid = perfilId();
  const quem = pid ? nomeProp(pid) : 'Coordenação do sindicato';
  const recentes = estado.avisos.slice(0, 3);
  tela.innerHTML = `
    <div class="cabeca"><div><h1>${esc(base.vizinhanca.nome)}</h1>
      <p>${base.propriedades.length} propriedades, ${esc(base.vizinhanca.municipio)}. Você está como <b>${esc(quem)}</b>.</p></div>
      <a class="botao" href="#registrar">Registrar o que viu</a></div>
    ${avisoAntigo()}
    <div class="kpis">
      ${kpi('Focos de annoni ativos', nf(r.focos_ativos), `${r.suspeitas} a confirmar`)}
      ${kpi('Manchas estabelecidas', `${nf(r.area_manchas_ha, 1)} ha`, `${r.manchas} manchas para conter`)}
      ${kpi('Sinais de javali', nf(r.javali_registros), 'nos últimos 60 dias')}
      ${kpi('Prejuízo com javali', brl(r.javali_prejuizo), `${r.javali_animais} animais mortos em 60 dias`, 'perda')}
    </div>
    <div class="grade-mapa">
      <section class="caixa-mapa">
        <div class="chips" role="group" aria-label="Mostrar">
          ${[['tudo', 'Tudo'], ['annoni', 'Capim-annoni'], ['javali', 'Javali']].map(([k, t]) => `<button data-acao="camada" data-camada="${k}" aria-pressed="${estado.camada === k}">${t}</button>`).join('')}
        </div>
        ${desenhar(base, m, { camada: estado.camada, perfil: pid, selecionado: estado.selecionado, clicavel: true })}
        ${legenda(estado.camada)}
      </section>
      <aside>
        ${detalhe(sel)}
        <h2>Avisos recentes</h2>
        ${recentes.length ? `<ul class="avisos">${recentes.map(linhaAviso).join('')}</ul><a href="#avisos">Todos os avisos</a>` : '<p class="vazio">Nenhum aviso.</p>'}
        <p class="privacidade">${pid ? 'O annoni dos vizinhos aparece só pela quadrícula de 1 km, sem dizer de quem é a terra. Pontos exatos: os seus, os da beira da estrada e os de quem escolheu compartilhar.' : 'A coordenação vê todos os pontos exatos para organizar a triagem e o mutirão.'}</p>
      </aside>
    </div>`;
}

// ------------------------------------------------------------------ tela: registrar
function renderRegistrar() {
  const { base, reg } = estado;
  if (!base) { tela.innerHTML = '<p class="vazio">Abra o app com sinal uma vez para baixar o mapa.</p>'; return; }
  const op = (k, v) => `<button data-acao="subtipo" data-sub="${k}" aria-pressed="${reg.subtipo === k}">${v}</button>`;
  const subtipos = reg.tipo === 'annoni'
    ? Object.entries(ANNONI).map(([k, [t, s]]) => `<button data-acao="subtipo" data-sub="${k}" aria-pressed="${reg.subtipo === k}"><b>${t}</b><small>${s}</small></button>`).join('')
    : reg.tipo === 'javali' ? Object.entries(JAVALI).map(([k, t]) => op(k, t)).join('') : '';
  const extra = reg.subtipo === 'avistamento' ? `<label class="campo">Quantos animais?<input name="animais" inputmode="numeric" value="${esc(reg.animais)}"></label>`
    : reg.subtipo === 'ataque_criacao' ? `<label class="campo">Quantos animais mortos ou feridos?<input name="animais" inputmode="numeric" value="${esc(reg.animais)}"></label>`
      : reg.subtipo === 'lavoura' ? `<label class="campo">Prejuízo estimado (R$)<input name="prejuizo" inputmode="decimal" value="${esc(reg.prejuizo)}" placeholder="opcional"></label>` : '';
  const onde = reg.km ? (reg.onde === 'gps' ? 'Pelo GPS do celular.' : 'Marcado no mapa.') + ' Toque no mapa para ajustar.' : 'Use o GPS ou toque no mapa onde você viu.';

  tela.innerHTML = `
    <div class="cabeca"><div><h1>O que você viu?</h1><p>Funciona sem sinal: o registro fica guardado e sobe quando o celular pegar rede.</p></div></div>
    <div class="tipos">
      <button data-acao="tipo" data-tipo="annoni" aria-pressed="${reg.tipo === 'annoni'}"><span class="ico annoni">${ICO.annoni}</span><b>Capim-annoni</b><small>Touceira, foco ou mancha</small></button>
      <button data-acao="tipo" data-tipo="javali" aria-pressed="${reg.tipo === 'javali'}"><span class="ico javali">${ICO.javali}</span><b>Javali</b><small>Rastro, fuçada, bando, dano</small></button>
    </div>
    ${reg.tipo ? `
    <section class="passo"><h2>${reg.tipo === 'annoni' ? 'Qual o tamanho?' : 'O que aconteceu?'}</h2>
      <div class="opcoes ${reg.tipo}">${subtipos}</div>${extra ? `<div class="campos">${extra}</div>` : ''}
      ${reg.tipo === 'annoni' ? '<p class="suave dica">Na dúvida, registre. Um técnico confirma pela foto ou no local antes de entrar no plano.</p>' : ''}
    </section>
    <section class="passo"><h2>Onde?</h2>
      <div class="onde-barra"><button class="botao sec" data-acao="gps">${ICO.gps}<span>Usar minha localização</span></button><span class="suave">${onde}</span></div>
      <div class="caixa-mapa pequena">${desenhar(base, estado.mapa, { camada: reg.tipo, perfil: perfilId(), marcador: reg.km, clicavel: 'marcar', rotulos: true })}</div>
    </section>
    <section class="passo"><h2>Foto e observação</h2>
      <div class="foto-linha">
        <button class="botao sec" data-acao="foto">${ICO.camera}<span>${reg.foto ? 'Trocar foto' : 'Tirar foto'}</span></button>
        ${reg.foto ? '<img class="miniatura" alt="Foto escolhida">' : `<span class="suave">${reg.tipo === 'annoni' ? 'A foto ajuda o técnico a confirmar. Se puder, pegue a espiga.' : 'Opcional.'}</span>`}
      </div>
      <label class="campo largo">Observação<textarea name="obs" placeholder="${reg.tipo === 'annoni' ? 'Ex.: do lado da porteira, umas 3 touceiras' : 'Ex.: bando passou pela sanga de madrugada'}">${esc(reg.obs)}</textarea></label>
    </section>
    <div class="acoes"><button class="botao grande" data-acao="registrar">Registrar</button><button class="botao perigo" data-acao="limpar">Limpar</button></div>` : ''}
    <div id="fila-lista"></div>
    ${estado.resultados.length ? `<h2>Enviados agora</h2>${estado.resultados.slice(0, 3).map(cartaoResultado).join('')}` : ''}`;
  if (reg.foto) $('.miniatura').src = URL.createObjectURL(reg.foto);
  renderFila();
}

async function renderFila() {
  const el = $('#fila-lista');
  if (!el) return;
  const itens = (await filaTodos()).sort((a, b) => a.criado_em.localeCompare(b.criado_em));
  el.innerHTML = itens.length ? `<h2>Guardados no celular (${itens.length})</h2>${itens.map((it) => `
    <article class="na-fila ${it.estado}"><div><b>${esc(textoOcorrencia({ ...it.dados, classe: ANNONI[it.dados.subtipo]?.[0] }))}</b>
      <small>${it.estado === 'erro' ? esc(it.erro) : 'Sobe sozinho quando tiver sinal.'}${it.foto ? ' Com foto.' : ''}</small></div>
      ${it.estado === 'erro' ? `<button class="botao perigo" data-acao="tirar-fila" data-id="${it.id}">Descartar</button>` : ''}</article>`).join('')}` : '';
}

function cartaoResultado(r) {
  const o = r.ocorrencia, p = r.prioridade;
  return `<article class="resultado">
    <b>${esc(textoOcorrencia({ ...o, classe: p?.classe }))}</b>
    <p>${r.avisados ? `${r.avisados} ${r.avisados === 1 ? 'propriedade vizinha avisada' : 'propriedades vizinhas avisadas'}, sem dizer de quem é a terra.` : 'Nenhum vizinho dentro do raio de aviso.'}</p>
    ${p ? `<p>Nota de prioridade <b class="num grande" style="color:${corNota(p.nota)}">${p.nota}</b>. ${esc(p.acao)}${p.mancha ? '' : ` Custo estimado: <b>${brl(p.custo)}</b>.`}</p>` : ''}
    ${o.status === 'suspeita' ? '<p class="suave">Vai para a triagem do técnico antes de entrar no plano.</p>' : ''}
  </article>`;
}

async function registrar() {
  const { reg } = estado;
  if (!reg.subtipo) { avisar(reg.tipo === 'annoni' ? 'Escolha o tamanho do foco.' : 'Escolha o que aconteceu.'); return; }
  if (!reg.km) { avisar('Marque onde foi: use o GPS ou toque no mapa.'); return; }
  const P = criarProjecao(estado.base);
  const [lat, lon] = P.paraLatLon(...reg.km);
  const animais = lerNumero(reg.animais);
  if (['avistamento', 'ataque_criacao'].includes(reg.subtipo) && reg.animais && !animais) { avisar('Quantos animais? Escreva só o número.'); return; }
  const dados = {
    client_id: novoId(), tipo: reg.tipo, subtipo: reg.subtipo, lat, lon,
    area_m2: reg.tipo === 'annoni' ? ANNONI[reg.subtipo][2] : null,
    animais: animais != null ? Math.round(animais) : null, prejuizo: lerNumero(reg.prejuizo),
    obs: reg.obs.trim() || null, observado_em: new Date().toISOString().slice(0, 19), perfil: estado.perfil,
  };
  await filaPor({ id: dados.client_id, dados, foto: reg.foto, estado: 'aguardando', criado_em: new Date().toISOString() });
  estado.reg = { tipo: null, subtipo: null, km: null, onde: null, foto: null, animais: '', prejuizo: '', obs: '' };
  avisar(navigator.onLine ? 'Enviando…' : 'Guardado no celular. Sobe quando tiver sinal.');
  renderRegistrar();
  await atualizarSinal();
  processarFila();
}

function usarGps(botao) {
  if (!navigator.geolocation) { avisar('Este celular não deu acesso ao GPS. Toque no mapa.'); return; }
  botao.disabled = true;
  botao.querySelector('span').textContent = 'Procurando…';
  navigator.geolocation.getCurrentPosition((pos) => {
    const P = criarProjecao(estado.base);
    const km = P.deLatLon(pos.coords.latitude, pos.coords.longitude);
    if (!P.dentro(...km)) {
      avisar('Seu GPS está fora do mapa da vizinhança. Toque no mapa onde você viu.');
      renderRegistrar();
      return;
    }
    Object.assign(estado.reg, { km, onde: 'gps' });
    renderRegistrar();
  }, () => { avisar('Não deu para pegar o GPS. Toque no mapa onde você viu.'); renderRegistrar(); },
  { enableHighAccuracy: true, timeout: 15000, maximumAge: 60000 });
}

// ------------------------------------------------------------------ tela: prioridades
function partes(p) {
  return `<ul class="partes">${p.partes.map((x) => `<li>${esc(x.fator)} <b>+${x.pontos}</b></li>`).join('')}</ul>`;
}

function cartaoFoco(o, i) {
  const p = o.prioridade;
  const sind = estado.perfil === 'sindicato';
  return `<article class="foco" data-id="${o.id}">
    <div class="rank num">${i + 1}</div>
    <div class="corpo">
      <header><div><b>${esc(p.classe[0].toUpperCase() + p.classe.slice(1))}</b>${o.area_m2 ? `<span class="suave">, ${nf(o.area_m2)} m²</span>` : ''}
        ${o.status === 'suspeita' ? ' <span class="tag suspeita">confirmar no local</span>' : ''}
        <br><small>${sind && o.propriedade_id ? esc(nomeProp(o.propriedade_id)) + ', ' : ''}registrado ${haQuanto(o.observado_em)}</small></div>
        <div class="nota" style="--cor:${corNota(p.nota)}"><span class="num">${p.nota}</span><small>de 100</small></div></header>
      ${partes(p)}
      <p class="acao">${esc(p.acao)}</p>
      <footer><span class="num custo">${brl(p.custo)}</span><span class="suave">${nf(p.horas, p.horas % 1 ? 1 : 0)} h de serviço</span>
        <span class="botoes"><button class="botao sec" data-acao="ver-mapa" data-id="${o.id}">Ver no mapa</button>
        <button class="botao" data-acao="eliminar" data-id="${o.id}">Eliminei</button></span></footer>
    </div></article>`;
}

async function renderPrioridades() {
  const p = estado.prioridades = await buscar('prioridades', '/api/prioridades');
  if (!p) { tela.innerHTML = '<p class="vazio">Sem sinal e sem dados guardados.</p>'; return; }
  const r = p.resumo, par = p.parametros;
  const sind = estado.perfil === 'sindicato';
  const top = p.semana[0]?.prioridade;
  tela.innerHTML = `
    <div class="cabeca"><div><h1>Onde gastar primeiro</h1>
      <p>${sind ? 'Toda a vizinhança.' : `Focos dentro da ${esc(nomeProp(perfilId()))}.`} Primeiro os focos pequenos, novos e isolados: são eles que espalham a invasão e os mais baratos de eliminar.</p></div></div>
    ${avisoAntigo()}${bannerEpoca()}
    <div class="kpis">
      ${kpi('Esta semana', `${r.focos_semana} ${r.focos_semana === 1 ? 'foco' : 'focos'}`, `de ${r.focos_ativos} focos ativos`)}
      ${kpi('Custo estimado', brl(r.custo_semana), `${nf(r.horas_semana, 1)} h de serviço`)}
      ${kpi('Recuperar 1 ha tomado', brl(r.custo_recuperar_ha), `${par.kg_pv_recuperacao_ha} kg de peso vivo/ha (Embrapa)`, 'perda')}
      ${kpi('Manchas para conter', `${nf(r.area_manchas_ha, 2)} ha`, r.manchas ? `recuperar custaria ${brl(r.custo_recuperar_manchas)}` : 'nenhuma', r.manchas ? 'perda' : '')}
    </div>
    ${sind && p.triagem?.length ? `<h2>Para confirmar (${p.triagem.length})</h2><p class="suave">Registros de produtores. Confirme pela foto ou na visita.</p>${p.triagem.map(cartaoTriagem).join('')}` : ''}
    <h2>Plano da semana</h2>
    ${p.semana.length ? `${top ? `<p class="comparacao">Eliminar o primeiro foco da lista custa <b>${brl(top.custo)}</b>. Se ele virar mancha, recuperar cada hectare custa <b class="perda">${brl(r.custo_recuperar_ha)}</b>.</p>` : ''}
      <div class="focos">${p.semana.map(cartaoFoco).join('')}</div>` : '<p class="vazio">Nenhum foco ativo para eliminar. Siga com a ronda.</p>'}
    ${p.revisitas.length ? `<h2>Voltar aos focos eliminados (${p.revisitas.length})</h2>
      <p class="suave">A semente fica viva no solo por mais de 20 anos. Volte a cada ${par.revisita_dias} dias.</p>
      <ul class="lista">${p.revisitas.map((o) => `<li><div><b>Foco eliminado em ${dataBr(o.eliminado_em)}</b><br><small>${o.atrasada ? 'Revisita atrasada' : 'Revisitar até'} ${dataBr(o.revisita_em)}${sind && o.propriedade_id ? `, ${esc(nomeProp(o.propriedade_id))}` : ''}</small></div>
        <div class="botoes"><button class="botao sec" data-acao="revisar" data-id="${o.id}" data-rebrota="0">Sem rebrota</button><button class="botao perigo" data-acao="revisar" data-id="${o.id}" data-rebrota="1">Rebrotou</button></div></li>`).join('')}</ul>` : ''}
    ${p.depois.length ? `<h2>Próximas semanas (${p.depois.length})</h2><ul class="lista">${p.depois.map((o) => `<li><div><b>${esc(o.prioridade.classe)}</b>${o.area_m2 ? `, ${nf(o.area_m2)} m²` : ''}<br><small>${esc(o.prioridade.partes.slice(1).map((x) => x.fator).join(', ') || 'longe de vetores e de campo limpo')}</small></div><span class="num nota-peq" style="color:${corNota(o.prioridade.nota)}">${o.prioridade.nota}</span></li>`).join('')}</ul>` : ''}
    ${p.manchas.length ? `<h2>Manchas: conter e recuperar (${p.manchas.length})</h2>
      <p class="suave">A mancha grande não é a prioridade da semana. O objetivo é não deixar sementear e não espalhar: roçar antes do espigamento e quarentena para o gado que sai dali.</p>
      <ul class="lista">${p.manchas.map((o) => `<li><div><b>Mancha de ${nf(o.area_m2)} m²</b><br><small>${esc(o.prioridade.vetor ? 'perto de ' + o.prioridade.vetor : '')}</small></div><span class="num valor">${brl(o.prioridade.custo)}<small> para recuperar</small></span></li>`).join('')}</ul>` : ''}
    <p class="nota-rodape">Custos estimados com mão de obra a ${brl(par.mao_de_obra_h)}/h e até ${nf(par.horas_semana)} h por semana. Recuperação pelo método Mirapasto (Embrapa Pecuária Sul): ${par.kg_pv_recuperacao_ha} kg de peso vivo por hectare, a ${brl(par.preco_kg_pv, 2)}/kg. Herbicida só com receituário agronômico.</p>`;
}

function cartaoTriagem(o) {
  const ia = o.triagem_ia;
  return `<article class="triagem">
    ${o.foto ? `<img src="/fotos/${esc(o.foto)}" alt="Foto enviada">` : '<div class="sem-foto">sem foto</div>'}
    <div><b>${esc(textoOcorrencia({ ...o, classe: ANNONI[o.subtipo]?.[0] }))}</b><br><small>${esc(nomeProp(o.propriedade_id))}, ${haQuanto(o.observado_em)}</small>
      ${o.obs ? `<p class="obs">“${esc(o.obs)}”</p>` : ''}
      ${ia ? `<p class="ia">Sugestão automática: ${esc(ia.parece_annoni)}. ${esc(ia.explicacao)}</p>` : ''}
      <div class="botoes"><button class="botao" data-acao="triar" data-id="${o.id}" data-status="confirmada">É annoni</button>
      <button class="botao perigo" data-acao="triar" data-id="${o.id}" data-status="descartada">Não é</button>
      <button class="botao sec" data-acao="ver-mapa" data-id="${o.id}">Mapa</button></div></div>
  </article>`;
}

// ------------------------------------------------------------------ tela: javali
function graficoHoras(horas) {
  const ordem = [...Array(24).keys()].map((i) => (i + 12) % 24); // meio-dia à esquerda, madrugada no meio
  const max = Math.max(...horas, 1);
  const w = 24, g = 6, H = 150;
  const barras = ordem.map((h, i) => {
    const v = horas[h], alt = (v / max) * H;
    const noite = h >= 18 || h < 6;
    return `<rect x="${i * (w + g)}" y="${H - alt}" width="${w}" height="${Math.max(alt, 1)}" rx="3" fill="${noite ? COR.javali : '#C9C2B2'}"><title>${h}h: ${v}</title></rect>
      ${i % 3 === 0 ? `<text x="${i * (w + g) + w / 2}" y="${H + 28}" text-anchor="middle">${h}h</text>` : ''}`;
  }).join('');
  return `<svg class="horas" viewBox="0 -6 ${24 * (w + g)} ${H + 36}" role="img" aria-label="Registros por hora do dia">${barras}</svg>`;
}

async function renderJavali() {
  const j = estado.javali = await buscar('javali', '/api/javali', false);
  const { base } = estado;
  if (!j || !base) { tela.innerHTML = '<p class="vazio">Sem sinal e sem dados guardados.</p>'; return; }
  const arm = base.dispositivos.find((d) => d.tipo === 'armadilha');
  const resp = arm?.responsavel_semana;
  tela.innerHTML = `
    <div class="cabeca"><div><h1>Javali na vizinhança</h1><p>Os registros de todos formam as rotas do bando. É ali que vão a câmera e a armadilha coletiva.</p></div></div>
    ${avisoAntigo()}
    <div class="kpis">
      ${kpi('Registros', nf(j.registros), `nos últimos ${j.dias} dias`)}
      ${kpi('À noite ou de madrugada', `${j.pct_noite}%`, 'entre 18h e 6h')}
      ${kpi('Animais mortos', nf(j.animais_mortos), 'ovinos e cordeiros', j.animais_mortos ? 'perda' : '')}
      ${kpi('Prejuízo registrado', brl(j.prejuizo), 'criação e lavoura', 'perda')}
    </div>
    <div class="grade-mapa">
      <section class="caixa-mapa">
        ${desenhar(base, estado.mapa, { camada: 'javali', perfil: perfilId(), quentes: j.quentes.slice(0, 3), clicavel: true, selecionado: estado.selecionado })}
        <p class="suave legenda-txt">Quadrados marcados: as 3 quadrículas de 1 km com mais sinais. Dano e registro recente pesam mais.</p>
      </section>
      <aside>
        <h2 style="margin-top:0">A que horas ele passa</h2>${graficoHoras(j.horas)}
        <h2>Onde pôr câmera e armadilha</h2>
        <ol class="quentes">${j.quentes.slice(0, 4).map((q) => `<li><b>${nf(q.n)} sinais</b>${q.tipos.ataque_criacao ? `, ${q.tipos.ataque_criacao} ataque(s)` : ''}${q.tipos.lavoura ? `, ${q.tipos.lavoura} dano(s) em lavoura` : ''}<br>
          <small>${q.coberto_por.length ? `Coberto: ${esc(q.coberto_por.join(', '))}` : '<b class="perda">Sem câmera nem armadilha por perto</b>'}</small></li>`).join('')}</ol>
      </aside>
    </div>
    ${arm ? `<h2>Armadilha coletiva</h2>
    <article class="armadilha ${arm.estado}">
      <div><b>${esc(arm.nome)}</b> <span class="tag ${arm.estado === 'fechada' ? 'alerta' : 'ok'}">${arm.estado === 'fechada' ? 'fechada: chamar controlador' : 'aberta e armada'}</span>
        <p class="suave">Curral com porteira de queda. Um sensor (ESP32 com chave magnética) avisa por LoRa ou SMS quando a porteira fecha.</p>
        <p>Rodízio: ${arm.rodizio.map((id) => `<span class="rod ${id === resp ? 'atual' : ''}">${esc(nomeProp(id))}${id === resp ? ' (esta semana)' : ''}</span>`).join(' ')}</p>
        ${arm.eventos?.length ? `<p class="suave">Último evento: ${esc(arm.eventos[0].evento)} em ${dataBr(arm.eventos[0].criado_em)} ${arm.eventos[0].criado_em.slice(11, 16)}</p>` : ''}</div>
      <div class="botoes">${arm.estado === 'fechada'
        ? `<button class="botao sec" data-acao="sensor" data-id="${arm.id}" data-evento="armada">Armar de novo</button>`
        : `<button class="botao sec" data-acao="sensor" data-id="${arm.id}" data-evento="fechou">Simular sensor: porteira fechou</button>`}</div>
    </article>` : ''}
    <h2>Controladores cadastrados</h2>
    <p class="suave">O abate do javali só pode ser feito por controlador com registro no Exército e cadastro no Ibama (SIMAF). O app liga o produtor a eles; não incentiva caçar por conta própria.</p>
    <ul class="lista">${base.controladores.map((c) => `<li><div><b>${esc(c.nome)}</b><br><small>${esc(c.municipio)}, ${esc(c.registro)}</small></div><span class="num">${esc(c.contato)}</span></li>`).join('')}</ul>
    <p class="nota-rodape">Ovino morto calculado a ${brl(base.valor_ovino)}: o caso de Sant'Ana do Livramento citado no desafio (6.255 ovinos, R$ 3,1 milhões).</p>`;
}

// ------------------------------------------------------------------ tela: avisos e prevenção
function linhaAviso(a) {
  const ico = { annoni: 'annoni', javali: 'javali', armadilha: 'alerta', triagem: 'annoni' }[a.tipo] || 'annoni';
  return `<li class="${a.lido ? '' : 'novo'}"><span class="pino ${ico}"></span><div>${esc(a.texto)}<br><small>${haQuanto(a.criado_em)}</small></div></li>`;
}

async function renderAvisos() {
  const pid = perfilId();
  const [avs, movs] = await Promise.all([buscar('avisos', '/api/avisos'), buscar('movimentos', '/api/movimentos')]);
  estado.avisos = avs || [];
  estado.movimentos = movs || [];
  const ativos = estado.movimentos.filter((m) => m.liberar_em && m.liberar_em >= hojeIso());
  const props = estado.base?.propriedades || [];
  tela.innerHTML = `
    <div class="cabeca"><div><h1>Avisos</h1><p>Quando aparece annoni ou javali perto da sua divisa, você fica sabendo aqui e no WhatsApp.</p></div></div>
    ${avisoAntigo()}
    <div class="duas-col">
      <section>${estado.avisos.length ? `<ul class="avisos">${estado.avisos.map(linhaAviso).join('')}</ul>` : '<p class="vazio">Nenhum aviso por enquanto.</p>'}</section>
      <section>
        <h2 style="margin-top:0">Prevenção: chegou gado ou máquina?</h2>
        ${pid ? `<form class="mov" data-form="movimento">
          <div class="chips" role="group" aria-label="O que chegou">
            <label><input type="radio" name="tipo" value="gado" checked> Gado</label>
            <label><input type="radio" name="tipo" value="maquina"> Máquina</label></div>
          <label class="campo">O quê<input name="descricao" placeholder="Ex.: 40 terneiros comprados" required></label>
          <label class="campo">De onde<select name="origem"><option value="">De fora da vizinhança</option>${props.filter((p) => p.id !== pid).map((p) => `<option value="${p.id}">${esc(p.nome)}</option>`).join('')}</select></label>
          <label class="campo">Chegada<input type="date" name="chegada" value="${hojeIso()}"></label>
          <button class="botao">Ver o que fazer</button>
        </form>` : '<p class="suave">Escolha uma propriedade no topo para registrar chegada de gado ou máquina.</p>'}
        ${estado.movimentos.length ? `<h2>Chegadas registradas</h2>${estado.movimentos.slice(0, 5).map(cartaoMovimento).join('')}` : ''}
        ${ativos.length ? `<p class="suave">${ativos.length} ${ativos.length === 1 ? 'lote em quarentena' : 'lotes em quarentena'} agora.</p>` : ''}
      </section>
    </div>`;
  if (estado.avisos.some((a) => !a.lido)) {
    postJson(comPerfil('/api/avisos/lidos'), {}).then(async () => { estado.resumo = await buscar('resumo', '/api/resumo'); atualizarSinal(); }).catch(() => {});
  }
}

function cartaoMovimento(m) {
  const risco = { alto: 'Vem de propriedade com annoni', desconhecido: 'Origem sem informação: trate como se tivesse annoni', baixo: 'Origem sem annoni registrado' }[m.risco];
  const passos = m.tipo === 'gado'
    ? (m.risco === 'baixo' ? ['Pode ir para o campo. Mesmo assim, olhe a mangueira na época de sementes.']
      : [`Deixe ${10} dias num piquete sem annoni ou na mangueira, até ${dataBr(m.liberar_em)}: a semente passa pelo trato digestivo e sai nas fezes por até 4 dias (Embrapa recomenda de 8 a 10).`,
        'Não solte direto no campo nativo limpo.', 'Depois, olhe o piquete da quarentena na época de sementes e arranque o que nascer.'])
    : ['Limpe roçadeira, grade e pneus antes de entrar num campo limpo.', 'Comece o serviço pelos campos limpos e termine nos infestados.',
      ...(m.risco !== 'baixo' ? ['Lave a máquina num ponto só e acompanhe o que nascer ali.'] : [])];
  return `<article class="movimento ${m.risco}"><b>${esc(m.descricao)}</b><br><small>${m.tipo === 'gado' ? 'Gado' : 'Máquina'}, chegada ${dataBr(m.chegada)}. ${risco}.</small>
    <ul>${passos.map((t) => `<li>${esc(t)}</li>`).join('')}</ul></article>`;
}

// ------------------------------------------------------------------ ícones
const ICO = {
  annoni: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M12 21V9M12 21c-1-5-4-8-7-9M12 21c1-5 4-8 7-9M12 13c-2-3-2-6-1-9M12 13c2-3 2-6 1-9"/></svg>',
  javali: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 13c0-4 3.5-7 8-7s8 3 8 7-3 6-8 6-8-2-8-6z"/><path d="M6 8L4 4M18 8l2-4M9.5 15.5h5M10 12h.01M14 12h.01"/></svg>',
  gps: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="7"/><circle cx="12" cy="12" r="2.5" fill="currentColor"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3"/></svg>',
  camera: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"><path d="M4 8h3l2-3h6l2 3h3v11H4z"/><circle cx="12" cy="13" r="3.5"/></svg>',
};

// ------------------------------------------------------------------ rotas e eventos
function rota() {
  const [nome, id] = (location.hash.slice(1) || 'mapa').split('/');
  return { nome, id: id ? Number(id) : null };
}

async function render(rolar = true) {
  const r = rota();
  document.querySelectorAll('.nav a').forEach((a) => {
    if (a.dataset.rota === r.nome) a.setAttribute('aria-current', 'page'); else a.removeAttribute('aria-current');
  });
  if (r.nome === 'registrar') renderRegistrar();
  else if (r.nome === 'prioridades') await renderPrioridades();
  else if (r.nome === 'javali') await renderJavali();
  else if (r.nome === 'avisos') await renderAvisos();
  else {
    if (!estado.avisos.length) estado.avisos = (await buscar('avisos', '/api/avisos')) || [];
    renderMapa();
  }
  if (rolar) window.scrollTo(0, 0);
}

function preencherPerfis() {
  const sel = $('#perfil');
  const props = estado.base?.propriedades || [];
  sel.innerHTML = props.map((p) => `<option value="${p.id}">${esc(p.nome)}</option>`).join('')
    + '<option value="sindicato">Sindicato rural (coordenação)</option>';
  sel.value = estado.perfil;
}

tela.addEventListener('click', async (e) => {
  const oc = e.target.closest('[data-oc]');
  if (oc && !e.target.closest('svg.marcar')) {
    estado.selecionado = Number(oc.dataset.oc);
    if (rota().nome === 'mapa') renderMapa();
    else if (rota().nome === 'javali') {
      const o = estado.mapa.exatos.find((x) => x.id === estado.selecionado);
      if (o) avisar(`${textoOcorrencia(o)}, ${haQuanto(o.observado_em)} ${periodo(o.observado_em)}.`);
    }
    return;
  }
  const svgMarcar = e.target.closest('svg.marcar');
  if (svgMarcar) {
    estado.reg.km = pontoDoToque(svgMarcar, e, estado.base).map((v) => +v.toFixed(4));
    estado.reg.onde = 'mapa';
    renderRegistrar();
    return;
  }
  const b = e.target.closest('[data-acao]');
  if (!b) return;
  const acao = b.dataset.acao;
  const id = Number(b.dataset.id);

  if (acao === 'camada') { estado.camada = b.dataset.camada; renderMapa(); }
  else if (acao === 'tipo') {
    if (estado.reg.tipo !== b.dataset.tipo) Object.assign(estado.reg, { tipo: b.dataset.tipo, subtipo: null, animais: '', prejuizo: '' });
    renderRegistrar();
  } else if (acao === 'subtipo') { estado.reg.subtipo = b.dataset.sub; renderRegistrar(); }
  else if (acao === 'gps') usarGps(b);
  else if (acao === 'foto') { $('#arquivo').value = ''; $('#arquivo').click(); }
  else if (acao === 'registrar') { b.disabled = true; await registrar(); }
  else if (acao === 'limpar') { estado.reg = { tipo: null, subtipo: null, km: null, onde: null, foto: null, animais: '', prejuizo: '', obs: '' }; renderRegistrar(); }
  else if (acao === 'tirar-fila') { await filaTirar(b.dataset.id); renderFila(); atualizarSinal(); }
  else if (acao === 'ver-mapa') { estado.selecionado = id; estado.camada = 'annoni'; location.hash = 'mapa'; }
  else if (acao === 'eliminar') {
    if (!b.dataset.armado) { b.dataset.armado = '1'; b.textContent = 'Confirmar'; return; }
    try {
      await postJson(`/api/ocorrencias/${id}/eliminar`, {});
      avisar('Foco marcado como eliminado. Volte nele daqui a 60 dias.');
      await carregarTudo();
      renderPrioridades();
    } catch (err) { avisar(err.status ? err.message : 'Sem sinal: marque quando tiver conexão.'); }
  } else if (acao === 'revisar') {
    try {
      await postJson(`/api/ocorrencias/${id}/revisar`, { rebrota: b.dataset.rebrota === '1' });
      avisar(b.dataset.rebrota === '1' ? 'Voltou para a lista de focos.' : 'Revisita anotada.');
      await carregarTudo();
      renderPrioridades();
    } catch (err) { avisar(err.status ? err.message : 'Sem sinal: anote quando tiver conexão.'); }
  } else if (acao === 'triar') {
    try {
      await postJson(`/api/ocorrencias/${id}/triagem`, { status: b.dataset.status });
      avisar(b.dataset.status === 'confirmada' ? 'Confirmado. Entrou no plano.' : 'Descartado.');
      await carregarTudo();
      renderPrioridades();
    } catch (err) { avisar(err.status ? err.message : 'Sem sinal.'); }
  } else if (acao === 'sensor') {
    try {
      const r = await postJson(`/api/dispositivos/${id}/sensor`, { evento: b.dataset.evento });
      avisar(b.dataset.evento === 'fechou' ? `Armadilha fechou. ${r.avisados} avisos enviados.` : 'Armadilha armada.');
      estado.base = await buscar('base', '/api/base', false);
      estado.resumo = await buscar('resumo', '/api/resumo');
      atualizarSinal();
      renderJavali();
    } catch (err) { avisar(err.status ? err.message : 'Sem sinal.'); }
  }
});

tela.addEventListener('input', (e) => {
  const n = e.target.name;
  if (rota().nome === 'registrar' && ['obs', 'animais', 'prejuizo'].includes(n)) estado.reg[n] = e.target.value;
});

tela.addEventListener('keydown', (e) => {
  if ((e.key === 'Enter' || e.key === ' ') && e.target.dataset?.oc) { e.preventDefault(); e.target.dispatchEvent(new MouseEvent('click', { bubbles: true })); }
});

tela.addEventListener('submit', async (e) => {
  if (e.target.dataset.form !== 'movimento') return;
  e.preventDefault();
  const f = new FormData(e.target);
  const origem = f.get('origem');
  try {
    await postJson('/api/movimentos', {
      client_id: novoId(), propriedade_id: perfilId(), tipo: f.get('tipo'), descricao: String(f.get('descricao')).trim(),
      origem_id: origem ? Number(origem) : null, origem_texto: origem ? null : 'fora da vizinhança', chegada: f.get('chegada'),
    });
    renderAvisos();
  } catch (err) { avisar(err.status ? err.message : 'Sem sinal: registre quando tiver conexão.'); }
});

$('#arquivo').addEventListener('change', async (e) => {
  const arq = e.target.files?.[0];
  if (!arq) return;
  estado.reg.foto = await comprimir(arq);
  renderRegistrar();
});

$('#perfil').addEventListener('change', async (e) => {
  estado.perfil = e.target.value;
  lembrar('perfil', estado.perfil);
  estado.selecionado = null;
  estado.avisos = [];
  await carregarTudo();
  await atualizarSinal();
  render();
});

window.addEventListener('hashchange', () => render());
window.addEventListener('online', () => { avisar('Sinal de volta. Enviando o que ficou guardado.'); processarFila(); });
window.addEventListener('offline', atualizarSinal);
setInterval(processarFila, 20000);

if ('serviceWorker' in navigator) navigator.serviceWorker.register('/sw.js').catch(() => { /* sem HTTPS: segue sem modo offline */ });

await carregarTudo();
if (estado.base && !estado.base.propriedades.some((p) => String(p.id) === String(estado.perfil)) && estado.perfil !== 'sindicato') estado.perfil = '6';
preencherPerfis();
await atualizarSinal();
await render();
processarFila();
