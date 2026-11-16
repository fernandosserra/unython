import { useState, useEffect, useCallback } from 'react';
import { useAuthStore } from './store/useAuthStore';
import { LoginView } from './components/LoginView';
import { Navbar } from './components/Navbar';
import { PDVView } from './components/PDVView';
import { AgendamentosView } from './components/AgendamentosView';
import { CaixaView } from './components/CaixaView';
import { AdminView } from './components/AdminView';
import { ConnectMobileModal } from './components/ConnectMobileModal';
import { apiClient } from './api/client';
import type { Evento, MovimentoCaixa, OrganizacaoConfig } from './types';

export function App() {
  const { isAuthenticated, logout } = useAuthStore();
  const [currentTab, setCurrentTab] = useState<'pdv' | 'agendamentos' | 'caixa' | 'admin'>('pdv');
  const [activeEvento, setActiveEvento] = useState<Evento | null>(null);
  const [activeMovimento, setActiveMovimento] = useState<MovimentoCaixa | null>(null);
  const [isMobileModalOpen, setIsMobileModalOpen] = useState(false);
  const [orgConfig, setOrgConfig] = useState<{nome_organizacao: string}>({nome_organizacao: ''});

  // Carrega status da sessão ativa (Evento aberto + Caixa ativo)
  const refreshActiveSession = useCallback(async () => {
    if (!isAuthenticated) return;

    try {
      // 1. Busca evento aberto
      try {
        const evResp = await apiClient.get('/eventos/aberto');
        setActiveEvento(evResp.data || null);
      } catch {
        setActiveEvento(null);
      }

      // 2. Busca caixas e vê se algum está com movimento ativo
      try {
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
          } catch {
            // Nenhum ativo para este caixa
          }
        }
        setActiveMovimento(foundMov);
      } catch {
        setActiveMovimento(null);
      }

      // 3. Busca nome da organização
      try {
        const orgResp = await apiClient.get('/organizacao/config');
        if (orgResp.data?.nome_organizacao) {
          setOrgConfig({ nome_organizacao: orgResp.data.nome_organizacao });
        }
      } catch {
        // Usa padrão
      }
    } catch (err) {
      console.error('Erro ao sincronizar sessão:', err);
    }
  }, [isAuthenticated]);

  useEffect(() => {
    if (isAuthenticated) {
      refreshActiveSession();
    }
  }, [isAuthenticated, refreshActiveSession]);

  // Listener para token expirado
  useEffect(() => {
    const handleExpired = () => {
      logout();
    };
    window.addEventListener('unython_auth_expired', handleExpired);
    return () => window.removeEventListener('unython_auth_expired', handleExpired);
  }, [logout]);

  if (!isAuthenticated) {
    return <LoginView />;
  }

  return (
    <div className="min-h-screen flex flex-col bg-slate-100 font-sans text-slate-900 pb-16 lg:pb-0">
      <Navbar
        currentTab={currentTab}
        setCurrentTab={setCurrentTab}
        activeEvento={activeEvento}
        activeMovimento={activeMovimento}
        onOpenMobileModal={() => setIsMobileModalOpen(true)}
        orgNomeOrganizacao={orgConfig.nome_organizacao}
      />

      <main className="flex-1 flex flex-col overflow-hidden">
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
          <AdminView activeEvento={activeEvento} />
        )}
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
