// Conta do Talhão: app web que funciona sem sinal.
// Fotos e frases vão para uma fila no celular (IndexedDB) e são lidas quando há sinal.
// O produtor confirma cada leitura antes de salvar.

const $ = (s, el = document) => el.querySelector(s);
const tela = $('#tela');
const estado = { fazenda: null, painel: null, painelAntigo: false, recentes: [], metrica: 'margem_ha' };

// ------------------------------------------------------------------ formatos
const nf = (v, c = 0) => Number(v).toLocaleString('pt-BR', { minimumFractionDigits: c, maximumFractionDigits: c });
const brl = (v, c = 0) => (v == null ? '–' : (v < 0 ? '−' : '') + 'R$ ' + nf(Math.abs(v), c));
const brlSinal = (v, c = 0) => (v == null ? '–' : (v > 0 ? '+' : '') + brl(v, c));
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (ch) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[ch]));
const lerNumero = (s) => {
  s = String(s ?? '').trim().replace(/[R$\s]/g, '');
  if (!s) return null;
  if (s.includes(',')) s = s.replace(/\./g, '').replace(',', '.');
  else if (/^\d{1,3}(\.\d{3})+$/.test(s)) s = s.replace(/\./g, '');
  const n = Number(s);
  return Number.isFinite(n) ? n : null;
};
const hoje = () => new Date().toISOString().slice(0, 10);
const novoId = () => (crypto.randomUUID ? crypto.randomUUID()
  : 'id-' + Date.now().toString(36) + '-' + Math.random().toString(36).slice(2, 10));

const DOCUMENTO = {
  nota_fiscal: 'Nota da revenda', conta_luz: 'Conta de luz', romaneio: 'Romaneio ou venda',
  venda_gado: 'Venda de gado', anotacao: 'Anotação', outro: 'Documento',
};

// ------------------------------------------------------------------ fila no celular (IndexedDB)
const BANCO = 'conta-talhao';
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

// ------------------------------------------------------------------ dados do servidor
const lembrar = (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); } catch { /* sem espaço: segue */ } };
const lembrado = (k) => { try { return JSON.parse(localStorage.getItem(k)); } catch { return null; } };

async function api(caminho, opcoes) {
  const r = await fetch(caminho, opcoes);
  if (!r.ok) {
    let detalhe;
    try { detalhe = (await r.json()).detail; } catch { /* corpo vazio */ }
    const e = new Error(typeof detalhe === 'string' ? detalhe : `O servidor respondeu ${r.status}.`);
    e.status = r.status;
    throw e;
  }
  return r.json();
}

async function carregarFazenda() {
  try { estado.fazenda = await api('/api/fazenda'); lembrar('fazenda', estado.fazenda); }
  catch { estado.fazenda = lembrado('fazenda'); }
}
async function carregarPainel() {
  try { estado.painel = await api('/api/painel'); estado.painelAntigo = false; lembrar('painel', estado.painel); }
  catch { estado.painel = lembrado('painel'); estado.painelAntigo = true; }
}
async function carregarRecentes() {
  try { estado.recentes = await api('/api/lancamentos?limite=8'); lembrar('recentes', estado.recentes); }
  catch { estado.recentes = lembrado('recentes') || []; }
}

function nomeAlvo(tipo, id) {
  const f = estado.fazenda;
  if (!f) return '';
  if (tipo === 'geral') return 'Geral da lavoura';
  const lista = { talhao: f.talhoes, lote: f.lotes, bomba: f.bombas }[tipo] || [];
  const x = lista.find((i) => i.id === id);
  return x ? (tipo === 'lote' ? `Lote ${x.nome}` : x.nome) : '';
}
const nomeCategoria = (c) => estado.fazenda?.categorias_custo[c] || estado.fazenda?.categorias_receita[c] || c;

// ------------------------------------------------------------------ aviso rápido
function avisar(texto) {
  document.querySelector('.toast')?.remove();
  const t = Object.assign(document.createElement('div'), { className: 'toast', role: 'status', textContent: texto });
  document.body.append(t);
  setTimeout(() => t.remove(), 3800);
}

// ------------------------------------------------------------------ sinal e fila
async function atualizarSinal() {
  const itens = await filaTodos();
  const envio = itens.filter((i) => i.estado === 'aguardando' || i.estado === 'salvando').length;
  const conferir = itens.filter((i) => i.estado === 'confirmar').length;
  const el = $('#sinal');
  el.className = 'sinal' + (!navigator.onLine ? ' off' : envio ? ' fila' : '');
  el.textContent = !navigator.onLine
    ? (envio ? `Sem sinal: ${envio} na fila` : 'Sem sinal')
    : (envio ? `Enviando ${envio}…` : 'Com sinal, tudo enviado');
  $('#nav-fila').innerHTML = conferir ? `<span class="contador">${conferir}</span>` : '';
}

let processando = false;
async function processarFila() {
  if (processando || !navigator.onLine) return atualizarSinal();
  processando = true;
  let mudou = false;
  try {
    for (const it of await filaTodos()) {
      if (it.estado === 'aguardando') {
        const fd = new FormData();
        fd.append('client_id', it.id);
        if (it.foto) {
          fd.append('arquivo', it.foto, `${it.id}.jpg`);
          if (it.dica) fd.append('dica', it.dica);
        } else {
          fd.append('texto', it.texto);
        }
        try {
          it.rascunho = await api('/api/extrair', { method: 'POST', body: fd });
          it.estado = 'confirmar';
          it.erro = null;
        } catch (e) {
          if (e.status && e.status !== 503) { // não adianta tentar de novo: vira preenchimento à mão
            it.rascunho = rascunhoVazio(it);
            it.estado = 'confirmar';
          }
          it.erro = e.message;
        }
        await filaPor(it);
        mudou = true;
      } else if (it.estado === 'salvando') {
        try {
          await api('/api/lancamentos', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(it.envio) });
          await filaTirar(it.id);
          mudou = true;
        } catch (e) {
          if (e.status && e.status < 500) { it.estado = 'confirmar'; it.erro = e.message; await filaPor(it); mudou = true; }
        }
      }
    }
  } finally {
    processando = false;
  }
  await atualizarSinal();
  if (mudou && rota().nome === 'registrar') {
    const digitando = document.activeElement?.closest?.('.conf');
    if (digitando) avisar('Uma nova leitura ficou pronta para conferir.');
    else renderRegistrar();
  }
}

function rascunhoVazio(it) {
  const cat = { conta_luz: 'energia', romaneio: 'venda_arroz', venda_gado: 'venda_gado' }[it.dica] || 'outros';
  return {
    documento: it.dica || (it.foto ? 'nota_fiscal' : 'anotacao'), data: null, alvo: null, fonte: 'manual', anexo: null,
    itens: [{ descricao: it.texto || '', categoria: cat, quantidade: null, unidade: null, valor_total: null }],
  };
}

async function comprimir(arquivo) {
  try {
    const img = await createImageBitmap(arquivo);
    const k = Math.min(1, 1600 / Math.max(img.width, img.height));
    const c = Object.assign(document.createElement('canvas'), { width: Math.round(img.width * k), height: Math.round(img.height * k) });
    c.getContext('2d').drawImage(img, 0, 0, c.width, c.height);
    return await new Promise((ok) => c.toBlob(ok, 'image/jpeg', 0.75));
  } catch {
    return arquivo;
  }
}

// ------------------------------------------------------------------ ícones
const ICO = {
  nota: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"><path d="M6 3h12v18l-3-2-3 2-3-2-3 2z"/><path d="M9 8h6M9 12h6M9 16h3"/></svg>',
  luz: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"><path d="M13 2L5 14h6l-1 8 8-12h-6z"/></svg>',
  venda: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"><path d="M2 7h11v9H2zM13 10h4l4 3v3h-8z"/><circle cx="6" cy="18" r="2"/><circle cx="17" cy="18" r="2"/></svg>',
  escrever: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"><path d="M4 20h4L19 9l-4-4L4 16z"/><path d="M13 7l4 4"/></svg>',
  mic: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><rect x="9" y="3" width="6" height="11" rx="3"/><path d="M5 11a7 7 0 0 0 14 0M12 18v3"/></svg>',
};

// ------------------------------------------------------------------ tela: registrar
async function renderRegistrar() {
  const itens = (await filaTodos()).sort((a, b) => a.criado_em.localeCompare(b.criado_em));
  const conferir = itens.filter((i) => i.estado === 'confirmar');
  const esperando = itens.filter((i) => i.estado === 'aguardando' || i.estado === 'salvando');
  const temVoz = 'SpeechRecognition' in window || 'webkitSpeechRecognition' in window;
  const auto = estado.fazenda?.leitura_automatica;

  tela.innerHTML = `
    <div class="cabeca">
      <div><h1>O que aconteceu na lavoura?</h1>
      <p>Tire a foto ou escreva. ${auto ? 'A leitura é automática; você só confere.' : 'Você confere e completa antes de salvar.'}</p></div>
    </div>
    <div class="captura">
      <button data-acao="foto" data-dica="nota_fiscal"><span class="ico">${ICO.nota}</span><b>Nota da revenda</b><small>Adubo, semente, defensivo, diesel</small></button>
      <button data-acao="foto" data-dica="conta_luz"><span class="ico">${ICO.luz}</span><b>Conta de luz</b><small>Da bomba de irrigação</small></button>
      <button data-acao="foto" data-dica="romaneio"><span class="ico">${ICO.venda}</span><b>Romaneio ou venda</b><small>Arroz entregue ou gado vendido</small></button>
      <button data-acao="focar-texto"><span class="ico">${ICO.escrever}</span><b>Escrever ou falar</b><small>“Passei 200 kg de ureia no talhão 3”</small></button>
    </div>
    <div class="escrever">
      <label class="sr" for="texto">O que aconteceu</label>
      <textarea id="texto" placeholder="Ex.: passei 200 kg de ureia no talhão 3 por 640 reais"></textarea>
      ${temVoz ? `<button class="botao sec" data-acao="falar" aria-pressed="false">${ICO.mic}<span>Falar</span></button>` : '<span></span>'}
      <button class="botao" data-acao="ler-texto">Registrar</button>
    </div>

    ${conferir.length ? `<h2>Para conferir (${conferir.length})</h2>${conferir.map(cartaoConferir).join('')}` : ''}
    ${esperando.length ? `<h2>Esperando sinal (${esperando.length})</h2>${esperando.map(cartaoEsperando).join('')}` : ''}

    <h2>Últimos lançamentos</h2>
    ${estado.recentes.length ? `<ul class="lista">${estado.recentes.map(linhaLancamento).join('')}</ul>`
      : '<p class="vazio">Nada lançado ainda. Comece pela foto de uma nota.</p>'}
  `;
  for (const it of conferir) {
    if (!it.foto) continue;
    const img = tela.querySelector(`.conf[data-id="${it.id}"] img`);
    if (img) img.src = URL.createObjectURL(it.foto);
  }
}

function cartaoEsperando(it) {
  const o_que = it.foto ? `Foto: ${DOCUMENTO[it.dica] || 'documento'}` : `“${esc(it.texto.slice(0, 80))}”`;
  const situacao = it.estado === 'salvando' ? 'Conferido; vai para o servidor quando tiver sinal.'
    : (it.erro ? esc(it.erro) : 'Guardado no celular; será lido quando tiver sinal.');
  return `<article class="conf espera"><header><div><b>${o_que}</b><small>${situacao}</small></div></header></article>`;
}

function opcoesAlvo(rascunho) {
  const f = estado.fazenda;
  const sel = rascunho.alvo ? `${rascunho.alvo.alvo_tipo}:${rascunho.alvo.alvo_id ?? ''}` : '';
  const op = (v, t) => `<option value="${v}" ${v === sel ? 'selected' : ''}>${esc(t)}</option>`;
  return `${sel ? '' : '<option value="" selected disabled>Escolha…</option>'}
    <optgroup label="Talhões">${f.talhoes.map((t) => op(`talhao:${t.id}`, t.nome)).join('')}</optgroup>
    <optgroup label="Lotes de gado">${f.lotes.map((l) => op(`lote:${l.id}`, `Lote ${l.nome}`)).join('')}</optgroup>
    <optgroup label="Bombas (conta de luz)">${f.bombas.map((b) => op(`bomba:${b.id}`, b.nome)).join('')}</optgroup>
    ${op('geral:', 'Geral da lavoura (dividir por área)')}`;
}

function opcoesCategoria(atual) {
  const f = estado.fazenda;
  const op = ([k, v]) => `<option value="${k}" ${k === atual ? 'selected' : ''}>${esc(v)}</option>`;
  return `<optgroup label="Custos">${Object.entries(f.categorias_custo).map(op).join('')}</optgroup>
    <optgroup label="Receitas">${Object.entries(f.categorias_receita).map(op).join('')}</optgroup>`;
}

function cartaoConferir(it) {
  const r = it.rascunho;
  const fonte = r.fonte === 'ia' ? 'Lido automaticamente. Confira os valores.'
    : r.fonte === 'regras' ? 'Lido da sua frase. Confira e complete.'
      : 'Leitura automática desligada. Preencha os campos.';
  const itens = r.itens.map((x, n) => `
    <div class="item largo campos" data-item="${n}">
      <label class="campo largo">Descrição<input name="descricao" value="${esc(x.descricao)}" required></label>
      <label class="campo">Categoria<select name="categoria">${opcoesCategoria(x.categoria)}</select></label>
      <label class="campo">Valor (R$)<input name="valor" inputmode="decimal" value="${x.valor_total != null ? nf(x.valor_total, 2) : ''}" placeholder="0,00" required></label>
      <label class="campo">Quantidade<input name="quantidade" inputmode="decimal" value="${x.quantidade != null ? nf(x.quantidade, x.quantidade % 1 ? 2 : 0) : ''}"></label>
      <label class="campo">Unidade<input name="unidade" value="${esc(x.unidade || '')}" placeholder="kg, L, sc, cab"></label>
    </div>`).join('');
  return `
    <article class="conf" data-id="${it.id}">
      <header><div><b>${DOCUMENTO[r.documento] || 'Registro'}</b><small>${fonte}</small></div>${it.foto ? '<img alt="Foto enviada">' : ''}</header>
      ${it.erro ? `<p class="aviso">${esc(it.erro)}</p>` : ''}
      <div class="campos">
        <label class="campo destaque largo">Em qual talhão, lote ou bomba?<select name="alvo">${opcoesAlvo(r)}</select></label>
        <label class="campo largo">Data<input type="date" name="data" value="${r.data || hoje()}"></label>
        ${itens}
      </div>
      <div class="acoes">
        <button class="botao" data-acao="salvar">Salvar</button>
        <button class="botao perigo" data-acao="descartar">Descartar</button>
      </div>
    </article>`;
}

function linhaLancamento(l, comApagar = false) {
  const receita = l.tipo === 'receita';
  const qtd = l.quantidade ? `${nf(l.quantidade, l.quantidade % 1 ? 1 : 0)} ${esc(l.unidade || '')}, ` : '';
  const data = l.data.split('-').reverse().join('/');
  return `<li>
    <div><b>${esc(l.descricao)}</b><br><small>${data}, ${qtd}${esc(nomeCategoria(l.categoria).toLowerCase())}, ${esc(nomeAlvo(l.alvo_tipo, l.alvo_id))}</small></div>
    <div><span class="valor ${receita ? 'ganho' : ''}">${receita ? '+' : ''}${brl(l.valor, 2)}</span>
    ${comApagar ? `<br><button class="apagar" data-acao="apagar" data-lanc="${l.id}">Apagar</button>` : ''}</div>
  </li>`;
}

async function salvar(cartao) {
  const id = cartao.dataset.id;
  const it = (await filaTodos()).find((x) => x.id === id);
  const alvo = cartao.querySelector('[name=alvo]').value;
  if (!alvo) { avisar('Escolha em qual talhão, lote ou bomba lançar.'); cartao.querySelector('[name=alvo]').focus(); return; }
  const [alvo_tipo, alvoId] = alvo.split(':');
  const data = cartao.querySelector('[name=data]').value || hoje();
  const envio = [];
  for (const el of cartao.querySelectorAll('[data-item]')) {
    const valor = lerNumero(el.querySelector('[name=valor]').value);
    const descricao = el.querySelector('[name=descricao]').value.trim();
    if (!valor || valor <= 0) { avisar('Falta o valor em reais.'); el.querySelector('[name=valor]').focus(); return; }
    if (!descricao) { avisar('Escreva uma descrição curta.'); el.querySelector('[name=descricao]').focus(); return; }
    envio.push({
      client_id: `${id}-${el.dataset.item}`, data, descricao, valor,
      categoria: el.querySelector('[name=categoria]').value,
      quantidade: lerNumero(el.querySelector('[name=quantidade]').value),
      unidade: el.querySelector('[name=unidade]').value.trim() || null,
      alvo_tipo, alvo_id: alvoId ? Number(alvoId) : null,
      origem: it.foto ? 'foto' : 'texto', anexo: it.rascunho?.anexo || null,
    });
  }
  const destino = nomeAlvo(alvo_tipo, alvoId ? Number(alvoId) : null);
  try {
    await api('/api/lancamentos', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(envio) });
    await filaTirar(id);
    avisar(`Salvo em ${destino}.`);
    await Promise.all([carregarRecentes(), carregarPainel()]);
  } catch (e) {
    if (e.status && e.status < 500) { avisar(e.message); return; }
    Object.assign(it, { estado: 'salvando', envio, erro: null });
    await filaPor(it);
    avisar(`Guardado no celular. Vai para ${destino} quando tiver sinal.`);
  }
  await atualizarSinal();
  renderRegistrar();
}

// ------------------------------------------------------------------ mapa
const METRICAS = {
  margem_ha: { rotulo: 'Margem por ha', valor: (t) => t.margem_ha, divergente: true },
  custo_ha: { rotulo: 'Custo por ha', valor: (t) => t.custo_ha },
  energia_ha: { rotulo: 'Energia por ha', valor: (t) => (t.por_categoria.energia || 0) / t.area_ha },
  adubo_ha: { rotulo: 'Adubo por ha', valor: (t) => (t.por_categoria.adubo || 0) / t.area_ha },
  defensivos_ha: { rotulo: 'Defensivos por ha', valor: (t) => (t.por_categoria.defensivos || 0) / t.area_ha },
};

function mistura(a, b, k) {
  const p = (h) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16));
  const [x, y] = [p(a), p(b)];
  return '#' + x.map((v, i) => Math.round(v + (y[i] - v) * k).toString(16).padStart(2, '0')).join('');
}

function corDe(metrica, v, valores) {
  if (metrica.divergente) {
    const lim = Math.max(...valores.map(Math.abs)) || 1;
    const k = Math.min(1, Math.abs(v) / lim);
    return v >= 0 ? [mistura('#D5E7EA', '#1F5F6B', k), k] : [mistura('#F1D9D1', '#B4432C', k), k];
  }
  const lo = Math.min(...valores), hi = Math.max(...valores);
  const k = hi > lo ? (v - lo) / (hi - lo) : 0.5;
  return [mistura('#F3E6DE', '#B4432C', k), k];
}

function centro(pts) {
  return pts.reduce(([x, y], [a, b]) => [x + a / pts.length, y + b / pts.length], [0, 0]);
}

function svgMapa() {
  const f = estado.fazenda, p = estado.painel;
  const m = METRICAS[estado.metrica];
  const linhas = Object.fromEntries(p.talhoes.map((t) => [t.id, t]));
  const valores = p.talhoes.map(m.valor);
  const lotes = Object.fromEntries(p.lotes.map((l) => [l.id, l]));
  const talhoes = f.talhoes.map((t) => {
    const v = m.valor(linhas[t.id]);
    const [cor, k] = corDe(m, v, valores);
    const [cx, cy] = centro(t.poligono);
    const claro = k > 0.55;
    const curto = t.nome.split(' ').slice(0, 2).join(' ');
    const valorTxt = m.divergente ? brlSinal(v) : brl(v);
    return `<g>
      <polygon class="talhao" tabindex="0" role="link" data-talhao="${t.id}" points="${t.poligono.map((q) => q.join(',')).join(' ')}" fill="${cor}">
        <title>${esc(t.nome)}: ${esc(m.rotulo.toLowerCase())} ${valorTxt}</title></polygon>
      <text x="${cx}" y="${cy - 10}" text-anchor="middle" class="rot-nome" fill="${claro ? '#fff' : '#15201E'}">${esc(curto)}</text>
      <text x="${cx}" y="${cy + 30}" text-anchor="middle" class="rot-valor" fill="${claro ? '#fff' : '#15201E'}">${valorTxt}<tspan class="rot-un" font-weight="600">/ha</tspan></text>
    </g>`;
  }).join('');
  const pastos = f.lotes.map((l) => {
    const [cx, cy] = centro(l.poligono);
    const r = lotes[l.id];
    return `<g><polygon class="pasto" points="${l.poligono.map((q) => q.join(',')).join(' ')}"><title>Pasto do lote ${esc(l.nome)}</title></polygon>
      <text x="${cx}" y="${cy - 4}" text-anchor="middle" class="rot-pasto">${esc(l.nome)}</text>
      <text x="${cx}" y="${cy + 22}" text-anchor="middle" class="rot-pasto">${r ? brlSinal(r.resultado_cabeca) + '/cab' : ''}</text></g>`;
  }).join('');
  const bombas = [[418, 292, 1], [792, 548, 2], [756, 248, 3]].map(([x, y, i]) => {
    const b = f.bombas.find((q) => q.id === i);
    return b ? `<g><circle cx="${x}" cy="${y}" r="11" fill="#fff" stroke="#1F5F6B" stroke-width="4"><title>${esc(b.nome)}</title></circle></g>` : '';
  }).join('');
  const mn = Math.min(...valores), mx = Math.max(...valores);
  const escala = m.divergente
    ? `linear-gradient(90deg, #B4432C, #F1D9D1 49%, #D5E7EA 51%, #1F5F6B)`
    : `linear-gradient(90deg, #F3E6DE, #B4432C)`;
  return `
    <svg class="mapa" viewBox="0 0 1000 620" role="group" aria-label="Mapa da propriedade, talhões coloridos por ${esc(m.rotulo.toLowerCase())}">
      <path d="M0 604 C 180 578, 360 618, 560 596 S 880 574, 1000 600 L1000 620 L0 620 Z" fill="#A9CDD3"/>
      <path d="M402 8 C 520 30, 640 2, 780 18" stroke="#A9CDD3" stroke-width="7" fill="none" stroke-linecap="round"/>
      ${pastos}${talhoes}${bombas}
    </svg>
    <div class="legenda" aria-hidden="true">
      <span>${m.divergente ? brlSinal(Math.min(mn, 0)) : brl(mn)}</span>
      <span class="escala" style="background:${escala}"></span>
      <span>${m.divergente ? brlSinal(Math.max(mx, 0)) : brl(mx)}</span>
      <span>○ bomba de irrigação</span>
    </div>`;
}

// ------------------------------------------------------------------ tela: painel
async function renderPainel() {
  if (!estado.painel) await carregarPainel();
  const p = estado.painel, f = estado.fazenda;
  if (!p || !f) { tela.innerHTML = '<p class="vazio">Sem sinal e sem dados guardados. Abra o app com sinal uma vez.</p>'; return; }
  const fz = p.fazenda;
  const vermelho = p.talhoes.filter((t) => t.receita && t.margem < 0).length;
  const m = METRICAS[estado.metrica];
  const ordenados = [...p.talhoes].sort((a, b) => m.valor(a) - m.valor(b));
  if (!m.divergente) ordenados.reverse();

  tela.innerHTML = `
    <div class="cabeca">
      <div><h1>Safra 2025/26</h1><p>${nf(fz.area_ha)} ha de arroz irrigado em ${p.talhoes.length} talhões</p></div>
      <a class="botao sec" href="/api/relatorio.pdf">${ICO.nota}<span>Relatório para o banco</span></a>
    </div>
    ${estado.painelAntigo ? '<p class="aviso suave">Sem sinal: mostrando os números da última vez que o app abriu com sinal.</p>' : ''}
    <div class="kpis">
      <div class="kpi"><small>Custo médio</small><strong class="num">${brl(fz.custo_ha)}</strong><small>por hectare</small></div>
      <div class="kpi"><small>Custo da saca</small><strong class="num">${brl(fz.custo_saca, 2)}</strong><small>média da fazenda</small></div>
      <div class="kpi"><small>Resultado da lavoura</small><strong class="num ${fz.margem < 0 ? 'perda' : 'ganho'}">${brlSinal(fz.margem)}</strong><small>na safra</small></div>
      <div class="kpi"><small>Talhões no vermelho</small><strong class="num ${vermelho ? 'perda' : ''}">${vermelho} de ${p.talhoes.length}</strong><small>margem negativa</small></div>
    </div>
    <div class="painel-grade">
      <section class="mapa-caixa" aria-labelledby="t-mapa">
        <h2 id="t-mapa" class="sr">Mapa</h2>
        <div class="metricas" role="group" aria-label="Pintar o mapa por">
          ${Object.entries(METRICAS).map(([k, v]) => `<button data-acao="metrica" data-metrica="${k}" aria-pressed="${k === estado.metrica}">${v.rotulo}</button>`).join('')}
        </div>
        ${svgMapa()}
      </section>
      <section>
        <h2 style="margin-top:0">O que olhar primeiro</h2>
        ${p.alertas.length ? `<ul class="alertas">${p.alertas.slice(0, 4).map((a) => `<li>${esc(a.texto)}<br><a href="#talhao/${a.talhao_id}">Abrir ${esc(nomeAlvo('talhao', a.talhao_id))}</a></li>`).join('')}</ul>`
          : '<p class="vazio">Nenhum talhão fora da curva.</p>'}
        <h2>Talhões por ${esc(m.rotulo.toLowerCase())}</h2>
        <ul class="talhoes">${ordenados.map((t) => {
          const v = m.valor(t);
          const cls = m.divergente ? (v < 0 ? 'perda' : 'ganho') : '';
          return `<li><a href="#talhao/${t.id}"><div><b>${esc(t.nome)}</b><br><small>${nf(t.area_ha)} ha, ${nf(t.sacas_ha)} sc/ha, saca a ${brl(t.custo_saca, 2)}</small></div>
            <span class="valor num ${cls}">${m.divergente ? brlSinal(v) : brl(v)}<small>/ha</small></span></a></li>`;
        }).join('')}</ul>
      </section>
    </div>`;
}

// ------------------------------------------------------------------ tela: detalhe do talhão
function barrasCategorias(porCategoria, divisor, mediaHa) {
  const linhas = Object.entries(porCategoria).map(([c, v]) => [c, v / divisor]);
  const maior = Math.max(...linhas.map(([c, v]) => Math.max(v, mediaHa?.[c] || 0)), 1);
  return `<ul class="barras">${linhas.map(([c, v]) => {
    const media = mediaHa?.[c];
    const alto = media && v > media * 1.3;
    return `<li><span>${esc(nomeCategoria(c))}</span>
      <i class="${alto ? 'alto' : ''}" style="width:${(100 * v) / maior}%"></i>
      <b>${brl(v)}${media != null ? `<span class="media">média ${brl(media)}</span>` : ''}</b></li>`;
  }).join('')}</ul>`;
}

async function renderTalhao(id) {
  if (!estado.painel) await carregarPainel();
  const t = estado.painel?.talhoes.find((x) => x.id === id);
  if (!t) { tela.innerHTML = '<p class="vazio">Talhão não encontrado. <a href="#painel">Voltar</a></p>'; return; }
  const fz = estado.painel.fazenda;
  let lancs = lembrado(`lanc-t${id}`) || [];
  try { lancs = await api(`/api/lancamentos?alvo_tipo=talhao&alvo_id=${id}&limite=200`); lembrar(`lanc-t${id}`, lancs); } catch { /* usa o guardado */ }
  const alertas = estado.painel.alertas.filter((a) => a.talhao_id === id);
  const prej = t.preco_medio != null && t.custo_saca > t.preco_medio;
  const topo = Math.max(t.custo_saca || 0, t.preco_medio || 0) * 1.2 || 1;
  const pos = (v) => `${(100 * v) / topo}%`;

  tela.innerHTML = `
    <a class="voltar" href="#painel">← Talhões</a>
    <h1>${esc(t.nome)}</h1><p class="suave">${nf(t.area_ha)} ha de arroz irrigado</p>
    <div class="kpis">
      <div class="kpi"><small>Custo</small><strong class="num">${brl(t.custo_ha)}</strong><small>por hectare (média ${brl(fz.custo_ha)})</small></div>
      <div class="kpi"><small>Produtividade</small><strong class="num">${nf(t.sacas_ha)} sc/ha</strong><small>${nf(t.sacas)} sacas</small></div>
      <div class="kpi"><small>Custo da saca</small><strong class="num ${prej ? 'perda' : ''}">${brl(t.custo_saca, 2)}</strong><small>vendida a ${brl(t.preco_medio, 2)}</small></div>
      <div class="kpi"><small>Margem</small><strong class="num ${t.margem < 0 ? 'perda' : 'ganho'}">${brlSinal(t.margem_ha)}</strong><small>por hectare</small></div>
    </div>
    ${alertas.length ? `<ul class="alertas">${alertas.map((a) => `<li>${esc(a.texto)}</li>`).join('')}</ul>` : ''}
    <div class="duas-col">
      <section>
        <h2>Para onde foi o dinheiro, por hectare</h2>
        ${barrasCategorias(t.por_categoria, t.area_ha, fz.media_categoria_ha)}
        <p class="suave" style="margin-top:.6rem;font-size:.88rem">Em vermelho: 30% ou mais acima da média da fazenda.</p>
      </section>
      <section>
        <h2>Custo da saca contra o preço de venda</h2>
        <div class="saca">
          <div class="linha">
            <span class="marco ${prej ? 'perda' : ''}" style="left:${pos(t.custo_saca)}">custo ${brl(t.custo_saca, 2)}</span>
            <span class="marco ganho" style="left:${pos(t.preco_medio || 0)};top:auto;bottom:-1.9rem;display:flex;flex-direction:column-reverse">preço ${brl(t.preco_medio, 2)}</span>
          </div>
          <p style="margin-top:2.4rem">${prej
            ? `Cada saca custou <b>${brl(t.custo_saca, 2)}</b> e foi vendida, em média, por <b>${brl(t.preco_medio, 2)}</b>: prejuízo de <b class="perda">${brl(t.custo_saca - t.preco_medio, 2)}</b> por saca.`
            : `Cada saca custou <b>${brl(t.custo_saca, 2)}</b> e foi vendida, em média, por <b>${brl(t.preco_medio, 2)}</b>: sobra de <b class="ganho">${brl(t.preco_medio - t.custo_saca, 2)}</b> por saca.`}</p>
        </div>
        <h2>Lançamentos do talhão</h2>
        <p class="suave" style="font-size:.88rem">Conta de luz da bomba e gastos gerais entram pelo rateio e aparecem só nos totais.</p>
        ${lancs.length ? `<ul class="lista">${lancs.map((l) => linhaLancamento(l, true)).join('')}</ul>` : '<p class="vazio">Nenhum lançamento direto neste talhão.</p>'}
      </section>
    </div>`;
}

// ------------------------------------------------------------------ tela: gado
async function renderGado() {
  if (!estado.painel) await carregarPainel();
  const p = estado.painel;
  if (!p) { tela.innerHTML = '<p class="vazio">Sem sinal e sem dados guardados.</p>'; return; }
  const blocos = await Promise.all(p.lotes.map(async (l) => {
    let lancs = lembrado(`lanc-l${l.id}`) || [];
    try { lancs = await api(`/api/lancamentos?alvo_tipo=lote&alvo_id=${l.id}&limite=100`); lembrar(`lanc-l${l.id}`, lancs); } catch { /* guardado */ }
    return `<section>
      <h2>Lote ${esc(l.nome)}</h2>
      <div class="kpis">
        <div class="kpi"><small>Cabeças</small><strong class="num">${nf(l.cabecas)}</strong><small>${l.cabecas_vendidas ? `${nf(l.cabecas_vendidas)} vendidas` : 'nenhuma venda'}</small></div>
        <div class="kpi"><small>Custo</small><strong class="num">${brl(l.custo_cabeca)}</strong><small>por cabeça</small></div>
        <div class="kpi"><small>Receita</small><strong class="num">${brl(l.receita)}</strong><small>no lote</small></div>
        <div class="kpi"><small>Resultado</small><strong class="num ${l.resultado < 0 ? 'perda' : 'ganho'}">${brlSinal(l.resultado_cabeca)}</strong><small>por cabeça</small></div>
      </div>
      <div class="duas-col">
        <div>${barrasCategorias(l.por_categoria, l.cabecas)}<p class="suave" style="margin-top:.5rem;font-size:.88rem">Custo por cabeça, por tipo de gasto.</p></div>
        <ul class="lista">${lancs.map((x) => linhaLancamento(x, true)).join('')}</ul>
      </div>
    </section>`;
  }));
  tela.innerHTML = `<div class="cabeca"><div><h1>Gado</h1><p>Custo e resultado de cada lote, por cabeça.</p></div></div>${blocos.join('')}`;
}

// ------------------------------------------------------------------ rotas e eventos
function rota() {
  const [nome, id] = (location.hash.slice(1) || 'painel').split('/');
  return { nome, id: id ? Number(id) : null };
}

async function render() {
  const r = rota();
  document.querySelectorAll('.nav a').forEach((a) => {
    const ativo = a.dataset.rota === r.nome || (r.nome === 'talhao' && a.dataset.rota === 'painel');
    a.toggleAttribute('aria-current', ativo);
    if (ativo) a.setAttribute('aria-current', 'page');
  });
  if (r.nome === 'registrar') await renderRegistrar();
  else if (r.nome === 'talhao') await renderTalhao(r.id);
  else if (r.nome === 'gado') await renderGado();
  else await renderPainel();
  window.scrollTo(0, 0);
}

let reconhecedor = null;
tela.addEventListener('click', async (e) => {
  const b = e.target.closest('[data-acao], [data-talhao]');
  if (!b) return;
  if (b.dataset.talhao) { location.hash = `talhao/${b.dataset.talhao}`; return; }
  const acao = b.dataset.acao;

  if (acao === 'foto') {
    const inp = $('#arquivo');
    inp.dataset.dica = b.dataset.dica;
    inp.value = '';
    inp.click();
  } else if (acao === 'focar-texto') {
    $('#texto').focus();
  } else if (acao === 'ler-texto') {
    const texto = $('#texto').value.trim();
    if (!texto) { avisar('Escreva o que aconteceu, por exemplo: passei 200 kg de ureia no talhão 3.'); return; }
    await filaPor({ id: novoId(), estado: 'aguardando', texto, criado_em: new Date().toISOString() });
    $('#texto').value = '';
    avisar(navigator.onLine ? 'Lendo…' : 'Guardado. Será lido quando tiver sinal.');
    await renderRegistrar();
    processarFila();
  } else if (acao === 'falar') {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (reconhecedor) { reconhecedor.stop(); return; }
    reconhecedor = new SR();
    reconhecedor.lang = 'pt-BR';
    reconhecedor.interimResults = false;
    b.setAttribute('aria-pressed', 'true');
    b.querySelector('span').textContent = 'Ouvindo…';
    reconhecedor.onresult = (ev) => {
      const t = Array.from(ev.results).map((r) => r[0].transcript).join(' ');
      const area = $('#texto');
      area.value = (area.value ? area.value + ' ' : '') + t;
    };
    reconhecedor.onerror = (ev) => avisar(ev.error === 'network' ? 'Para falar é preciso sinal. Escreva a frase.' : 'Não deu para ouvir. Tente de novo ou escreva.');
    reconhecedor.onend = () => { reconhecedor = null; b.setAttribute('aria-pressed', 'false'); b.querySelector('span').textContent = 'Falar'; };
    reconhecedor.start();
  } else if (acao === 'salvar') {
    b.disabled = true;
    await salvar(b.closest('.conf'));
  } else if (acao === 'descartar') {
    await filaTirar(b.closest('.conf').dataset.id);
    avisar('Descartado.');
    await atualizarSinal();
    renderRegistrar();
  } else if (acao === 'metrica') {
    estado.metrica = b.dataset.metrica;
    renderPainel();
  } else if (acao === 'apagar') {
    if (!b.dataset.armado) { b.dataset.armado = '1'; b.textContent = 'Toque de novo para apagar'; return; }
    try {
      await api(`/api/lancamentos/${b.dataset.lanc}`, { method: 'DELETE' });
      avisar('Lançamento apagado.');
      await Promise.all([carregarPainel(), carregarRecentes()]);
      render();
    } catch (err) {
      avisar(err.status ? err.message : 'Sem sinal: tente apagar quando tiver conexão.');
    }
  }
});

tela.addEventListener('keydown', (e) => {
  if ((e.key === 'Enter' || e.key === ' ') && e.target.dataset?.talhao) {
    e.preventDefault();
    location.hash = `talhao/${e.target.dataset.talhao}`;
  }
});

$('#arquivo').addEventListener('change', async (e) => {
  const arq = e.target.files?.[0];
  if (!arq) return;
  const foto = await comprimir(arq);
  await filaPor({ id: novoId(), estado: 'aguardando', foto, dica: e.target.dataset.dica, criado_em: new Date().toISOString() });
  avisar(navigator.onLine ? 'Foto recebida. Lendo…' : 'Foto guardada. Será lida quando tiver sinal.');
  if (rota().nome !== 'registrar') location.hash = 'registrar';
  else await renderRegistrar();
  processarFila();
});

window.addEventListener('hashchange', render);
window.addEventListener('online', () => { avisar('Sinal de volta. Enviando o que ficou guardado.'); processarFila(); carregarPainel(); });
window.addEventListener('offline', atualizarSinal);
setInterval(processarFila, 20000);

if ('serviceWorker' in navigator) navigator.serviceWorker.register('/sw.js').catch(() => { /* sem HTTPS: segue sem modo offline do app */ });

await Promise.all([carregarFazenda(), carregarPainel(), carregarRecentes()]);
await atualizarSinal();
await render();
processarFila();
