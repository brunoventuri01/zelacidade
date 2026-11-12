import { useEffect, useState } from 'react';
import { api } from '../api.js';
import { useConfig } from '../App.jsx';
import { formatarData, rotulo } from '../util.js';

// Nomes amigáveis para as colunas e KPIs da tabela Ouro (as desconhecidas aparecem como vêm).
const NOMES = {
  bairro: 'Bairro',
  categoria: 'Categoria',
  abertas: 'Abertas',
  resolvidas: 'Resolvidas',
  total: 'Total',
  confirmacoes: 'Confirmações',
  horas_media_triagem: 'Triagem média (h)',
  dias_media_resolucao: 'Resolução média (dias)',
  pct_resolvidas_com_evidencia: '% resolvidas com evidência',
  moradores_ativos: 'Moradores ativos',
};

function nome(chave) {
  return NOMES[chave] ?? chave.replace(/_/g, ' ');
}

function valor(chave, v, config) {
  if (v === null || v === undefined) return '—';
  if (chave === 'categoria') return rotulo(config.categorias, v);
  if (typeof v === 'number' && chave.startsWith('pct')) return `${Math.round(v * (v <= 1 ? 100 : 1))}%`;
  if (typeof v === 'number') return Number.isInteger(v) ? v.toLocaleString('pt-BR') : v.toLocaleString('pt-BR', { maximumFractionDigits: 1 });
  return String(v);
}

export default function Painel() {
  const config = useConfig();
  const [dados, setDados] = useState(null);
  const [erro, setErro] = useState('');

  useEffect(() => {
    api.painel().then(setDados).catch((e) => setErro(e.message));
  }, []);

  if (erro) return <p className="aviso aviso--erro" role="alert">{erro}</p>;
  if (!dados) return <p className="carregando" role="status">Carregando indicadores…</p>;

  const { ouro, ao_vivo: vivo } = dados;
  const colunas = ouro?.linhas?.length ? Object.keys(ouro.linhas[0]) : [];
  const maxCategoria = Math.max(1, ...Object.values(vivo.abertas_por_categoria));

  return (
    <section>
      <h1>Painel de indicadores</h1>

      <section aria-labelledby="ouro">
        <h2 id="ouro">Indicadores do lakehouse</h2>
        {ouro ? (
          <>
            <p className="discreto">
              Fonte: <code>{ouro.fonte}</code> · gerado em {formatarData(ouro.gerado_em)} · publicado no MVP em{' '}
              {formatarData(ouro.importado_em)}
            </p>
            {ouro.kpis && Object.keys(ouro.kpis).length > 0 && (
              <ul className="kpis">
                {Object.entries(ouro.kpis).map(([chave, v]) => (
                  <li key={chave}>
                    <span className="kpis__valor">{valor(chave, v, config)}</span>
                    <span className="kpis__nome">{nome(chave)}</span>
                  </li>
                ))}
              </ul>
            )}
            <div className="rolagem">
              <table>
                <caption>Ocorrências por bairro e categoria (tabela Ouro)</caption>
                <thead>
                  <tr>{colunas.map((c) => <th key={c} scope="col">{nome(c)}</th>)}</tr>
                </thead>
                <tbody>
                  {ouro.linhas.map((linha, i) => (
                    <tr key={i}>{colunas.map((c) => <td key={c}>{valor(c, linha[c], config)}</td>)}</tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        ) : (
          <p className="aviso">
            Ainda não há publicação da tabela Ouro. Quando o pipeline do Databricks rodar, o robô de integração
            publica os indicadores aqui.
          </p>
        )}
      </section>

      <section aria-labelledby="ao-vivo">
        <h2 id="ao-vivo">Contagem ao vivo no MVP</h2>
        <p className="discreto">
          {vivo.total} ocorrência(s) no total, das quais {vivo.simulados} simulada(s). Contagem direta do banco, sem
          tratamento do pipeline.
        </p>
        <h3>Abertas por categoria</h3>
        <ul className="barras">
          {Object.entries(vivo.abertas_por_categoria)
            .sort((a, b) => b[1] - a[1])
            .map(([cat, n]) => (
              <li key={cat}>
                <span className="barras__nome">{rotulo(config.categorias, cat)}</span>
                <span className="barras__trilho" aria-hidden="true">
                  <span className="barras__barra" style={{ width: `${(n / maxCategoria) * 100}%` }} />
                </span>
                <span className="barras__valor">{n}</span>
              </li>
            ))}
        </ul>
        <h3>Por status</h3>
        <table>
          <thead><tr><th scope="col">Status</th><th scope="col">Ocorrências</th></tr></thead>
          <tbody>
            {Object.entries(vivo.por_status).map(([s, n]) => (
              <tr key={s}><td>{rotulo(config.status, s)}</td><td>{n}</td></tr>
            ))}
          </tbody>
        </table>
      </section>
    </section>
  );
}
