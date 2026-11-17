import React, { useState, useEffect, useMemo } from 'react';
import {
  Search,
  Plus,
  Minus,
  Trash2,
  CheckCircle2,
  AlertTriangle,
  QrCode,
  Banknote,
  CreditCard,
  X,
  Receipt,
  ShoppingBag,
  ArrowRight,
  ChevronUp,
  ChevronDown,
  History,
  RefreshCw,
} from 'lucide-react';
import { apiClient } from '../api/client';
import { useCartStore } from '../store/useCartStore';
import { useAuthStore } from '../store/useAuthStore';
import { useOrgStore } from '../store/useOrgStore';
import type { Evento, MovimentoCaixa, Item } from '../types';

interface PDVViewProps {
  activeEvento: Evento | null;
  activeMovimento: MovimentoCaixa | null;
  onNavigateToCaixa?: () => void;
}

interface VendaRecente {
  id: number;
  data_venda: string;
  data_hora_venda: string | null;
  responsavel: string;
  itens: Array<{
    id_item: number;
    nome: string;
    quantidade: number;
    valor_unitario: number | string;
    subtotal: number | string;
  }>;
  total: number | string;
}

export const PDVView: React.FC<PDVViewProps> = ({
  activeEvento,
  activeMovimento,
  onNavigateToCaixa,
}) => {
  const { user } = useAuthStore();
  const aliasEvento = useOrgStore((state) => state.config.alias_evento);
  const { items, addItem, updateQuantity, removeItem, clearCart, getTotalPrice, getTotalItems } =
    useCartStore();

  const [catalogGroups, setCatalogGroups] = useState<Record<string, Item[]>>({});
  const [catalogError, setCatalogError] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('Todos');
  const [searchQuery, setSearchQuery] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [recentSales, setRecentSales] = useState<VendaRecente[]>([]);
  const [isRecentSalesOpen, setIsRecentSalesOpen] = useState(false);
  const [isLoadingRecentSales, setIsLoadingRecentSales] = useState(false);
  const [recentSalesError, setRecentSalesError] = useState('');
  const [hasLoadedRecentSales, setHasLoadedRecentSales] = useState(false);

  // Controle de Carrinho no Celular
  const [isMobileCartOpen, setIsMobileCartOpen] = useState(false);

  // Modal de Pagamento
  const [isPaymentModalOpen, setIsPaymentModalOpen] = useState(false);
  const [paymentMethod, setPaymentMethod] = useState<'dinheiro' | 'pix' | 'cartao'>('dinheiro');
  const [amountReceived, setAmountReceived] = useState<number>(0);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [saleSuccess, setSaleSuccess] = useState<boolean>(false);
  const [lastSaleId, setLastSaleId] = useState<number | null>(null);
  const [saleError, setSaleError] = useState('');

  // Carrega Catálogo Agrupado
  const loadCatalog = async () => {
    setIsLoading(true);
    try {
      const resp = await apiClient.get('/catalogo/grupos');
      setCatalogGroups(resp.data || {});
      setCatalogError('');
    } catch (err) {
      console.error('Erro ao carregar catálogo', err);
      setCatalogError('Não foi possível carregar o catálogo. Verifique a conexão e tente novamente.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadCatalog();
  }, []);

  const loadRecentSales = async () => {
    setIsLoadingRecentSales(true);
    setRecentSalesError('');
    try {
      const response = await apiClient.get('/vendas/ultimas', { params: { limite: 10 } });
      setRecentSales(response.data || []);
      setHasLoadedRecentSales(true);
    } catch (err) {
      console.error('Erro ao carregar últimas vendas:', err);
      setRecentSalesError('Não foi possível carregar as últimas vendas.');
      setHasLoadedRecentSales(false);
    } finally {
      setIsLoadingRecentSales(false);
    }
  };

  const toggleRecentSales = () => {
    const opening = !isRecentSalesOpen;
    setIsRecentSalesOpen(opening);
    if (opening && (!hasLoadedRecentSales || recentSalesError)) void loadRecentSales();
  };

  // Lista linear de todos os itens com categoria
  const allItems = useMemo(() => {
    const list: (Item & { categoriaNome: string })[] = [];
    Object.entries(catalogGroups).forEach(([catName, itemList]) => {
      itemList.forEach((item) => {
        list.push({ ...item, categoriaNome: catName });
      });
    });
    return list;
  }, [catalogGroups]);

  // Categorias disponíveis
  const categories = useMemo(() => {
    return ['Todos', ...Object.keys(catalogGroups)];
  }, [catalogGroups]);

  // Itens filtrados por categoria e pesquisa
  const filteredItems = useMemo(() => {
    return allItems.filter((item) => {
      const matchesCategory =
        selectedCategory === 'Todos' || item.categoriaNome === selectedCategory;
      const matchesSearch = item.nome.toLowerCase().includes(searchQuery.toLowerCase());
      return matchesCategory && matchesSearch;
    });
  }, [allItems, selectedCategory, searchQuery]);

  const totalPrice = getTotalPrice();
  const totalItemsCount = getTotalItems();

  // Cálculo de troco
  const changeDue = useMemo(() => {
    if (paymentMethod !== 'dinheiro') return 0;
    return Math.max(0, amountReceived - totalPrice);
  }, [paymentMethod, amountReceived, totalPrice]);

  const handleOpenPayment = () => {
    if (items.length === 0) return;
    setSaleError('');
    setAmountReceived(totalPrice);
    setIsMobileCartOpen(false);
    setIsPaymentModalOpen(true);
  };

  const handleQuickAddBill = (val: number) => {
    setAmountReceived((prev) => prev + val);
  };

  const handleFinalizeSale = async () => {
    setSaleError('');
    if (!activeEvento) {
      alert(`Atenção: É necessário abrir ${aliasEvento} antes de registrar vendas.`);
      return;
    }
    if (!activeMovimento) {
      alert('Atenção: É necessário abrir um Movimento de Caixa antes de registrar vendas.');
      return;
    }

    setIsSubmitting(true);
    try {
      const payload = {
        eventoId: activeEvento.id,
        responsavelId: user?.id || 1,
        pessoaId: user?.id || null,
        movimentoCaixaId: activeMovimento.id,
        itens: items.map((i) => ({
          itemId: i.id_item,
          quantidade: i.quantidade,
          valor_unitario: Number(i.valor_unitario),
        })),
      };

      const resp = await apiClient.post('/vendas/', payload);
      setLastSaleId(resp.data?.id_venda || null);
      setSaleSuccess(true);
      clearCart();
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail
        || 'Não foi possível confirmar a venda. Confira a conexão e o histórico antes de tentar novamente.';
      setSaleError(errorMsg);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCloseSuccess = () => {
    setSaleSuccess(false);
    setIsPaymentModalOpen(false);
    setAmountReceived(0);
  };

  return (
    <div className="min-h-0 flex-1 flex flex-col lg:flex-row overflow-hidden bg-slate-100 relative">
      {/* Coluna da Esquerda: Catálogo e Produtos */}
      <div className="min-h-0 min-w-0 flex-1 flex flex-col p-3 sm:p-6 overflow-hidden pb-24 lg:pb-6">
        {/* Aviso se Caixa ou Evento não estiverem abertos */}
        {(!activeEvento || !activeMovimento) && (
          <div className="mb-3 p-3.5 rounded-2xl bg-amber-50 border border-amber-200 text-amber-800 flex items-center justify-between gap-3 shadow-xs">
            <div className="flex items-center gap-2.5 min-w-0">
              <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0" />
              <div className="text-xs sm:text-sm truncate">
                <span className="font-bold">Aviso: </span>
                {!activeEvento && `Abra ${aliasEvento}. `}
                {!activeMovimento && 'Abra um Caixa.'}
              </div>
            </div>
            {onNavigateToCaixa && <button
              onClick={onNavigateToCaixa}
              className="min-h-11 px-3 bg-amber-600 hover:bg-amber-700 text-white rounded-lg text-xs font-bold transition-colors cursor-pointer shrink-0"
            >
              Abrir
            </button>}
          </div>
        )}

        <section className="mb-3 rounded-2xl border border-slate-200/80 bg-white shadow-xs">
          <div className="flex items-center justify-between gap-3 p-3">
            <button
              type="button"
              onClick={toggleRecentSales}
              aria-expanded={isRecentSalesOpen}
              aria-controls="pdv-recent-sales"
              className="min-h-11 flex min-w-0 flex-1 items-center gap-2 text-left text-sm font-bold text-slate-800"
            >
              <History className="h-4 w-4 shrink-0 text-emerald-600" />
              <span>Últimas vendas</span>
              <span className="text-xs font-medium text-slate-400">(10)</span>
              {isRecentSalesOpen ? (
                <ChevronUp className="ml-auto h-4 w-4 shrink-0" />
              ) : (
                <ChevronDown className="ml-auto h-4 w-4 shrink-0" />
              )}
            </button>
            {isRecentSalesOpen && (
              <button
                type="button"
                onClick={() => void loadRecentSales()}
                disabled={isLoadingRecentSales}
                aria-label="Atualizar últimas vendas"
                className="min-h-11 min-w-11 rounded-lg p-1.5 text-slate-500 hover:bg-slate-100 disabled:opacity-50"
              >
                <RefreshCw className={`h-4 w-4 ${isLoadingRecentSales ? 'animate-spin' : ''}`} />
              </button>
            )}
          </div>
          {isRecentSalesOpen && (
            <div id="pdv-recent-sales" className="max-h-64 space-y-2 overflow-y-auto border-t border-slate-100 p-3">
              {isLoadingRecentSales ? (
                <p className="text-xs text-slate-500">Carregando vendas...</p>
              ) : recentSalesError ? (
                <p role="alert" className="text-xs font-medium text-rose-700">{recentSalesError}</p>
              ) : recentSales.length === 0 ? (
                <p className="text-xs text-slate-500">Nenhuma venda registrada.</p>
              ) : (
                recentSales.map((sale) => (
                  <article key={sale.id} className="rounded-xl border border-slate-100 bg-slate-50 p-2.5">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="text-xs font-bold text-slate-800">Venda #{sale.id}</p>
                        <p className="text-[11px] text-slate-500">
                          {sale.data_hora_venda
                            ? new Date(sale.data_hora_venda).toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' })
                            : `${sale.data_venda.split('-').reverse().join('/')} · horário não registrado`}
                        </p>
                      </div>
                      <p className="whitespace-nowrap text-xs font-black text-emerald-700">
                        R$ {Number(sale.total).toFixed(2).replace('.', ',')}
                      </p>
                    </div>
                    <ul className="mt-1.5 space-y-0.5">
                      {sale.itens.map((item, index) => (
                        <li key={`${sale.id}-${item.id_item}-${index}`} className="text-[11px] text-slate-600">
                          {item.quantidade}× {item.nome} · R$ {Number(item.subtotal).toFixed(2).replace('.', ',')}
                        </li>
                      ))}
                    </ul>
                    <p className="mt-1.5 text-[11px] text-slate-500">Responsável: {sale.responsavel}</p>
                  </article>
                ))
              )}
            </div>
          )}
        </section>

        {/* Barra de Pesquisa e Filtro de Categorias */}
        <div className="bg-white rounded-2xl shadow-xs border border-slate-200/80 p-3 sm:p-4 mb-3 sm:mb-4">
          <div className="relative mb-2.5">
            <Search className="w-4 h-4 sm:w-5 sm:h-5 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Buscar produto pelo nome..."
              className="min-h-11 w-full pl-10 sm:pl-11 pr-4 py-2 sm:py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 placeholder-slate-400 text-xs sm:text-sm focus:outline-hidden focus:ring-2 focus:ring-emerald-500 font-medium"
            />
          </div>

          {/* Categorias Pills */}
          <div className="flex items-center gap-1.5 sm:gap-2 overflow-x-auto pb-1 scrollbar-thin">
            {categories.map((cat) => (
              <button
                key={cat}
                onClick={() => setSelectedCategory(cat)}
                className={`min-h-11 px-3 rounded-xl text-xs font-bold transition-all shrink-0 cursor-pointer ${
                  selectedCategory === cat
                    ? 'bg-emerald-600 text-white shadow-xs'
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                }`}
              >
                {cat}
              </button>
            ))}
          </div>
        </div>

        {/* Grade de Produtos */}
        <div className="min-h-0 flex-1 overflow-y-auto pr-1">
          {isLoading ? (
            <div className="h-full flex items-center justify-center text-slate-400 text-sm font-medium">
              Carregando produtos...
            </div>
          ) : catalogError ? (
            <div className="flex h-full flex-col items-center justify-center gap-3 text-center text-sm text-rose-700">
              <p role="alert">{catalogError}</p>
              <button
                type="button"
                onClick={() => void loadCatalog()}
                className="min-h-11 rounded-xl bg-emerald-600 px-4 font-bold text-white"
              >
                Tentar novamente
              </button>
            </div>
          ) : filteredItems.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-slate-400 gap-2">
              <ShoppingBag className="w-12 h-12 text-slate-300" />
              <p className="text-sm font-medium">Nenhum produto encontrado.</p>
            </div>
          ) : (
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 xl:grid-cols-5 gap-2.5 sm:gap-3">
              {filteredItems.map((item) => {
                const inCart = items.find((i) => i.id_item === item.id);
                return (
                  <button
                    key={item.id}
                    onClick={() => addItem(item, 1)}
                    className="group relative flex min-h-28 flex-col justify-between p-3 sm:p-3.5 bg-white hover:bg-emerald-50/50 rounded-2xl border border-slate-200/80 hover:border-emerald-300 shadow-xs hover:shadow-md transition-all text-left cursor-pointer active:scale-98"
                  >
                    {inCart && (
                      <span className="absolute -top-1.5 -right-1.5 w-5 h-5 sm:w-6 sm:h-6 bg-emerald-600 text-white text-[10px] sm:text-xs font-black rounded-full flex items-center justify-center shadow-xs">
                        {inCart.quantidade}
                      </span>
                    )}
                    <div>
                      <span className="text-[9px] sm:text-[10px] font-bold uppercase tracking-wider text-emerald-700 bg-emerald-100/60 px-1.5 py-0.5 rounded">
                        {item.categoriaNome}
                      </span>
                      <h3 className="font-bold text-slate-900 text-xs sm:text-sm mt-1.5 line-clamp-2 leading-snug">
                        {item.nome}
                      </h3>
                    </div>
                    <div className="mt-2.5 flex items-center justify-between pt-2 border-t border-slate-100">
                      <span className="text-xs sm:text-sm font-black text-slate-800">
                        R$ {Number(item.valor_venda).toFixed(2).replace('.', ',')}
                      </span>
                      <div className="w-6 h-6 sm:w-7 sm:h-7 rounded-lg bg-emerald-100 text-emerald-700 flex items-center justify-center group-hover:bg-emerald-600 group-hover:text-white transition-colors">
                        <Plus className="w-3.5 h-3.5 sm:w-4 sm:h-4" />
                      </div>
                    </div>
                  </button>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Coluna Desktop: Carrinho Fixo Lateral */}
      <div className="hidden lg:flex w-96 bg-white border-l border-slate-200 flex-col shadow-lg z-20">
        <div className="p-4 border-b border-slate-100 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Receipt className="w-5 h-5 text-emerald-600" />
            <h2 className="font-bold text-slate-900 text-base">Pedido Atual</h2>
            <span className="text-xs bg-slate-100 text-slate-700 font-semibold px-2 py-0.5 rounded-full">
              {totalItemsCount} {totalItemsCount === 1 ? 'item' : 'itens'}
            </span>
          </div>
          {items.length > 0 && (
            <button
              onClick={clearCart}
              className="text-xs text-rose-500 hover:text-rose-700 font-semibold transition-colors cursor-pointer"
            >
              Limpar
            </button>
          )}
        </div>

        {/* Lista de Itens no Desktop */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {items.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-slate-400 gap-2 py-10">
              <ShoppingBag className="w-10 h-10 text-slate-300" />
              <p className="text-sm font-medium">O carrinho está vazio</p>
              <p className="text-xs text-slate-400 text-center max-w-[200px]">
                Toque nos itens do catálogo ao lado para adicioná-los.
              </p>
            </div>
          ) : (
            items.map((cartItem) => (
              <div
                key={cartItem.id_item}
                className="flex items-center justify-between p-3 rounded-xl bg-slate-50 border border-slate-200/80"
              >
                <div className="flex-1 min-w-0 pr-2">
                  <h4 className="font-semibold text-slate-900 text-xs truncate">{cartItem.nome}</h4>
                  <p className="text-xs font-bold text-slate-600 mt-0.5">
                    R$ {(cartItem.quantidade * cartItem.valor_unitario).toFixed(2).replace('.', ',')}
                    <span className="text-[10px] font-normal text-slate-400 ml-1">
                      (R$ {cartItem.valor_unitario.toFixed(2).replace('.', ',')} cada)
                    </span>
                  </p>
                </div>

                <div className="flex items-center gap-1.5 shrink-0">
                  <button
                    onClick={() => updateQuantity(cartItem.id_item, -1)}
                    aria-label={`Diminuir quantidade de ${cartItem.nome}`}
                    className="h-11 w-11 rounded-lg bg-white border border-slate-200 text-slate-700 hover:bg-slate-100 flex items-center justify-center cursor-pointer"
                  >
                    <Minus className="w-3.5 h-3.5" />
                  </button>
                  <span className="w-6 text-center text-xs font-bold text-slate-800">
                    {cartItem.quantidade}
                  </span>
                  <button
                    onClick={() => updateQuantity(cartItem.id_item, 1)}
                    aria-label={`Aumentar quantidade de ${cartItem.nome}`}
                    className="h-11 w-11 rounded-lg bg-white border border-slate-200 text-slate-700 hover:bg-slate-100 flex items-center justify-center cursor-pointer"
                  >
                    <Plus className="w-3.5 h-3.5" />
                  </button>
                  <button
                    onClick={() => removeItem(cartItem.id_item)}
                    aria-label={`Remover ${cartItem.nome} do carrinho`}
                    className="h-11 w-11 rounded-lg text-slate-400 hover:text-rose-600 hover:bg-rose-50 flex items-center justify-center cursor-pointer ml-1"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Resumo e Botão Desktop */}
        <div className="p-4 bg-slate-50 border-t border-slate-200 space-y-3">
          <div className="flex justify-between items-baseline">
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Total</span>
            <span className="text-2xl font-black text-slate-900">
              R$ {totalPrice.toFixed(2).replace('.', ',')}
            </span>
          </div>

          <button
            onClick={handleOpenPayment}
            disabled={items.length === 0}
            className="min-h-11 w-full py-3.5 px-4 bg-emerald-600 hover:bg-emerald-700 disabled:bg-slate-300 text-white font-bold rounded-xl shadow-lg shadow-emerald-600/20 hover:shadow-xl transition-all flex items-center justify-center gap-2 text-sm cursor-pointer disabled:cursor-not-allowed"
          >
            <span>Cobrar / Finalizar</span>
            <span className="font-mono bg-emerald-700/60 px-2 py-0.5 rounded text-xs">
              R$ {totalPrice.toFixed(2).replace('.', ',')}
            </span>
          </button>
        </div>
      </div>

      {/* Barra Flutuante de Carrinho para Celular (Mobile) */}
      {items.length > 0 && (
        <div className="lg:hidden fixed bottom-[calc(4.25rem_+_env(safe-area-inset-bottom))] left-0 right-0 p-3 bg-white/95 backdrop-blur-md border-t border-slate-200 z-30 shadow-2xl">
          <button
            onClick={() => setIsMobileCartOpen(true)}
            className="min-h-11 w-full py-3 px-4 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-2xl shadow-lg flex items-center justify-between transition-transform active:scale-98 cursor-pointer"
          >
            <div className="flex items-center gap-2.5">
              <span className="w-6 h-6 rounded-full bg-emerald-800 text-white text-xs font-black flex items-center justify-center">
                {totalItemsCount}
              </span>
              <span className="text-xs uppercase font-extrabold tracking-wider">Ver Carrinho</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-base font-black">
                R$ {totalPrice.toFixed(2).replace('.', ',')}
              </span>
              <ChevronUp className="w-4 h-4" />
            </div>
          </button>
        </div>
      )}

      {/* Drawer / Modal de Carrinho no Celular */}
      {isMobileCartOpen && (
        <div className="lg:hidden fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex flex-col justify-end">
          <div className="bg-white rounded-t-3xl max-h-[85dvh] flex flex-col shadow-2xl overflow-hidden animate-slide-up">
            <div className="p-4 border-b border-slate-100 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Receipt className="w-5 h-5 text-emerald-600" />
                <h3 className="font-black text-slate-900 text-base">Itens do Pedido ({totalItemsCount})</h3>
              </div>
              <button
                onClick={() => setIsMobileCartOpen(false)}
                aria-label="Fechar carrinho"
                className="min-h-11 min-w-11 rounded-lg text-slate-400 hover:text-slate-600 cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-3">
              {items.map((cartItem) => (
                <div
                  key={cartItem.id_item}
                  className="flex items-center justify-between p-3 rounded-2xl bg-slate-50 border border-slate-200/80"
                >
                  <div className="flex-1 min-w-0 pr-2">
                    <h4 className="font-bold text-slate-900 text-xs truncate">{cartItem.nome}</h4>
                    <p className="text-xs font-bold text-slate-600 mt-0.5">
                      R$ {(cartItem.quantidade * cartItem.valor_unitario).toFixed(2).replace('.', ',')}
                    </p>
                  </div>
                  <div className="flex items-center gap-1.5 shrink-0">
                    <button
                      onClick={() => updateQuantity(cartItem.id_item, -1)}
                      aria-label={`Diminuir quantidade de ${cartItem.nome}`}
                      className="h-11 w-11 rounded-lg bg-white border border-slate-200 text-slate-700 flex items-center justify-center"
                    >
                      <Minus className="w-3.5 h-3.5" />
                    </button>
                    <span className="w-6 text-center text-xs font-bold text-slate-800">
                      {cartItem.quantidade}
                    </span>
                    <button
                      onClick={() => updateQuantity(cartItem.id_item, 1)}
                      aria-label={`Aumentar quantidade de ${cartItem.nome}`}
                      className="h-11 w-11 rounded-lg bg-white border border-slate-200 text-slate-700 flex items-center justify-center"
                    >
                      <Plus className="w-3.5 h-3.5" />
                    </button>
                    <button
                      onClick={() => removeItem(cartItem.id_item)}
                      aria-label={`Remover ${cartItem.nome} do carrinho`}
                      className="h-11 w-11 rounded-lg text-slate-400 hover:text-rose-600 flex items-center justify-center ml-1"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              ))}
            </div>

            <div className="p-4 pb-[calc(1rem_+_env(safe-area-inset-bottom))] bg-slate-50 border-t border-slate-200 space-y-3">
              <div className="flex justify-between items-baseline">
                <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Total</span>
                <span className="text-2xl font-black text-slate-900">
                  R$ {totalPrice.toFixed(2).replace('.', ',')}
                </span>
              </div>
              <button
                onClick={handleOpenPayment}
                className="min-h-11 w-full py-3.5 px-4 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-2xl shadow-lg flex items-center justify-center gap-2 text-sm cursor-pointer"
              >
                <span>Avançar para Pagamento</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal de Pagamento & Troco */}
      {isPaymentModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 animate-fade-in">
          <div className="bg-white rounded-3xl max-w-md w-full shadow-2xl border border-slate-100 overflow-hidden">
            {saleSuccess ? (
              <div className="p-8 text-center flex flex-col items-center">
                <div className="w-16 h-16 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center mb-4">
                  <CheckCircle2 className="w-10 h-10" />
                </div>
                <h3 className="text-2xl font-black text-slate-900">Venda Concluída!</h3>
                <p className="text-sm text-slate-500 mt-1">
                  Venda #{lastSaleId} registrada com baixa de estoque automática.
                </p>

                {paymentMethod === 'dinheiro' && changeDue > 0 && (
                  <div className="mt-4 p-4 rounded-2xl bg-emerald-50 border border-emerald-200 w-full">
                    <span className="text-xs uppercase font-bold text-emerald-700">Troco a Devolver</span>
                    <p className="text-2xl font-black text-emerald-800">
                      R$ {changeDue.toFixed(2).replace('.', ',')}
                    </p>
                  </div>
                )}

                <button
                  onClick={handleCloseSuccess}
                  className="mt-6 w-full py-3 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-xl text-sm transition-colors cursor-pointer"
                >
                  Próxima Venda (Novo Cliente)
                </button>
              </div>
            ) : (
              <div className="p-6">
                <div className="flex items-center justify-between pb-4 border-b border-slate-100">
                  <h3 className="font-black text-slate-900 text-lg">Pagamento do Pedido</h3>
                  <button
                    onClick={() => setIsPaymentModalOpen(false)}
                    className="p-1 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 cursor-pointer"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>

                {saleError && (
                  <p role="alert" className="mt-4 rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm font-medium text-rose-800">
                    {saleError}
                  </p>
                )}

                <div className="grid grid-cols-3 gap-2 my-5">
                  <button
                    type="button"
                    onClick={() => setPaymentMethod('dinheiro')}
                    className={`p-3 rounded-2xl border flex flex-col items-center gap-1.5 font-bold text-xs transition-all cursor-pointer ${
                      paymentMethod === 'dinheiro'
                        ? 'border-emerald-600 bg-emerald-50/50 text-emerald-800 shadow-xs'
                        : 'border-slate-200 text-slate-600 hover:bg-slate-50'
                    }`}
                  >
                    <Banknote className="w-5 h-5" />
                    <span>Dinheiro</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => setPaymentMethod('pix')}
                    className={`p-3 rounded-2xl border flex flex-col items-center gap-1.5 font-bold text-xs transition-all cursor-pointer ${
                      paymentMethod === 'pix'
                        ? 'border-emerald-600 bg-emerald-50/50 text-emerald-800 shadow-xs'
                        : 'border-slate-200 text-slate-600 hover:bg-slate-50'
                    }`}
                  >
                    <QrCode className="w-5 h-5" />
                    <span>Pix</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => setPaymentMethod('cartao')}
                    className={`p-3 rounded-2xl border flex flex-col items-center gap-1.5 font-bold text-xs transition-all cursor-pointer ${
                      paymentMethod === 'cartao'
                        ? 'border-emerald-600 bg-emerald-50/50 text-emerald-800 shadow-xs'
                        : 'border-slate-200 text-slate-600 hover:bg-slate-50'
                    }`}
                  >
                    <CreditCard className="w-5 h-5" />
                    <span>Cartão</span>
                  </button>
                </div>

                {paymentMethod === 'dinheiro' && (
                  <div className="space-y-4">
                    <div>
                      <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                        Valor Recebido do Cliente
                      </label>
                      <input
                        type="number"
                        step="0.50"
                        value={amountReceived || ''}
                        onChange={(e) => setAmountReceived(parseFloat(e.target.value) || 0)}
                        className="w-full text-xl font-bold px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 focus:bg-white focus:outline-hidden focus:ring-2 focus:ring-emerald-500"
                      />
                    </div>

                    <div className="flex gap-2">
                      {[10, 20, 50, 100].map((val) => (
                        <button
                          key={val}
                          type="button"
                          onClick={() => handleQuickAddBill(val)}
                          className="min-h-11 flex-1 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold rounded-lg transition-colors cursor-pointer"
                        >
                          +{val}
                        </button>
                      ))}
                    </div>

                    <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 flex justify-between items-center">
                      <span className="text-xs font-bold text-slate-600">Troco:</span>
                      <span
                        className={`text-lg font-black ${
                          changeDue >= 0 ? 'text-emerald-700' : 'text-rose-600'
                        }`}
                      >
                        R$ {changeDue.toFixed(2).replace('.', ',')}
                      </span>
                    </div>
                  </div>
                )}

                {paymentMethod === 'pix' && (
                  <div className="p-4 bg-emerald-50/60 rounded-2xl border border-emerald-200/80 flex flex-col items-center text-center">
                    <QrCode className="w-24 h-24 text-emerald-800 mb-2" />
                    <p className="text-xs font-bold text-emerald-900">Chave Pix da Instituição</p>
                    <p className="text-xs font-mono text-emerald-700 mt-1 select-all bg-emerald-100/70 px-2 py-1 rounded">
                      financeiro@ongimpacto.org.br
                    </p>
                  </div>
                )}

                {paymentMethod === 'cartao' && (
                  <div className="p-4 bg-slate-50 rounded-2xl border border-slate-200 text-center">
                    <CreditCard className="w-10 h-10 text-slate-400 mx-auto mb-2" />
                    <p className="text-xs font-bold text-slate-700">Aproxime ou insira o cartão na maquininha</p>
                    <p className="text-[11px] text-slate-500 mt-0.5">Confirme após a emissão do comprovante.</p>
                  </div>
                )}

                <div className="mt-6 flex gap-3">
                  <button
                    type="button"
                    onClick={() => setIsPaymentModalOpen(false)}
                    className="flex-1 py-3 border border-slate-200 hover:bg-slate-100 rounded-xl text-slate-700 font-bold text-xs transition-colors cursor-pointer"
                  >
                    Voltar
                  </button>
                  <button
                    type="button"
                    disabled={isSubmitting || (paymentMethod === 'dinheiro' && amountReceived < totalPrice)}
                    onClick={handleFinalizeSale}
                    className="flex-2 py-3 bg-emerald-600 hover:bg-emerald-700 disabled:bg-slate-300 text-white font-bold rounded-xl text-xs transition-all shadow-md shadow-emerald-600/20 cursor-pointer disabled:cursor-not-allowed flex items-center justify-center gap-2"
                  >
                    {isSubmitting ? 'Registrando...' : 'Confirmar Pagamento'}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
