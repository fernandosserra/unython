import React from 'react';
import {
  ShoppingBag,
  Users,
  Wallet,
  Settings,
  LogOut,
  HeartHandshake,
  Smartphone,
} from 'lucide-react';
import { useAuthStore } from '../store/useAuthStore';
import type { Evento, MovimentoCaixa } from '../types';

interface NavbarProps {
  currentTab: 'pdv' | 'agendamentos' | 'caixa' | 'admin';
  setCurrentTab: (tab: 'pdv' | 'agendamentos' | 'caixa' | 'admin') => void;
  activeEvento: Evento | null;
  activeMovimento: MovimentoCaixa | null;
  onOpenMobileModal: () => void;
  orgNomeOrganizacao?: string;
}

export const Navbar: React.FC<NavbarProps> = ({
  currentTab,
  setCurrentTab,
  activeEvento,
  activeMovimento,
  onOpenMobileModal,
  orgNomeOrganizacao,
}) => {
  const { user, logout } = useAuthStore();

  const navItems: { id: 'pdv' | 'agendamentos' | 'caixa' | 'admin'; label: string; icon: React.ComponentType<{ className?: string }> }[] = [
    { id: 'pdv', label: 'PDV / Vendas', icon: ShoppingBag },
    { id: 'agendamentos', label: 'Atendimentos', icon: Users },
    { id: 'caixa', label: 'Caixa', icon: Wallet },
    { id: 'admin', label: 'Administração', icon: Settings },
  ];

  return (
    <>
      {/* Header Superior (Desktop e Tablets) */}
      <header className="sticky top-0 z-30 bg-white/95 backdrop-blur-md border-b border-slate-200/80 shadow-xs">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16 gap-3">
            {/* Logo e Identidade */}
            <div className="flex items-center gap-3 shrink-0">
              <div className="w-10 h-10 rounded-xl bg-emerald-600 text-white flex items-center justify-center shadow-sm">
                <HeartHandshake className="w-6 h-6" />
              </div>
              <div className="flex flex-col">
                <div className="flex items-center gap-2">
                  <span className="font-black text-xl tracking-tight text-slate-900 leading-none">Unython</span>
                  <span className="text-[10px] uppercase font-extrabold tracking-wider bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded-full leading-none">
                    {orgNomeOrganizacao || 'ONG Impact'}
                  </span>
                </div>
                <p className="text-[11px] text-slate-500 font-medium hidden 2xl:block mt-1">
                  Gestão Solidária & Operação por Evento
                </p>
              </div>
            </div>

            {/* Navegação Central Segmentada (Tabs Perfeitamente Simétricas) */}
            <nav className="hidden lg:inline-flex items-center p-1 bg-slate-100/90 rounded-2xl border border-slate-200/70 shadow-inner shrink-0">
              {navItems.map((item) => {
                const Icon = item.icon;
                const isActive = currentTab === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => setCurrentTab(item.id)}
                    className={`h-9 px-3.5 inline-flex items-center gap-2 rounded-xl text-xs font-bold whitespace-nowrap transition-all cursor-pointer ${
                      isActive
                        ? 'bg-white text-emerald-800 shadow-sm border border-slate-200/60'
                        : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/60'
                    }`}
                  >
                    <Icon className={`w-4 h-4 ${isActive ? 'text-emerald-600' : 'text-slate-500'}`} />
                    <span>{item.label}</span>
                  </button>
                );
              })}
            </nav>

            {/* Ações da Direita: Modo Celular + Status + Usuário */}
            <div className="flex items-center gap-2 shrink-0">
              {/* Botão Modo Celular (Mesma altura h-9, alinhamento horizontal) */}
              <button
                onClick={onOpenMobileModal}
                title="Abrir no celular via QR Code / Rede Local"
                className="h-9 px-3 inline-flex items-center gap-2 rounded-xl bg-emerald-50 hover:bg-emerald-100/90 text-emerald-800 text-xs font-bold border border-emerald-200/90 transition-all cursor-pointer active:scale-95 shadow-xs whitespace-nowrap shrink-0"
              >
                <Smartphone className="w-4 h-4 text-emerald-600 shrink-0" />
                <span className="hidden sm:inline">Modo Celular</span>
                <span className="sm:hidden font-black">Celular</span>
              </button>

              {/* Badges de Status (Mesma altura h-9, alinhadas) */}
              <div className="hidden xl:flex items-center gap-2 shrink-0">
                <div
                  className="h-9 px-3 rounded-xl text-xs font-semibold bg-slate-50 text-slate-700 border border-slate-200/80 inline-flex items-center gap-2 whitespace-nowrap shrink-0"
                  title={activeEvento ? `Evento: ${activeEvento.nome}` : 'Nenhum evento ativo no momento'}
                >
                  <span className={`w-2 h-2 rounded-full shrink-0 ${activeEvento ? 'bg-emerald-500 ring-2 ring-emerald-200' : 'bg-amber-400'}`} />
                  <span className="max-w-[130px] truncate">{activeEvento ? activeEvento.nome : 'Sem Evento Ativo'}</span>
                </div>

                <div className="h-9 px-3 rounded-xl text-xs font-semibold bg-slate-50 text-slate-700 border border-slate-200/80 inline-flex items-center gap-2 whitespace-nowrap shrink-0">
                  <span className={`w-2 h-2 rounded-full shrink-0 ${activeMovimento ? 'bg-emerald-500 ring-2 ring-emerald-200' : 'bg-rose-400'}`} />
                  <span>{activeMovimento ? 'Caixa Aberto' : 'Caixa Fechado'}</span>
                </div>
              </div>

              {/* Informações do Usuário & Logout */}
              <div className="flex items-center gap-2 pl-2 border-l border-slate-200 shrink-0">
                <div className="text-right hidden md:block max-w-[150px]">
                  <p className="text-xs font-bold text-slate-800 leading-tight truncate">{user?.email}</p>
                  <p className="text-[10px] text-slate-500 font-semibold leading-tight">{user?.role}</p>
                </div>
                <button
                  onClick={logout}
                  title="Sair do sistema"
                  className="h-9 w-9 rounded-xl border border-slate-200/80 bg-white hover:bg-rose-50 hover:border-rose-200 text-slate-500 hover:text-rose-600 flex items-center justify-center transition-all cursor-pointer shadow-2xs"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Barra de Navegação Inferior (Mobile Bottom Navigation Bar) */}
      <nav className="lg:hidden fixed bottom-0 left-0 right-0 z-40 bg-white/95 backdrop-blur-md border-t border-slate-200 px-3 py-1.5 flex items-center justify-around shadow-2xl safe-area-bottom">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setCurrentTab(item.id)}
              className={`flex-1 flex flex-col items-center justify-center gap-1 py-1 rounded-xl transition-all cursor-pointer ${
                isActive ? 'text-emerald-700 font-black' : 'text-slate-500 hover:text-slate-800 font-medium'
              }`}
            >
              <div className={`p-1.5 rounded-xl transition-colors ${isActive ? 'bg-emerald-100/90 text-emerald-800' : ''}`}>
                <Icon className="w-5 h-5" />
              </div>
              <span className="text-[10px] leading-none tracking-tight">{item.id === 'admin' ? 'Cadastros' : item.label.split('/')[0].trim()}</span>
            </button>
          );
        })}
      </nav>
    </>
  );
};
