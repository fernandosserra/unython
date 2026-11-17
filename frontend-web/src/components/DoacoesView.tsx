import { useEffect, useState } from 'react';
import type { FormEvent } from 'react';
import { apiClient } from '../api/client';
import { useOrgStore } from '../store/useOrgStore';
import type { Evento } from '../types';

interface Doacao {
  id: number;
  data_registro: string;
  valor: string | number;
  nome_doador: string | null;
  forma_pagamento: string | null;
  descricao: string | null;
  evento: string | null;
  status: string;
}

const hoje = () => {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
};

export function DoacoesView() {
  const aliasEvento = useOrgStore((state) => state.config.alias_evento);
  const [doacoes, setDoacoes] = useState<Doacao[] | null>(null);
  const [eventos, setEventos] = useState<Evento[]>([]);
  const [valor, setValor] = useState('');
  const [data, setData] = useState(hoje);
  const [doador, setDoador] = useState('');
  const [pagamento, setPagamento] = useState('');
  const [descricao, setDescricao] = useState('');
  const [evento, setEvento] = useState('');
  const [error, setError] = useState('');
  const [eventosError, setEventosError] = useState(false);
  const [success, setSuccess] = useState('');
  const [busy, setBusy] = useState(false);

  const loadDoacoes = async () => {
    try {
      const res = await apiClient.get('/doacoes/');
      setDoacoes(res.data);
      setError('');
    } catch { setDoacoes(null); setError('Não foi possível carregar as doações.'); }
  };
  useEffect(() => {
    void loadDoacoes();
    apiClient.get('/eventos/').then(res => setEventos(res.data)).catch(() => setEventosError(true));
  }, []);

  const save = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true); setError(''); setSuccess('');
    try {
      await apiClient.post('/doacoes/', {
        valor, data, nome_doador: doador.trim() || null, forma_pagamento: pagamento.trim() || null,
        descricao: descricao.trim() || null, id_evento: evento ? Number(evento) : null,
      });
      setValor(''); setDoador(''); setPagamento(''); setDescricao(''); setEvento(''); setData(hoje());
      await loadDoacoes();
      setSuccess('Doação registrada no fluxo financeiro.');
    } catch { setError('Não foi possível registrar a doação. Confira os dados e tente novamente.'); }
    finally { setBusy(false); }
  };

  const cancel = async (item: Doacao) => {
    if (!window.confirm('Cancelar esta doação e retirá-la do saldo financeiro?')) return;
    setBusy(true); setError(''); setSuccess('');
    try {
      await apiClient.patch(`/doacoes/${item.id}/cancelar`);
      await loadDoacoes();
      setSuccess('Doação cancelada.');
    } catch { setError('Não foi possível cancelar a doação.'); }
    finally { setBusy(false); }
  };

  return <div className="flex-1 overflow-y-auto bg-slate-100 p-4 sm:p-6">
    <div className="max-w-5xl mx-auto space-y-4">
      <h1 className="text-2xl font-black text-slate-900">Doações financeiras</h1>
      <p className="text-sm text-slate-600">Registre receitas com ou sem {aliasEvento}, sem abrir uma sessão de caixa.</p>
      {error && <p role="alert" className="p-3 bg-rose-50 text-rose-800 rounded-xl">{error}</p>}
      {eventosError && <p role="alert" className="p-3 bg-amber-50 text-amber-800 rounded-xl">Não foi possível carregar {aliasEvento}; você ainda pode registrar uma doação sem vinculá-lo.</p>}
      {success && <p role="status" className="p-3 bg-emerald-50 text-emerald-800 rounded-xl">{success}</p>}
      <form onSubmit={save} className="bg-white rounded-2xl p-5 space-y-3">
        <h2 className="font-bold">Registrar doação</h2>
        <div className="grid sm:grid-cols-2 gap-3">
          <label className="text-xs font-bold">Valor (R$)<input required type="number" min="0.01" step="0.01" value={valor} onChange={e => setValor(e.target.value)} className="block w-full border rounded-lg p-2" /></label>
          <label className="text-xs font-bold">Data<input required type="date" value={data} onChange={e => setData(e.target.value)} className="block w-full border rounded-lg p-2" /></label>
          <label className="text-xs font-bold">Doador (opcional)<input maxLength={255} value={doador} onChange={e => setDoador(e.target.value)} className="block w-full border rounded-lg p-2" /></label>
          <label className="text-xs font-bold">Forma de pagamento (opcional)<input maxLength={100} value={pagamento} onChange={e => setPagamento(e.target.value)} placeholder="Ex: PIX, dinheiro" className="block w-full border rounded-lg p-2" /></label>
          <label className="text-xs font-bold">{aliasEvento} (opcional)<select value={evento} onChange={e => setEvento(e.target.value)} className="block w-full border rounded-lg p-2">
            <option value="">Sem {aliasEvento}</option>
            {eventos.map(item => <option key={item.id} value={item.id}>{item.nome} ({item.data_evento.split('-').reverse().join('/')})</option>)}
          </select></label>
          <label className="text-xs font-bold">Observações (opcional)<input value={descricao} onChange={e => setDescricao(e.target.value)} className="block w-full border rounded-lg p-2" /></label>
        </div>
        <button disabled={busy} className="bg-emerald-700 text-white rounded-lg p-2 font-bold text-sm">Registrar doação</button>
      </form>
      <div className="bg-white rounded-2xl p-5 space-y-2">
        <h2 className="font-bold">Histórico</h2>
        {doacoes?.length === 0 && <p className="text-sm text-slate-500">Nenhuma doação registrada.</p>}
        {doacoes?.map(item => <div key={item.id} className="border rounded-xl p-3 flex flex-wrap justify-between gap-2">
          <div>
            <strong>R$ {Number(item.valor).toFixed(2).replace('.', ',')}</strong>
            <p className="text-sm text-slate-600">{item.data_registro.slice(0, 10).split('-').reverse().join('/')} · {item.nome_doador || 'Doador não informado'} · {item.status}</p>
            {(item.forma_pagamento || item.evento || item.descricao) && <p className="text-sm text-slate-500">{[item.forma_pagamento, item.evento, item.descricao].filter(Boolean).join(' · ')}</p>}
          </div>
          {item.status === 'Ativo' && <button type="button" disabled={busy} onClick={() => void cancel(item)} className="text-rose-700 text-sm font-bold">Cancelar doação</button>}
        </div>)}
      </div>
    </div>
  </div>;
}
