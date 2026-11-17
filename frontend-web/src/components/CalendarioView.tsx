import { useEffect, useState } from 'react';
import type { FormEvent } from 'react';
import { apiClient } from '../api/client';
import type { Evento } from '../types';

interface Props {
  activeEvento: Evento | null;
  onRefreshState: () => Promise<void>;
}

const dateKey = (year: number, month: number, day: number) =>
  `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;

export function CalendarioView({ activeEvento, onRefreshState }: Props) {
  const [month, setMonth] = useState(() => new Date(new Date().getFullYear(), new Date().getMonth(), 1));
  const [eventos, setEventos] = useState<Evento[]>([]);
  const [selected, setSelected] = useState<Evento | null>(null);
  const [nome, setNome] = useState('');
  const [data, setData] = useState('');
  const [tipo, setTipo] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const year = month.getFullYear();
  const monthIndex = month.getMonth();
  const days = new Date(year, monthIndex + 1, 0).getDate();
  const offset = new Date(year, monthIndex, 1).getDay();

  const load = async () => {
    try {
      const res = await apiClient.get('/eventos/', { params: { data_inicio: dateKey(year, monthIndex, 1), data_fim: dateKey(year, monthIndex, days) } });
      setEventos(res.data);
      setError('');
    } catch {
      setError('Não foi possível carregar os eventos.');
    }
  };

  useEffect(() => { void load(); }, [year, monthIndex]);

  const criar = async (e: FormEvent) => {
    e.preventDefault();
    if (!nome.trim() || !tipo.trim()) {
      setError('Informe nome e tipo do evento.');
      return;
    }
    setBusy(true);
    try {
      await apiClient.post('/eventos/novo', null, { params: { nome: nome.trim(), data_evento: data, tipo: tipo.trim() } });
      setNome(''); setTipo(''); setData('');
      const [y, m] = data.split('-').map(Number);
      if (y === year && m === monthIndex + 1) await load();
      else setMonth(new Date(y, m - 1, 1));
    } catch {
      setError('Não foi possível criar o evento.');
    } finally { setBusy(false); }
  };

  const iniciar = async (evento: Evento) => {
    if (activeEvento && activeEvento.id !== evento.id && !window.confirm(`Iniciar este evento fechará "${activeEvento.nome}". Continuar?`)) return;
    setBusy(true);
    try {
      await apiClient.post(`/eventos/${evento.id}/iniciar`);
      setSelected(null);
      await onRefreshState();
      await load();
    } catch {
      setError('Não foi possível iniciar o evento.');
    } finally { setBusy(false); }
  };

  return <div className="space-y-4">
    {error && <p role="alert" className="p-3 bg-rose-50 text-rose-800 rounded-xl">{error}</p>}
    <form onSubmit={criar} className="bg-white rounded-2xl p-4 flex flex-wrap gap-3 items-end">
      <label className="text-xs font-bold">Nome<input required minLength={2} value={nome} onChange={e => setNome(e.target.value)} className="block border rounded-lg p-2" /></label>
      <label className="text-xs font-bold">Data<input required type="date" value={data} onChange={e => setData(e.target.value)} className="block border rounded-lg p-2" /></label>
      <label className="text-xs font-bold">Tipo<input required value={tipo} onChange={e => setTipo(e.target.value)} className="block border rounded-lg p-2" /></label>
      <button disabled={busy} className="bg-emerald-700 text-white rounded-lg p-2 font-bold text-sm">Criar evento</button>
    </form>
    <div className="bg-white rounded-2xl p-4">
      <div className="flex items-center justify-between mb-4">
        <button type="button" aria-label="Mês anterior" onClick={() => setMonth(new Date(year, monthIndex - 1, 1))}>←</button>
        <h2 className="font-bold capitalize">{month.toLocaleDateString('pt-BR', { month: 'long', year: 'numeric' })}</h2>
        <button type="button" aria-label="Próximo mês" onClick={() => setMonth(new Date(year, monthIndex + 1, 1))}>→</button>
      </div>
      <div className="grid grid-cols-7 gap-1">
        {['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb'].map(d => <div key={d} className="text-center text-xs font-bold">{d}</div>)}
        {Array.from({ length: offset }, (_, i) => <div key={`blank-${i}`} />)}
        {Array.from({ length: days }, (_, i) => {
          const date = dateKey(year, monthIndex, i + 1);
          return <div key={date} className="min-h-20 bg-slate-50 border border-slate-100 p-1 rounded-lg">
            <span className="text-xs font-bold">{i + 1}</span>
            {eventos.filter(ev => ev.data_evento === date).map(ev => <button key={ev.id} type="button" onClick={() => setSelected(ev)} className="block w-full text-left text-xs bg-emerald-100 rounded p-1 mt-1 break-words">{ev.nome}</button>)}
          </div>;
        })}
      </div>
    </div>
    {selected && <div className="bg-white p-4 rounded-2xl">
      <h3 className="font-bold">{selected.nome}</h3>
      <p className="text-sm">{selected.data_evento.split('-').reverse().join('/')} · {selected.tipo} · {selected.status}</p>
      {selected.status === 'Agendado' && <button disabled={busy} onClick={() => void iniciar(selected)} className="mt-2 text-emerald-700 font-bold">Iniciar evento</button>}
      <button onClick={() => setSelected(null)} className="ml-4 text-slate-600">Fechar detalhes</button>
    </div>}
  </div>;
}
