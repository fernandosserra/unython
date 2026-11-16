import React, { useState, useEffect } from 'react';
import { BarChart3, TrendingUp, PieChart, RefreshCw, Package, AlertTriangle } from 'lucide-react';
import { apiClient } from '../api/client';

interface InventarioItem {
  id: number;
  nome: string;
  saldo_atual: number;
  custo_total_estoque: number;
  valor_venda: number;
}

export const RelatoriosView: React.FC = () => {
  const [saldoCaixa, setSaldoCaixa] = useState<string>('R$ 0,00');
  const [despesas, setDespesas] = useState<{ categoria: string; total_gasto: number }[]>([]);
  const [inventario, setInventario] = useState<InventarioItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [activeReportTab, setActiveReportTab] = useState<'financeiro' | 'estoque'>('financeiro');

  const fetchReports = async () => {
    setIsLoading(true);
    try {
      const [saldoResp, despesasResp, invResp] = await Promise.allSettled([
        apiClient.get('/relatorios/caixa/saldo'),
        apiClient.get('/relatorios/despesas/categoria'),
        apiClient.get('/relatorios/inventario'),
      ]);

      if (saldoResp.status === 'fulfilled') {
        setSaldoCaixa(saldoResp.value.data?.saldo_atual || 'R$ 0,00');
      }
      if (despesasResp.status === 'fulfilled') {
        setDespesas(despesasResp.value.data || []);
      }
      if (invResp.status === 'fulfilled') {
        setInventario(invResp.value.data || []);
      }
    } catch (err) {
      console.error('Erro ao buscar relatórios:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchReports();
  }, []);

  const totalCustoEstoque = inventario.reduce((acc, item) => acc + Number(item.custo_total_estoque || 0), 0);
  const totalItensEstoque = inventario.reduce((acc, item) => acc + item.saldo_atual, 0);
  const itensZerados = inventario.filter((item) => item.saldo_atual <= 0);

  const reportTabs = [
    { id: 'financeiro' as const, label: 'Financeiro', icon: TrendingUp },
    { id: 'estoque' as const, label: 'Estoque & Inventário', icon: Package },
  ];

  return (
    <div className="flex-1 overflow-y-auto bg-slate-100 p-4 sm:p-6 lg:p-8">
      <div className="max-w-5xl mx-auto space-y-6">
        {/* Cabeçalho */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <h1 className="text-xl sm:text-2xl font-black text-slate-900 tracking-tight flex items-center gap-2.5">
              <BarChart3 className="w-6 h-6 sm:w-7 sm:h-7 text-emerald-600 shrink-0" />
              Painel Financeiro & Prestação de Contas
            </h1>
            <p className="text-xs sm:text-sm text-slate-500 font-medium mt-0.5">
              Visão consolidada para transparência e prestação de contas da ONG.
            </p>
          </div>
          <button
            onClick={fetchReports}
            disabled={isLoading}
            className="h-10 px-3.5 bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 font-bold text-xs rounded-xl shadow-xs transition-colors cursor-pointer inline-flex items-center gap-2 shrink-0 self-start sm:self-auto"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
            <span>Atualizar</span>
          </button>
        </div>

        {/* Tabs de Relatório */}
        <div className="inline-flex items-center p-1 bg-slate-200/70 rounded-2xl border border-slate-200/80 gap-1">
          {reportTabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeReportTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveReportTab(tab.id)}
                className={`h-9 px-4 inline-flex items-center gap-2 rounded-xl text-xs font-bold whitespace-nowrap transition-all cursor-pointer ${
                  isActive
                    ? 'bg-white text-emerald-800 shadow-sm border border-slate-200/60'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100/80'
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? 'text-emerald-600' : 'text-slate-500'}`} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>

        {/* ========== ABA FINANCEIRO ========== */}
        {activeReportTab === 'financeiro' && (
          <div className="space-y-4">
            {/* Card Saldo em Caixa */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              <div className="bg-white p-5 sm:p-6 rounded-3xl border border-slate-200/80 shadow-xs flex items-center justify-between">
                <div>
                  <span className="text-[10px] sm:text-xs font-bold uppercase tracking-wider text-slate-500">
                    Saldo Atual do Fluxo
                  </span>
                  <p className="text-2xl sm:text-3xl font-black text-emerald-700 mt-1">{saldoCaixa}</p>
                  <p className="text-[10px] sm:text-[11px] text-slate-400 mt-1">Receitas totais menos despesas</p>
                </div>
                <div className="w-10 h-10 sm:w-12 sm:h-12 rounded-2xl bg-emerald-100 text-emerald-700 flex items-center justify-center shrink-0">
                  <TrendingUp className="w-5 h-5 sm:w-6 sm:h-6" />
                </div>
              </div>
            </div>

            {/* Despesas por Categoria */}
            <div className="bg-white p-5 sm:p-6 rounded-3xl border border-slate-200/80 shadow-xs">
              <div className="flex items-center gap-2 mb-4">
                <PieChart className="w-5 h-5 text-emerald-600" />
                <h2 className="text-sm sm:text-base font-bold text-slate-900">Despesas por Categoria</h2>
              </div>

              {isLoading ? (
                <div className="py-8 text-center text-slate-400 text-xs">Carregando dados...</div>
              ) : despesas.length === 0 ? (
                <p className="text-xs text-slate-400 py-6 text-center">Nenhuma despesa ativa registrada no período.</p>
              ) : (
                <div className="space-y-2.5">
                  {despesas.map((item, idx) => (
                    <div
                      key={idx}
                      className="flex items-center justify-between p-3 sm:p-3.5 rounded-2xl bg-slate-50 border border-slate-100"
                    >
                      <span className="text-xs font-bold text-slate-800">{item.categoria}</span>
                      <span className="text-xs font-black text-rose-600">
                        R$ {Number(item.total_gasto).toFixed(2).replace('.', ',')}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* ========== ABA ESTOQUE & INVENTÁRIO ========== */}
        {activeReportTab === 'estoque' && (
          <div className="space-y-4">
            {/* Cards resumo do estoque */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="bg-white p-5 rounded-3xl border border-slate-200/80 shadow-xs flex items-center justify-between">
                <div>
                  <span className="text-[10px] sm:text-xs font-bold uppercase tracking-wider text-slate-500">
                    Total de Itens em Estoque
                  </span>
                  <p className="text-2xl sm:text-3xl font-black text-indigo-700 mt-1">{totalItensEstoque}</p>
                  <p className="text-[10px] sm:text-[11px] text-slate-400 mt-1">unidades no inventário</p>
                </div>
                <div className="w-10 h-10 sm:w-12 sm:h-12 rounded-2xl bg-indigo-100 text-indigo-700 flex items-center justify-center shrink-0">
                  <Package className="w-5 h-5 sm:w-6 sm:h-6" />
                </div>
              </div>

              <div className="bg-white p-5 rounded-3xl border border-slate-200/80 shadow-xs flex items-center justify-between">
                <div>
                  <span className="text-[10px] sm:text-xs font-bold uppercase tracking-wider text-slate-500">
                    Custo Total em Estoque
                  </span>
                  <p className="text-2xl sm:text-3xl font-black text-emerald-700 mt-1">
                    R$ {totalCustoEstoque.toFixed(2).replace('.', ',')}
                  </p>
                  <p className="text-[10px] sm:text-[11px] text-slate-400 mt-1">valor de custo investido</p>
                </div>
                <div className="w-10 h-10 sm:w-12 sm:h-12 rounded-2xl bg-emerald-100 text-emerald-700 flex items-center justify-center shrink-0">
                  <TrendingUp className="w-5 h-5 sm:w-6 sm:h-6" />
                </div>
              </div>

              <div className="bg-white p-5 rounded-3xl border border-slate-200/80 shadow-xs flex items-center justify-between">
                <div>
                  <span className="text-[10px] sm:text-xs font-bold uppercase tracking-wider text-slate-500">
                    Itens Zerados / Esgotados
                  </span>
                  <p className={`text-2xl sm:text-3xl font-black mt-1 ${itensZerados.length > 0 ? 'text-rose-600' : 'text-slate-400'}`}>
                    {itensZerados.length}
                  </p>
                  <p className="text-[10px] sm:text-[11px] text-slate-400 mt-1">precisam reposição</p>
                </div>
                <div className={`w-10 h-10 sm:w-12 sm:h-12 rounded-2xl flex items-center justify-center shrink-0 ${
                  itensZerados.length > 0 ? 'bg-rose-100 text-rose-600' : 'bg-slate-100 text-slate-400'
                }`}>
                  <AlertTriangle className="w-5 h-5 sm:w-6 sm:h-6" />
                </div>
              </div>
            </div>

            {/* Tabela de Inventário */}
            <div className="bg-white rounded-3xl border border-slate-200/80 shadow-xs overflow-hidden">
              <div className="flex items-center gap-2 p-5 border-b border-slate-100">
                <Package className="w-5 h-5 text-emerald-600" />
                <h2 className="text-sm sm:text-base font-bold text-slate-900">Inventário Completo</h2>
                <span className="text-[10px] bg-slate-100 text-slate-600 font-bold px-2 py-0.5 rounded-full">
                  {inventario.length} produtos
                </span>
              </div>

              {isLoading ? (
                <div className="py-10 text-center text-slate-400 text-xs">Carregando inventário...</div>
              ) : inventario.length === 0 ? (
                <div className="py-10 text-center">
                  <Package className="w-10 h-10 text-slate-300 mx-auto mb-2" />
                  <p className="text-sm font-bold text-slate-500">Nenhum item cadastrado no catálogo</p>
                  <p className="text-xs text-slate-400 mt-1">
                    Cadastre produtos na aba Administração para vê-los aqui.
                  </p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="bg-slate-50 border-b border-slate-100">
                        <th className="text-left text-[10px] sm:text-xs font-bold text-slate-500 uppercase tracking-wider px-4 sm:px-5 py-3">
                          Produto
                        </th>
                        <th className="text-center text-[10px] sm:text-xs font-bold text-slate-500 uppercase tracking-wider px-3 py-3">
                          Saldo
                        </th>
                        <th className="text-right text-[10px] sm:text-xs font-bold text-slate-500 uppercase tracking-wider px-3 py-3 hidden sm:table-cell">
                          Custo Unit.
                        </th>
                        <th className="text-right text-[10px] sm:text-xs font-bold text-slate-500 uppercase tracking-wider px-3 py-3 hidden sm:table-cell">
                          Custo Total
                        </th>
                        <th className="text-right text-[10px] sm:text-xs font-bold text-slate-500 uppercase tracking-wider px-4 sm:px-5 py-3">
                          Venda Unit.
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {inventario.map((item) => {
                        const custoUnitario = item.saldo_atual > 0
                          ? Number(item.custo_total_estoque) / item.saldo_atual
                          : 0;
                        return (
                          <tr key={item.id} className="hover:bg-slate-50/60 transition-colors">
                            <td className="px-4 sm:px-5 py-3">
                              <span className="text-xs sm:text-sm font-bold text-slate-800">{item.nome}</span>
                            </td>
                            <td className="px-3 py-3 text-center">
                              <span
                                className={`inline-flex items-center justify-center min-w-[2.5rem] px-2 py-0.5 rounded-lg text-xs font-black ${
                                  item.saldo_atual <= 0
                                    ? 'bg-rose-100 text-rose-700 border border-rose-200'
                                    : item.saldo_atual <= 5
                                    ? 'bg-amber-100 text-amber-800 border border-amber-200'
                                    : 'bg-emerald-100 text-emerald-800 border border-emerald-200'
                                }`}
                              >
                                {item.saldo_atual}
                              </span>
                            </td>
                            <td className="px-3 py-3 text-right hidden sm:table-cell">
                              <span className="text-xs text-slate-500">
                                R$ {custoUnitario.toFixed(2).replace('.', ',')}
                              </span>
                            </td>
                            <td className="px-3 py-3 text-right hidden sm:table-cell">
                              <span className="text-xs font-bold text-slate-700">
                                R$ {Number(item.custo_total_estoque).toFixed(2).replace('.', ',')}
                              </span>
                            </td>
                            <td className="px-4 sm:px-5 py-3 text-right">
                              <span className="text-xs font-black text-emerald-700">
                                R$ {Number(item.valor_venda).toFixed(2).replace('.', ',')}
                              </span>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            {/* Alerta de itens zerados */}
            {itensZerados.length > 0 && (
              <div className="bg-rose-50 p-4 sm:p-5 rounded-3xl border border-rose-200/80 shadow-xs">
                <div className="flex items-center gap-2 mb-3">
                  <AlertTriangle className="w-5 h-5 text-rose-600 shrink-0" />
                  <h3 className="text-sm font-bold text-rose-800">
                    Itens que precisam de reposição ({itensZerados.length})
                  </h3>
                </div>
                <div className="flex flex-wrap gap-2">
                  {itensZerados.map((item) => (
                    <span
                      key={item.id}
                      className="text-xs font-bold bg-white text-rose-700 px-3 py-1.5 rounded-xl border border-rose-200"
                    >
                      {item.nome}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
