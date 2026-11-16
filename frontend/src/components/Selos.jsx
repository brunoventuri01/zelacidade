import { useConfig } from '../App.jsx';
import { CORES_STATUS, rotulo } from '../util.js';

export function SeloStatus({ status }) {
  const config = useConfig();
  return (
    <span className="selo" style={{ '--cor': CORES_STATUS[status] ?? '#4b5563' }}>
      {rotulo(config.status, status)}
    </span>
  );
}

export function SeloPrioridade({ prioridade }) {
  const config = useConfig();
  if (!prioridade) return null;
  return <span className={`selo selo--prioridade selo--${prioridade}`}>Prioridade {rotulo(config.prioridades, prioridade).toLowerCase()}</span>;
}

export function SeloOrigem({ ocorrencia }) {
  if (ocorrencia.origem === 'robo') {
    return <span className="selo selo--neutro">{ocorrencia.simulado ? 'Robô · teste de bancada' : 'Robô Maker Lab'}</span>;
  }
  if (ocorrencia.simulado) return <span className="selo selo--neutro">Simulado</span>;
  return null;
}
