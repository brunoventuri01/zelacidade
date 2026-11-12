import { useCallback, useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { api, urlFoto } from '../api.js';
import { useConfig } from '../App.jsx';
import Mapa from '../components/Mapa.jsx';
import { SeloOrigem, SeloPrioridade, SeloStatus } from '../components/Selos.jsx';
import { comprimirImagem, formatarData, porcentagem, rotulo } from '../util.js';

const ATORES = {
  morador: 'Morador',
  ia: 'IA de visão',
  robo_rpa: 'Robô de triagem',
  robo_maker: 'Robô Maker Lab',
  gestor: 'Organização responsável',
  sistema: 'Sistema',
};
const TIPOS_FOTO = { registro: 'Foto do registro', evidencia: 'Foto enviada por vizinho', resolucao: 'Foto da solução' };

export default function Detalhe() {
  const { id } = useParams();
  const config = useConfig();
  const [o, setO] = useState(null);
  const [erro, setErro] = useState('');

  const carregar = useCallback(() => {
    api.detalhe(id).then(setO).catch((e) => setErro(e.message));
  }, [id]);
  useEffect(carregar, [carregar]);

  if (erro) return <p className="aviso aviso--erro" role="alert">{erro}</p>;
  if (!o) return <p className="carregando" role="status">Carregando ocorrência…</p>;

  const categoria = rotulo(config.categorias, o.categoria);
  const contexto = [categoria, o.severidade_ia ? `severidade ${o.severidade_ia}` : null].filter(Boolean).join(', ');
  const perguntaPadrao = `O que fazer com: ${categoria.toLowerCase()}?`;
  const consulta = new URLSearchParams();
  consulta.set('pergunta', perguntaPadrao);
  consulta.set('contexto', contexto);
  consulta.set('categoria', o.categoria);
  const linkAssistente = '/assistente?' + consulta.toString();
  const recebeConfirmacao = !['resolvida', 'duplicada'].includes(o.status);

  return (
    <article className="detalhe">
      <p><Link to="/">← Voltar ao mapa</Link></p>
      <div className="cartao__selos">
        <SeloStatus status={o.status} />
        <SeloPrioridade prioridade={o.prioridade} />
        <SeloOrigem ocorrencia={o} />
      </div>
      <h1>{categoria}</h1>
      <p className="discreto">Protocolo {o.protocolo} · registrada em {formatarData(o.criado_em)} · {o.bairro}</p>

      <div className="detalhe__grade">
        <div>
          {o.foto_id ? (
            <img className="foto" src={urlFoto(o.foto_id)} alt={`Foto do registro: ${categoria}`} />
          ) : (
            <p className="discreto">Registro sem foto.</p>
          )}
          <p>{o.descricao}</p>
          <dl className="dados">
            <dt>Sugestão da IA</dt>
            <dd>
              {o.categoria_ia
                ? `${rotulo(config.categorias, o.categoria_ia)} (${porcentagem(o.confianca_ia)}${o.severidade_ia ? `, severidade ${o.severidade_ia}` : ''})`
                : 'Sem sugestão automática'}
            </dd>
            <dt>Categoria confirmada</dt>
            <dd>{categoria}</dd>
            {o.prioridade_motivo && (
              <>
                <dt>Por que esta prioridade</dt>
                <dd>{o.prioridade_motivo}</dd>
              </>
            )}
            {o.duplicada_de && (
              <>
                <dt>Registro original</dt>
                <dd><Link to={`/ocorrencias/${o.duplicada_de}`}>{o.duplicada_de_protocolo}</Link></dd>
              </>
            )}
            <dt>Confirmações</dt>
            <dd>{o.confirmacoes}</dd>
            {o.local_aproximado && (
              <>
                <dt>Local</dt>
                <dd>Aproximado (centro da área piloto)</dd>
              </>
            )}
          </dl>
          <p><Link className="botao botao--secundario" to={linkAssistente}>Perguntar ao assistente o que fazer</Link></p>
        </div>
        <Mapa itens={[o]} centro={[o.latitude, o.longitude]} zoom={16} altura={280} rotuloAcessivel="Local da ocorrência" />
      </div>

      <section aria-labelledby="linha-do-tempo">
        <h2 id="linha-do-tempo">Linha do tempo</h2>
        <ol className="linha-do-tempo">
          {o.eventos.map((e, i) => (
            <li key={i}>
              <p className="discreto">{formatarData(e.criado_em)} · {ATORES[e.ator] ?? e.ator}</p>
              <p>{e.descricao}</p>
            </li>
          ))}
        </ol>
      </section>

      {o.fotos.length > 1 && (
        <section aria-labelledby="fotos">
          <h2 id="fotos">Fotos</h2>
          <ul className="galeria">
            {o.fotos.map((f) => (
              <li key={f.id}>
                <img src={urlFoto(f.id)} alt={TIPOS_FOTO[f.tipo] ?? 'Foto'} loading="lazy" />
                <p className="discreto">{TIPOS_FOTO[f.tipo] ?? f.tipo}</p>
              </li>
            ))}
          </ul>
        </section>
      )}

      {o.comentarios.length > 0 && (
        <section aria-labelledby="comentarios">
          <h2 id="comentarios">O que os vizinhos disseram</h2>
          <ul className="lista">
            {o.comentarios.map((c, i) => (
              <li key={i} className="cartao">
                {c.comentario && <p>{c.comentario}</p>}
                <p className="discreto">{formatarData(c.criado_em)}{c.foto_id ? ' · com foto' : ''}</p>
              </li>
            ))}
          </ul>
        </section>
      )}

      {recebeConfirmacao && <Confirmar id={o.id} aoConfirmar={carregar} />}
    </article>
  );
}

function Confirmar({ id, aoConfirmar }) {
  const [comentario, setComentario] = useState('');
  const [foto, setFoto] = useState(null);
  const [mensagem, setMensagem] = useState('');
  const [erro, setErro] = useState('');
  const [enviando, setEnviando] = useState(false);

  async function enviar(evento) {
    evento.preventDefault();
    setErro('');
    setMensagem('');
    const dados = new FormData();
    if (comentario.trim()) dados.append('comentario', comentario.trim());
    if (foto) dados.append('foto', await comprimirImagem(foto), 'foto.jpg');
    setEnviando(true);
    try {
      await api.confirmar(id, dados);
      setMensagem('Obrigado! Sua confirmação foi registrada.');
      setComentario('');
      setFoto(null);
      aoConfirmar();
    } catch (e) {
      setErro(e.message);
    } finally {
      setEnviando(false);
    }
  }

  return (
    <section aria-labelledby="confirmar" className="confirmar">
      <h2 id="confirmar">Você também viu este problema?</h2>
      <form className="formulario" onSubmit={enviar}>
        <label htmlFor="comentario">Comentário (opcional)</label>
        <textarea id="comentario" rows={2} maxLength={500} value={comentario} onChange={(e) => setComentario(e.target.value)} />
        <label htmlFor="foto-evidencia">Foto (opcional)</label>
        <input id="foto-evidencia" type="file" accept="image/*" onChange={(e) => setFoto(e.target.files?.[0] ?? null)} />
        <div aria-live="polite">
          {mensagem && <p className="aviso aviso--ok">{mensagem}</p>}
          {erro && <p className="aviso aviso--erro">{erro}</p>}
        </div>
        <button type="submit" className="botao" disabled={enviando}>{enviando ? 'Enviando…' : 'Eu também vi'}</button>
      </form>
    </section>
  );
}
