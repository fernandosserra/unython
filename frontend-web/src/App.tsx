import { useState, useEffect, useCallback, useRef } from 'react';
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
import { availableTabs, hasPermission, type AppTab } from './permissions';

export function App() {
  const { isAuthenticated, authReady, refreshUser, logout, user } = useAuthStore();
  const [currentTab, setCurrentTab] = useState<AppTab>('pdv');
  const [activeEvento, setActiveEvento] = useState<Evento | null>(null);
  const [activeMovimento, setActiveMovimento] = useState<MovimentoCaixa | null>(null);
  const [isMobileModalOpen, setIsMobileModalOpen] = useState(false);
  const loadConfig = useOrgStore((state) => state.loadConfig);
  const config = useOrgStore((state) => state.config);
  const [configStatus, setConfigStatus] = useState<'loading' | 'ready' | 'error'>('loading');
  const [configRetry, setConfigRetry] = useState(0);
  const [authError, setAuthError] = useState(false);
  const sessionVersion = useRef(0);
  const allowedTabs = availableTabs(user, config);
  const effectiveTab = allowedTabs.includes(currentTab) ? currentTab : allowedTabs[0] ?? null;
  const canReadEvento = allowedTabs.some((tab) => tab !== 'admin') || hasPermission(user, 'eventos') || hasPermission(user, 'estoque');
  const canReadCaixa = allowedTabs.includes('caixa') || allowedTabs.includes('pdv');

  // Carrega status da sessão ativa (Evento aberto + Caixa ativo)
  const refreshActiveSession = useCallback(async () => {
    const version = ++sessionVersion.current;
    if (!isAuthenticated || !authReady || user?.require_password_change || configStatus !== 'ready') return;

    try {
      // 1. Busca evento aberto
      try {
        const evResp = canReadEvento ? await apiClient.get('/eventos/aberto') : null;
        if (version === sessionVersion.current) setActiveEvento(evResp?.data || null);
      } catch (err) {
        if (axios.isAxiosError(err) && err.response?.status === 404) {
          if (version === sessionVersion.current) setActiveEvento(null);
        } else {
          throw err;
        }
      }

      // 2. Busca caixas e vê se algum está com movimento ativo
      if (!canReadCaixa) {
        if (version === sessionVersion.current) setActiveMovimento(null);
        return;
      }
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
      if (version === sessionVersion.current) setActiveMovimento(foundMov);
    } catch (err) {
      console.error('Erro ao sincronizar sessão:', err);
    }
  }, [isAuthenticated, authReady, user?.require_password_change, configStatus, canReadEvento, canReadCaixa]);

  useEffect(() => {
    setActiveEvento(null);
    setActiveMovimento(null);
    void refreshActiveSession();
    return () => { sessionVersion.current++; };
  }, [refreshActiveSession]);

  useEffect(() => {
    if (!isAuthenticated || configStatus !== 'ready') return;
    const refresh = () => { void refreshActiveSession(); };
    window.addEventListener('focus', refresh);
    const timer = window.setInterval(refresh, 60_000);
    return () => { window.removeEventListener('focus', refresh); window.clearInterval(timer); };
  }, [isAuthenticated, configStatus, refreshActiveSession]);

  const openScheduledEvent = async (id: number) => {
    await apiClient.post(`/eventos/${id}/iniciar`);
    await refreshActiveSession();
  };

  const closeActiveEvent = async (): Promise<boolean> => {
    if (!activeEvento || !window.confirm(`Deseja encerrar "${activeEvento.nome}"?`)) return false;
    try {
      await apiClient.post(`/eventos/${activeEvento.id}/fechar`);
    } catch (error) {
      if (!axios.isAxiosError(error) || error.response?.status !== 409 ||
          error.response.data?.detail?.code !== 'caixa_aberto') throw error;
      const count = error.response.data.detail.movimentos_abertos;
      if (!window.confirm(`Há ${count} movimento(s) de caixa aberto(s) vinculado(s) a este evento. Encerrar mesmo assim?`)) return false;
      await apiClient.post(`/eventos/${activeEvento.id}/fechar`, null, { params: { confirmar_caixa_aberto: true } });
    }
    await refreshActiveSession();
    return true;
  };

  useEffect(() => {
    if (!isAuthenticated || !authReady || user?.require_password_change) {
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
  }, [isAuthenticated, authReady, user?.require_password_change, loadConfig, configRetry]);

  useEffect(() => {
    if (!isAuthenticated) return;
    let active = true;
    const verify = async (block = false) => {
      const ok = await refreshUser(block);
      if (active) setAuthError(!ok);
    };
    void verify();
    const onFocus = () => {
      void verify().then(() => {
        const state = useAuthStore.getState();
        if (state.authReady && !state.user?.require_password_change) {
          void loadConfig().catch(() => { if (active) setConfigStatus('error'); });
        }
      });
    };
    const timer = window.setInterval(onFocus, 60_000);
    let lastForbidden = 0;
    const interceptor = apiClient.interceptors.response.use(undefined, (error: unknown) => {
      if (axios.isAxiosError(error) && error.response?.status === 403 &&
          !error.config?.url?.includes('/auth/me') && !error.config?.url?.includes('/token') &&
          Date.now() - lastForbidden > 5000) {
        lastForbidden = Date.now();
        void verify(true);
      }
      return Promise.reject(error);
    });
    window.addEventListener('focus', onFocus);
    return () => {
      active = false;
      window.clearInterval(timer);
      window.removeEventListener('focus', onFocus);
      apiClient.interceptors.response.eject(interceptor);
    };
  }, [isAuthenticated, refreshUser, loadConfig]);

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

  if (!authReady) {
    return <><ConnectivityBanner /><div className="p-6" role={authError ? 'alert' : 'status'}>
      {authError ? <><p>Não foi possível verificar sua sessão.</p>
        <button type="button" className="mt-3 rounded-lg bg-slate-900 px-4 py-2 text-white" onClick={() => { setAuthError(false); void refreshUser(true).then((ok) => setAuthError(!ok)); }}>Tentar novamente</button>
        <button type="button" className="ml-3 text-slate-700" onClick={logout}>Sair</button></> : 'Verificando sessão...'}
    </div></>;
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
        currentTab={effectiveTab}
        setCurrentTab={setCurrentTab}
        activeEvento={activeEvento}
        activeMovimento={activeMovimento}
        onOpenEvento={openScheduledEvent}
        onCloseEvento={closeActiveEvent}
        onOpenMobileModal={() => setIsMobileModalOpen(true)}
      />
      <ConnectivityBanner />

      <main className="min-h-0 min-w-0 flex-1 flex flex-col overflow-x-hidden">
        {!effectiveTab && <div role="status" className="p-6">Você não possui acesso a nenhum módulo. Entre em contato com um administrador.</div>}
        {effectiveTab === 'pdv' && (
          <PDVView
            activeEvento={activeEvento}
            activeMovimento={activeMovimento}
            onNavigateToCaixa={allowedTabs.includes('caixa') ? () => setCurrentTab('caixa') : undefined}
          />
        )}

        {effectiveTab === 'agendamentos' && (
          <AgendamentosView
            activeEvento={activeEvento}
            onNavigateToCaixa={allowedTabs.includes('caixa') ? () => setCurrentTab('caixa') : undefined}
            onRefreshState={refreshActiveSession}
          />
        )}

        {effectiveTab === 'caixa' && (
          <CaixaView
            activeEvento={activeEvento}
            activeMovimento={activeMovimento}
            onRefreshState={refreshActiveSession}
            onCloseEvento={closeActiveEvent}
          />
        )}

        {effectiveTab === 'admin' && (
          <AdminView activeEvento={activeEvento} onRefreshState={refreshActiveSession} />
        )}
        {effectiveTab === 'estoque' && (
          <AdminView activeEvento={activeEvento} onRefreshState={refreshActiveSession} initialTab="estoque" />
        )}
        {effectiveTab === 'doacoes' && <DoacoesView activeEvento={activeEvento} />}
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
