import React, { useState, useEffect } from 'react';
import {
  Settings,
  Package,
  Layers,
  Users,
  BarChart3,
  Plus,
  Search,
  CheckCircle2,
  AlertCircle,
  ArrowDownCircle,
  ArrowUpCircle,
  Shield,
  Smartphone,
} from 'lucide-react';
import { apiClient } from '../api/client';
import { useAuthStore } from '../store/useAuthStore';
import { ConnectMobileModal } from './ConnectMobileModal';
import { RelatoriosView } from './RelatoriosView';
import { CalendarioView } from './CalendarioView';
import { FacilitadoresView } from './FacilitadoresView';
import { AtividadesView } from './AtividadesView';
import type { Categoria, Item, Usuario, Evento } from '../types';

interface AdminViewProps {
  activeEvento: Evento | null;
  onRefreshState: () => Promise<void>;
}

export const AdminView: React.FC<AdminViewProps> = ({ activeEvento, onRefreshState }) => {
  const { user, setUser, setNotice, logout } = useAuthStore();
  const [activeTab, setActiveTab] = useState<'produtos' | 'estoque' | 'usuarios' | 'relatorios' | 'calendario' | 'facilitadores' | 'atividades'>('produtos');
  const [termos, setTermos] = useState({ termo_atendente: 'Atendente', termo_atividade: 'Entidade / Serviço' });

  // Estados de Produtos e Categorias
  const [itens, setItens] = useState<Item[]>([]);
  const [categorias, setCategorias] = useState<Categoria[]>([]);
  const [searchProduto, setSearchProduto] = useState('');

  // Formulário Produto
  const [nomeProduto, setNomeProduto] = useState('');
  const [idCategoriaProduto, setIdCategoriaProduto] = useState<number | ''>('');
  const [valorCompra, setValorCompra] = useState<number | ''>('');
  const [valorVenda, setValorVenda] = useState<number>(0);
  const [estoqueMinimo, setEstoqueMinimo] = useState(0);
  const [editItem, setEditItem] = useState<Item | null>(null);

  // Formulário Categoria
  const [nomeCategoria, setNomeCategoria] = useState('');
  const [descCategoria, setDescCategoria] = useState('');

  // Formulário Entrada de Estoque
  const [estoqueItemId, setEstoqueItemId] = useState<number | ''>('');
  const [estoqueQtd, setEstoqueQtd] = useState<number>(10);
  const [estoqueTipo, setEstoqueTipo] = useState<'Entrada' | 'Saida'>('Entrada');
  const [estoqueOrigem, setEstoqueOrigem] = useState<string>('Doação');

  // Formulário Usuário
  const [usuarios, setUsuarios] = useState<Usuario[]>([]);
  const [nomeUser, setNomeUser] = useState('');
  const [emailUser, setEmailUser] = useState('');
  const [funcaoUser, setFuncaoUser] = useState('Voluntário');
  const [roleUser, setRoleUser] = useState<'Administrador' | 'Operador' | 'Recepcionista' | 'Vendedor'>('Vendedor');
  const [senhaUser, setSenhaUser] = useState('');
  const [requirePasswordChange, setRequirePasswordChange] = useState(true);
  const [editingUser, setEditingUser] = useState<Usuario | null>(null);
  const [editingFuncao, setEditingFuncao] = useState('');
  const [editingRole, setEditingRole] = useState<Usuario['role']>('Vendedor');
  const [editingStatus, setEditingStatus] = useState<Usuario['status']>('Ativo');

  // Feedback e Modal
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isMobileModalOpen, setIsMobileModalOpen] = useState(false);

  // Carrega Catálogo e Categorias
  const loadCatalogData = async () => {
    try {
      const [catRes, itemRes] = await Promise.all([
        apiClient.get('/catalogo/categorias'),
        apiClient.get('/catalogo/itens'),
      ]);
      setCategorias(catRes.data || []);
      setItens(itemRes.data || []);
      if (catRes.data?.length > 0 && idCategoriaProduto === '') {
        setIdCategoriaProduto(catRes.data[0].id);
      }
      if (itemRes.data?.length > 0 && estoqueItemId === '') {
        setEstoqueItemId(itemRes.data[0].id);
      }
    } catch (err) {
      console.error('Erro ao carregar catálogo:', err);
    }
  };

  // Carrega Usuários
  const loadUsers = async () => {
    try {
      const res = await apiClient.get('/usuarios/');
      setUsuarios(res.data || []);
    } catch (err) {
      console.error('Erro ao carregar usuários:', err);
    }
  };


  const showFeedback = (type: 'success' | 'error', text: string) => {
    setFeedback({ type, text });
    setTimeout(() => setFeedback(null), 4000);
  };

  useEffect(() => {
    loadCatalogData();
    loadUsers();
    apiClient.get('/organizacao/config').then(res => setTermos(res.data)).catch(() => {
      showFeedback('error', 'Não foi possível carregar os termos da organização.');
    });
  }, []);

  // Salvar Novo Produto
  const handleSaveProduto = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!nomeProduto.trim() || (!idCategoriaProduto && !editItem)) {
      showFeedback('error', 'Preencha o nome e selecione uma categoria.');
      return;
    }
    setIsLoading(true);
    try {
      const payload = {
        nome: nomeProduto,
        id_categoria: idCategoriaProduto === '' ? null : Number(idCategoriaProduto),
        valor_compra: valorCompra === '' ? null : Number(valorCompra),
        valor_venda: Number(valorVenda),
        estoque_minimo: estoqueMinimo,
        status: editItem?.status || 'Ativo',
      };
      if (editItem) await apiClient.put(`/catalogo/itens/${editItem.id}`, payload);
      else await apiClient.post('/catalogo/itens', payload);
      showFeedback('success', `Produto "${nomeProduto}" cadastrado com sucesso!`);
      setNomeProduto('');
      setValorCompra('');
      setValorVenda(0);
      setEstoqueMinimo(0);
      setEditItem(null);
      await loadCatalogData();
    } catch (err: any) {
      showFeedback('error', err.response?.data?.detail || 'Erro ao cadastrar produto.');
    } finally {
      setIsLoading(false);
    }
  };

  // Salvar Nova Categoria
  const handleSaveCategoria = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!nomeCategoria) return;
    setIsLoading(true);
    try {
      await apiClient.post('/catalogo/categorias', {
        nome: nomeCategoria,
        descricao: descCategoria || '',
        status: 'Ativo',
      });
      showFeedback('success', `Categoria "${nomeCategoria}" criada!`);
      setNomeCategoria('');
      setDescCategoria('');
      await loadCatalogData();
    } catch (err: any) {
      showFeedback('error', err.response?.data?.detail || 'Erro ao criar categoria.');
    } finally {
      setIsLoading(false);
    }
  };

  // Salvar movimentação manual de estoque
  const handleMovimentacaoEstoque = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!estoqueItemId || !activeEvento) {
      showFeedback('error', !activeEvento ? 'Abra um Evento antes de lançar estoque.' : 'Selecione um produto.');
      return;
    }
    if (!estoqueOrigem.trim()) {
      showFeedback('error', 'Informe a origem ou o motivo da movimentação.');
      return;
    }
    setIsLoading(true);
    try {
      await apiClient.post(estoqueTipo === 'Entrada' ? '/estoque/entrada' : '/estoque/saida', {
        itemId: Number(estoqueItemId),
        quantidade: Number(estoqueQtd),
        origem_recurso: estoqueOrigem.trim(),
        usuarioId: user?.id || 1,
        eventoId: activeEvento.id,
      });
      showFeedback('success', `${estoqueTipo} de ${estoqueQtd} unidades registrada no estoque!`);
      setEstoqueQtd(10);
      setEstoqueOrigem('');
    } catch (err: any) {
      showFeedback('error', err.response?.data?.detail || 'Erro ao registrar movimentação de estoque.');
    } finally {
      setIsLoading(false);
    }
  };

  // Salvar Novo Usuário
  const handleSaveUser = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!nomeUser || !emailUser || !senhaUser) {
      showFeedback('error', 'Preencha todos os campos do usuário.');
      return;
    }
    setIsLoading(true);
    try {
      await apiClient.post('/usuarios/', {
        nome: nomeUser,
        email: emailUser,
        funcao: funcaoUser,
        role: roleUser,
        status: 'Ativo',
        senha: senhaUser,
        require_password_change: requirePasswordChange,
      });
      showFeedback('success', `Usuário "${nomeUser}" cadastrado!`);
      setNomeUser('');
      setEmailUser('');
      setSenhaUser('');
      setRequirePasswordChange(true);
      await loadUsers();
    } catch (err: any) {
      showFeedback('error', err.response?.data?.detail || 'Erro ao cadastrar usuário.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleUpdateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingUser) return;

    setIsLoading(true);
    try {
      await apiClient.put(`/usuarios/${editingUser.id}/role`, {
        role: editingRole,
        status: editingStatus,
        funcao: editingFuncao,
      });
      if (editingUser.id === user?.id) {
        if (editingStatus === 'Inativo') {
          setNotice('Sua conta foi desativada. Entre em contato com um administrador.');
          logout();
          return;
        }
        setUser({ ...user, role: editingRole, status: editingStatus, funcao: editingFuncao });
      }
      showFeedback('success', `Usuário "${editingUser.nome}" atualizado.`);
      setEditingUser(null);
      await loadUsers();
    } catch (err: any) {
      showFeedback('error', err.response?.data?.detail || 'Erro ao atualizar usuário.');
    } finally {
      setIsLoading(false);
    }
  };

  const startEditingUser = (usuario: Usuario) => {
    setEditingUser(usuario);
    setEditingFuncao(usuario.funcao || '');
    setEditingRole(usuario.role);
    setEditingStatus(usuario.status);
  };

  const filteredProdutos = itens.filter((i) =>
    i.nome.toLowerCase().includes(searchProduto.toLowerCase())
  );

  return (
    <div className="flex-1 overflow-y-auto bg-slate-100 p-4 sm:p-6 lg:p-8">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Cabeçalho */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-black text-slate-900 tracking-tight flex items-center gap-2.5">
              <Settings className="w-7 h-7 text-emerald-600" />
              Painel de Administração & Cadastros
            </h1>
            <p className="text-xs sm:text-sm text-slate-500 font-medium">
              Gerencie catálogo de produtos, entradas de estoque, voluntários e métricas financeiras.
            </p>
          </div>

          <button
            onClick={() => setIsMobileModalOpen(true)}
            className="h-10 px-4 inline-flex items-center gap-2 bg-emerald-600 hover:bg-emerald-700 active:scale-95 text-white rounded-xl text-xs font-bold shadow-xs transition-all cursor-pointer shrink-0"
          >
            <Smartphone className="w-4 h-4" />
            <span>Conectar Celular / Wi-Fi</span>
          </button>
        </div>

        {/* Feedback visual */}
        {feedback && (
          <div
            className={`p-4 rounded-2xl border text-sm font-semibold flex items-center gap-3 animate-fade-in ${
              feedback.type === 'success'
                ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
                : 'bg-rose-50 border-rose-200 text-rose-800'
            }`}
          >
            {feedback.type === 'success' ? (
              <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
            ) : (
              <AlertCircle className="w-5 h-5 text-rose-600 shrink-0" />
            )}
            <span>{feedback.text}</span>
          </div>
        )}

        {/* Barra de Sub-abas */}
        <div className="flex items-center gap-2 bg-white p-1.5 rounded-2xl border border-slate-200/80 shadow-xs overflow-x-auto">
          <button onClick={() => setActiveTab('calendario')} className={`h-10 px-4 rounded-xl text-xs font-bold whitespace-nowrap cursor-pointer ${activeTab === 'calendario' ? 'bg-slate-900 text-white' : 'text-slate-600'}`}>Calendário & Eventos</button>
          <button onClick={() => setActiveTab('facilitadores')} className={`h-10 px-4 rounded-xl text-xs font-bold whitespace-nowrap cursor-pointer ${activeTab === 'facilitadores' ? 'bg-slate-900 text-white' : 'text-slate-600'}`}>{termos.termo_atendente}</button>
          <button onClick={() => setActiveTab('atividades')} className={`h-10 px-4 rounded-xl text-xs font-bold whitespace-nowrap cursor-pointer ${activeTab === 'atividades' ? 'bg-slate-900 text-white' : 'text-slate-600'}`}>{termos.termo_atividade}</button>
          <button
            onClick={() => setActiveTab('produtos')}
            className={`h-10 px-4 inline-flex items-center gap-2 rounded-xl text-xs font-bold whitespace-nowrap transition-all cursor-pointer shrink-0 ${
              activeTab === 'produtos' ? 'bg-slate-900 text-white shadow-xs' : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
            }`}
          >
            <Package className="w-4 h-4" />
            <span>Produtos & Categorias</span>
          </button>

          <button
            onClick={() => setActiveTab('estoque')}
            className={`h-10 px-4 inline-flex items-center gap-2 rounded-xl text-xs font-bold whitespace-nowrap transition-all cursor-pointer shrink-0 ${
              activeTab === 'estoque' ? 'bg-slate-900 text-white shadow-xs' : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
            }`}
          >
            <ArrowDownCircle className="w-4 h-4" />
            <span>Entrada de Estoque</span>
          </button>

          <button
            onClick={() => setActiveTab('usuarios')}
            className={`h-10 px-4 inline-flex items-center gap-2 rounded-xl text-xs font-bold whitespace-nowrap transition-all cursor-pointer shrink-0 ${
              activeTab === 'usuarios' ? 'bg-slate-900 text-white shadow-xs' : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
            }`}
          >
            <Users className="w-4 h-4" />
            <span>Voluntários & Usuários</span>
          </button>

          <button
            onClick={() => setActiveTab('relatorios')}
            className={`h-10 px-4 inline-flex items-center gap-2 rounded-xl text-xs font-bold whitespace-nowrap transition-all cursor-pointer shrink-0 ${
              activeTab === 'relatorios' ? 'bg-slate-900 text-white shadow-xs' : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
            }`}
          >
            <BarChart3 className="w-4 h-4" />
            <span>DRE & Relatórios</span>
          </button>
        </div>

        {/* Conteúdo da Aba 1: Produtos e Categorias */}
        {activeTab === 'produtos' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Formulário Novo Produto */}
              <div className="bg-white p-6 rounded-3xl border border-slate-200/80 shadow-xs">
                <div className="flex items-center gap-2 mb-4 pb-3 border-b border-slate-100">
                  <Package className="w-5 h-5 text-emerald-600" />
                  <h3 className="font-black text-slate-900 text-base">{editItem ? 'Editar Produto' : 'Cadastrar Novo Produto'}</h3>
                </div>

                <form onSubmit={handleSaveProduto} className="space-y-4">
                  <div>
                    <label className="block text-xs font-bold text-slate-700 uppercase mb-1">
                      Nome do Produto / Item
                    </label>
                    <input
                      type="text"
                      required
                      value={nomeProduto}
                      onChange={(e) => setNomeProduto(e.target.value)}
                      placeholder="Ex: Coca-Cola Lata, Pastel de Queijo, Camiseta..."
                      className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 text-sm focus:bg-white focus:ring-2 focus:ring-emerald-500 font-medium"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-slate-700 uppercase mb-1">
                      Categoria do Catálogo
                    </label>
                    <select
                      value={idCategoriaProduto}
                      onChange={(e) => setIdCategoriaProduto(e.target.value ? Number(e.target.value) : '')}
                      className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 text-sm focus:bg-white focus:ring-2 focus:ring-emerald-500 font-medium"
                    >
                      <option value="">Sem categoria</option>
                      {categorias.map((c) => (
                        <option key={c.id} value={c.id}>
                          {c.nome}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-xs font-bold text-slate-700 uppercase mb-1">
                        Preço Custo (R$) — opcional
                      </label>
                      <input
                        type="number"
                        step="0.01"
                        min="0"
                        value={valorCompra}
                        onChange={(e) => setValorCompra(e.target.value === '' ? '' : Number(e.target.value))}
                        className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 text-sm focus:bg-white focus:ring-2 focus:ring-emerald-500 font-medium"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-bold text-slate-700 uppercase mb-1">
                        Preço Venda (R$)
                      </label>
                      <input
                        type="number"
                        step="0.10"
                        min="0"
                        value={valorVenda}
                        onChange={(e) => setValorVenda(parseFloat(e.target.value) || 0)}
                        className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 text-sm focus:bg-white focus:ring-2 focus:ring-emerald-500 font-medium font-bold text-emerald-800"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-slate-700 uppercase mb-1" htmlFor="estoque-minimo">Estoque mínimo</label>
                    <input id="estoque-minimo" type="number" min="0" step="1" required value={estoqueMinimo} onChange={(e) => setEstoqueMinimo(Number(e.target.value))} className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm" />
                  </div>

                  <button
                    type="submit"
                    disabled={isLoading}
                    className="w-full h-11 bg-emerald-600 hover:bg-emerald-700 active:scale-[0.99] text-white rounded-xl text-xs sm:text-sm font-bold transition-all shadow-xs cursor-pointer flex items-center justify-center gap-2"
                  >
                    <Plus className="w-4 h-4" />
                    <span>{editItem ? 'Salvar alterações' : 'Salvar Produto no Catálogo'}</span>
                  </button>
                  {editItem && <button type="button" onClick={() => { setEditItem(null); setNomeProduto(''); setValorCompra(''); setValorVenda(0); setEstoqueMinimo(0); }} className="text-sm text-slate-600">Cancelar edição</button>}
                </form>
              </div>

              {/* Formulário Nova Categoria */}
              <div className="bg-white p-6 rounded-3xl border border-slate-200/80 shadow-xs flex flex-col justify-between">
                <div>
                  <div className="flex items-center gap-2 mb-4 pb-3 border-b border-slate-100">
                    <Layers className="w-5 h-5 text-emerald-600" />
                    <h3 className="font-black text-slate-900 text-base">Cadastrar Nova Categoria</h3>
                  </div>

                  <form onSubmit={handleSaveCategoria} className="space-y-4">
                    <div>
                      <label className="block text-xs font-bold text-slate-700 uppercase mb-1">
                        Nome da Categoria
                      </label>
                      <input
                        type="text"
                        required
                        value={nomeCategoria}
                        onChange={(e) => setNomeCategoria(e.target.value)}
                        placeholder="Ex: Bebidas, Salgados, Bazar, Livraria..."
                        className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 text-sm focus:bg-white focus:ring-2 focus:ring-emerald-500 font-medium"
                      />
                    </div>

                    <div>
                      <label className="block text-xs font-bold text-slate-700 uppercase mb-1">
                        Descrição (Opcional)
                      </label>
                      <input
                        type="text"
                        value={descCategoria}
                        onChange={(e) => setDescCategoria(e.target.value)}
                        placeholder="Ex: Refrigerantes, Sucos e Água"
                        className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 text-sm focus:bg-white focus:ring-2 focus:ring-emerald-500 font-medium"
                      />
                    </div>

                    <button
                      type="submit"
                      disabled={isLoading}
                      className="w-full h-11 bg-slate-800 hover:bg-slate-900 active:scale-[0.99] text-white rounded-xl text-xs sm:text-sm font-bold transition-all shadow-xs cursor-pointer flex items-center justify-center gap-2"
                    >
                      <Plus className="w-4 h-4" />
                      <span>Salvar Categoria</span>
                    </button>
                  </form>
                </div>

                {/* Categorias já criadas */}
                <div className="mt-6 pt-4 border-t border-slate-100">
                  <span className="text-[10px] uppercase font-bold text-slate-400 block mb-2">
                    Categorias Ativas ({categorias.length})
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {categorias.map((c) => (
                      <span
                        key={c.id}
                        className="px-2.5 py-1 bg-slate-100 text-slate-700 rounded-lg text-xs font-bold"
                      >
                        {c.nome}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Lista Geral de Produtos */}
            <div className="bg-white p-6 rounded-3xl border border-slate-200/80 shadow-xs">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
                <h3 className="font-black text-slate-900 text-base">
                  Produtos no Catálogo ({itens.length})
                </h3>
                <div className="relative w-full sm:w-64">
                  <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                  <input
                    type="text"
                    value={searchProduto}
                    onChange={(e) => setSearchProduto(e.target.value)}
                    placeholder="Filtrar por nome..."
                    className="w-full pl-9 pr-3 py-1.5 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-900 focus:bg-white font-medium"
                  />
                </div>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b border-slate-200 text-slate-400 font-bold uppercase text-[10px]">
                      <th className="py-2.5 px-3">Item</th>
                      <th className="py-2.5 px-3">Custo</th>
                      <th className="py-2.5 px-3">Preço Venda</th>
                      <th className="py-2.5 px-3">Mínimo</th>
                      <th className="py-2.5 px-3">Status</th>
                      <th className="py-2.5 px-3">Ações</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {filteredProdutos.map((p) => (
                      <tr key={p.id} className="hover:bg-slate-50/50">
                        <td className="py-2.5 px-3 font-bold text-slate-800">{p.nome}</td>
                        <td className="py-2.5 px-3 text-slate-500">
                          {p.valor_compra == null ? 'Não informado' : `R$ ${Number(p.valor_compra).toFixed(2).replace('.', ',')}`}
                        </td>
                        <td className="py-2.5 px-3 font-bold text-emerald-700">
                          R$ {Number(p.valor_venda).toFixed(2).replace('.', ',')}
                        </td>
                        <td className="py-2.5 px-3">{p.estoque_minimo}</td>
                        <td className="py-2.5 px-3">
                          <span className="px-2 py-0.5 rounded-md text-[10px] font-bold bg-emerald-100 text-emerald-800">
                            {p.status}
                          </span>
                        </td>
                        <td className="py-2.5 px-3"><button type="button" className="text-emerald-700 font-bold" onClick={() => { setEditItem(p); setNomeProduto(p.nome); setIdCategoriaProduto(p.id_categoria ?? ''); setValorCompra(p.valor_compra == null ? '' : Number(p.valor_compra)); setValorVenda(Number(p.valor_venda)); setEstoqueMinimo(p.estoque_minimo); }}>Editar</button></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* Conteúdo da Aba 2: Movimentação de Estoque */}
        {activeTab === 'estoque' && (
          <div className="bg-white p-6 rounded-3xl border border-slate-200/80 shadow-xs max-w-xl mx-auto">
            <div className="flex items-center gap-2 mb-4 pb-3 border-b border-slate-100">
              {estoqueTipo === 'Entrada'
                ? <ArrowDownCircle className="w-5 h-5 text-emerald-600" />
                : <ArrowUpCircle className="w-5 h-5 text-rose-600" />}
              <h3 className="font-black text-slate-900 text-base">Movimentação Manual de Estoque</h3>
            </div>

            <form onSubmit={handleMovimentacaoEstoque} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase mb-1">
                  Tipo de Movimentação
                </label>
                <select
                  value={estoqueTipo}
                  onChange={(e) => {
                    const tipo = e.target.value as 'Entrada' | 'Saida';
                    setEstoqueTipo(tipo);
                    setEstoqueOrigem(tipo === 'Entrada' ? 'Doação' : 'Consumo Interno');
                  }}
                  className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 text-sm focus:bg-white focus:ring-2 focus:ring-emerald-500 font-medium"
                >
                  <option value="Entrada">Entrada</option>
                  <option value="Saida">Saída</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase mb-1">
                  Selecione o Produto
                </label>
                <select
                  value={estoqueItemId}
                  onChange={(e) => setEstoqueItemId(Number(e.target.value))}
                  className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 text-sm focus:bg-white focus:ring-2 focus:ring-emerald-500 font-medium"
                >
                  {itens.map((i) => (
                    <option key={i.id} value={i.id}>
                      {i.nome} (R$ {Number(i.valor_venda).toFixed(2).replace('.', ',')})
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase mb-1">
                    Quantidade de {estoqueTipo === 'Entrada' ? 'Entrada' : 'Saída'}
                  </label>
                  <input
                    type="number"
                    min="1"
                    required
                    value={estoqueQtd}
                    onChange={(e) => setEstoqueQtd(parseInt(e.target.value) || 1)}
                    className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 text-sm focus:bg-white focus:ring-2 focus:ring-emerald-500 font-bold"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase mb-1">
                    Origem / Motivo
                  </label>
                  <input
                    type="text"
                    required
                    value={estoqueOrigem}
                    onChange={(e) => setEstoqueOrigem(e.target.value)}
                    placeholder={estoqueTipo === 'Entrada' ? 'Ex.: Doação recebida' : 'Ex.: Consumo interno'}
                    className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 text-sm focus:bg-white focus:ring-2 focus:ring-emerald-500 font-medium"
                  />
                </div>
              </div>

              {activeEvento ? (
                <p className="text-xs text-emerald-800 bg-emerald-50 p-2.5 rounded-xl border border-emerald-200">
                  Entrada será vinculada ao evento ativo: <span className="font-bold">{activeEvento.nome}</span>
                </p>
              ) : (
                <p className="text-xs text-amber-800 bg-amber-50 p-2.5 rounded-xl border border-amber-200">
                  ⚠️ Abra um Evento na aba Caixa para poder registrar movimentos de estoque.
                </p>
              )}

              <button
                type="submit"
                disabled={isLoading || !activeEvento}
                className="w-full h-11 bg-emerald-600 hover:bg-emerald-700 active:scale-[0.99] disabled:bg-slate-200 disabled:text-slate-400 disabled:cursor-not-allowed text-white rounded-xl text-xs sm:text-sm font-bold transition-all shadow-xs cursor-pointer flex items-center justify-center gap-2"
              >
                <Plus className="w-4 h-4" />
                <span>Registrar {estoqueTipo === 'Entrada' ? 'Entrada' : 'Saída'}</span>
              </button>
            </form>
          </div>
        )}

        {/* Conteúdo da Aba 3: Usuários e Voluntários */}
        {activeTab === 'usuarios' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Formulário Novo Usuário */}
              <div className="bg-white p-6 rounded-3xl border border-slate-200/80 shadow-xs">
                <div className="flex items-center gap-2 mb-4 pb-3 border-b border-slate-100">
                  <Shield className="w-5 h-5 text-emerald-600" />
                  <h3 className="font-black text-slate-900 text-base">Cadastrar Novo Voluntário</h3>
                </div>

                <form onSubmit={handleSaveUser} className="space-y-3.5">
                  <div>
                    <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Nome Completo</label>
                    <input
                      type="text"
                      required
                      value={nomeUser}
                      onChange={(e) => setNomeUser(e.target.value)}
                      placeholder="Ex: Maria dos Santos"
                      className="w-full px-3.5 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:bg-white font-medium"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-slate-700 uppercase mb-1">E-mail de Login</label>
                    <input
                      type="email"
                      required
                      value={emailUser}
                      onChange={(e) => setEmailUser(e.target.value)}
                      placeholder="maria@unython.local"
                      className="w-full px-3.5 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:bg-white font-medium"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Função / Atividade na ONG</label>
                    <input
                      type="text"
                      required
                      value={funcaoUser}
                      onChange={(e) => setFuncaoUser(e.target.value)}
                      placeholder="Ex: Voluntário Geral, Cozinha, Bazar, Apoio"
                      className="w-full px-3.5 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:bg-white font-medium"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Nível de Acesso</label>
                      <select
                        value={roleUser}
                        onChange={(e: any) => setRoleUser(e.target.value)}
                        className="w-full px-3.5 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:bg-white font-medium"
                      >
                        <option value="Vendedor">Vendedor / Caixa</option>
                        <option value="Recepcionista">Recepcionista</option>
                        <option value="Operador">Operador Geral</option>
                        <option value="Administrador">Administrador</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Senha Inicial</label>
                      <input
                        type="password"
                        required
                        value={senhaUser}
                        onChange={(e) => setSenhaUser(e.target.value)}
                        placeholder="••••••••"
                        className="w-full px-3.5 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:bg-white font-medium"
                      />
                    </div>
                  </div>

                  <label className="flex items-center gap-2 text-xs font-semibold text-slate-700">
                    <input
                      type="checkbox"
                      checked={requirePasswordChange}
                      onChange={(e) => setRequirePasswordChange(e.target.checked)}
                      className="rounded border-slate-300 text-emerald-600"
                    />
                    Exigir troca de senha no primeiro login
                  </label>

                  <button
                    type="submit"
                    disabled={isLoading}
                    className="w-full h-11 bg-emerald-600 hover:bg-emerald-700 active:scale-[0.99] text-white rounded-xl text-xs sm:text-sm font-bold transition-all shadow-xs cursor-pointer flex items-center justify-center gap-2 mt-2"
                  >
                    <Plus className="w-4 h-4" />
                    <span>Cadastrar Voluntário</span>
                  </button>
                </form>
              </div>

              {/* Lista de Usuários */}
              <div className="bg-white p-6 rounded-3xl border border-slate-200/80 shadow-xs">
                <h3 className="font-black text-slate-900 text-base mb-4 pb-3 border-b border-slate-100">
                  Voluntários Cadastrados ({usuarios.length})
                </h3>

                <div className="space-y-3 max-h-96 overflow-y-auto pr-1">
                  {usuarios.map((u) => (
                    <div
                      key={u.id}
                      className="p-3 bg-slate-50 rounded-2xl border border-slate-200/80"
                    >
                      {editingUser?.id === u.id ? (
                        <form onSubmit={handleUpdateUser} className="space-y-2">
                          <p className="font-bold text-slate-900 text-xs">{u.nome}</p>
                          <p className="text-[11px] text-slate-500">{u.email}</p>
                          <label className="block text-xs font-semibold text-slate-700">
                            Função
                            <input
                              required
                              value={editingFuncao}
                              onChange={(e) => setEditingFuncao(e.target.value)}
                              className="mt-1 block w-full border border-slate-200 rounded-lg p-2"
                            />
                          </label>
                          <div className="grid grid-cols-2 gap-2">
                            <label className="block text-xs font-semibold text-slate-700">
                              Papel
                              <select
                                value={editingRole}
                                onChange={(e) => setEditingRole(e.target.value as Usuario['role'])}
                                className="mt-1 block w-full border border-slate-200 rounded-lg p-2"
                              >
                                <option value="Administrador">Administrador</option>
                                <option value="Operador">Operador</option>
                                <option value="Recepcionista">Recepcionista</option>
                                <option value="Vendedor">Vendedor</option>
                              </select>
                            </label>
                            <label className="block text-xs font-semibold text-slate-700">
                              Status
                              <select
                                value={editingStatus}
                                onChange={(e) => setEditingStatus(e.target.value as Usuario['status'])}
                                className="mt-1 block w-full border border-slate-200 rounded-lg p-2"
                              >
                                <option value="Ativo">Ativo</option>
                                <option value="Inativo">Inativo</option>
                              </select>
                            </label>
                          </div>
                          <div className="flex gap-2 pt-1">
                            <button
                              type="submit"
                              disabled={isLoading}
                              className="text-xs font-bold text-white bg-emerald-700 rounded-lg px-3 py-1.5 disabled:opacity-50"
                            >
                              Salvar
                            </button>
                            <button
                              type="button"
                              onClick={() => setEditingUser(null)}
                              className="text-xs font-bold text-slate-600 px-2"
                            >
                              Cancelar
                            </button>
                          </div>
                        </form>
                      ) : (
                        <div className="flex items-center justify-between gap-3">
                          <div>
                            <h4 className="font-bold text-slate-900 text-xs">{u.nome}</h4>
                            <p className="text-[11px] text-slate-500">{u.email}</p>
                            <p className="text-[11px] text-slate-500">{u.funcao} · {u.status}</p>
                          </div>
                          <div className="flex flex-col items-end gap-2">
                            <span className="px-2.5 py-1 rounded-lg text-[10px] font-bold bg-slate-200 text-slate-800">
                              {u.role}
                            </span>
                            <button
                              type="button"
                              onClick={() => startEditingUser(u)}
                              className="text-xs font-bold text-emerald-700"
                            >
                              Editar
                            </button>
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Conteúdo da Aba 4: DRE e Relatórios */}
        {activeTab === 'relatorios' && (
          <RelatoriosView />
        )}
        {activeTab === 'calendario' && <CalendarioView activeEvento={activeEvento} onRefreshState={onRefreshState} />}
        {activeTab === 'facilitadores' && <FacilitadoresView />}
        {activeTab === 'atividades' && <AtividadesView termo={termos.termo_atividade} />}
      </div>

      {/* Modal QR Code Celular */}
      <ConnectMobileModal
        isOpen={isMobileModalOpen}
        onClose={() => setIsMobileModalOpen(false)}
      />
    </div>
  );
};
