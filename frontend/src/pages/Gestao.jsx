import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api.js';
import { useConfig } from '../App.jsx';
import { SeloOrigem, SeloPrioridade, SeloStatus } from '../components/Selos.jsx';
import { comprimirImagem, formatarData, rotulo } from '../util.js';

function lerToken() {
  try {
    return sessionStorage.getItem('zc-token-gestao') ?? '';
  } catch {
    return '';
  }
}

function salvarToken(token) {
  try {
    if (token) sessionStorage.setItem('zc-token-gestao', token);
    else sessionStorage.removeItem('zc-token-gestao');
  } catch {
    /* navegador sem armazenamento: o token vale só nesta tela */
  }
}

export default function Gestao() {
  const config = useConfig();
  const [token, setToken] = useState(lerToken);
  const [rascunho, setRascunho] = useState('');
  const [itens, setItens] = useState(null);
  const [erro, setErro] = useState('');
  const [simulados, setSimulados] = useState(false);

  const carregar = (t = token) => {
    if (!t) return;
    setErro('');
    api.gestao
      .listar(t)
      .then(setItens)
      .catch((e) => {
        setErro(e.status === 401 ? 'Token inválido.' : e.message);
        if (e.status === 401) {
          setToken('');
          salvarToken('');
        }
      });
  };
  useEffect(() => carregar(), [token]); // eslint-disable-line react-hooks/exhaustive-deps

  if (!token) {
    return (
      <section>
        <h1>Gestão da organização</h1>
        <p>Área do condomínio, associação ou gestor do espaço: fila por prioridade e registro da solução.</p>
        <form
          className="formulario"
          onSubmit={(e) => {
            e.preventDefault();
            salvarToken(rascunho);
            setToken(rascunho);
          }}
        >
          <label htmlFor="token">Token de acesso</label>
          <input id="token" type="password" required autoComplete="off" value={rascunho} onChange={(e) => setRascunho(e.target.value)} />
          {erro && <p className="aviso aviso--erro" role="alert">{erro}</p>}
          <button type="submit" className="botao">Entrar</button>
        </form>
      </section>
    );
  }

  const visiveis = (itens ?? []).filter((o) => simulados || !o.simulado);

  return (
    <section>
      <h1>Gestão da organização</h1>
      <p>
        Fila ordenada por prioridade. Para marcar como resolvida, anexe a foto da solução.{' '}
        <button type="button" className="link" onClick={() => { salvarToken(''); setToken(''); }}>Sair</button>
      </p>
      <label className="caixa">
        <input type="checkbox" checked={simulados} onChange={(e) => setSimulados(e.target.checked)} />
        Mostrar dados simulados
      </label>
      {erro && <p className="aviso aviso--erro" role="alert">{erro}</p>}
      {!itens && <p className="carregando" role="status">Carregando fila…</p>}
      <ul className="lista">
        {visiveis.map((o) => (
          <li key={o.id} className="cartao">
            <div className="cartao__selos">
              <SeloStatus status={o.status} />
              <SeloPrioridade prioridade={o.prioridade} />
              <SeloOrigem ocorrencia={o} />
            </div>
            <h2 className="cartao__titulo">
              <Link to={`/ocorrencias/${o.id}`}>{rotulo(config.categorias, o.categoria)} · {o.protocolo}</Link>
            </h2>
            <p>{o.descricao}</p>
            <p className="discreto">{o.bairro} · {formatarData(o.criado_em)} · {o.confirmacoes} confirmação(ões)</p>
            {o.prioridade_motivo && <p className="discreto">Motivo da prioridade: {o.prioridade_motivo}</p>}
            {o.status !== 'resolvida' && <MudarStatus ocorrencia={o} token={token} aoMudar={() => carregar()} />}
          </li>
        ))}
      </ul>
    </section>
  );
}

function MudarStatus({ ocorrencia, token, aoMudar }) {
  const [status, setStatus] = useState('em_andamento');
  const [comentario, setComentario] = useState('');
  const [foto, setFoto] = useState(null);
  const [erro, setErro] = useState('');
  const [enviando, setEnviando] = useState(false);
  const idBase = `gestao-${ocorrencia.id}`;

  async function enviar(evento) {
    evento.preventDefault();
    setErro('');
    if (status === 'resolvida' && !foto) {
      setErro('Anexe a foto da solução para marcar como resolvida.');
      return;
    }
    const dados = new FormData();
    dados.append('status', status);
    if (comentario.trim()) dados.append('comentario', comentario.trim());
    if (foto) dados.append('foto', await comprimirImagem(foto), 'foto.jpg');
    setEnviando(true);
    try {
      await api.gestao.mudar(token, ocorrencia.id, dados);
      aoMudar();
    } catch (e) {
      setErro(e.message);
    } finally {
      setEnviando(false);
    }
  }

  return (
    <form className="formulario formulario--compacto" onSubmit={enviar}>
      <label htmlFor={`${idBase}-status`}>Novo status</label>
      <select id={`${idBase}-status`} value={status} onChange={(e) => setStatus(e.target.value)}>
        <option value="em_andamento">Em andamento</option>
        <option value="resolvida">Resolvida (com foto)</option>
      </select>
      <label htmlFor={`${idBase}-comentario`}>Comentário (opcional)</label>
      <input id={`${idBase}-comentario`} value={comentario} maxLength={500} onChange={(e) => setComentario(e.target.value)} />
      <label htmlFor={`${idBase}-foto`}>Foto da solução {status === 'resolvida' ? '(obrigatória)' : '(opcional)'}</label>
      <input id={`${idBase}-foto`} type="file" accept="image/*" onChange={(e) => setFoto(e.target.files?.[0] ?? null)} />
      {erro && <p className="aviso aviso--erro" role="alert">{erro}</p>}
      <button type="submit" className="botao" disabled={enviando}>{enviando ? 'Salvando…' : 'Salvar'}</button>
    </form>
  );
}
