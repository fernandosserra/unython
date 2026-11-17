import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { useAuthStore } from './store/useAuthStore';
import { useOrgStore } from './store/useOrgStore';
import { LoginView } from './components/LoginView';
import { Navbar } from './components/Navbar';
import { PDVView } from './components/PDVView';
import { AgendamentosView } from './components/AgendamentosView';
import { CaixaView } from './components/CaixaView';
import { AdminView } from './components/AdminView';
import { DoacoesView } from './components/DoacoesView';
import { ChangePasswordModal } from './components/ChangePasswordModal';
import { ConnectMobileModal } from './components/ConnectMobileModal';
import { ConnectivityBanner } from './components/ConnectivityBanner';
import { apiClient } from './api/client';
import type { Evento, MovimentoCaixa } from './types';

export function App() {
  const { isAuthenticated, logout, user } = useAuthStore();
  const [currentTab, setCurrentTab] = useState<'pdv' | 'agendamentos' | 'caixa' | 'admin' | 'doacoes'>('pdv');
  const [activeEvento, setActiveEvento] = useState<Evento | null>(null);
  const [activeMovimento, setActiveMovimento] = useState<MovimentoCaixa | null>(null);
  const [isMobileModalOpen, setIsMobileModalOpen] = useState(false);
  const loadConfig = useOrgStore((state) => state.loadConfig);
  const [configStatus, setConfigStatus] = useState<'loading' | 'ready' | 'error'>('loading');
  const [configRetry, setConfigRetry] = useState(0);

  // Carrega status da sessão ativa (Evento aberto + Caixa ativo)
  const refreshActiveSession = useCallback(async () => {
    if (!isAuthenticated) return;

    try {
      // 1. Busca evento aberto
      try {
        const evResp = await apiClient.get('/eventos/aberto');
        setActiveEvento(evResp.data || null);
      } catch (err) {
        if (axios.isAxiosError(err) && err.response?.status === 404) {
          setActiveEvento(null);
        } else {
          throw err;
        }
      }

      // 2. Busca caixas e vê se algum está com movimento ativo
      const caixasResp = await apiClient.get('/caixas/');
      const caixasList = caixasResp.data || [];
      let foundMov: MovimentoCaixa | null = null;

      for (const c of caixasList) {
        try {
          const movResp = await apiClient.get(`/caixas/${c.id}/movimento-ativo`);
          if (movResp.data?.id) {
            foundMov = movResp.data;
            break;
          }
        } catch (err) {
          if (!axios.isAxiosError(err) || err.response?.status !== 404) {
            throw err;
          }
        }
      }
      setActiveMovimento(foundMov);
    } catch (err) {
      console.error('Erro ao sincronizar sessão:', err);
    }
  }, [isAuthenticated]);

  useEffect(() => {
    if (isAuthenticated) {
      refreshActiveSession();
    }
  }, [isAuthenticated, refreshActiveSession]);

  useEffect(() => {
    if (!isAuthenticated) {
      setConfigStatus('loading');
      return;
    }
    let active = true;
    setConfigStatus('loading');
    loadConfig().then(
      () => { if (active) setConfigStatus('ready'); },
      () => { if (active) setConfigStatus('error'); },
    );
    return () => { active = false; };
  }, [isAuthenticated, loadConfig, configRetry]);

  useEffect(() => {
    if (currentTab === 'admin' && user?.role !== 'Administrador') {
      setCurrentTab('pdv');
    }
  }, [currentTab, user?.role]);

  // Listener para token expirado
  useEffect(() => {
    const handleExpired = () => {
      logout();
    };
    window.addEventListener('unython_auth_expired', handleExpired);
    return () => window.removeEventListener('unython_auth_expired', handleExpired);
  }, [logout]);

  if (!isAuthenticated) {
    return (
      <>
        <ConnectivityBanner />
        <LoginView />
      </>
    );
  }

  if (user?.require_password_change) {
    return (
      <>
        <ConnectivityBanner />
        <ChangePasswordModal isOpen required onClose={logout} />
      </>
    );
  }

  if (configStatus !== 'ready') {
    return (
      <>
        <ConnectivityBanner />
        <div className="p-6" role={configStatus === 'error' ? 'alert' : 'status'}>
          {configStatus === 'error' ? (
            <>
              <p>Não foi possível carregar a configuração da organização.</p>
              <button type="button" onClick={() => setConfigRetry((count) => count + 1)} className="mt-3 rounded-lg bg-slate-900 px-4 py-2 text-white">Tentar novamente</button>
            </>
          ) : 'Carregando configuração da organização...'}
        </div>
      </>
    );
  }

  return (
    <div className="h-dvh min-h-0 flex flex-col overflow-hidden bg-slate-100 font-sans text-slate-900 pb-[calc(4.25rem_+_env(safe-area-inset-bottom))] lg:pb-0">
      <Navbar
        currentTab={currentTab}
        setCurrentTab={setCurrentTab}
        activeEvento={activeEvento}
        activeMovimento={activeMovimento}
        onOpenMobileModal={() => setIsMobileModalOpen(true)}
      />
      <ConnectivityBanner />

      <main className="min-h-0 min-w-0 flex-1 flex flex-col overflow-x-hidden">
        {currentTab === 'pdv' && (
          <PDVView
            activeEvento={activeEvento}
            activeMovimento={activeMovimento}
            onNavigateToCaixa={() => setCurrentTab('caixa')}
          />
        )}

        {currentTab === 'agendamentos' && (
          <AgendamentosView
            activeEvento={activeEvento}
            onNavigateToCaixa={() => setCurrentTab('caixa')}
            onRefreshState={refreshActiveSession}
          />
        )}

        {currentTab === 'caixa' && (
          <CaixaView
            activeEvento={activeEvento}
            activeMovimento={activeMovimento}
            onRefreshState={refreshActiveSession}
          />
        )}

        {currentTab === 'admin' && (
          <AdminView activeEvento={activeEvento} onRefreshState={refreshActiveSession} />
        )}
        {currentTab === 'doacoes' && <DoacoesView />}
      </main>

      {/* Rodapé – Branding & Licença */}
      <footer className="hidden lg:flex items-center justify-center gap-1.5 py-2.5 bg-white/80 backdrop-blur-sm border-t border-slate-200/60 text-[11px] text-slate-400 font-medium shrink-0">
        <span>Powered by</span>
        <span className="font-black text-slate-600">Unython</span>
        <span>•</span>
        <span>Software Livre sob Licença</span>
        <a href="https://www.gnu.org/licenses/gpl-3.0.html" target="_blank" rel="noopener noreferrer" className="font-bold text-emerald-600 hover:text-emerald-700 underline underline-offset-2">GPL-3.0</a>
      </footer>

      {/* Modal QR Code / Conexão Wi-Fi no Smartphone */}
      <ConnectMobileModal
        isOpen={isMobileModalOpen}
        onClose={() => setIsMobileModalOpen(false)}
      />
    </div>
  );
}

export default App;
