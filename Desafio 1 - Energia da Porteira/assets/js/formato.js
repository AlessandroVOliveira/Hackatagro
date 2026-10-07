/* Energia da Porteira — formatação pt-BR e atalhos de DOM.
 * Usado por todas as camadas; carregado antes delas. */

'use strict';

const fmt0 = new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 0 });
const fmtT = new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 1 });
const fmtPay = new Intl.NumberFormat('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 1 });

function brl(v, casas = 0) {
  return 'R$ ' + new Intl.NumberFormat('pt-BR', { minimumFractionDigits: casas, maximumFractionDigits: casas }).format(v);
}
const n0 = (v) => fmt0.format(Math.round(v));
const ton = (v) => fmtT.format(v) + ' t';
const pct = (f) => fmt0.format(f * 100) + '%';
const cap = (s) => s.charAt(0).toUpperCase() + s.slice(1);

const el = (id) => document.getElementById(id);
const num = (id) => { const v = parseFloat(el(id).value); return isNaN(v) ? 0 : v; };
