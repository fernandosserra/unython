import React, { useState, useEffect } from 'react';
import {
  Wallet,
  Calendar,
  Lock,
  Unlock,
  AlertCircle,
  PlusCircle,
  CheckCircle2,
} from 'lucide-react';
import { apiClient } from '../api/client';
import { useAuthStore } from '../store/useAuthStore';
import type { Evento, Caixa, MovimentoCaixa } from '../types';

interface CaixaViewProps {
  activeEvento: Evento | null;
  activeMovimento: MovimentoCaixa | null;
  onRefreshState: () => Promise<void>;
}

export const CaixaView: React.FC<CaixaViewProps> = ({
  activeEvento,
  activeMovimento,
  onRefreshState,
}) => {
  const { user } = useAuthStore();
  const [caixas, setCaixas] = useState<Caixa[]>([]);
  const [selectedCaixaId, setSelectedCaixaId] = useState<number | null>(null);
  const [valorAbertura, setValorAbertura] = useState<number>(50);
  const [nomeNovoEvento, setNomeNovoEvento] = useState('');
  const [tipoNovoEvento, setTipoNovoEvento] = useState('Atendimento');
  const [nomeNovoCaixa, setNomeNovoCaixa] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const fetchCaixas = async () => {
    try {
      const resp = await apiClient.get('/caixas/');
      const list: Caixa[] = resp.data || [];
      setCaixas(list);
      if (list.length > 0 && !selectedCaixaId) {
        setSelectedCaixaId(list[0].id);
      }
    } catch (err) {
      console.error('Erro ao carregar caixas:', err);
    }
  };

  useEffect(() => {
    fetchCaixas();
  }, []);

  const handleAbrirEvento = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setMessage(null);
    try {
      const hoje = new Date().toLocaleDateString('pt-BR');
      const nomeFinal = nomeNovoEvento || `Atendimento & Bazar (${hoje})`;
      await apiClient.post('/eventos/abrir', null, {
        params: { nome: nomeFinal, tipo: tipoNovoEvento },
      });
      setMessage({ type: 'success', text: `Evento "${nomeFinal}" aberto com sucesso!` });
      setNomeNovoEvento('');
      await onRefreshState();
    } catch (err: any) {
      setMessage({ type: 'error', text: err.response?.data?.detail || 'Erro ao abrir evento.' });
    } finally {
      setIsLoading(false);
    }
  };

  const handleFecharEvento = async () => {
    if (!activeEvento) return;
    if (!confirm(`Deseja realmente fechar o evento "${activeEvento.nome}"?`)) return;

    setIsLoading(true);
    setMessage(null);
    try {
      await apiClient.post(`/eventos/${activeEvento.id}/fechar`);
      setMessage({ type: 'success', text: 'Evento fechado com sucesso.' });
      await onRefreshState();
    } catch (err: any) {
      setMessage({ type: 'error', text: err.response?.data?.detail || 'Erro ao fechar evento.' });
    } finally {
      setIsLoading(false);
    }
  };

  const handleAbrirCaixa = async () => {
    if (!selectedCaixaId) {
      alert('Selecione um ponto de caixa.');
      return;
    }
    if (!activeEvento) {
      alert('É necessário ter um Evento aberto antes de abrir a sessão de caixa.');
      return;
    }

    setIsLoading(true);
    setMessage(null);
    try {
      await apiClient.post(`/caixas/${selectedCaixaId}/abrir`, {
        usuario_id: user?.id || 1,
        valor_abertura: Number(valorAbertura) || 0,
        id_evento: activeEvento.id,
      });
      setMessage({ type: 'success', text: 'Sessão de caixa aberta com sucesso!' });
      await onRefreshState();
    } catch (err: any) {
      setMessage({ type: 'error', text: err.response?.data?.detail || 'Erro ao abrir caixa.' });
    } finally {
      setIsLoading(false);
    }
  };

  const handleFecharCaixa = async () => {
    if (!activeMovimento) return;
    if (!confirm('Deseja realmente fechar este turno de caixa?')) return;

    setIsLoading(true);
    setMessage(null);
    try {
      await apiClient.post(`/caixas/${activeMovimento.id}/fechar`);
      setMessage({ type: 'success', text: 'Movimento de caixa encerrado com sucesso.' });
      await onRefreshState();
    } catch (err: any) {
      setMessage({ type: 'error', text: err.response?.data?.detail || 'Erro ao fechar caixa.' });
    } finally {
      setIsLoading(false);
    }
  };

  const handleCriarCaixa = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!nomeNovoCaixa) return;
    setIsLoading(true);
    try {
      await apiClient.post('/caixas/', {
        nome: nomeNovoCaixa,
        descricao: 'Ponto de venda físico',
        status: 'Ativo',
      });
      setNomeNovoCaixa('');
      await fetchCaixas();
      setMessage({ type: 'success', text: 'Novo caixa cadastrado!' });
    } catch (err: any) {
      setMessage({ type: 'error', text: err.response?.data?.detail || 'Erro ao criar caixa.' });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex-1 overflow-y-auto bg-slate-100 p-4 sm:p-6 lg:p-8">
      <div className="max-w-5xl mx-auto space-y-6">
        <div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight flex items-center gap-2.5">
            <Wallet className="w-7 h-7 text-emerald-600" />
            Turno, Caixa & Operação
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 font-medium">
            Gerenciamento de eventos fiscais e controle de abertura/fechamento de gaveta.
          </p>
        </div>

        {message && (
          <div
            className={`p-4 rounded-2xl border text-sm font-semibold flex items-center gap-3 ${
              message.type === 'success'
                ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
                : 'bg-rose-50 border-rose-200 text-rose-800'
            }`}
          >
            {message.type === 'success' ? (
              <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
            ) : (
              <AlertCircle className="w-5 h-5 text-rose-600 shrink-0" />
            )}
            <span>{message.text}</span>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Card 1: Evento / Dia Fiscal */}
          <div className="bg-white p-6 rounded-3xl border border-slate-200/80 shadow-xs flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-4">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
                  <Calendar className="w-4 h-4 text-emerald-600" />
                  1. Evento / Dia de Trabalho
                </span>
                <span
                  className={`px-2.5 py-0.5 rounded-full text-xs font-bold ${
                    activeEvento ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-100 text-slate-600'
                  }`}
                >
                  {activeEvento ? 'Ativo' : 'Nenhum Aberto'}
                </span>
              </div>

              {activeEvento ? (
                <div className="p-4 rounded-2xl bg-emerald-50/60 border border-emerald-200/80">
                  <h3 className="font-black text-lg text-emerald-950">{activeEvento.nome}</h3>
                  <p className="text-xs text-emerald-700 mt-1">
                    Data: <span className="font-semibold">{activeEvento.data_evento}</span> • Tipo:{' '}
                    <span className="font-semibold">{activeEvento.tipo}</span>
                  </p>
                  <p className="text-[11px] text-slate-500 mt-3">
                    Todas as vendas e atendimentos registrados agora serão vinculados a este evento fiscal.
                  </p>
                </div>
              ) : (
                <form onSubmit={handleAbrirEvento} className="space-y-3">
                  <div>
                    <label className="block text-xs font-bold text-slate-700 uppercase mb-1">
                      Nome do Evento
                    </label>
                    <input
                      type="text"
                      value={nomeNovoEvento}
                      onChange={(e) => setNomeNovoEvento(e.target.value)}
                      placeholder="Ex: Bazar Beneficente de Sábado"
                      className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 text-sm focus:bg-white focus:outline-hidden focus:ring-2 focus:ring-emerald-500 font-medium"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-slate-700 uppercase mb-1">
                      Tipo de Operação
                    </label>
                    <input
                      type="text"
                      value={tipoNovoEvento}
                      onChange={(e) => setTipoNovoEvento(e.target.value)}
                      placeholder="Ex: Encontro, atendimento, evento beneficente"
                      className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 text-sm focus:bg-white focus:outline-hidden focus:ring-2 focus:ring-emerald-500 font-medium"
                    />
                  </div>
                  <button
                    type="submit"
                    disabled={isLoading}
                    className="w-full h-11 bg-emerald-600 hover:bg-emerald-700 active:scale-[0.99] text-white rounded-xl text-xs sm:text-sm font-bold transition-all cursor-pointer shadow-xs disabled:opacity-50 flex items-center justify-center gap-2"
                  >
                    Abrir Novo Evento
                  </button>
                </form>
              )}
            </div>

            {activeEvento && (
              <div className="mt-6 pt-4 border-t border-slate-100">
                <button
                  type="button"
                  onClick={handleFecharEvento}
                  disabled={isLoading}
                  className="w-full h-11 border border-rose-200 hover:bg-rose-50 text-rose-700 rounded-xl text-xs sm:text-sm font-bold transition-all cursor-pointer flex items-center justify-center gap-2"
                >
                  <Lock className="w-4 h-4" />
                  <span>Encerrar Evento do Dia</span>
                </button>
              </div>
            )}
          </div>

          {/* Card 2: Sessão de Caixa */}
          <div className="bg-white p-6 rounded-3xl border border-slate-200/80 shadow-xs flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-4">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
                  <Wallet className="w-4 h-4 text-emerald-600" />
                  2. Sessão de Caixa (PDV)
                </span>
                <span
                  className={`px-2.5 py-0.5 rounded-full text-xs font-bold ${
                    activeMovimento ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-100 text-slate-600'
                  }`}
                >
                  {activeMovimento ? 'Caixa Aberto' : 'Caixa Fechado'}
                </span>
              </div>

              {activeMovimento ? (
                <div className="p-4 rounded-2xl bg-emerald-50/60 border border-emerald-200/80 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-slate-600">Status da Sessão:</span>
                    <span className="text-xs font-black text-emerald-700 bg-emerald-200/60 px-2 py-0.5 rounded">
                      ABERTO PARA VENDAS
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-500">Fundo de Troco Inicial:</span>
                    <span className="font-bold text-slate-800">
                      R$ {Number(activeMovimento.valor_abertura).toFixed(2).replace('.', ',')}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-500">Aberto em:</span>
                    <span className="font-medium text-slate-700">
                      {new Date(activeMovimento.data_abertura).toLocaleTimeString([], {
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-500 pt-2 border-t border-emerald-200/60">
                    O PDV está pronto e sincronizado para registrar vendas imediatamente.
                  </p>
                </div>
              ) : (
                <div className="space-y-4">
                  <div>
                    <label className="block text-xs font-bold text-slate-700 uppercase mb-1">
                      Selecione o Ponto de Caixa
                    </label>
                    <select
                      value={selectedCaixaId || ''}
                      onChange={(e) => setSelectedCaixaId(Number(e.target.value))}
                      className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 text-sm focus:bg-white focus:outline-hidden focus:ring-2 focus:ring-emerald-500 font-medium"
                    >
                      {caixas.map((c) => (
                        <option key={c.id} value={c.id}>
                          {c.nome} ({c.descricao || 'Ativo'})
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-slate-700 uppercase mb-1">
                      Fundo de Troco (R$)
                    </label>
                    <input
                      type="number"
                      step="5"
                      value={valorAbertura}
                      onChange={(e) => setValorAbertura(parseFloat(e.target.value) || 0)}
                      className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 text-sm focus:bg-white focus:outline-hidden focus:ring-2 focus:ring-emerald-500 font-medium"
                    />
                  </div>

                  <button
                    type="button"
                    onClick={handleAbrirCaixa}
                    disabled={isLoading || !activeEvento}
                    className="w-full h-11 bg-emerald-600 hover:bg-emerald-700 active:scale-[0.99] disabled:bg-slate-200 disabled:text-slate-400 disabled:cursor-not-allowed text-white rounded-xl text-xs sm:text-sm font-bold transition-all cursor-pointer shadow-xs flex items-center justify-center gap-2"
                  >
                    <Unlock className="w-4 h-4" />
                    <span>Abrir Caixa para Vendas</span>
                  </button>
                  {!activeEvento && (
                    <p className="text-[11px] text-amber-600 font-medium text-center">
                      * Abra o Evento ao lado antes de abrir o caixa.
                    </p>
                  )}
                </div>
              )}
            </div>

            {activeMovimento && (
              <div className="mt-6 pt-4 border-t border-slate-100">
                <button
                  type="button"
                  onClick={handleFecharCaixa}
                  disabled={isLoading}
                  className="w-full h-11 border border-slate-300 hover:bg-slate-50 text-slate-700 rounded-xl text-xs sm:text-sm font-bold transition-all cursor-pointer flex items-center justify-center gap-2"
                >
                  <Lock className="w-4 h-4 text-slate-500" />
                  <span>Fechar Movimento / Turno do Caixa</span>
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Cadastro Rápido de Novo Ponto de Caixa */}
        <div className="bg-white p-5 rounded-3xl border border-slate-200/80 shadow-xs">
          <div className="flex items-center gap-2 mb-3">
            <PlusCircle className="w-4 h-4 text-slate-400" />
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-600">
              Cadastrar Novo Ponto de Venda Físico (Opcional)
            </h3>
          </div>
          <form onSubmit={handleCriarCaixa} className="flex gap-2">
            <input
              type="text"
              value={nomeNovoCaixa}
              onChange={(e) => setNomeNovoCaixa(e.target.value)}
              placeholder="Ex: Caixa 2 - Pastelaria / Bazar"
              className="flex-1 h-11 px-3.5 bg-slate-50 border border-slate-200 rounded-xl text-xs sm:text-sm text-slate-900 focus:bg-white focus:outline-hidden focus:ring-2 focus:ring-emerald-500 font-medium"
            />
            <button
              type="submit"
              disabled={isLoading || !nomeNovoCaixa}
              className="h-11 px-5 bg-slate-800 hover:bg-slate-900 disabled:bg-slate-200 disabled:text-slate-400 text-white rounded-xl text-xs sm:text-sm font-bold transition-all cursor-pointer shrink-0 flex items-center justify-center"
            >
              Adicionar Caixa
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};
