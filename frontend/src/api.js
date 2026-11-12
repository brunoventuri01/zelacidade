import { idDispositivo } from './util.js';

const SEM_CONEXAO = 'Sem conexão com o servidor. Verifique a internet e tente de novo.';

async function pedir(url, opcoes = {}) {
  let resposta;
  try {
    resposta = await fetch(url, opcoes);
  } catch {
    throw new Error(SEM_CONEXAO);
  }
  const tipo = resposta.headers.get('content-type') ?? '';
  const corpo = tipo.includes('application/json') ? await resposta.json() : await resposta.text();
  if (!resposta.ok) {
    const detalhe = typeof corpo === 'object' ? corpo?.detail : null;
    const mensagem =
      typeof detalhe === 'string' ? detalhe : 'Não foi possível concluir. Confira os campos e tente de novo.';
    const erro = new Error(mensagem);
    erro.status = resposta.status;
    throw erro;
  }
  return corpo;
}

const json = (corpo) => ({
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(corpo),
});

export const api = {
  config: () => pedir('/api/v1/config'),
  listar: (params = {}) => pedir(`/api/v1/ocorrencias?${new URLSearchParams(params)}`),
  detalhe: (id) => pedir(`/api/v1/ocorrencias/${id}`),
  classificar: (foto) => {
    const dados = new FormData();
    dados.append('foto', foto);
    return pedir('/api/v1/ia/classificar', { method: 'POST', body: dados });
  },
  criar: (dados) => pedir('/api/v1/ocorrencias', { method: 'POST', body: dados }),
  confirmar: (id, dados) =>
    pedir(`/api/v1/ocorrencias/${id}/confirmacoes`, {
      method: 'POST',
      body: dados,
      headers: { 'X-Dispositivo': idDispositivo() },
    }),
  painel: () => pedir('/api/v1/painel'),
  perguntar: (corpo) => pedir('/api/v1/assistente', json(corpo)),
  gestao: {
    listar: (token) =>
      pedir('/api/v1/gestao/ocorrencias', { headers: { Authorization: `Bearer ${token}` } }),
    mudar: (token, id, dados) =>
      pedir(`/api/v1/gestao/ocorrencias/${id}`, {
        method: 'PATCH',
        body: dados,
        headers: { Authorization: `Bearer ${token}` },
      }),
  },
};

export const urlFoto = (id) => `/api/v1/fotos/${id}`;
