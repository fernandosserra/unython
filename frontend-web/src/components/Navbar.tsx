import React, { useState } from 'react';
import {
  ShoppingBag, Users, Wallet, Settings, LogOut, HeartHandshake,
  Smartphone, KeyRound, MoreHorizontal,
} from 'lucide-react';
import { useAuthStore } from '../store/useAuthStore';
import { useOrgStore } from '../store/useOrgStore';
import type { Evento, MovimentoCaixa } from '../types';
import { ChangePasswordModal } from './ChangePasswordModal';
import { availableTabs, type AppTab } from '../permissions';

interface NavbarProps {
  currentTab: AppTab | null;
  setCurrentTab: (tab: AppTab) => void;
  activeEvento: Evento | null;
  activeMovimento: MovimentoCaixa | null;
  onOpenMobileModal: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  currentTab, setCurrentTab, activeEvento, activeMovimento, onOpenMobileModal,
}) => {
  const { user, logout } = useAuthStore();
  const config = useOrgStore((state) => state.config);
  const [isPasswordModalOpen, setIsPasswordModalOpen] = useState(false);
  const navItems = [
    { id: 'pdv' as const, label: 'PDV / Vendas', mobile: 'PDV', icon: ShoppingBag },
    { id: 'agendamentos' as const, label: 'Atendimentos', mobile: 'Atend.', icon: Users },
    { id: 'caixa' as const, label: 'Caixa', mobile: 'Caixa', icon: Wallet },
    { id: 'doacoes' as const, label: 'Doações', mobile: 'Doações', icon: HeartHandshake },
    { id: 'admin' as const, label: 'Administração', mobile: 'Admin', icon: Settings },
  ].filter((item) => availableTabs(user, config).includes(item.id));

  return (
    <>
      <header className="sticky top-0 z-30 border-b border-slate-200 bg-white/95 shadow-xs backdrop-blur-md">
        <div className="mx-auto flex min-h-16 max-w-screen-2xl items-center justify-between gap-3 px-3 sm:px-5 lg:px-6">
          <div className="flex min-w-0 items-center gap-2">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-emerald-600 text-white">
              <HeartHandshake className="h-5 w-5" />
            </div>
            <div className="min-w-0">
              <span className="block font-black leading-tight tracking-tight text-slate-900">Unython</span>
              <span title={config.nome_organizacao} className="block max-w-[10rem] truncate text-xs font-medium text-slate-500 xl:max-w-[14rem]">{config.nome_organizacao}</span>
            </div>
          </div>

          <nav aria-label="Navegação principal" className="hidden items-center gap-0.5 rounded-xl border border-slate-200 bg-slate-100 p-1 lg:flex">
            {navItems.map((item) => {
              const Icon = item.icon;
              return <button key={item.id} type="button" onClick={() => setCurrentTab(item.id)}
                aria-current={currentTab === item.id ? 'page' : undefined}
                className={`inline-flex min-h-10 items-center gap-1.5 rounded-lg px-2.5 text-xs font-bold whitespace-nowrap transition-colors ${currentTab === item.id ? 'bg-white text-emerald-800 shadow-sm' : 'text-slate-600 hover:bg-white/70'}`}>
                <Icon className="h-4 w-4" />{item.label}
              </button>;
            })}
          </nav>

          <details className="relative shrink-0">
            <summary aria-label="Status e ações da conta" className="flex min-h-11 cursor-pointer list-none items-center gap-2 rounded-xl border border-slate-200 px-3 text-xs font-bold text-slate-700 hover:bg-slate-50 [&::-webkit-details-marker]:hidden">
              <span className={`h-2 w-2 rounded-full ${activeEvento && activeMovimento ? 'bg-emerald-500' : 'bg-amber-400'}`} />
              <span className="hidden sm:inline">Status e conta</span><MoreHorizontal className="h-4 w-4" />
            </summary>
            <div className="absolute right-0 mt-2 w-72 max-w-[calc(100vw-1.5rem)] rounded-2xl border border-slate-200 bg-white p-3 text-sm shadow-xl">
              <p className="break-words font-bold text-slate-800">{config.nome_organizacao}</p>
              <p className="mt-1 break-words text-xs text-slate-500">{user?.email} · {user?.role}</p>
              <div className="my-3 space-y-1 border-y border-slate-100 py-2 text-xs text-slate-600">
                <p className="break-words">{config.alias_evento}: {activeEvento?.nome || 'Nenhum ativo'}</p>
                <p>{activeMovimento ? 'Caixa aberto' : 'Caixa fechado'}</p>
              </div>
              <button type="button" onClick={onOpenMobileModal} className="flex min-h-10 w-full items-center gap-2 rounded-lg px-2 text-left hover:bg-slate-100"><Smartphone className="h-4 w-4" />Conectar celular</button>
              <button type="button" onClick={() => setIsPasswordModalOpen(true)} className="flex min-h-10 w-full items-center gap-2 rounded-lg px-2 text-left hover:bg-slate-100"><KeyRound className="h-4 w-4" />Alterar senha</button>
              <button type="button" onClick={logout} className="flex min-h-10 w-full items-center gap-2 rounded-lg px-2 text-left text-rose-700 hover:bg-rose-50"><LogOut className="h-4 w-4" />Sair do sistema</button>
            </div>
          </details>
        </div>
      </header>

      <nav aria-label="Navegação principal mobile" className="safe-area-bottom fixed inset-x-0 bottom-0 z-40 flex justify-around border-t border-slate-200 bg-white/95 px-2 py-1.5 shadow-2xl backdrop-blur-md lg:hidden">
        {navItems.map((item) => {
          const Icon = item.icon;
          return <button key={item.id} type="button" onClick={() => setCurrentTab(item.id)}
            aria-current={currentTab === item.id ? 'page' : undefined}
            className={`flex min-h-11 min-w-0 flex-1 flex-col items-center justify-center gap-1 rounded-xl ${currentTab === item.id ? 'font-bold text-emerald-700' : 'text-slate-500'}`}>
            <Icon className="h-5 w-5" /><span className="text-[10px]">{item.mobile}</span>
          </button>;
        })}
      </nav>
      <ChangePasswordModal isOpen={isPasswordModalOpen} onClose={() => setIsPasswordModalOpen(false)} />
    </>
  );
};
