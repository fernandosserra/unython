import { useEffect, useState } from 'react';
import type { FormEvent } from 'react';
import { apiClient } from '../api/client';
import type { Facilitador } from '../types';

export function FacilitadoresView() {
  const [items, setItems] = useState<Facilitador[]>([]);
  const [termo, setTermo] = useState('Atendente');
  const [editing, setEditing] = useState<Facilitador | null>(null);
  const [nome, setNome] = useState('');
  const [especialidade, setEspecialidade] = useState('');
  const [observacoes, setObservacoes] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const load = async () => {
    try {
      const [list, config] = await Promise.all([apiClient.get('/facilitadores/'), apiClient.get('/organizacao/config')]);
      setItems(list.data); setTermo(config.data.termo_atendente); setError('');
    } catch { setError('Não foi possível carregar os cadastros ou a configuração.'); }
  };
  useEffect(() => { void load(); }, []);
  const clear = () => { setEditing(null); setNome(''); setEspecialidade(''); setObservacoes(''); };
  const save = async (e: FormEvent) => {
    e.preventDefault(); setBusy(true);
    try {
      const payload = { nome: nome.trim(), especialidade: especialidade.trim() || null, observacoes: observacoes.trim() || null, status: editing?.status || 'Ativo' };
      if (editing) await apiClient.put(`/facilitadores/${editing.id}`, payload);
      else await apiClient.post('/facilitadores/', payload);
      clear(); await load();
    } catch { setError('Não foi possível salvar o cadastro.'); }
    finally { setBusy(false); }
  };
  const toggle = async (item: Facilitador) => {
    if (item.status === 'Ativo' && !window.confirm(`Inativar "${item.nome}"? Os agendamentos existentes serão preservados.`)) return;
    setBusy(true);
    try {
      if (item.status === 'Ativo') await apiClient.delete(`/facilitadores/${item.id}`);
      else await apiClient.put(`/facilitadores/${item.id}`, { ...item, status: 'Ativo' });
      if (editing?.id === item.id) clear();
      await load();
    } catch { setError('Não foi possível alterar o cadastro.'); }
    finally { setBusy(false); }
  };
  return <div className="space-y-4">
    {error && <p role="alert" className="p-3 bg-rose-50 text-rose-800 rounded-xl">{error}</p>}
    <form onSubmit={save} className="bg-white rounded-2xl p-5 space-y-3">
      <h2 className="font-bold">{editing ? 'Editar' : 'Cadastrar'} {termo}</h2>
      <label className="block text-xs font-bold">Nome<input required minLength={2} maxLength={255} value={nome} onChange={e => setNome(e.target.value)} className="block w-full border rounded-lg p-2" /></label>
      <label className="block text-xs font-bold">Especialidade<input maxLength={255} value={especialidade} onChange={e => setEspecialidade(e.target.value)} className="block w-full border rounded-lg p-2" /></label>
      <label className="block text-xs font-bold">Observações<textarea value={observacoes} onChange={e => setObservacoes(e.target.value)} className="block w-full border rounded-lg p-2" /></label>
      <button disabled={busy} className="bg-emerald-700 text-white rounded-lg p-2 font-bold text-sm">Salvar</button>
      {editing && <button type="button" onClick={clear} className="ml-3 text-sm">Cancelar</button>}
    </form>
    <div className="bg-white rounded-2xl p-5 space-y-2">
      <h2 className="font-bold">Cadastros</h2>
      {items.length === 0 && <p className="text-sm text-slate-500">Nenhum cadastro encontrado.</p>}
      {items.map(item => <div key={item.id} className="border rounded-xl p-3 flex flex-wrap justify-between gap-2">
        <div><strong>{item.nome}</strong><p className="text-sm">{item.especialidade} · {item.status}</p>{item.observacoes && <p className="text-sm">{item.observacoes}</p>}</div>
        <div className="space-x-3 text-sm"><button type="button" onClick={() => { setEditing(item); setNome(item.nome); setEspecialidade(item.especialidade || ''); setObservacoes(item.observacoes || ''); }} className="text-emerald-700">Editar</button><button type="button" disabled={busy} onClick={() => void toggle(item)}>{item.status === 'Ativo' ? 'Inativar' : 'Reativar'}</button></div>
      </div>)}
    </div>
  </div>;
}
