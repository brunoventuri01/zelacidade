import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api.js';
import { useConfig } from '../App.jsx';
import Mapa from '../components/Mapa.jsx';
import { comprimirImagem, porcentagem, rotulo, textoSeveridade } from '../util.js';

export default function Registrar() {
  const config = useConfig();
  const [foto, setFoto] = useState(null);
  const [previa, setPrevia] = useState('');
  const [ia, setIa] = useState(null);
  const [analisando, setAnalisando] = useState(false);
  const [categoria, setCategoria] = useState('');
  const [categoriaTocada, setCategoriaTocada] = useState(false);
  const [ponto, setPonto] = useState(null);
  const [bairro, setBairro] = useState('');
  const [descricao, setDescricao] = useState('');
  const [email, setEmail] = useState('');
  const [consentimento, setConsentimento] = useState(false);
  const [aviso, setAviso] = useState('');
  const [erro, setErro] = useState('');
  const [enviando, setEnviando] = useState(false);
  const [criada, setCriada] = useState(null);

  useEffect(() => () => previa && URL.revokeObjectURL(previa), [previa]);

  async function escolherFoto(evento) {
    const arquivo = evento.target.files?.[0];
    setIa(null);
    if (!arquivo) {
      setFoto(null);
      setPrevia('');
      return;
    }
    const reduzida = await comprimirImagem(arquivo);
    setFoto(reduzida);
    setPrevia(URL.createObjectURL(reduzida));
    setAnalisando(true);
    try {
      const resultado = await api.classificar(reduzida);
      setIa(resultado);
      if (resultado.disponivel && resultado.categoria_sugerida && !categoriaTocada) {
        setCategoria(resultado.categoria_sugerida);
      }
    } catch (e) {
      setIa({ disponivel: false, motivo: e.message });
    } finally {
      setAnalisando(false);
    }
  }

  function usarMinhaLocalizacao() {
    setAviso('');
    if (!navigator.geolocation) {
      setAviso('Seu navegador não informa a localização. Toque no mapa para marcar o local.');
      return;
    }
    setAviso('Buscando sua localização…');
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setPonto({ latitude: pos.coords.latitude, longitude: pos.coords.longitude });
        setAviso('Local marcado pela sua localização. Ajuste tocando no mapa, se precisar.');
      },
      () => setAviso('Não foi possível obter a localização. Toque no mapa para marcar o local.'),
      { enableHighAccuracy: true, timeout: 10000 },
    );
  }

  async function enviar(evento) {
    evento.preventDefault();
    setErro('');
    if (!ponto) {
      setErro('Marque o local do problema no mapa ou use a sua localização.');
      return;
    }
    if (email && !consentimento) {
      setErro('Para receber avisos por e-mail, marque o consentimento.');
      return;
    }
    const dados = new FormData();
    dados.append('categoria', categoria);
    dados.append('descricao', descricao);
    dados.append('bairro', bairro);
    dados.append('latitude', String(ponto.latitude));
    dados.append('longitude', String(ponto.longitude));
    if (email) dados.append('email', email);
    dados.append('consentimento', consentimento ? 'true' : 'false');
    if (foto) dados.append('foto', foto, 'foto.jpg');
    setEnviando(true);
    try {
      setCriada(await api.criar(dados));
      window.scrollTo(0, 0);
    } catch (e) {
      setErro(e.message);
    } finally {
      setEnviando(false);
    }
  }

  if (criada) {
    return (
      <section className="sucesso" role="status">
        <h1>Ocorrência registrada</h1>
        <p>Guarde o protocolo <strong>{criada.protocolo}</strong>. Agora o robô de triagem analisa o registro.</p>
        <p>
          <Link className="botao" to={`/ocorrencias/${criada.id}`}>Acompanhar esta ocorrência</Link>{' '}
          <Link className="botao botao--secundario" to="/" >Voltar ao mapa</Link>
        </p>
      </section>
    );
  }

  return (
    <section>
      <h1>Registrar ocorrência</h1>
      <p>Leva cerca de 1 minuto. Não fotografe rostos nem placas de carro.</p>
      <form className="formulario" onSubmit={enviar} noValidate={false}>
        <fieldset>
          <legend>1. Foto do problema (recomendada)</legend>
          <label htmlFor="foto">Escolha ou tire uma foto</label>
          <input id="foto" type="file" accept="image/*" capture="environment" onChange={escolherFoto} />
          {previa && <img className="previa" src={previa} alt="Prévia da foto escolhida" />}
          <div aria-live="polite">
            {analisando && <p className="discreto">Analisando a foto…</p>}
            {ia && !analisando && <SugestaoIa ia={ia} config={config} />}
          </div>
        </fieldset>

        <fieldset>
          <legend>2. Que problema é?</legend>
          <label htmlFor="categoria">Categoria</label>
          <select
            id="categoria"
            required
            value={categoria}
            onChange={(e) => {
              setCategoria(e.target.value);
              setCategoriaTocada(true);
            }}
          >
            <option value="">Escolha a categoria</option>
            {config.categorias.map((c) => <option key={c.valor} value={c.valor}>{c.rotulo}</option>)}
          </select>
          <label htmlFor="descricao">Descrição</label>
          <textarea
            id="descricao"
            required
            minLength={3}
            maxLength={1000}
            rows={4}
            value={descricao}
            onChange={(e) => setDescricao(e.target.value)}
            placeholder="Ex.: buraco grande perto da faixa de pedestres, em frente ao número 120"
            aria-describedby="descricao-ajuda"
          />
          <p id="descricao-ajuda" className="discreto">{descricao.length}/1000 caracteres</p>
        </fieldset>

        <fieldset>
          <legend>3. Onde fica?</legend>
          <button type="button" className="botao botao--secundario" onClick={usarMinhaLocalizacao}>
            Usar minha localização
          </button>
          <p className="discreto" aria-live="polite">{aviso || 'Ou toque no mapa para marcar o local.'}</p>
          <Mapa ponto={ponto} aoClicar={setPonto} altura={300} rotuloAcessivel="Mapa para marcar o local do problema" />
          <p className="discreto">
            {ponto ? `Local marcado: ${ponto.latitude.toFixed(5)}, ${ponto.longitude.toFixed(5)}` : 'Nenhum local marcado ainda.'}
          </p>
          <label htmlFor="bairro">Bairro</label>
          <select id="bairro" required value={bairro} onChange={(e) => setBairro(e.target.value)}>
            <option value="">Escolha o bairro</option>
            {config.area.bairros.map((b) => <option key={b} value={b}>{b}</option>)}
          </select>
        </fieldset>

        <fieldset>
          <legend>4. Quer receber avisos? (opcional)</legend>
          <label htmlFor="email">E-mail</label>
          <input id="email" type="email" autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} />
          <label className="caixa">
            <input type="checkbox" checked={consentimento} onChange={(e) => setConsentimento(e.target.checked)} />
            Aceito receber avisos sobre esta ocorrência. O e-mail não aparece para ninguém.
          </label>
          <p className="discreto">
            Veja o que coletamos e por quê em <Link to="/privacidade">Privacidade</Link>.
          </p>
        </fieldset>

        {erro && <p className="aviso aviso--erro" role="alert">{erro}</p>}
        <button type="submit" className="botao botao--grande" disabled={enviando}>
          {enviando ? 'Enviando…' : 'Enviar ocorrência'}
        </button>
      </form>
    </section>
  );
}

function SugestaoIa({ ia, config }) {
  if (!ia.disponivel) {
    return <p className="aviso">{ia.motivo ?? 'Análise automática indisponível.'} Escolha a categoria abaixo.</p>;
  }
  if (!ia.categoria_sugerida) {
    return <p className="aviso">A IA não encontrou buraco nesta foto. Escolha a categoria abaixo.</p>;
  }
  return (
    <p className="aviso aviso--ia">
      A IA sugere <strong>{rotulo(config.categorias, ia.categoria_sugerida)}</strong> com{' '}
      {porcentagem(ia.confianca)} de confiança
      {textoSeveridade(ia.severidade) ? `, severidade ${textoSeveridade(ia.severidade)}` : ''}. Confira e confirme a categoria abaixo: quem decide é você.
    </p>
  );
}
