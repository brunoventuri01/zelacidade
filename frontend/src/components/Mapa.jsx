import { CircleMarker, MapContainer, Popup, Rectangle, TileLayer, useMapEvents } from 'react-leaflet';
import { Link } from 'react-router-dom';
import { useConfig } from '../App.jsx';
import { CORES_STATUS, rotulo } from '../util.js';

function CliqueNoMapa({ aoClicar }) {
  useMapEvents({
    click(evento) {
      aoClicar?.({ latitude: evento.latlng.lat, longitude: evento.latlng.lng });
    },
  });
  return null;
}

export default function Mapa({ itens = [], ponto, aoClicar, centro, zoom, rotuloAcessivel, altura = 380 }) {
  const config = useConfig();
  const { area } = config;
  const inicio = centro ?? [area.centro.latitude, area.centro.longitude];
  const limites = [
    [area.limites.sul, area.limites.oeste],
    [area.limites.norte, area.limites.leste],
  ];

  return (
    <div className="mapa" style={{ height: altura }} role="region" aria-label={rotuloAcessivel ?? 'Mapa'}>
      <MapContainer center={inicio} zoom={zoom ?? area.zoom} scrollWheelZoom={false} style={{ height: '100%' }}>
        <TileLayer
          attribution='&copy; colaboradores do <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <Rectangle bounds={limites} pathOptions={{ color: '#0b5cad', weight: 1, fillOpacity: 0.03, dashArray: '4 4' }} />
        {itens.map((o) => (
          <CircleMarker
            key={o.id}
            center={[o.latitude, o.longitude]}
            radius={8}
            pathOptions={{ color: '#ffffff', weight: 2, fillColor: CORES_STATUS[o.status], fillOpacity: o.simulado ? 0.55 : 0.95 }}
          >
            <Popup>
              <strong>{rotulo(config.categorias, o.categoria)}</strong>
              <br />
              {rotulo(config.status, o.status)} · {o.protocolo}
              <br />
              <Link to={`/ocorrencias/${o.id}`}>Ver detalhes</Link>
            </Popup>
          </CircleMarker>
        ))}
        {ponto && (
          <CircleMarker
            center={[ponto.latitude, ponto.longitude]}
            radius={10}
            pathOptions={{ color: '#111827', weight: 3, fillColor: '#facc15', fillOpacity: 1 }}
          />
        )}
        {aoClicar && <CliqueNoMapa aoClicar={aoClicar} />}
      </MapContainer>
    </div>
  );
}
