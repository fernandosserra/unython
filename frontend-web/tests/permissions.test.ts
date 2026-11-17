import { test } from 'node:test';
import assert from 'node:assert/strict';
import { availableTabs, hasPermission } from '../src/permissions.ts';
import type { OrganizacaoConfig, Usuario } from '../src/types/index.ts';

const user: Usuario = {
  id: 1, nome: 'Pessoa', email: 'pessoa@example.com', role: 'Operador', status: 'Ativo', permissoes: null,
};
const config = {} as OrganizacaoConfig;

test('acesso legado é limitado aos módulos operacionais', () => {
  assert.deepEqual(availableTabs(user, config), ['pdv', 'agendamentos', 'caixa', 'doacoes']);
  assert.equal(hasPermission(user, 'estoque'), false);
});

test('lista vazia nega todos os módulos e lista explícita libera apenas os correspondentes', () => {
  assert.deepEqual(availableTabs({ ...user, permissoes: [] }, config), []);
  assert.deepEqual(availableTabs({ ...user, permissoes: ['estoque', 'relatorios'] }, config), ['admin']);
  assert.deepEqual(availableTabs({ ...user, permissoes: ['atendimentos'] }, config), ['agendamentos', 'admin']);
});

test('flags desabilitam módulos operacionais e preservam configuração do administrador', () => {
  const disabled = { habilitar_pdv: false, habilitar_atendimentos: false, habilitar_doacoes: false } as OrganizacaoConfig;
  assert.deepEqual(availableTabs(user, disabled), ['caixa']);
  assert.deepEqual(availableTabs({ ...user, role: 'Administrador', permissoes: [] }, disabled), ['caixa', 'admin']);
  assert.deepEqual(availableTabs({ ...user, permissoes: ['atendimentos'] }, disabled), []);
});

test('usuário inativo não tem acesso', () => {
  assert.deepEqual(availableTabs({ ...user, status: 'Inativo', role: 'Administrador' }, config), []);
});
