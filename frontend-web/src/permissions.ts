import type { OrganizacaoConfig, Usuario } from './types';

export type Permissao = 'pdv' | 'caixa' | 'atendimentos' | 'doacoes' | 'estoque' | 'relatorios' | 'eventos';
export type AppTab = 'pdv' | 'agendamentos' | 'caixa' | 'admin' | 'doacoes';

export const permissionGroups: { title: string; items: { id: Permissao; label: string }[] }[] = [
  { title: 'Operação', items: [{ id: 'pdv', label: 'PDV / Vendas' }, { id: 'eventos', label: 'Eventos' }] },
  { title: 'Pessoas', items: [{ id: 'atendimentos', label: 'Atendimentos' }] },
  { title: 'Logística', items: [{ id: 'estoque', label: 'Estoque e catálogo' }] },
  { title: 'Financeiro', items: [{ id: 'caixa', label: 'Caixa' }, { id: 'doacoes', label: 'Doações' }, { id: 'relatorios', label: 'Relatórios' }] },
];

export const legacyPermissions: Permissao[] = ['pdv', 'caixa', 'atendimentos', 'doacoes'];

export function hasPermission(user: Usuario | null, permission: Permissao): boolean {
  if (!user || user.status !== 'Ativo') return false;
  return user.role === 'Administrador' || (user.permissoes ?? legacyPermissions).includes(permission);
}

type ModuleConfig = OrganizacaoConfig & {
  habilitar_pdv?: boolean;
  habilitar_atendimentos?: boolean;
  habilitar_doacoes?: boolean;
};

export function availableTabs(user: Usuario | null, config: OrganizacaoConfig): AppTab[] {
  const flags: ModuleConfig = config;
  const tabs: AppTab[] = [];
  if (flags.habilitar_pdv !== false && hasPermission(user, 'pdv')) tabs.push('pdv');
  if (flags.habilitar_atendimentos !== false && hasPermission(user, 'atendimentos')) tabs.push('agendamentos');
  if (hasPermission(user, 'caixa')) tabs.push('caixa');
  if (flags.habilitar_doacoes !== false && hasPermission(user, 'doacoes')) tabs.push('doacoes');
  if (user?.role === 'Administrador' && user.status === 'Ativo' ||
      hasPermission(user, 'estoque') || hasPermission(user, 'relatorios') ||
      hasPermission(user, 'eventos') ||
      (flags.habilitar_atendimentos !== false && user?.permissoes != null && hasPermission(user, 'atendimentos'))) tabs.push('admin');
  return tabs;
}
