import { useState } from 'react';
import type { FormEvent } from 'react';
import { useOrgStore } from '../store/useOrgStore';
import type { OrganizacaoConfig } from '../types';

const presets: { nome: string; valores?: OrganizacaoConfig }[] = [
  {
    nome: 'Terreiro',
    valores: {
      nome_organizacao: 'Terreiro',
      tipo_organizacao: 'Terreiro de Umbanda / Centro Espírita',
      termo_assistido: 'Consulente', termo_assistido_plural: 'Consulentes',
      termo_atendente: 'Médium / Cambone', termo_servico: 'Passe / Consulta',
      termo_atividade: 'Entidade', alias_evento: 'Gira',
    },
  },
  {
    nome: 'Igreja / Comunidade',
    valores: {
      nome_organizacao: 'Igreja / Comunidade',
      tipo_organizacao: 'Igreja / Comunidade',
      termo_assistido: 'Fiel', termo_assistido_plural: 'Fiéis',
      termo_atendente: 'Ministro', termo_servico: 'Aconselhamento',
      termo_atividade: 'Serviço', alias_evento: 'Encontro',
    },
  },
  {
    nome: 'Albergue / Assistência Social',
    valores: {
      nome_organizacao: 'Albergue / Assistência Social',
      tipo_organizacao: 'Albergue / Assistência Social',
      termo_assistido: 'Acolhido', termo_assistido_plural: 'Acolhidos',
      termo_atendente: 'Assistente Social', termo_servico: 'Acolhimento',
      termo_atividade: 'Serviço', alias_evento: 'Evento',
    },
  },
  { nome: 'Personalizado' },
];

const fields: { key: keyof OrganizacaoConfig; label: string; maxLength: number }[] = [
  { key: 'nome_organizacao', label: 'Nome da organização', maxLength: 150 },
  { key: 'tipo_organizacao', label: 'Tipo da organização', maxLength: 100 },
  { key: 'termo_assistido', label: 'Pessoa atendida (singular)', maxLength: 50 },
  { key: 'termo_assistido_plural', label: 'Pessoas atendidas (plural)', maxLength: 50 },
  { key: 'termo_atendente', label: 'Atendente', maxLength: 50 },
  { key: 'termo_servico', label: 'Serviço', maxLength: 50 },
  { key: 'termo_atividade', label: 'Atividade', maxLength: 50 },
  { key: 'alias_evento', label: 'Evento', maxLength: 50 },
];

export function OrganizacaoConfigView() {
  const config = useOrgStore((state) => state.config);
  const saveConfig = useOrgStore((state) => state.saveConfig);
  const [draft, setDraft] = useState<OrganizacaoConfig>(() => ({ ...config }));
  const [selectedPreset, setSelectedPreset] = useState(() =>
    presets.find((preset) => preset.valores?.tipo_organizacao === config.tipo_organizacao)?.nome ?? 'Personalizado'
  );
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<{ error: boolean; text: string } | null>(null);

  const save = async (event: FormEvent) => {
    event.preventDefault();
    setBusy(true);
    setMessage(null);
    try {
      await saveConfig(draft);
      setMessage({ error: false, text: 'Configuração salva com sucesso.' });
    } catch (error) {
      setMessage({ error: true, text: error instanceof Error ? error.message : 'Erro ao salvar a configuração.' });
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="bg-white p-4 sm:p-5 rounded-2xl border border-slate-200/80 shadow-xs space-y-4">
      <div>
        <h2 className="font-black text-slate-900 text-lg">Configuração da organização</h2>
        <p className="text-sm text-slate-500 mt-1">Escolha um modelo ou personalize os termos. As alterações só são aplicadas ao salvar.</p>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
        {presets.map((preset) => (
          <button key={preset.nome} type="button" disabled={busy}
            onClick={() => {
              if (preset.valores) setDraft({ ...preset.valores });
              else setDraft((current) => ({ ...current, tipo_organizacao: 'Personalizado' }));
              setSelectedPreset(preset.nome);
              setMessage(null);
            }}
            aria-pressed={selectedPreset === preset.nome}
            className={`px-3 py-2.5 rounded-xl border text-left font-bold text-sm disabled:opacity-50 ${selectedPreset === preset.nome ? 'border-emerald-500 bg-emerald-50 text-emerald-900' : 'border-slate-200 hover:bg-slate-50'}`}>
            {preset.nome}
          </button>
        ))}
      </div>
      <form onSubmit={save} className="space-y-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {fields.map(({ key, label, maxLength }) => (
            <label key={key} className="block text-xs font-bold text-slate-700 uppercase">
              {label}
              <input required minLength={2} maxLength={maxLength} value={draft[key]} disabled={busy}
                onChange={(event) => {
                  setDraft((current) => ({ ...current, [key]: event.target.value }));
                  if (key === 'tipo_organizacao') setSelectedPreset('Personalizado');
                  setMessage(null);
                }}
                className="block mt-1 w-full h-10 px-3 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium focus:bg-white" />
            </label>
          ))}
        </div>
        {message && <p role={message.error ? 'alert' : 'status'} className={message.error ? 'text-sm text-rose-700' : 'text-sm text-emerald-700'}>{message.text}</p>}
        <button type="submit" disabled={busy} className="h-11 px-6 bg-slate-900 text-white font-bold text-sm rounded-xl disabled:opacity-50">
          {busy ? 'Salvando...' : 'Salvar'}
        </button>
      </form>
    </div>
  );
}
