import { test } from 'node:test';
import assert from 'node:assert/strict';
import { addPermissions, availableTabs, hasPermission, permissionPresets } from '../src/permissions.ts';
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
  assert.deepEqual(availableTabs({ ...user, permissoes: ['estoque', 'relatorios'] }, config), ['estoque', 'admin']);
  assert.deepEqual(availableTabs({ ...user, permissoes: ['atendimentos'] }, config), ['agendamentos', 'admin']);
});

test('flags desabilitam módulos operacionais e preservam configuração do administrador', () => {
  const disabled = { habilitar_pdv: false, habilitar_atendimentos: false, habilitar_doacoes: false } as OrganizacaoConfig;
  assert.deepEqual(availableTabs(user, disabled), ['caixa']);
  assert.deepEqual(availableTabs({ ...user, role: 'Administrador', permissoes: [] }, disabled), ['caixa', 'estoque', 'admin']);
  assert.deepEqual(availableTabs({ ...user, permissoes: ['atendimentos'] }, disabled), []);
});

test('perfis podem ser combinados sem duplicar módulos', () => {
  const recepcao = permissionPresets.find((preset) => preset.label === 'Perfil Recepção')!;
  const lanchonete = permissionPresets.find((preset) => preset.label === 'Perfil Lanchonete / Caixa')!;
  const combined = addPermissions(recepcao.permissions, lanchonete.permissions);
  assert.deepEqual(combined, ['atendimentos', 'pdv', 'caixa']);
  assert.deepEqual(addPermissions(combined, lanchonete.permissions), combined);
  assert.deepEqual(availableTabs({ ...user, permissoes: ['estoque'] }, config), ['estoque', 'admin']);
});

test('usuário inativo não tem acesso', () => {
  assert.deepEqual(availableTabs({ ...user, status: 'Inativo', role: 'Administrador' }, config), []);
});
