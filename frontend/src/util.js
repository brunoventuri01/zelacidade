// Funções puras e utilitários do navegador usados pelas telas.

export const CORES_STATUS = {
  recebida: '#4b5563',
  triada: '#1d4ed8',
  duplicada: '#6b7280',
  precisa_info: '#b45309',
  em_andamento: '#6d28d9',
  resolvida: '#15803d',
};

export function rotulo(lista, valor) {
  return lista?.find((item) => item.valor === valor)?.rotulo ?? valor ?? '—';
}

const SEVERIDADES = { alta: 'alta', media: 'média', baixa: 'baixa' };

// Texto da severidade da visão; "nenhuma" (sem buraco) não é exibida.
export function textoSeveridade(severidade) {
  return SEVERIDADES[severidade] ?? '';
}

export function porcentagem(valor) {
  if (valor === null || valor === undefined || Number.isNaN(Number(valor))) return '—';
  return `${Math.round(Number(valor) * 100)}%`;
}

export function formatarData(iso) {
  if (!iso) return '—';
  return new Date(iso).toLocaleString('pt-BR', {
    dateStyle: 'short',
    timeStyle: 'short',
    timeZone: 'America/Sao_Paulo',
  });
}

export function filtrarOcorrencias(itens, filtros) {
  return itens.filter((o) => {
    if (filtros.status && o.status !== filtros.status) return false;
    if (filtros.categoria && o.categoria !== filtros.categoria) return false;
    if (filtros.bairro && o.bairro !== filtros.bairro) return false;
    if (!filtros.simulados && o.simulado) return false;
    return true;
  });
}

export function contarPor(itens, campo) {
  return itens.reduce((acc, item) => {
    acc[item[campo]] = (acc[item[campo]] ?? 0) + 1;
    return acc;
  }, {});
}

// Identificador aleatório do aparelho, usado só para contar uma confirmação por pessoa.
// No servidor ele vira um hash; nunca identifica quem é a pessoa.
export function idDispositivo() {
  const gerar = () =>
    globalThis.crypto?.randomUUID?.() ?? `${Date.now()}-${Math.random().toString(16).slice(2)}`;
  try {
    let id = localStorage.getItem('zc-dispositivo');
    if (!id) {
      id = gerar();
      localStorage.setItem('zc-dispositivo', id);
    }
    return id;
  } catch {
    return `sessao-${gerar()}`;
  }
}

// Reduz a foto no próprio celular antes do envio (menos dados em conexão fraca).
// Redesenhar no canvas também descarta o EXIF; o servidor remove de novo por garantia.
export async function comprimirImagem(arquivo, maxLado = 1280, qualidade = 0.82) {
  try {
    const bitmap = await createImageBitmap(arquivo, { imageOrientation: 'from-image' });
    const escala = Math.min(1, maxLado / Math.max(bitmap.width, bitmap.height));
    const canvas = document.createElement('canvas');
    canvas.width = Math.round(bitmap.width * escala);
    canvas.height = Math.round(bitmap.height * escala);
    canvas.getContext('2d').drawImage(bitmap, 0, 0, canvas.width, canvas.height);
    bitmap.close?.();
    const blob = await new Promise((resolver) => canvas.toBlob(resolver, 'image/jpeg', qualidade));
    return blob ? new File([blob], 'foto.jpg', { type: 'image/jpeg' }) : arquivo;
  } catch {
    return arquivo;
  }
}
