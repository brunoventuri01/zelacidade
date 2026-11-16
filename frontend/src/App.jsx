import { createContext, useContext, useEffect, useState } from 'react';
import { NavLink, Route, Routes } from 'react-router-dom';
import { api } from './api.js';
import Assistente from './pages/Assistente.jsx';
import Detalhe from './pages/Detalhe.jsx';
import Gestao from './pages/Gestao.jsx';
import Inicio from './pages/Inicio.jsx';
import NaoEncontrada from './pages/NaoEncontrada.jsx';
import Painel from './pages/Painel.jsx';
import Privacidade from './pages/Privacidade.jsx';
import Registrar from './pages/Registrar.jsx';

const ConfigContexto = createContext(null);
export const useConfig = () => useContext(ConfigContexto);

const LINKS = [
  ['/', 'Mapa'],
  ['/registrar', 'Registrar'],
  ['/painel', 'Painel'],
  ['/assistente', 'Assistente'],
  ['/gestao', 'Gestão'],
];

export default function App() {
  const [config, setConfig] = useState(null);
  const [erro, setErro] = useState('');

  const carregar = () => {
    setErro('');
    api.config().then(setConfig).catch((e) => setErro(e.message));
  };
  useEffect(carregar, []);

  return (
    <>
      <a className="pular" href="#conteudo">Pular para o conteúdo</a>
      <header className="topo">
        <div className="topo__marca">
          <span className="topo__logo" aria-hidden="true">◉</span>
          <div>
            <p className="topo__nome">ZelaCidade</p>
            <p className="topo__lema">Cuidar da cidade começa por enxergar seus problemas.</p>
          </div>
        </div>
        <nav aria-label="Principal">
          <ul className="menu">
            {LINKS.map(([para, texto]) => (
              <li key={para}>
                <NavLink to={para} end={para === '/'}>{texto}</NavLink>
              </li>
            ))}
          </ul>
        </nav>
      </header>

      <main id="conteudo" tabIndex={-1}>
        {erro && (
          <div className="aviso aviso--erro" role="alert">
            <p>{erro}</p>
            <button type="button" onClick={carregar}>Tentar de novo</button>
          </div>
        )}
        {!config && !erro && <p className="carregando" role="status">Carregando…</p>}
        {config && (
          <ConfigContexto.Provider value={config}>
            {config.area.provisoria && (
              <p className="faixa">{config.area.nome}: bairros e limites ainda provisórios.</p>
            )}
            <Routes>
              <Route path="/" element={<Inicio />} />
              <Route path="/registrar" element={<Registrar />} />
              <Route path="/ocorrencias/:id" element={<Detalhe />} />
              <Route path="/painel" element={<Painel />} />
              <Route path="/assistente" element={<Assistente />} />
              <Route path="/gestao" element={<Gestao />} />
              <Route path="/privacidade" element={<Privacidade />} />
              <Route path="*" element={<NaoEncontrada />} />
            </Routes>
          </ConfigContexto.Provider>
        )}
      </main>

      <footer className="rodape">
        <p>
          Global Solution FIAP 2026.2 · Dados simulados aparecem com o selo “Simulado”. ·{' '}
          <NavLink to="/privacidade">Privacidade e LGPD</NavLink>
        </p>
      </footer>
    </>
  );
}
