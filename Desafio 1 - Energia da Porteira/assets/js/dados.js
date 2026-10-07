/* Energia da Porteira — dados do protótipo.
 *
 * TODOS os coeficientes abaixo são REFERÊNCIAS da literatura (Embrapa, IRGA,
 * manuais de biodigestão). Servem para a demonstração e precisam ser validados
 * com IRGA/Emater e com compradores da região. Cada parâmetro que aparece na
 * tela traz faixa (mín / méd / máx), unidade e fonte — é o que o pitch mostra
 * para tratar o risco de "coeficiente impreciso".
 *
 * Os dados ficam aqui como constantes (e não num .json carregado por fetch) de
 * propósito: assim a página abre com um duplo-clique, sem servidor e sem erro
 * de CORS no navegador.
 */

/* Faixa com fonte: `med` é o valor usado nas contas; `min`/`max` aparecem como
 * faixa; a pessoa pode editar o valor nas "premissas" de cada seção. */
function faixa(min, med, max, unid, fonte) {
  return { min, med, max, unid, fonte };
}

const COEFICIENTES = {
  arroz: {
    produtividade: faixa(7.0, 8.5, 10.0, "t/ha", "Produtividade média do arroz irrigado no RS (IRGA)."),
    casca_fracao: faixa(0.18, 0.20, 0.22, "t casca / t arroz", "Casca ≈ 20% do peso do grão colhido (desafio; Embrapa)."),
    palha_grao: faixa(0.75, 1.0, 1.5, "t palha / t grão", "Relação palha/grão do arroz (literatura)."),
    palha_recolhivel: faixa(0.30, 0.40, 0.50, "fração", "Parte da palha que dá para recolher sem tirar a cobertura do solo."),
  },

  energia: {
    pci_casca: faixa(3.6, 3.75, 4.4, "kWh/kg", "Poder calorífico da casca de arroz (~13,5 MJ/kg)."),
    pci_palha: faixa(3.3, 3.5, 3.9, "kWh/kg", "Poder calorífico da palha de arroz (~12,6 MJ/kg)."),
    secagem_por_t_grao: faixa(70, 110, 150, "kWh térmicos / t de grão", "Energia térmica para secar o grão (remoção de umidade)."),
  },

  esterco: {
    kg_cab_dia: faixa(8, 10, 12, "kg/cabeça/dia", "Esterco fresco por bovino (Embrapa)."),
    // Fração do esterco que dá para recolher — depende do manejo.
    recolhivel: {
      extensivo: faixa(0.02, 0.05, 0.10, "fração", "Pasto aberto: esterco espalhado, quase nada recolhível."),
      semiconfinado: faixa(0.20, 0.30, 0.45, "fração", "Mangueira / semiconfinamento: parte do dia concentrado."),
      confinamento: faixa(0.60, 0.70, 0.85, "fração", "Confinamento ou leite: esterco concentrado e recolhível."),
    },
    biogas_por_t: faixa(20, 30, 40, "m³ biogás / t esterco", "Rendimento de biogás do esterco bovino."),
    biogas_kwh_m3: faixa(5.5, 6.0, 6.5, "kWh/m³", "Energia do biogás (~60% metano, ~21,5 MJ/m³)."),
    biogas_kwh_m3_eletrico: faixa(1.7, 2.0, 2.3, "kWh elétricos / m³", "Biogás vira eletricidade num motogerador (~33%)."),
  },
};

const PRECOS = {
  energia_irrigacao: faixa(800, 1124, 1500, "R$/ha por safra", "Custo de energia da irrigação (desafio: R$ 1.124/ha)."),
  tarifa_energia: faixa(0.45, 0.60, 0.80, "R$/kWh", "Tarifa de energia elétrica rural/irrigação."),
  energia_termica: faixa(0.15, 0.25, 0.35, "R$/kWh", "Custo do calor que a biomassa substitui (lenha/GLP na secagem)."),
  casca: faixa(30, 50, 90, "R$/t", "Preço de venda da casca de arroz (cerâmicas, termelétricas)."),
  palha: faixa(40, 70, 120, "R$/t", "Preço de venda da palha enfardada (cama, forragem, indústria)."),
  briquete: faixa(400, 550, 750, "R$/t", "Preço de venda do briquete/pellet de biomassa."),
};

const CUSTOS_OP = {
  venda: faixa(10, 25, 60, "R$/t", "Manuseio, carregamento e frete do resíduo até o comprador."),
  briquete: faixa(200, 380, 480, "R$/t produzida", "Energia, mão de obra e manutenção da briquetagem."),
  secagem: faixa(10, 30, 60, "R$/t de biomassa", "Operação da fornalha/secador a biomassa."),
  biodigestor_frac: faixa(0.10, 0.15, 0.25, "fração da economia", "Operação e manutenção do biodigestor."),
};

const INVESTIMENTOS = {
  enfardadeira: faixa(40000, 90000, 150000, "R$", "Enfardadeira para recolher e enfardar a palha."),
  briquetadeira: faixa(80000, 180000, 300000, "R$", "Linha de briquetagem de pequeno/médio porte."),
  biodigestor: faixa(40000, 130000, 260000, "R$", "Biodigestor + motogerador no porte de uma propriedade."),
  secador: faixa(20000, 60000, 120000, "R$", "Fornalha/secador a biomassa."),
};

const RENDIMENTOS = {
  briquete: faixa(0.85, 0.90, 0.95, "t briquete / t resíduo", "Massa de briquete por tonelada de resíduo seco."),
};

/* Escalas mínimas que o consórcio precisa atingir (camada 3). */
const ESCALA = {
  caminhao_t: 28, // caminhão cheio para venda conjunta de resíduo (t/ano, por viagem típica)
  usina_t_ano: 5000, // biomassa/ano para uma rota coletiva (usina ou briquetagem compartilhada)
  raio_padrao_km: 20,
};

/* Alegrete/RS — centro aproximado da cidade. */
const ALEGRETE = { lat: -29.7833, lng: -55.7919 };

/* ~12 propriedades FICTÍCIAS na região de Alegrete, cada uma declarando quanto
 * resíduo gera por ano. Servem só para demonstrar o mapa do consórcio; no piloto
 * viram cadastros reais. Volume em toneladas de resíduo/ano (palha + casca +
 * esterco recolhível, já somados para simplificar o mapa). */
const PROPRIEDADES = [
  { nome: "Estância Santa Rita", tipo: "Orizicultor", lat: -29.712, lng: -55.861, residuo_t_ano: 1020 },
  { nome: "Fazenda Butiá", tipo: "Pecuarista (confinamento)", lat: -29.845, lng: -55.705, residuo_t_ano: 1280 },
  { nome: "Estância do Ibirapuitã", tipo: "Orizicultor + engenho", lat: -29.690, lng: -55.740, residuo_t_ano: 1870 },
  { nome: "Sítio Passo Novo", tipo: "Misto", lat: -29.905, lng: -55.838, residuo_t_ano: 640 },
  { nome: "Fazenda Inhanduí", tipo: "Orizicultor", lat: -29.770, lng: -55.930, residuo_t_ano: 880 },
  { nome: "Estância Caverá", tipo: "Pecuarista (mangueira)", lat: -29.980, lng: -55.700, residuo_t_ano: 410 },
  { nome: "Fazenda Jacaquá", tipo: "Orizicultor", lat: -29.640, lng: -55.930, residuo_t_ano: 1190 },
  { nome: "Estância Guará", tipo: "Misto", lat: -29.820, lng: -55.985, residuo_t_ano: 720 },
  { nome: "Fazenda Rincão dos Mellos", tipo: "Pecuarista (leite)", lat: -29.735, lng: -55.640, residuo_t_ano: 530 },
  { nome: "Estância Uruguai", tipo: "Orizicultor + engenho", lat: -29.880, lng: -55.930, residuo_t_ano: 2040 },
  { nome: "Sítio Vacacaí", tipo: "Orizicultor", lat: -29.700, lng: -55.690, residuo_t_ano: 760 },
  { nome: "Fazenda Capivari", tipo: "Misto", lat: -29.955, lng: -55.860, residuo_t_ano: 690 },
];
