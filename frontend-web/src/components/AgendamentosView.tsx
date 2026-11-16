import React, { useState, useEffect, useMemo } from 'react';
import {
  Users,
  Search,
  Check,
  X,
  Clock,
  UserCheck,
  UserX,
  RefreshCw,
  Plus,
  HeartHandshake,
  Settings,
  RotateCcw,
  Sparkles,
  Phone,
  AlertCircle,
  Megaphone,
  Calendar,
  CalendarPlus,
  ArrowRight,
} from 'lucide-react';
import { apiClient } from '../api/client';
import type { Agendamento, Evento, Pessoa, OrganizacaoConfig } from '../types';

interface AgendamentosViewProps {
  activeEvento: Evento | null;
  onNavigateToCaixa?: () => void;
}

export const AgendamentosView: React.FC<AgendamentosViewProps> = ({
  activeEvento,
  onNavigateToCaixa,
}) => {
  // Configuração de terminologia da organização
  const [orgConfig, setOrgConfig] = useState<OrganizacaoConfig>({
    tipo_organizacao: 'Terreiro de Umbanda / Centro Espírita',
    termo_assistido: 'Consulente',
    termo_assistido_plural: 'Consulentes',
    termo_atendente: 'Médium / Cambone',
    termo_servico: 'Passe / Consulta',
  });

  // Eventos disponíveis (abertos e agendados para o futuro)
  const [eventosDisponiveis, setEventosDisponiveis] = useState<Evento[]>([]);
  const [selectedEventoId, setSelectedEventoId] = useState<number | null>(null);

  // Estados de dados da fila e pré-agendamentos
  const [fila, setFila] = useState<Agendamento[]>([]);
  const [preAgendados, setPreAgendados] = useState<Agendamento[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeTab, setActiveTab] = useState<'fila' | 'preagendados' | 'ausentes' | 'atendidos' | 'config'>('fila');
  const [updatingId, setUpdatingId] = useState<number | null>(null);

  // Modais
  const [isPresencialModalOpen, setIsPresencialModalOpen] = useState(false);
  const [isPreAgendarModalOpen, setIsPreAgendarModalOpen] = useState(false);
  const [isNovoEventoModalOpen, setIsNovoEventoModalOpen] = useState(false);

  // Pessoas cadastradas para auto-complete
  const [pessoasCadastradas, setPessoasCadastradas] = useState<Pessoa[]>([]);
  const [modoCadastro, setModoCadastro] = useState<'novo' | 'existente'>('novo');
  const [selectedPessoaId, setSelectedPessoaId] = useState<number | null>(null);

  // Campos do formulário
  const [formNome, setFormNome] = useState('');
  const [formTelefone, setFormTelefone] = useState('');
  const [formDocumento, setFormDocumento] = useState('');
  const [formPreferencial, setFormPreferencial] = useState(false);
  const [formServico, setFormServico] = useState('');
  const [formObservacoes, setFormObservacoes] = useState('');
  const [formEventoAlvoId, setFormEventoAlvoId] = useState<number | null>(null);

  // Campos para criação de novo evento futuro no calendário
  const [novoEvNome, setNovoEvNome] = useState('');
  const [novoEvData, setNovoEvData] = useState('');
  const [novoEvTipo, setNovoEvTipo] = useState('Gira / Culto / Atendimento');

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [feedbackMsg, setFeedbackMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const showFeedback = (type: 'success' | 'error', text: string) => {
    setFeedbackMsg({ type, text });
    setTimeout(() => setFeedbackMsg(null), 4500);
  };

  // Carrega configurações da organização
  const fetchConfig = async () => {
    try {
      const resp = await apiClient.get('/organizacao/config');
      if (resp.data) {
        setOrgConfig(resp.data);
        if (!formServico) {
          setFormServico(resp.data.termo_servico || 'Passe / Consulta');
        }
      }
    } catch {
      console.warn('Usando vocabulário padrão da organização.');
    }
  };

  // Carrega lista de eventos futuros e abertos
  const fetchEventos = async () => {
    try {
      const resp = await apiClient.get('/eventos/ativos-e-futuros');
      const list: Evento[] = resp.data || [];
      setEventosDisponiveis(list);

      // Define evento selecionado inicialmente
      if (!selectedEventoId) {
        if (activeEvento) {
          setSelectedEventoId(activeEvento.id);
        } else if (list.length > 0) {
          setSelectedEventoId(list[0].id);
        }
      }
    } catch (err) {
      console.error('Erro ao buscar eventos:', err);
    }
  };

  // Carrega fila ativa e pré-agendados do evento selecionado
  const fetchFilaEPreAgendados = async (eventoId?: number) => {
    const id = eventoId || selectedEventoId;
    if (!id) {
      setFila([]);
      setPreAgendados([]);
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    try {
      const [filaResp, preResp] = await Promise.allSettled([
        apiClient.get(`/agendamentos/fila/${id}`),
        apiClient.get(`/agendamentos/pre-agendados/${id}`),
      ]);

      if (filaResp.status === 'fulfilled') {
        setFila(filaResp.value.data || []);
      } else {
        setFila([]);
      }

      if (preResp.status === 'fulfilled') {
        setPreAgendados(preResp.value.data || []);
      } else {
        setPreAgendados([]);
      }
    } catch (err) {
      console.error('Erro ao buscar dados do evento:', err);
    } finally {
      setIsLoading(false);
    }
  };

  // Carrega pessoas para auto-complete
  const fetchPessoas = async () => {
    try {
      const resp = await apiClient.get('/pessoas/');
      setPessoasCadastradas(resp.data || []);
    } catch (err) {
      console.error('Erro ao carregar pessoas:', err);
    }
  };

  useEffect(() => {
    fetchConfig();
    fetchEventos();
    fetchPessoas();
  }, []);

  useEffect(() => {
    if (activeEvento && (!selectedEventoId || selectedEventoId !== activeEvento.id)) {
      setSelectedEventoId(activeEvento.id);
    }
  }, [activeEvento]);

  useEffect(() => {
    if (selectedEventoId) {
      fetchFilaEPreAgendados(selectedEventoId);
    }
  }, [selectedEventoId]);

  // Acolhimento Presencial / Encaixe na Porta (Emite senha imediata)
  const handleAcolherPresencial = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedEventoId) {
      showFeedback('error', 'Selecione ou abra um evento para registrar presença.');
      return;
    }

    if (modoCadastro === 'novo' && !formNome.trim()) {
      showFeedback('error', `Informe o nome do(a) ${orgConfig.termo_assistido.toLowerCase()}.`);
      return;
    }

    if (modoCadastro === 'existente' && !selectedPessoaId) {
      showFeedback('error', `Selecione um(a) ${orgConfig.termo_assistido.toLowerCase()} cadastrado(a).`);
      return;
    }

    setIsSubmitting(true);
    try {
      const payload = {
        id_evento: selectedEventoId,
        id_pessoa: modoCadastro === 'existente' ? selectedPessoaId : null,
        nome: modoCadastro === 'novo' ? formNome.trim() : null,
        telefone: modoCadastro === 'novo' ? formTelefone.trim() : null,
        documento: modoCadastro === 'novo' ? formDocumento.trim() : null,
        preferencial: formPreferencial,
        tipo_servico: formServico || orgConfig.termo_servico,
        observacoes: formObservacoes.trim() || null,
      };

      const resp = await apiClient.post('/agendamentos/acolher', payload);
      const senhaGerada = resp.data?.numero_senha || (formPreferencial ? 'P-01' : 'G-01');

      showFeedback('success', `Senha ${senhaGerada} gerada para ${formNome || 'o acolhido'}!`);

      // Limpa formulário
      setFormNome('');
      setFormTelefone('');
      setFormDocumento('');
      setFormObservacoes('');
      setFormPreferencial(false);
      setSelectedPessoaId(null);
      setIsPresencialModalOpen(false);

      await fetchFilaEPreAgendados();
      await fetchPessoas();
    } catch (err: any) {
      showFeedback('error', err.response?.data?.detail || 'Erro ao registrar acolhimento.');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Pré-Agendar com Antecedência para um Evento Futuro
  const handlePreAgendar = async (e: React.FormEvent) => {
    e.preventDefault();
    const eventoAlvo = formEventoAlvoId || selectedEventoId;
    if (!eventoAlvo) {
      showFeedback('error', 'Selecione o evento para o qual deseja agendar.');
      return;
    }

    if (modoCadastro === 'novo' && !formNome.trim()) {
      showFeedback('error', `Informe o nome do(a) ${orgConfig.termo_assistido.toLowerCase()}.`);
      return;
    }

    if (modoCadastro === 'existente' && !selectedPessoaId) {
      showFeedback('error', `Selecione um(a) ${orgConfig.termo_assistido.toLowerCase()} cadastrado(a).`);
      return;
    }

    setIsSubmitting(true);
    try {
      const payload = {
        id_evento: eventoAlvo,
        id_pessoa: modoCadastro === 'existente' ? selectedPessoaId : null,
        nome: modoCadastro === 'novo' ? formNome.trim() : null,
        telefone: modoCadastro === 'novo' ? formTelefone.trim() : null,
        documento: modoCadastro === 'novo' ? formDocumento.trim() : null,
        preferencial: formPreferencial,
        tipo_servico: formServico || orgConfig.termo_servico,
        observacoes: formObservacoes.trim() || null,
      };

      await apiClient.post('/agendamentos/pre-agendar', payload);
      const evObj = eventosDisponiveis.find((x) => x.id === eventoAlvo);
      showFeedback(
        'success',
        `Pré-agendamento confirmado com sucesso para ${formNome || 'o acolhido'} no evento "${evObj?.nome || 'selecionado'}"!`
      );

      // Limpa formulário
      setFormNome('');
      setFormTelefone('');
      setFormDocumento('');
      setFormObservacoes('');
      setFormPreferencial(false);
      setSelectedPessoaId(null);
      setIsPreAgendarModalOpen(false);

      await fetchFilaEPreAgendados();
      await fetchPessoas();
    } catch (err: any) {
      showFeedback('error', err.response?.data?.detail || 'Erro ao realizar agendamento prévio.');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Realizar Check-in / Chegada do Pré-Agendado no Dia
  const handleCheckin = async (idAgendamento: number, nomePessoa: string) => {
    setUpdatingId(idAgendamento);
    try {
      const resp = await apiClient.post(`/agendamentos/${idAgendamento}/checkin`);
      const senha = resp.data?.numero_senha || 'G-01';
      showFeedback('success', `Check-in realizado! Senha ${senha} emitida para ${nomePessoa}.`);
      await fetchFilaEPreAgendados();
    } catch (err: any) {
      alert('Falha ao realizar check-in: ' + (err.response?.data?.detail || 'Tente novamente.'));
    } finally {
      setUpdatingId(null);
    }
  };

  // Criar Novo Evento Futuro no Calendário
  const handleCriarEventoFuturo = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!novoEvNome || !novoEvData) {
      showFeedback('error', 'Preencha o nome e a data do evento.');
      return;
    }

    setIsSubmitting(true);
    try {
      const resp = await apiClient.post('/eventos/novo', null, {
        params: {
          nome: novoEvNome,
          data_evento: novoEvData,
          tipo: novoEvTipo,
          status: 'Agendado',
        },
      });

      showFeedback('success', `Evento "${novoEvNome}" agendado no calendário com sucesso!`);
      setNovoEvNome('');
      setNovoEvData('');
      setIsNovoEventoModalOpen(false);

      await fetchEventos();
      if (resp.data?.id) {
        setSelectedEventoId(resp.data.id);
      }
    } catch (err: any) {
      showFeedback('error', err.response?.data?.detail || 'Erro ao criar evento futuro.');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Iniciar / Abrir um evento agendado
  const handleIniciarEvento = async (idEvento: number) => {
    if (!confirm('Deseja iniciar e abrir este evento para a operação de hoje?')) return;
    try {
      await apiClient.post(`/eventos/${idEvento}/iniciar`);
      showFeedback('success', 'Evento aberto para operação com sucesso!');
      await fetchEventos();
      setSelectedEventoId(idEvento);
    } catch (err) {
      alert('Erro ao iniciar o evento.');
    }
  };

  // Alterar Status do Atendimento ('Chamado', 'Atendido', 'Ausente')
  const handleMudarStatus = async (id: number, novoStatus: 'Aguardando' | 'Chamado' | 'Atendido' | 'Ausente') => {
    setUpdatingId(id);
    try {
      await apiClient.patch(`/agendamentos/${id}/status`, { status: novoStatus });
      setFila((prev) =>
        prev.map((item) =>
          item.id === id
            ? {
                ...item,
                status: novoStatus,
                compareceu: novoStatus === 'Atendido' ? 'Sim' : novoStatus === 'Ausente' ? 'Nao' : 'Pendente',
              }
            : item
        )
      );
      if (novoStatus === 'Atendido') {
        showFeedback('success', 'Atendimento concluído com sucesso!');
      } else if (novoStatus === 'Ausente') {
        showFeedback('error', 'Marcado como ausente. Pode ser reativado na aba de Ausentes.');
      }
    } catch {
      alert('Falha ao atualizar status do atendimento.');
    } finally {
      setUpdatingId(null);
    }
  };

  // Reativar da lista de ausentes caso não tenha ouvido a chamada
  const handleReativarAusente = async (id: number) => {
    setUpdatingId(id);
    try {
      await apiClient.patch(`/agendamentos/${id}/reativar`);
      setFila((prev) =>
        prev.map((item) =>
          item.id === id ? { ...item, status: 'Aguardando', compareceu: 'Pendente' } : item
        )
      );
      showFeedback('success', 'O acolhido foi reativado e voltou para a fila ativa!');
    } catch {
      alert('Falha ao reativar ausente.');
    } finally {
      setUpdatingId(null);
    }
  };

  // Salvar Parâmetros da Organização
  const handleSalvarConfigOrg = async (preset?: Partial<OrganizacaoConfig>) => {
    const dataToSend = { ...orgConfig, ...preset };
    try {
      await apiClient.put('/organizacao/config', dataToSend);
      setOrgConfig(dataToSend);
      showFeedback('success', 'Vocabulário da organização salvo com sucesso!');
    } catch {
      alert('Erro ao salvar parâmetros da organização.');
    }
  };

  // Pre-sets de entidades
  const presets = [
    {
      tipo: 'Terreiro de Umbanda / Centro Espírita',
      assistido: 'Consulente',
      assistidos: 'Consulentes',
      atendente: 'Médium / Cambone',
      servico: 'Passe / Consulta',
      icon: '🕊️',
    },
    {
      tipo: 'Igreja Católica',
      assistido: 'Fiel',
      assistidos: 'Fiéis',
      atendente: 'Padre / Diácono',
      servico: 'Confissão / Escuta Pastoral',
      icon: '⛪',
    },
    {
      tipo: 'Igreja Evangélica',
      assistido: 'Irmão / Visitante',
      assistidos: 'Irmãos / Visitantes',
      atendente: 'Pastor / Ministro',
      servico: 'Oração / Aconselhamento',
      icon: '📖',
    },
    {
      tipo: 'Albergue / Casa de Passagem',
      assistido: 'Acolhido',
      assistidos: 'Acolhidos',
      atendente: 'Assistente Social',
      servico: 'Triagem / Acolhimento & Refeição',
      icon: '🏠',
    },
    {
      tipo: 'Clínica Social / Terapia',
      assistido: 'Paciente',
      assistidos: 'Pacientes',
      atendente: 'Terapeuta / Psicólogo',
      servico: 'Sessão / Terapia Integrativa',
      icon: '🩺',
    },
  ];

  // Separação de Filas Ativas
  const filaAtiva = useMemo(() => {
    return fila.filter((a) => a.status === 'Aguardando' || a.status === 'Chamado');
  }, [fila]);

  const filaPreferencial = useMemo(() => {
    return filaAtiva.filter((a) => a.preferencial);
  }, [filaAtiva]);

  const filaComum = useMemo(() => {
    return filaAtiva.filter((a) => !a.preferencial);
  }, [filaAtiva]);

  const listaAusentes = useMemo(() => {
    return fila.filter((a) => a.status === 'Ausente');
  }, [fila]);

  const listaAtendidos = useMemo(() => {
    return fila.filter((a) => a.status === 'Atendido');
  }, [fila]);

  // Evento atualmente em exibição
  const eventoAtual = useMemo(() => {
    return eventosDisponiveis.find((e) => e.id === selectedEventoId) || activeEvento;
  }, [eventosDisponiveis, selectedEventoId, activeEvento]);

  // Filtro de busca textual
  const filtraPorBusca = (lista: Agendamento[]) => {
    if (!searchQuery.trim()) return lista;
    const q = searchQuery.toLowerCase();
    return lista.filter(
      (item) =>
        item.pessoa?.toLowerCase().includes(q) ||
        item.numero_senha?.toLowerCase().includes(q) ||
        item.telefone?.includes(q) ||
        item.tipo_servico?.toLowerCase().includes(q)
    );
  };

  return (
    <div className="flex-1 overflow-y-auto bg-slate-100 p-4 sm:p-6 lg:p-8">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Cabeçalho */}
        <div className="flex flex-col gap-4">
          {/* Título centralizado */}
          <div className="w-full text-center">
            <div className="flex items-center justify-center gap-2 flex-wrap">
              <h1 className="text-xl sm:text-2xl font-black text-slate-900 tracking-tight flex items-center gap-2.5">
                <HeartHandshake className="w-6 h-6 sm:w-7 sm:h-7 text-emerald-600 shrink-0" />
                Acolhimento, Agendamentos & Triagem
              </h1>
              <span className="text-[10px] sm:text-xs bg-emerald-100 text-emerald-800 font-bold px-2.5 py-0.5 rounded-full whitespace-nowrap">
                {orgConfig.tipo_organizacao.split('/')[0].trim()}
              </span>
            </div>
            <p className="text-xs sm:text-sm text-slate-500 font-medium mt-1">
              Pré-agendamento com antecedência, check-in na chegada e controle de filas dos {orgConfig.termo_assistido_plural.toLowerCase()}.
            </p>
          </div>

          {/* Botões de Ação do Cabeçalho */}
          <div className="flex flex-wrap items-center justify-center gap-2">
            <button
              onClick={() => fetchFilaEPreAgendados()}
              disabled={isLoading}
              className="h-10 px-3 bg-white hover:bg-slate-50 text-slate-700 font-bold text-xs rounded-xl border border-slate-200 transition-all inline-flex items-center gap-1.5 cursor-pointer shadow-xs"
              title="Recarregar fila e agendamentos"
            >
              <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
              <span className="hidden sm:inline">Atualizar</span>
            </button>

            <button
              onClick={() => setIsPreAgendarModalOpen(true)}
              className="h-10 px-3.5 bg-indigo-50 hover:bg-indigo-100 active:scale-95 text-indigo-900 font-bold text-xs sm:text-sm rounded-xl border border-indigo-200 transition-all inline-flex items-center gap-2 cursor-pointer shadow-xs"
              title="Agendar um consulente com antecedência para uma data futura"
            >
              <Calendar className="w-4 h-4 text-indigo-600" />
              <span>📅 Pré-Agendar com Antecedência</span>
            </button>

            <button
              onClick={() => setIsPresencialModalOpen(true)}
              className="h-10 px-4 bg-emerald-600 hover:bg-emerald-700 active:scale-95 text-white font-bold text-xs sm:text-sm rounded-xl shadow-sm transition-all inline-flex items-center gap-2 cursor-pointer"
              title="Para quem chegou na porta agora (sem agendamento prévio)"
            >
              <Plus className="w-4 h-4" />
              <span>+ Check-in Presencial / Porta</span>
            </button>
          </div>
        </div>

        {/* Feedback visual */}
        {feedbackMsg && (
          <div
            className={`p-4 rounded-2xl border text-sm font-semibold flex items-center gap-3 animate-fade-in ${
              feedbackMsg.type === 'success'
                ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
                : 'bg-rose-50 border-rose-200 text-rose-800'
            }`}
          >
            {feedbackMsg.type === 'success' ? (
              <Check className="w-5 h-5 text-emerald-600 shrink-0" />
            ) : (
              <AlertCircle className="w-5 h-5 text-rose-600 shrink-0" />
            )}
            <span>{feedbackMsg.text}</span>
          </div>
        )}

        {/* SELETOR E STATUS DO EVENTO / CALENDÁRIO */}
        <div className="bg-white p-4 rounded-3xl border border-slate-200/80 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-3">
          <div className="flex flex-col sm:flex-row sm:items-center gap-3">
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-slate-500 uppercase tracking-wider flex items-center gap-1.5">
                <Calendar className="w-4 h-4 text-emerald-600" />
                Evento / Gira Selecionada:
              </span>
            </div>

            <select
              value={selectedEventoId || ''}
              onChange={(e) => setSelectedEventoId(Number(e.target.value))}
              className="h-10 px-3.5 bg-slate-50 border border-slate-200 rounded-xl text-xs sm:text-sm font-bold text-slate-900 focus:bg-white focus:outline-hidden focus:ring-2 focus:ring-emerald-500"
            >
              {eventosDisponiveis.map((ev) => (
                <option key={ev.id} value={ev.id}>
                  {ev.nome} ({ev.data_evento}) &bull; [{ev.status}]
                </option>
              ))}
            </select>

            {eventoAtual && (
              <span
                className={`px-2.5 py-1 rounded-lg text-xs font-bold ${
                  eventoAtual.status === 'Aberto'
                    ? 'bg-emerald-100 text-emerald-800 border border-emerald-200'
                    : 'bg-amber-100 text-amber-800 border border-amber-200'
                }`}
              >
                {eventoAtual.status === 'Aberto' ? '🟢 Operação Ativa' : '🟡 Agendado no Calendário'}
              </span>
            )}
          </div>

          <div className="flex items-center gap-2">
            {eventoAtual && eventoAtual.status === 'Agendado' && (
              <button
                onClick={() => handleIniciarEvento(eventoAtual.id)}
                className="h-9 px-3.5 bg-emerald-600 hover:bg-emerald-700 active:scale-95 text-white font-bold text-xs rounded-xl shadow-xs transition-all cursor-pointer inline-flex items-center gap-1.5"
              >
                <span>Iniciar / Abrir Evento Hoje</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            )}

            {onNavigateToCaixa && (
              <button
                onClick={onNavigateToCaixa}
                className="h-9 px-3 bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs rounded-xl transition-all cursor-pointer inline-flex items-center gap-1.5 shrink-0"
                title="Abrir ou fechar turnos de caixa para a operação do evento"
              >
                <span>Gestão de Caixa &rarr;</span>
              </button>
            )}

            <button
              onClick={() => setIsNovoEventoModalOpen(true)}
              className="h-9 px-3 bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs rounded-xl transition-all cursor-pointer inline-flex items-center gap-1.5 shrink-0"
              title="Cadastrar uma nova data no calendário (ex: Gira da próxima semana)"
            >
              <CalendarPlus className="w-4 h-4 text-slate-500" />
              <span>+ Nova Data / Evento</span>
            </button>
          </div>
        </div>

        {/* MÉTRICAS RÁPIDAS */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="bg-white p-4 rounded-2xl border border-indigo-200/80 bg-indigo-50/20 shadow-xs flex items-center justify-between">
            <div>
              <span className="text-[10px] uppercase font-bold text-indigo-700 tracking-wider">📋 Pré-Agendados</span>
              <p className="text-2xl font-black text-indigo-900 mt-0.5">{preAgendados.length}</p>
            </div>
            <div className="w-10 h-10 rounded-xl bg-indigo-100 text-indigo-800 flex items-center justify-center font-bold text-xs">
              <Calendar className="w-5 h-5" />
            </div>
          </div>

          <div className="bg-white p-4 rounded-2xl border border-amber-200/80 bg-amber-50/20 shadow-xs flex items-center justify-between">
            <div>
              <span className="text-[10px] uppercase font-bold text-amber-700 tracking-wider">⚡ Na Fila Preferencial</span>
              <p className="text-2xl font-black text-amber-800 mt-0.5">{filaPreferencial.length}</p>
            </div>
            <div className="w-10 h-10 rounded-xl bg-amber-100 text-amber-800 flex items-center justify-center font-black text-xs">
              P-XX
            </div>
          </div>

          <div className="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-xs flex items-center justify-between">
            <div>
              <span className="text-[10px] uppercase font-bold text-slate-600 tracking-wider">👥 Na Fila Geral</span>
              <p className="text-2xl font-black text-slate-800 mt-0.5">{filaComum.length}</p>
            </div>
            <div className="w-10 h-10 rounded-xl bg-slate-100 text-slate-700 flex items-center justify-center font-black text-xs">
              G-XX
            </div>
          </div>

          <div className="bg-white p-4 rounded-2xl border border-emerald-200/80 bg-emerald-50/20 shadow-xs flex items-center justify-between">
            <div>
              <span className="text-[10px] uppercase font-bold text-emerald-700 tracking-wider">✅ Atendidos</span>
              <p className="text-2xl font-black text-emerald-800 mt-0.5">{listaAtendidos.length}</p>
            </div>
            <div className="w-10 h-10 rounded-xl bg-emerald-100 text-emerald-800 flex items-center justify-center">
              <UserCheck className="w-5 h-5" />
            </div>
          </div>
        </div>

        {/* NAVEGAÇÃO DE ABAS & BUSCA */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
          <div className="flex items-center gap-1.5 bg-white p-1.5 rounded-2xl border border-slate-200/80 shadow-xs overflow-x-auto shrink-0">
            <button
              onClick={() => setActiveTab('fila')}
              className={`h-9 px-3.5 inline-flex items-center gap-2 rounded-xl text-xs font-bold transition-all whitespace-nowrap cursor-pointer ${
                activeTab === 'fila' ? 'bg-slate-900 text-white shadow-xs' : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
              }`}
            >
              <Users className="w-4 h-4" />
              <span>Fila Ativa ({filaAtiva.length})</span>
            </button>

            <button
              onClick={() => setActiveTab('preagendados')}
              className={`h-9 px-3.5 inline-flex items-center gap-2 rounded-xl text-xs font-bold transition-all whitespace-nowrap cursor-pointer ${
                activeTab === 'preagendados' ? 'bg-indigo-600 text-white shadow-xs' : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
              }`}
            >
              <Calendar className="w-4 h-4" />
              <span>Pré-Agendados ({preAgendados.length})</span>
            </button>

            <button
              onClick={() => setActiveTab('ausentes')}
              className={`h-9 px-3.5 inline-flex items-center gap-2 rounded-xl text-xs font-bold transition-all whitespace-nowrap cursor-pointer ${
                activeTab === 'ausentes' ? 'bg-rose-600 text-white shadow-xs' : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
              }`}
            >
              <UserX className="w-4 h-4" />
              <span>Ausentes ({listaAusentes.length})</span>
            </button>

            <button
              onClick={() => setActiveTab('atendidos')}
              className={`h-9 px-3.5 inline-flex items-center gap-2 rounded-xl text-xs font-bold transition-all whitespace-nowrap cursor-pointer ${
                activeTab === 'atendidos' ? 'bg-slate-900 text-white shadow-xs' : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
              }`}
            >
              <Check className="w-4 h-4" />
              <span>Atendidos ({listaAtendidos.length})</span>
            </button>

            <button
              onClick={() => setActiveTab('config')}
              className={`h-9 px-3.5 inline-flex items-center gap-2 rounded-xl text-xs font-bold transition-all whitespace-nowrap cursor-pointer ${
                activeTab === 'config' ? 'bg-slate-900 text-white shadow-xs' : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
              }`}
            >
              <Settings className="w-4 h-4" />
              <span>Configurações</span>
            </button>
          </div>

          {activeTab !== 'config' && (
            <div className="relative flex-1 max-w-md">
              <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder={`Buscar senha, nome do ${orgConfig.termo_assistido.toLowerCase()} ou telefone...`}
                className="w-full h-10 pl-10 pr-4 bg-white border border-slate-200 rounded-xl text-xs sm:text-sm text-slate-900 placeholder-slate-400 focus:outline-hidden focus:ring-2 focus:ring-emerald-500 font-medium shadow-xs"
              />
            </div>
          )}
        </div>

        {/* ABA 1: FILA ATIVA (PREFERENCIAL & GERAL) */}
        {activeTab === 'fila' && (
          <div className="space-y-6">
            {filaAtiva.length === 0 ? (
              <div className="bg-white rounded-3xl p-12 text-center border border-slate-200/80 shadow-xs flex flex-col items-center">
                <Users className="w-12 h-12 text-slate-300 mb-3" />
                <h3 className="font-bold text-slate-700 text-base">Fila ativa vazia no momento</h3>
                <p className="text-xs text-slate-400 mt-1 max-w-md">
                  {preAgendados.length > 0
                    ? `Existem ${preAgendados.length} ${orgConfig.termo_assistido_plural.toLowerCase()} pré-agendados. Clique na aba "Pré-Agendados" para fazer o Check-in e emitir senhas conforme chegam.`
                    : `Use o botão verde "+ Check-in Presencial" acima para acolher quem chegou na porta, ou agende previamente na aba Pré-Agendar.`}
                </p>
                {preAgendados.length > 0 && (
                  <button
                    onClick={() => setActiveTab('preagendados')}
                    className="mt-4 h-9 px-4 bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs rounded-xl shadow-xs transition-all cursor-pointer inline-flex items-center gap-2"
                  >
                    <Calendar className="w-4 h-4" />
                    <span>Ver {preAgendados.length} Pré-Agendados &rarr;</span>
                  </button>
                )}
              </div>
            ) : (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* COLUNA 1: FILA PREFERENCIAL */}
                <div className="space-y-3">
                  <div className="flex items-center justify-between pb-2 border-b border-amber-200">
                    <div className="flex items-center gap-2">
                      <span className="w-3 h-3 rounded-full bg-amber-500 animate-pulse" />
                      <h3 className="font-black text-slate-900 text-sm uppercase tracking-wider flex items-center gap-1.5 text-amber-900">
                        ⚡ Fila Preferencial ({filtraPorBusca(filaPreferencial).length})
                      </h3>
                    </div>
                    <span className="text-[10px] font-bold bg-amber-100 text-amber-800 px-2 py-0.5 rounded-md">
                      Idosos • Gestantes • PCD • Colo
                    </span>
                  </div>

                  {filtraPorBusca(filaPreferencial).length === 0 ? (
                    <div className="p-6 text-center bg-white/60 border border-dashed border-amber-200 rounded-2xl text-xs text-slate-400 font-medium">
                      Nenhum {orgConfig.termo_assistido.toLowerCase()} preferencial na espera.
                    </div>
                  ) : (
                    filtraPorBusca(filaPreferencial).map((item) => (
                      <div
                        key={item.id}
                        className={`p-4 rounded-2xl border transition-all shadow-xs bg-white ${
                          item.status === 'Chamado'
                            ? 'border-amber-400 ring-2 ring-amber-200 bg-amber-50/40'
                            : 'border-amber-200/80 hover:border-amber-300'
                        }`}
                      >
                        <div className="flex items-start justify-between gap-3">
                          <div className="flex items-center gap-3 min-w-0">
                            <div className="w-14 h-14 rounded-2xl bg-amber-500 text-white flex flex-col items-center justify-center font-black shrink-0 shadow-xs">
                              <span className="text-base leading-none">{item.numero_senha || 'P-01'}</span>
                              <span className="text-[9px] uppercase font-bold opacity-80 mt-0.5">#{item.ordem_chegada}º</span>
                            </div>

                            <div className="min-w-0">
                              <div className="flex items-center gap-2">
                                <h4 className="font-black text-slate-900 text-sm truncate">{item.pessoa}</h4>
                                {item.status === 'Chamado' && (
                                  <span className="text-[10px] font-extrabold bg-amber-200 text-amber-900 px-2 py-0.5 rounded-full flex items-center gap-1 animate-pulse">
                                    <Megaphone className="w-3 h-3" /> Chamando
                                  </span>
                                )}
                              </div>
                              <p className="text-xs text-slate-500 font-medium mt-0.5 flex items-center gap-1.5">
                                <span>{item.tipo_servico || orgConfig.termo_servico}</span>
                                {item.telefone && (
                                  <>
                                    <span>•</span>
                                    <span className="flex items-center gap-0.5 text-slate-600">
                                      <Phone className="w-3 h-3 text-slate-400" /> {item.telefone}
                                    </span>
                                  </>
                                )}
                              </p>
                              {item.observacoes && (
                                <p className="text-[11px] text-amber-800 bg-amber-50/80 px-2 py-0.5 rounded-md mt-1 italic">
                                  {item.observacoes}
                                </p>
                              )}
                            </div>
                          </div>

                          <div className="text-right shrink-0">
                            <span className="text-[11px] font-bold text-slate-400 flex items-center gap-1 justify-end">
                              <Clock className="w-3 h-3" />
                              {new Date(item.data_hora).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                            </span>
                          </div>
                        </div>

                        <div className="mt-3 pt-3 border-t border-slate-100 flex items-center justify-end gap-2">
                          <button
                            onClick={() => handleMudarStatus(item.id, 'Ausente')}
                            disabled={updatingId === item.id}
                            className="h-8 px-2.5 rounded-xl border border-slate-200 hover:border-rose-300 hover:bg-rose-50 text-slate-500 hover:text-rose-700 text-xs font-bold transition-all cursor-pointer inline-flex items-center gap-1"
                          >
                            <UserX className="w-3.5 h-3.5" />
                            <span>Ausente</span>
                          </button>

                          <button
                            onClick={() => handleMudarStatus(item.id, 'Chamado')}
                            disabled={updatingId === item.id || item.status === 'Chamado'}
                            className="h-8 px-3 rounded-xl border border-amber-300 bg-amber-50 hover:bg-amber-100 text-amber-900 text-xs font-bold transition-all cursor-pointer inline-flex items-center gap-1"
                          >
                            <Megaphone className="w-3.5 h-3.5 text-amber-600" />
                            <span>Chamar Senha</span>
                          </button>

                          <button
                            onClick={() => handleMudarStatus(item.id, 'Atendido')}
                            disabled={updatingId === item.id}
                            className="h-8 px-3.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 active:scale-95 text-white text-xs font-bold shadow-xs transition-all cursor-pointer inline-flex items-center gap-1.5"
                          >
                            <Check className="w-3.5 h-3.5" />
                            <span>Dar Baixa / Atendido</span>
                          </button>
                        </div>
                      </div>
                    ))
                  )}
                </div>

                {/* COLUNA 2: FILA GERAL / COMUM */}
                <div className="space-y-3">
                  <div className="flex items-center justify-between pb-2 border-b border-slate-200">
                    <div className="flex items-center gap-2">
                      <span className="w-3 h-3 rounded-full bg-emerald-500" />
                      <h3 className="font-black text-slate-900 text-sm uppercase tracking-wider flex items-center gap-1.5">
                        👥 Fila Comum / Geral ({filtraPorBusca(filaComum).length})
                      </h3>
                    </div>
                    <span className="text-[10px] font-bold bg-slate-100 text-slate-600 px-2 py-0.5 rounded-md">
                      Ordem de Chegada
                    </span>
                  </div>

                  {filtraPorBusca(filaComum).length === 0 ? (
                    <div className="p-6 text-center bg-white/60 border border-dashed border-slate-200 rounded-2xl text-xs text-slate-400 font-medium">
                      Nenhum {orgConfig.termo_assistido.toLowerCase()} na fila comum.
                    </div>
                  ) : (
                    filtraPorBusca(filaComum).map((item) => (
                      <div
                        key={item.id}
                        className={`p-4 rounded-2xl border transition-all shadow-xs bg-white ${
                          item.status === 'Chamado'
                            ? 'border-emerald-400 ring-2 ring-emerald-200 bg-emerald-50/40'
                            : 'border-slate-200/80 hover:border-slate-300'
                        }`}
                      >
                        <div className="flex items-start justify-between gap-3">
                          <div className="flex items-center gap-3 min-w-0">
                            <div className="w-14 h-14 rounded-2xl bg-slate-800 text-white flex flex-col items-center justify-center font-black shrink-0 shadow-xs">
                              <span className="text-base leading-none">{item.numero_senha || 'G-01'}</span>
                              <span className="text-[9px] uppercase font-bold opacity-80 mt-0.5">#{item.ordem_chegada}º</span>
                            </div>

                            <div className="min-w-0">
                              <div className="flex items-center gap-2">
                                <h4 className="font-black text-slate-900 text-sm truncate">{item.pessoa}</h4>
                                {item.status === 'Chamado' && (
                                  <span className="text-[10px] font-extrabold bg-emerald-200 text-emerald-900 px-2 py-0.5 rounded-full flex items-center gap-1 animate-pulse">
                                    <Megaphone className="w-3 h-3" /> Chamando
                                  </span>
                                )}
                              </div>
                              <p className="text-xs text-slate-500 font-medium mt-0.5 flex items-center gap-1.5">
                                <span>{item.tipo_servico || orgConfig.termo_servico}</span>
                                {item.telefone && (
                                  <>
                                    <span>•</span>
                                    <span className="flex items-center gap-0.5 text-slate-600">
                                      <Phone className="w-3 h-3 text-slate-400" /> {item.telefone}
                                    </span>
                                  </>
                                )}
                              </p>
                              {item.observacoes && (
                                <p className="text-[11px] text-slate-600 bg-slate-50 px-2 py-0.5 rounded-md mt-1 italic">
                                  {item.observacoes}
                                </p>
                              )}
                            </div>
                          </div>

                          <div className="text-right shrink-0">
                            <span className="text-[11px] font-bold text-slate-400 flex items-center gap-1 justify-end">
                              <Clock className="w-3 h-3" />
                              {new Date(item.data_hora).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                            </span>
                          </div>
                        </div>

                        <div className="mt-3 pt-3 border-t border-slate-100 flex items-center justify-end gap-2">
                          <button
                            onClick={() => handleMudarStatus(item.id, 'Ausente')}
                            disabled={updatingId === item.id}
                            className="h-8 px-2.5 rounded-xl border border-slate-200 hover:border-rose-300 hover:bg-rose-50 text-slate-500 hover:text-rose-700 text-xs font-bold transition-all cursor-pointer inline-flex items-center gap-1"
                          >
                            <UserX className="w-3.5 h-3.5" />
                            <span>Ausente</span>
                          </button>

                          <button
                            onClick={() => handleMudarStatus(item.id, 'Chamado')}
                            disabled={updatingId === item.id || item.status === 'Chamado'}
                            className="h-8 px-3 rounded-xl border border-slate-300 bg-slate-50 hover:bg-slate-100 text-slate-800 text-xs font-bold transition-all cursor-pointer inline-flex items-center gap-1"
                          >
                            <Megaphone className="w-3.5 h-3.5 text-slate-600" />
                            <span>Chamar Senha</span>
                          </button>

                          <button
                            onClick={() => handleMudarStatus(item.id, 'Atendido')}
                            disabled={updatingId === item.id}
                            className="h-8 px-3.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 active:scale-95 text-white text-xs font-bold shadow-xs transition-all cursor-pointer inline-flex items-center gap-1.5"
                          >
                            <Check className="w-3.5 h-3.5" />
                            <span>Dar Baixa / Atendido</span>
                          </button>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {/* ABA 2: PRÉ-AGENDADOS (CHECK-IN CONFORME CHEGAM NA CASA) */}
        {activeTab === 'preagendados' && (
          <div className="space-y-4">
            <div className="p-4 rounded-2xl bg-indigo-50 border border-indigo-200 text-indigo-950 text-xs flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 shadow-xs">
              <div className="flex items-center gap-2">
                <Calendar className="w-5 h-5 text-indigo-600 shrink-0" />
                <div>
                  <p className="font-bold">Agendamentos feitos previamente durante a semana</p>
                  <p className="text-indigo-700 mt-0.5">
                    Conforme o(a) {orgConfig.termo_assistido.toLowerCase()} chegar à casa, clique em <strong>"Fazer Check-in & Emitir Senha"</strong> para colocá-lo na Fila Ativa de chamada.
                  </p>
                </div>
              </div>

              <button
                onClick={() => setIsPreAgendarModalOpen(true)}
                className="h-9 px-3.5 bg-indigo-600 hover:bg-indigo-700 active:scale-95 text-white font-bold text-xs rounded-xl shadow-xs transition-all cursor-pointer whitespace-nowrap inline-flex items-center gap-1.5"
              >
                <Plus className="w-4 h-4" />
                <span>+ Novo Pré-Agendamento</span>
              </button>
            </div>

            {filtraPorBusca(preAgendados).length === 0 ? (
              <div className="bg-white rounded-3xl p-12 text-center border border-slate-200/80 shadow-xs flex flex-col items-center">
                <Calendar className="w-12 h-12 text-indigo-300 mb-3" />
                <h3 className="font-bold text-slate-800 text-base">Nenhum pré-agendamento pendente para este evento</h3>
                <p className="text-xs text-slate-400 mt-1 max-w-md">
                  Pessoas que ligam ou mandam WhatsApp durante a semana podem ser pré-agendadas clicando no botão acima.
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {filtraPorBusca(preAgendados).map((item) => (
                  <div
                    key={item.id}
                    className={`p-5 rounded-2xl border bg-white shadow-xs flex flex-col justify-between transition-all ${
                      item.preferencial ? 'border-amber-300 ring-1 ring-amber-200' : 'border-slate-200/80'
                    }`}
                  >
                    <div>
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <div className="flex items-center gap-2">
                            <h4 className="font-black text-slate-900 text-base">{item.pessoa}</h4>
                            {item.preferencial && (
                              <span className="text-[10px] font-bold bg-amber-100 text-amber-800 px-2 py-0.5 rounded-full">
                                ⚡ Preferencial
                              </span>
                            )}
                          </div>

                          <p className="text-xs text-slate-600 mt-1 flex items-center gap-2">
                            <span>{item.tipo_servico || orgConfig.termo_servico}</span>
                            {item.telefone && (
                              <>
                                <span>&bull;</span>
                                <span className="flex items-center gap-1 text-slate-500">
                                  <Phone className="w-3 h-3 text-slate-400" /> {item.telefone}
                                </span>
                              </>
                            )}
                          </p>

                          {item.observacoes && (
                            <p className="text-xs text-slate-600 bg-slate-50 p-2 rounded-xl mt-2 italic border border-slate-100">
                              {item.observacoes}
                            </p>
                          )}
                        </div>

                        <span className="text-[11px] font-semibold text-indigo-700 bg-indigo-50 px-2.5 py-1 rounded-lg border border-indigo-100 shrink-0">
                          Reserva Confirmada
                        </span>
                      </div>
                    </div>

                    <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between gap-2">
                      <span className="text-[11px] text-slate-400">
                        Agendado em: {new Date(item.data_hora).toLocaleDateString()}
                      </span>

                      <button
                        onClick={() => handleCheckin(item.id, item.pessoa || 'o consulente')}
                        disabled={updatingId === item.id}
                        className="h-10 px-4 bg-emerald-600 hover:bg-emerald-700 active:scale-95 text-white font-bold text-xs rounded-xl shadow-xs transition-all cursor-pointer inline-flex items-center gap-1.5"
                      >
                        <UserCheck className="w-4 h-4" />
                        <span>Fazer Check-in & Emitir Senha</span>
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* ABA 3: AUSENTES */}
        {activeTab === 'ausentes' && (
          <div className="space-y-4">
            <div className="p-4 rounded-2xl bg-amber-50/70 border border-amber-200 text-amber-900 text-xs flex items-center justify-between gap-3">
              <div className="flex items-center gap-2">
                <RotateCcw className="w-4 h-4 text-amber-700 shrink-0" />
                <span>
                  <strong>Não ouviu a chamada de sua senha?</strong> O indivíduo pode ser reativado a qualquer momento com 1 clique abaixo, voltando diretamente para a fila ativa de chamada.
                </span>
              </div>
            </div>

            {filtraPorBusca(listaAusentes).length === 0 ? (
              <div className="bg-white rounded-3xl p-12 text-center border border-slate-200/80 shadow-xs flex flex-col items-center">
                <UserCheck className="w-12 h-12 text-emerald-400 mb-3" />
                <h3 className="font-bold text-slate-800 text-base">Nenhum {orgConfig.termo_assistido.toLowerCase()} ausente</h3>
                <p className="text-xs text-slate-400 mt-1">Todos que foram chamados compareceram ou já foram atendidos.</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {filtraPorBusca(listaAusentes).map((item) => (
                  <div key={item.id} className="p-5 rounded-2xl border border-rose-200 bg-white shadow-xs flex flex-col justify-between">
                    <div>
                      <div className="flex items-center justify-between gap-3">
                        <div className="flex items-center gap-3">
                          <span className="h-10 px-3 rounded-xl bg-rose-100 text-rose-800 font-black text-sm flex items-center justify-center">
                            {item.numero_senha || 'SEM-SENHA'}
                          </span>
                          <div>
                            <h4 className="font-black text-slate-900 text-sm">{item.pessoa}</h4>
                            <p className="text-xs text-slate-500">{item.tipo_servico || orgConfig.termo_servico}</p>
                          </div>
                        </div>
                        <span className="text-[10px] uppercase font-extrabold bg-rose-100 text-rose-700 px-2 py-0.5 rounded-md">
                          Ausente
                        </span>
                      </div>
                    </div>

                    <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between gap-2">
                      <span className="text-xs text-slate-400">Ordem original: #{item.ordem_chegada}º</span>
                      <button
                        onClick={() => handleReativarAusente(item.id)}
                        disabled={updatingId === item.id}
                        className="h-9 px-4 bg-emerald-600 hover:bg-emerald-700 active:scale-95 text-white text-xs font-bold rounded-xl shadow-xs transition-all cursor-pointer inline-flex items-center gap-1.5"
                      >
                        <RotateCcw className="w-3.5 h-3.5" />
                        <span>Reativar / Voltar para a Fila</span>
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* ABA 4: ATENDIDOS */}
        {activeTab === 'atendidos' && (
          <div className="space-y-4">
            {filtraPorBusca(listaAtendidos).length === 0 ? (
              <div className="bg-white rounded-3xl p-12 text-center border border-slate-200/80 shadow-xs flex flex-col items-center">
                <Clock className="w-12 h-12 text-slate-300 mb-3" />
                <h3 className="font-bold text-slate-800 text-base">Nenhum atendimento finalizado ainda</h3>
                <p className="text-xs text-slate-400 mt-1">Conforme os atendimentos forem concluídos na fila, eles aparecerão aqui.</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {filtraPorBusca(listaAtendidos).map((item) => (
                  <div key={item.id} className="p-4 rounded-2xl border border-emerald-200 bg-white shadow-xs">
                    <div className="flex items-center justify-between gap-2">
                      <span className="h-8 px-2.5 rounded-lg bg-emerald-100 text-emerald-800 font-black text-xs flex items-center justify-center">
                        {item.numero_senha || 'OK'}
                      </span>
                      <span className="text-[10px] font-bold text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded-md flex items-center gap-1">
                        <Check className="w-3 h-3" /> Concluído
                      </span>
                    </div>
                    <h4 className="font-bold text-slate-900 text-sm mt-2 truncate">{item.pessoa}</h4>
                    <p className="text-xs text-slate-500 mt-0.5">{item.tipo_servico || orgConfig.termo_servico}</p>
                    <p className="text-[10px] text-slate-400 mt-2">
                      Chegada: {new Date(item.data_hora).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} &bull; #{item.ordem_chegada}º
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* ABA 5: CONFIGURAÇÕES DA ENTIDADE */}
        {activeTab === 'config' && (
          <div className="space-y-6">
            <div className="bg-white p-6 rounded-3xl border border-slate-200/80 shadow-xs space-y-6">
              <div>
                <h3 className="font-black text-slate-900 text-lg flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-emerald-600" />
                  Adaptação da Entidade / Vocabulário Customizado
                </h3>
                <p className="text-xs sm:text-sm text-slate-500 font-medium mt-1">
                  O Unython se adapta ao seu contexto social ou espiritual. Escolha um modelo pronto ou personalize cada termo livremente.
                </p>
              </div>

              {/* Modelos Rápidos */}
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase mb-2">Modelos Rápidos (1 Clique)</label>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5">
                  {presets.map((p) => {
                    const isCurrent = orgConfig.tipo_organizacao.toLowerCase().includes(p.tipo.toLowerCase().split('/')[0].trim());
                    return (
                      <button
                        key={p.tipo}
                        type="button"
                        onClick={() => {
                          handleSalvarConfigOrg({
                            tipo_organizacao: p.tipo,
                            termo_assistido: p.assistido,
                            termo_assistido_plural: p.assistidos,
                            termo_atendente: p.atendente,
                            termo_servico: p.servico,
                          });
                        }}
                        className={`p-3.5 rounded-2xl border text-left transition-all cursor-pointer ${
                          isCurrent
                            ? 'border-emerald-500 bg-emerald-50/50 shadow-xs'
                            : 'border-slate-200 hover:border-slate-300 hover:bg-slate-50'
                        }`}
                      >
                        <div className="flex items-center gap-2 font-black text-sm text-slate-900">
                          <span className="text-xl">{p.icon}</span>
                          <span>{p.tipo.split('/')[0].trim()}</span>
                        </div>
                        <p className="text-xs text-slate-500 mt-1">
                          {p.assistido} &bull; {p.atendente} &bull; {p.servico}
                        </p>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Edição Manual */}
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  handleSalvarConfigOrg();
                }}
                className="space-y-4 pt-4 border-t border-slate-100"
              >
                <h4 className="font-bold text-slate-800 text-xs uppercase tracking-wider">Ajuste Manual dos Termos</h4>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Tipo da Organização</label>
                    <input
                      type="text"
                      value={orgConfig.tipo_organizacao}
                      onChange={(e) => setOrgConfig({ ...orgConfig, tipo_organizacao: e.target.value })}
                      className="w-full h-11 px-3.5 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium focus:bg-white"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-slate-700 uppercase mb-1">
                      Termo para a Pessoa Atendida (Singular)
                    </label>
                    <input
                      type="text"
                      placeholder="Ex: Consulente, Fiel, Acolhido, Paciente"
                      value={orgConfig.termo_assistido}
                      onChange={(e) => setOrgConfig({ ...orgConfig, termo_assistido: e.target.value })}
                      className="w-full h-11 px-3.5 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium focus:bg-white"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-slate-700 uppercase mb-1">
                      Termo para as Pessoas Atendidas (Plural)
                    </label>
                    <input
                      type="text"
                      placeholder="Ex: Consulentes, Fiéis, Acolhidos, Pacientes"
                      value={orgConfig.termo_assistido_plural}
                      onChange={(e) => setOrgConfig({ ...orgConfig, termo_assistido_plural: e.target.value })}
                      className="w-full h-11 px-3.5 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium focus:bg-white"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-slate-700 uppercase mb-1">
                      Termo para o Atendente / Facilitador
                    </label>
                    <input
                      type="text"
                      placeholder="Ex: Médium, Pastor, Padre, Assistente Social"
                      value={orgConfig.termo_atendente}
                      onChange={(e) => setOrgConfig({ ...orgConfig, termo_atendente: e.target.value })}
                      className="w-full h-11 px-3.5 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium focus:bg-white"
                    />
                  </div>

                  <div className="sm:col-span-2">
                    <label className="block text-xs font-bold text-slate-700 uppercase mb-1">
                      Termo Padrão do Serviço / Atendimento
                    </label>
                    <input
                      type="text"
                      placeholder="Ex: Passe / Consulta, Oração, Triagem, Aconselhamento"
                      value={orgConfig.termo_servico}
                      onChange={(e) => setOrgConfig({ ...orgConfig, termo_servico: e.target.value })}
                      className="w-full h-11 px-3.5 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium focus:bg-white"
                    />
                  </div>
                </div>

                <div className="pt-2 flex justify-end">
                  <button
                    type="submit"
                    className="h-11 px-6 bg-slate-900 hover:bg-slate-800 text-white font-bold text-xs sm:text-sm rounded-xl shadow-xs transition-all cursor-pointer"
                  >
                    Salvar Parâmetros Customizados
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>

      {/* MODAL 1: CHECK-IN PRESENCIAL NA PORTA (EMITE SENHA IMEDIATA) */}
      {isPresencialModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 animate-fade-in">
          <div className="bg-white rounded-3xl max-w-lg w-full shadow-2xl border border-slate-100 p-6 flex flex-col max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-lg bg-emerald-100 text-emerald-800 flex items-center justify-center font-bold">
                  <Plus className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="font-black text-slate-900 text-base">Check-in Presencial / Porta</h3>
                  <p className="text-xs text-slate-500">Para quem chegou agora na casa sem agendamento prévio</p>
                </div>
              </div>
              <button
                onClick={() => setIsPresencialModalOpen(false)}
                className="p-1 rounded-lg text-slate-400 hover:text-slate-600 cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleAcolherPresencial} className="space-y-4 mt-4">
              <div className="flex p-1 bg-slate-100 rounded-xl gap-1">
                <button
                  type="button"
                  onClick={() => setModoCadastro('novo')}
                  className={`flex-1 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${
                    modoCadastro === 'novo' ? 'bg-white text-emerald-800 shadow-xs' : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  Novo(a) {orgConfig.termo_assistido}
                </button>
                <button
                  type="button"
                  onClick={() => setModoCadastro('existente')}
                  className={`flex-1 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${
                    modoCadastro === 'existente' ? 'bg-white text-emerald-800 shadow-xs' : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  Já Cadastrado(a)
                </button>
              </div>

              {modoCadastro === 'existente' ? (
                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase mb-1">
                    Selecione o(a) {orgConfig.termo_assistido}
                  </label>
                  <select
                    value={selectedPessoaId || ''}
                    onChange={(e) => {
                      const id = Number(e.target.value);
                      setSelectedPessoaId(id);
                      const p = pessoasCadastradas.find((x) => x.id === id);
                      if (p) setFormPreferencial(!!p.preferencial);
                    }}
                    required
                    className="w-full h-11 px-3.5 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium focus:bg-white"
                  >
                    <option value="">Selecione na lista...</option>
                    {pessoasCadastradas.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.nome} {p.telefone ? `(${p.telefone})` : ''} {p.preferencial ? '⚡ [Preferencial]' : ''}
                      </option>
                    ))}
                  </select>
                </div>
              ) : (
                <div className="space-y-3">
                  <div>
                    <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Nome Completo *</label>
                    <input
                      type="text"
                      required
                      value={formNome}
                      onChange={(e) => setFormNome(e.target.value)}
                      placeholder="Ex: Maria das Graças"
                      className="w-full h-11 px-3.5 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium focus:bg-white"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Telefone / WhatsApp</label>
                      <input
                        type="text"
                        value={formTelefone}
                        onChange={(e) => setFormTelefone(e.target.value)}
                        placeholder="(11) 99999-9999"
                        className="w-full h-11 px-3.5 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium focus:bg-white"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Documento / CPF</label>
                      <input
                        type="text"
                        value={formDocumento}
                        onChange={(e) => setFormDocumento(e.target.value)}
                        placeholder="Opcional"
                        className="w-full h-11 px-3.5 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium focus:bg-white"
                      />
                    </div>
                  </div>
                </div>
              )}

              {/* Fila Preferencial ou Geral */}
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase mb-1.5">Fila de Atendimento</label>
                <div className="grid grid-cols-2 gap-2.5">
                  <button
                    type="button"
                    onClick={() => setFormPreferencial(false)}
                    className={`p-3 rounded-2xl border text-left transition-all cursor-pointer ${
                      !formPreferencial
                        ? 'border-slate-800 bg-slate-900 text-white shadow-xs'
                        : 'border-slate-200 text-slate-700 hover:bg-slate-50'
                    }`}
                  >
                    <div className="flex items-center gap-1.5 font-black text-xs">
                      <span>👥 Fila Geral</span>
                    </div>
                    <p className={`text-[11px] mt-1 ${!formPreferencial ? 'text-slate-300' : 'text-slate-500'}`}>
                      Gera senha <strong>G-XX</strong>
                    </p>
                  </button>

                  <button
                    type="button"
                    onClick={() => setFormPreferencial(true)}
                    className={`p-3 rounded-2xl border text-left transition-all cursor-pointer ${
                      formPreferencial
                        ? 'border-amber-500 bg-amber-500 text-white shadow-xs'
                        : 'border-slate-200 text-slate-700 hover:bg-slate-50'
                    }`}
                  >
                    <div className="flex items-center gap-1.5 font-black text-xs">
                      <span>⚡ Preferencial</span>
                    </div>
                    <p className={`text-[11px] mt-1 ${formPreferencial ? 'text-amber-100' : 'text-slate-500'}`}>
                      Gera senha <strong>P-XX</strong> (Prioridade)
                    </p>
                  </button>
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Atendimento Solicitado</label>
                <input
                  type="text"
                  value={formServico}
                  onChange={(e) => setFormServico(e.target.value)}
                  placeholder={`Ex: ${orgConfig.termo_servico}`}
                  className="w-full h-11 px-3.5 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium focus:bg-white"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Observações</label>
                <input
                  type="text"
                  value={formObservacoes}
                  onChange={(e) => setFormObservacoes(e.target.value)}
                  placeholder="Ex: Primeira vez na casa..."
                  className="w-full h-11 px-3.5 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium focus:bg-white"
                />
              </div>

              <div className="pt-2 flex gap-2">
                <button
                  type="button"
                  onClick={() => setIsPresencialModalOpen(false)}
                  className="flex-1 h-11 border border-slate-200 hover:bg-slate-100 rounded-xl text-slate-700 font-bold text-xs transition-colors cursor-pointer"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="flex-2 h-11 bg-emerald-600 hover:bg-emerald-700 active:scale-95 text-white font-bold text-xs sm:text-sm rounded-xl shadow-xs transition-all cursor-pointer flex items-center justify-center gap-2"
                >
                  {isSubmitting ? 'Emitindo Senha...' : 'Emitir Senha & Entrar na Fila'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL 2: PRÉ-AGENDAMENTO COM ANTECEDÊNCIA (PARA EVENTO FUTURO) */}
      {isPreAgendarModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 animate-fade-in">
          <div className="bg-white rounded-3xl max-w-lg w-full shadow-2xl border border-slate-100 p-6 flex flex-col max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-lg bg-indigo-100 text-indigo-800 flex items-center justify-center font-bold">
                  <Calendar className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="font-black text-slate-900 text-base">Pré-Agendar com Antecedência</h3>
                  <p className="text-xs text-slate-500">Garante vaga para uma data futura (a senha será emitida no dia)</p>
                </div>
              </div>
              <button
                onClick={() => setIsPreAgendarModalOpen(false)}
                className="p-1 rounded-lg text-slate-400 hover:text-slate-600 cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handlePreAgendar} className="space-y-4 mt-4">
              {/* Seleção do Evento Futuro */}
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase mb-1">
                  Selecione o Evento / Gira Futura *
                </label>
                <select
                  value={formEventoAlvoId || selectedEventoId || ''}
                  onChange={(e) => setFormEventoAlvoId(Number(e.target.value))}
                  required
                  className="w-full h-11 px-3.5 bg-slate-50 border border-slate-200 rounded-xl text-sm font-bold text-slate-900 focus:bg-white"
                >
                  {eventosDisponiveis.map((ev) => (
                    <option key={ev.id} value={ev.id}>
                      {ev.nome} ({ev.data_evento}) &bull; [{ev.status}]
                    </option>
                  ))}
                </select>
                <p className="text-[11px] text-slate-400 mt-1">
                  Não encontrou a data desejada? Feche e clique em "+ Nova Data / Evento".
                </p>
              </div>

              {/* Alternador Novo / Já Cadastrado */}
              <div className="flex p-1 bg-slate-100 rounded-xl gap-1">
                <button
                  type="button"
                  onClick={() => setModoCadastro('novo')}
                  className={`flex-1 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${
                    modoCadastro === 'novo' ? 'bg-white text-indigo-900 shadow-xs' : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  Novo(a) {orgConfig.termo_assistido}
                </button>
                <button
                  type="button"
                  onClick={() => setModoCadastro('existente')}
                  className={`flex-1 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${
                    modoCadastro === 'existente' ? 'bg-white text-indigo-900 shadow-xs' : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  Já Cadastrado(a)
                </button>
              </div>

              {modoCadastro === 'existente' ? (
                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase mb-1">
                    Selecione o(a) {orgConfig.termo_assistido}
                  </label>
                  <select
                    value={selectedPessoaId || ''}
                    onChange={(e) => {
                      const id = Number(e.target.value);
                      setSelectedPessoaId(id);
                      const p = pessoasCadastradas.find((x) => x.id === id);
                      if (p) setFormPreferencial(!!p.preferencial);
                    }}
                    required
                    className="w-full h-11 px-3.5 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium focus:bg-white"
                  >
                    <option value="">Selecione na lista...</option>
                    {pessoasCadastradas.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.nome} {p.telefone ? `(${p.telefone})` : ''} {p.preferencial ? '⚡ [Preferencial]' : ''}
                      </option>
                    ))}
                  </select>
                </div>
              ) : (
                <div className="space-y-3">
                  <div>
                    <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Nome Completo *</label>
                    <input
                      type="text"
                      required
                      value={formNome}
                      onChange={(e) => setFormNome(e.target.value)}
                      placeholder="Ex: João da Silva"
                      className="w-full h-11 px-3.5 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium focus:bg-white"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Telefone / WhatsApp</label>
                      <input
                        type="text"
                        value={formTelefone}
                        onChange={(e) => setFormTelefone(e.target.value)}
                        placeholder="(11) 98888-8888"
                        className="w-full h-11 px-3.5 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium focus:bg-white"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Documento / CPF</label>
                      <input
                        type="text"
                        value={formDocumento}
                        onChange={(e) => setFormDocumento(e.target.value)}
                        placeholder="Opcional"
                        className="w-full h-11 px-3.5 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium focus:bg-white"
                      />
                    </div>
                  </div>
                </div>
              )}

              {/* Fila Preferencial */}
              <div className="flex items-center gap-3 p-3 rounded-2xl bg-slate-50 border border-slate-200">
                <input
                  type="checkbox"
                  id="prefCheck"
                  checked={formPreferencial}
                  onChange={(e) => setFormPreferencial(e.target.checked)}
                  className="w-4 h-4 text-amber-600 rounded focus:ring-amber-500"
                />
                <label htmlFor="prefCheck" className="text-xs font-bold text-slate-800 cursor-pointer">
                  ⚡ Marcar como Fila Preferencial (Idoso 60+, Gestante, PCD, Colo)
                </label>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Atendimento Desejado</label>
                <input
                  type="text"
                  value={formServico}
                  onChange={(e) => setFormServico(e.target.value)}
                  placeholder={`Ex: ${orgConfig.termo_servico}`}
                  className="w-full h-11 px-3.5 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium focus:bg-white"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Observações da Reserva</label>
                <input
                  type="text"
                  value={formObservacoes}
                  onChange={(e) => setFormObservacoes(e.target.value)}
                  placeholder="Ex: Confirmou presença pelo WhatsApp..."
                  className="w-full h-11 px-3.5 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium focus:bg-white"
                />
              </div>

              <div className="pt-2 flex gap-2">
                <button
                  type="button"
                  onClick={() => setIsPreAgendarModalOpen(false)}
                  className="flex-1 h-11 border border-slate-200 hover:bg-slate-100 rounded-xl text-slate-700 font-bold text-xs transition-colors cursor-pointer"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="flex-2 h-11 bg-indigo-600 hover:bg-indigo-700 active:scale-95 text-white font-bold text-xs sm:text-sm rounded-xl shadow-xs transition-all cursor-pointer flex items-center justify-center gap-2"
                >
                  {isSubmitting ? 'Confirmando Reserva...' : 'Confirmar Pré-Agendamento'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL 3: CADASTRAR NOVO EVENTO NO CALENDÁRIO */}
      {isNovoEventoModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 animate-fade-in">
          <div className="bg-white rounded-3xl max-w-md w-full shadow-2xl border border-slate-100 p-6 flex flex-col">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <CalendarPlus className="w-5 h-5 text-emerald-600" />
                <h3 className="font-black text-slate-900 text-base">Nova Data no Calendário</h3>
              </div>
              <button
                onClick={() => setIsNovoEventoModalOpen(false)}
                className="p-1 rounded-lg text-slate-400 hover:text-slate-600 cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCriarEventoFuturo} className="space-y-3.5 mt-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase mb-1">
                  Nome do Evento / Trabalho *
                </label>
                <input
                  type="text"
                  required
                  value={novoEvNome}
                  onChange={(e) => setNovoEvNome(e.target.value)}
                  placeholder="Ex: Gira de Marinheiro, Culto de Cura, Bazar Beneficente"
                  className="w-full h-11 px-3.5 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium focus:bg-white"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Data Prevista *</label>
                <input
                  type="date"
                  required
                  value={novoEvData}
                  onChange={(e) => setNovoEvData(e.target.value)}
                  className="w-full h-11 px-3.5 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium focus:bg-white"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Tipo de Trabalho</label>
                <input
                  type="text"
                  value={novoEvTipo}
                  onChange={(e) => setNovoEvTipo(e.target.value)}
                  placeholder="Ex: Gira, Culto, Passe, Acolhimento"
                  className="w-full h-11 px-3.5 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium focus:bg-white"
                />
              </div>

              <div className="pt-2 flex gap-2">
                <button
                  type="button"
                  onClick={() => setIsNovoEventoModalOpen(false)}
                  className="flex-1 h-11 border border-slate-200 hover:bg-slate-100 rounded-xl text-slate-700 font-bold text-xs transition-colors cursor-pointer"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="flex-2 h-11 bg-slate-900 hover:bg-slate-800 text-white font-bold text-xs sm:text-sm rounded-xl shadow-xs transition-all cursor-pointer flex items-center justify-center gap-2"
                >
                  {isSubmitting ? 'Agendando...' : 'Cadastrar no Calendário'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
