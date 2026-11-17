import { test } from 'node:test';
import assert from 'node:assert/strict';
import { proximoDaFila } from '../src/filaAtendimento.ts';
import type { Agendamento } from '../src/types/index.ts';

const item = (id: number, preferencial: boolean, ordem: number, status = 'Aguardando'): Agendamento => ({
  id, id_pessoa: id, id_evento: 1, data_hora: '2026-11-17T12:00:00',
  tipo_servico: 'Atendimento', status, compareceu: 'Pendente', preferencial, ordem_chegada: ordem,
});

test('prioriza a primeira pessoa preferencial aguardando, mesmo fora da ordem da lista', () => {
  const fila = [item(1, false, 1), item(2, true, 4), item(3, true, 2), item(4, true, 1, 'Chamado')];
  assert.equal(proximoDaFila(fila)?.id, 3);
});

test('chama a fila geral quando não há preferenciais aguardando', () => {
  const fila = [item(1, true, 1, 'Chamado'), item(2, false, 3), item(3, false, 2)];
  assert.equal(proximoDaFila(fila)?.id, 3);
});

test('não chama atendidos, ausentes ou pessoas já chamadas', () => {
  assert.equal(proximoDaFila([item(1, true, 1, 'Chamado'), item(2, false, 2, 'Atendido')]), undefined);
  assert.equal(proximoDaFila([]), undefined);
});

test('desempata ordem de chegada pela data e pelo identificador', () => {
  const primeiro = { ...item(2, false, 1), data_hora: '2026-11-17T11:00:00' };
  const mesmoHorario = { ...primeiro, id: 1 };
  assert.equal(proximoDaFila([item(3, false, 1), primeiro, mesmoHorario])?.id, 1);
});
