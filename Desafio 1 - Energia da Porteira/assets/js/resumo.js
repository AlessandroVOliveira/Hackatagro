/* Resumo compartilhável (feature 4).
 * Monta um cartão com o essencial — valor anual, volumes, melhores rotas e
 * situação do consórcio — para o produtor levar ao banco ou ao comprador, e
 * permite baixar como imagem (html2canvas) ou imprimir em PDF. Não inclui o
 * mapa: os blocos de mapa vêm de fora e quebrariam a imagem. */

'use strict';

function descricaoPerfil() {
  const area = num('area_arroz'), cab = num('cabecas');
  const manejoTxt = el('manejo').selectedOptions[0].text;
  const engenho = el('engenho').value === 'sim';
  const partes = [];
  if (area > 0) partes.push(`${n0(area)} ha de arroz${engenho ? ' com engenho próprio' : ''}`);
  if (cab > 0) partes.push(`${n0(cab)} cabeças (${manejoTxt.toLowerCase()})`);
  return partes.length ? partes.join(' · ') : 'propriedade sem resíduo declarado';
}

function gerarResumo() {
  const inv = estado.inv, rotas = estado.rotas || [];
  const viaveis = rotas.filter((x) => x.valor_anual > 0).sort((a, b) => b.valor_anual - a.valor_anual);
  const hoje = new Date().toLocaleDateString('pt-BR');

  const volumes = [];
  if (inv.palha_t > 0) volumes.push(`Palha ${ton(inv.palha_t)}/ano`);
  if (inv.casca_t > 0) volumes.push(`Casca ${ton(inv.casca_t)}/ano`);
  if (inv.esterco_t > 0) volumes.push(`Esterco ${ton(inv.esterco_t)}/ano`);

  const linhasRotas = viaveis.slice(0, 3).map((r) => `
    <tr>
      <td>${r.nome}</td>
      <td class="num">${brl(r.valor_anual)}/ano</td>
      <td class="num">${textoPayback(r.payback)}</td>
    </tr>`).join('');

  const valorTopo = viaveis.length ? brl(viaveis[0].valor_anual) : 'R$ 0';

  const c = estado.consorcio;
  const consorcioTxt = c
    ? (c.atingiu
        ? `No raio de ${c.raio} km, ${c.dentro} vizinhos + você somam ${n0(c.soma)} t/ano e atingem a escala de uma rota compartilhada.`
        : `No raio de ${c.raio} km, o grupo soma ${n0(c.soma)} t/ano; faltam ${n0(ESCALA.usina_t_ano - c.soma)} t/ano para a escala compartilhada.`)
    : '';

  el('resumo-card').innerHTML = `
    <div class="rc-top"><b>Energia da Porteira</b><span>${hoje}</span></div>
    <p class="rc-perfil">${descricaoPerfil()}</p>
    <p class="rc-rotulo">Seus resíduos podem render, por ano, até</p>
    <div class="rc-valor">${valorTopo}</div>
    ${volumes.length ? `<p class="rc-vol">${volumes.join(' · ')}</p>` : ''}
    ${viaveis.length
      ? `<table class="rc-tab"><thead><tr><th>Melhores rotas</th><th class="num">R$/ano</th><th class="num">Paga em</th></tr></thead><tbody>${linhasRotas}</tbody></table>`
      : '<p class="rc-vol">Nenhuma rota individual fecha sozinha. Veja o consórcio.</p>'}
    ${consorcioTxt ? `<p class="rc-cons">${consorcioTxt}</p>` : ''}
    <p class="rc-rodape">Valores de referência a validar com IRGA, Emater e compradores da região.<br>
      Fontes: Emater/RS (safra 2021/22), IRGA, Embrapa e estudo publicado na Redalyc.</p>`;

  el('resumo-saida').hidden = false;
  el('resumo-msg').textContent = '';
  el('resumo-saida').scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function baixarArquivo(blob, nome) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = nome;
  document.body.appendChild(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function baixarResumoImagem() {
  const card = el('resumo-card');
  const msg = el('resumo-msg');
  if (!card.innerHTML.trim()) { gerarResumo(); }
  if (typeof html2canvas === 'undefined') {
    msg.textContent = 'Geração de imagem indisponível offline. Use "Imprimir / PDF".';
    return;
  }
  msg.textContent = 'Gerando imagem…';
  html2canvas(card, { backgroundColor: '#ffffff', scale: 2 })
    .then((canvas) => canvas.toBlob((blob) => {
      baixarArquivo(blob, 'energia-da-porteira-resumo.png');
      msg.textContent = 'Imagem baixada.';
    }))
    .catch(() => { msg.textContent = 'Não foi possível gerar a imagem.'; });
}
