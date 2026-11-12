import { useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { api } from '../api.js';

export default function Assistente() {
  const [params] = useSearchParams();
  const [pergunta, setPergunta] = useState(params.get('pergunta') ?? '');
  const contexto = params.get('contexto') ?? '';
  const categoria = params.get('categoria') ?? '';
  const [resposta, setResposta] = useState(null);
  const [erro, setErro] = useState('');
  const [enviando, setEnviando] = useState(false);

  async function enviar(evento) {
    evento.preventDefault();
    setErro('');
    setResposta(null);
    setEnviando(true);
    try {
      setResposta(await api.perguntar({ pergunta, contexto: contexto || null, categoria: categoria || null }));
    } catch (e) {
      setErro(e.message);
    } finally {
      setEnviando(false);
    }
  }

  return (
    <section>
      <h1>Assistente de orientação</h1>
      <p>
        Pergunte o que fazer diante de um problema na rua: quem acionar, como agir e regras de acessibilidade.
        As respostas vêm de documentos oficiais e mostram a fonte.
      </p>
      <p className="aviso">Em emergência, ligue 190 (Polícia Militar), 193 (Bombeiros) ou 199 (Defesa Civil).</p>
      <form className="formulario" onSubmit={enviar}>
        <label htmlFor="pergunta">Sua pergunta</label>
        <textarea
          id="pergunta"
          required
          minLength={3}
          maxLength={500}
          rows={3}
          value={pergunta}
          onChange={(e) => setPergunta(e.target.value)}
          placeholder="Ex.: Tem um poste apagado na minha rua. Quem eu aciono?"
        />
        {contexto && <p className="discreto">Contexto enviado junto: {contexto}</p>}
        <button type="submit" className="botao" disabled={enviando}>
          {enviando ? 'Consultando a base oficial…' : 'Perguntar'}
        </button>
        {enviando && <p className="discreto" role="status">Pode levar até 20 segundos.</p>}
      </form>

      <div aria-live="polite">
        {erro && <p className="aviso aviso--erro">{erro}</p>}
        {resposta && <Resposta resposta={resposta} />}
      </div>
    </section>
  );
}

function Fontes({ fontes }) {
  if (!fontes?.length) return null;
  return (
    <>
      <h3>Fontes</h3>
      <ul>
        {fontes.map((f, i) => (
          <li key={i}>
            {f.url ? <a href={f.url} target="_blank" rel="noreferrer noopener">{f.titulo}</a> : f.titulo}
            {f.orgao ? ` · ${f.orgao}` : ''}
          </li>
        ))}
      </ul>
    </>
  );
}

function Resposta({ resposta }) {
  if (!resposta.disponivel) {
    return (
      <section className="resposta">
        <p className="aviso">{resposta.mensagem}</p>
        {resposta.trechos?.length ? (
          <ul className="lista">
            {resposta.trechos.map((t, i) => (
              <li key={i} className="cartao">
                <p>{t.texto}</p>
                <p className="discreto">
                  {t.url ? <a href={t.url} target="_blank" rel="noreferrer noopener">{t.titulo}</a> : t.titulo}
                  {t.orgao ? ` · ${t.orgao}` : ''}
                </p>
              </li>
            ))}
          </ul>
        ) : (
          <p>Tente de novo mais tarde ou procure o SP156 da Prefeitura de São Paulo.</p>
        )}
      </section>
    );
  }
  return (
    <section className="resposta">
      <h2>Resposta</h2>
      {resposta.recusou ? (
        <p className="aviso">Não consta na base oficial do assistente. Para não inventar, ele não responde a esta pergunta.</p>
      ) : (
        <p className="resposta__texto">{resposta.resposta}</p>
      )}
      {resposta.risco && <p className="discreto">Risco estimado: {resposta.risco}</p>}
      <Fontes fontes={resposta.fontes} />
      <p className="discreto">Resposta gerada por IA a partir de documentos oficiais. Confira a fonte antes de agir.</p>
    </section>
  );
}
