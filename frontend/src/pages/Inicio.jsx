import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api.js';
import { useConfig } from '../App.jsx';
import Mapa from '../components/Mapa.jsx';
import { SeloOrigem, SeloPrioridade, SeloStatus } from '../components/Selos.jsx';
import { filtrarOcorrencias, formatarData, rotulo } from '../util.js';

const FILTRO_INICIAL = { status: '', categoria: '', bairro: '', simulados: true };

export default function Inicio() {
  const config = useConfig();
  const [itens, setItens] = useState([]);
  const [erro, setErro] = useState('');
  const [carregando, setCarregando] = useState(true);
  const [filtros, setFiltros] = useState(FILTRO_INICIAL);

  useEffect(() => {
    api.listar()
      .then(setItens)
      .catch((e) => setErro(e.message))
      .finally(() => setCarregando(false));
  }, []);

  const visiveis = useMemo(() => filtrarOcorrencias(itens, filtros), [itens, filtros]);
  const mudar = (campo) => (e) =>
    setFiltros({ ...filtros, [campo]: e.target.type === 'checkbox' ? e.target.checked : e.target.value });

  return (
    <>
      <section className="destaque">
        <h1>Viu um problema na rua? Registre em 1 minuto.</h1>
        <p>
          Buracos, calçadas quebradas, postes apagados e obstáculos ficam no mapa até a solução, com a
          confirmação de quem mora por perto.
        </p>
        <Link className="botao botao--grande" to="/registrar">Registrar ocorrência</Link>
      </section>

      <section aria-labelledby="como-funciona" className="passos">
        <h2 id="como-funciona">Como funciona</h2>
        <ol>
          <li><strong>Registre.</strong> Tire uma foto, marque o local e descreva. A IA sugere a categoria e você confirma.</li>
          <li><strong>Acompanhe.</strong> Um robô faz a triagem e explica a prioridade. Vizinhos confirmam o problema.</li>
          <li><strong>Veja resolver.</strong> A organização responsável só marca como resolvido com foto da solução.</li>
        </ol>
      </section>

      <section aria-labelledby="titulo-mapa">
        <h2 id="titulo-mapa">Ocorrências em {config.area.cidade}</h2>
        <form className="filtros" onSubmit={(e) => e.preventDefault()} aria-label="Filtros">
          <label>
            Status
            <select value={filtros.status} onChange={mudar('status')}>
              <option value="">Todos</option>
              {config.status.map((s) => <option key={s.valor} value={s.valor}>{s.rotulo}</option>)}
            </select>
          </label>
          <label>
            Categoria
            <select value={filtros.categoria} onChange={mudar('categoria')}>
              <option value="">Todas</option>
              {config.categorias.map((c) => <option key={c.valor} value={c.valor}>{c.rotulo}</option>)}
            </select>
          </label>
          <label>
            Bairro
            <select value={filtros.bairro} onChange={mudar('bairro')}>
              <option value="">Todos</option>
              {config.area.bairros.map((b) => <option key={b} value={b}>{b}</option>)}
            </select>
          </label>
          <label className="caixa">
            <input type="checkbox" checked={filtros.simulados} onChange={mudar('simulados')} />
            Mostrar dados simulados
          </label>
        </form>

        {erro && <p className="aviso aviso--erro" role="alert">{erro}</p>}
        <p role="status" className="contagem">
          {carregando ? 'Carregando ocorrências…' : `${visiveis.length} ocorrência(s) exibida(s).`}
        </p>
        <Mapa itens={visiveis} rotuloAcessivel="Mapa das ocorrências. A mesma informação está na lista abaixo." />

        <h3>Lista</h3>
        {visiveis.length === 0 && !carregando ? (
          <p>Nenhuma ocorrência com esses filtros.</p>
        ) : (
          <ul className="lista">
            {visiveis.slice(0, 100).map((o) => (
              <li key={o.id} className="cartao">
                <div className="cartao__selos">
                  <SeloStatus status={o.status} />
                  <SeloPrioridade prioridade={o.prioridade} />
                  <SeloOrigem ocorrencia={o} />
                </div>
                <h4><Link to={`/ocorrencias/${o.id}`}>{rotulo(config.categorias, o.categoria)}</Link></h4>
                <p>{o.descricao}</p>
                <p className="discreto">
                  {o.bairro} · {formatarData(o.criado_em)} · {o.confirmacoes} confirmação(ões) · {o.protocolo}
                </p>
              </li>
            ))}
          </ul>
        )}
        {visiveis.length > 100 && <p className="discreto">Mostrando as 100 mais recentes. Use os filtros para ver outras.</p>}
      </section>
    </>
  );
}
