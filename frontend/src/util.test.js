import { describe, expect, it } from 'vitest';
import { contarPor, filtrarOcorrencias, porcentagem, rotulo } from './util.js';

const itens = [
  { id: 1, status: 'recebida', categoria: 'buraco', bairro: 'Santana', simulado: false },
  { id: 2, status: 'resolvida', categoria: 'buraco', bairro: 'Mandaqui', simulado: true },
  { id: 3, status: 'triada', categoria: 'iluminacao', bairro: 'Santana', simulado: true },
];

describe('filtrarOcorrencias', () => {
  it('aplica status, categoria e bairro', () => {
    const filtro = { status: '', categoria: 'buraco', bairro: 'Santana', simulados: true };
    expect(filtrarOcorrencias(itens, filtro).map((o) => o.id)).toEqual([1]);
  });

  it('esconde dados simulados quando pedido', () => {
    const filtro = { status: '', categoria: '', bairro: '', simulados: false };
    expect(filtrarOcorrencias(itens, filtro).map((o) => o.id)).toEqual([1]);
  });
});

describe('formatação', () => {
  it('porcentagem arredonda e trata vazio', () => {
    expect(porcentagem(0.874)).toBe('87%');
    expect(porcentagem(null)).toBe('—');
  });

  it('rotulo cai no valor quando não acha', () => {
    const lista = [{ valor: 'buraco', rotulo: 'Buraco na via' }];
    expect(rotulo(lista, 'buraco')).toBe('Buraco na via');
    expect(rotulo(lista, 'outro')).toBe('outro');
  });

  it('contarPor agrupa por campo', () => {
    expect(contarPor(itens, 'bairro')).toEqual({ Santana: 2, Mandaqui: 1 });
  });
});
