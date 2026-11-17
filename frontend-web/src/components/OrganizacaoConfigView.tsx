import { useState } from 'react';
import type { FormEvent } from 'react';
import { useOrgStore } from '../store/useOrgStore';
import type { OrganizacaoConfig } from '../types';

type PresetValues = Pick<OrganizacaoConfig,
  'tipo_organizacao' | 'termo_assistido' | 'termo_assistido_plural' |
  'termo_atendente' | 'termo_atendente_plural' | 'termo_atividade' |
  'termo_atividade_plural' | 'alias_evento' | 'alias_evento_plural' |
  'habilitar_pdv' | 'habilitar_atendimentos' | 'habilitar_doacoes' |
  'exigir_documento_atendimento'>;

const presets: { nome: string; valores?: PresetValues }[] = [
  {
    nome: 'Terreiro',
    valores: {
      tipo_organizacao: 'Terreiro de Umbanda / Centro Espírita',
      termo_assistido: 'Consulente', termo_assistido_plural: 'Consulentes',
      termo_atendente: 'Médium / Cambone', termo_atendente_plural: 'Médiuns / Cambones',
      termo_atividade: 'Entidade', termo_atividade_plural: 'Entidades',
      alias_evento: 'Gira', alias_evento_plural: 'Giras',
      habilitar_pdv: true, habilitar_atendimentos: true, habilitar_doacoes: true,
      exigir_documento_atendimento: false,
    },
  },
  {
    nome: 'Igreja / Comunidade',
    valores: {
      tipo_organizacao: 'Igreja / Comunidade',
      termo_assistido: 'Fiel', termo_assistido_plural: 'Fiéis',
      termo_atendente: 'Ministro', termo_atendente_plural: 'Ministros',
      termo_atividade: 'Serviço', termo_atividade_plural: 'Serviços',
      alias_evento: 'Encontro', alias_evento_plural: 'Encontros',
      habilitar_pdv: true, habilitar_atendimentos: true, habilitar_doacoes: true,
      exigir_documento_atendimento: false,
    },
  },
  {
    nome: 'Albergue / Assistência Social',
    valores: {
      tipo_organizacao: 'Albergue / Assistência Social',
      termo_assistido: 'Acolhido', termo_assistido_plural: 'Acolhidos',
      termo_atendente: 'Assistente Social', termo_atendente_plural: 'Assistentes Sociais',
      termo_atividade: 'Serviço', termo_atividade_plural: 'Serviços',
      alias_evento: 'Evento', alias_evento_plural: 'Eventos',
      habilitar_pdv: true, habilitar_atendimentos: true, habilitar_doacoes: true,
      exigir_documento_atendimento: true,
    },
  },
  {
    nome: 'Associação / Coletivo',
    valores: {
      tipo_organizacao: 'Associação / Coletivo',
      termo_assistido: 'Participante', termo_assistido_plural: 'Participantes',
      termo_atendente: 'Facilitador', termo_atendente_plural: 'Facilitadores',
      termo_atividade: 'Atividade', termo_atividade_plural: 'Atividades',
      alias_evento: 'Evento', alias_evento_plural: 'Eventos',
      habilitar_pdv: true, habilitar_atendimentos: true, habilitar_doacoes: true,
      exigir_documento_atendimento: false,
    },
  },
  { nome: 'Personalizado' },
];

type TextKey = Exclude<keyof OrganizacaoConfig,
  'habilitar_pdv' | 'habilitar_atendimentos' | 'habilitar_doacoes' | 'exigir_documento_atendimento'>;
type TextField = { key: TextKey; label: string; maxLength?: number; optional?: boolean };

const identityFields: TextField[] = [
  { key: 'nome_organizacao', label: 'Nome da organização', maxLength: 150 },
  { key: 'tipo_organizacao', label: 'Tipo da organização', maxLength: 100 },
  { key: 'subtitulo', label: 'Subtítulo / Slogan', optional: true },
  { key: 'registro', label: 'CNPJ / Registro', optional: true },
  { key: 'cidade_uf', label: 'Cidade / UF', optional: true },
  { key: 'telefone_contato', label: 'Telefone de contato', optional: true },
];

const vocabularyFields: TextField[] = [
  { key: 'termo_assistido', label: 'Pessoa atendida (singular)', maxLength: 50 },
  { key: 'termo_assistido_plural', label: 'Pessoas atendidas (plural)', maxLength: 50 },
  { key: 'termo_atendente', label: 'Atendente (singular)', maxLength: 50 },
  { key: 'termo_atendente_plural', label: 'Atendentes (plural)', maxLength: 50 },
  { key: 'termo_atividade', label: 'Atividade (singular)', maxLength: 50 },
  { key: 'termo_atividade_plural', label: 'Atividades (plural)', maxLength: 50 },
  { key: 'alias_evento', label: 'Evento (singular)', maxLength: 50 },
  { key: 'alias_evento_plural', label: 'Eventos (plural)', maxLength: 50 },
  { key: 'termo_servico', label: 'Serviço', maxLength: 50 },
];

const rules: { key: 'habilitar_pdv' | 'habilitar_atendimentos' | 'habilitar_doacoes' | 'exigir_documento_atendimento'; label: string }[] = [
  { key: 'habilitar_pdv', label: 'Habilitar PDV' },
  { key: 'habilitar_atendimentos', label: 'Habilitar atendimentos' },
  { key: 'habilitar_doacoes', label: 'Habilitar doações' },
  { key: 'exigir_documento_atendimento', label: 'Exigir documento no atendimento' },
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

  const renderFields = (fields: TextField[]) => (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
      {fields.map(({ key, label, maxLength, optional }) => (
        <label key={key} className="block text-xs font-bold text-slate-700 uppercase">
          {label}{optional && ' (opcional)'}
          <input required={!optional} minLength={optional ? undefined : 2} maxLength={maxLength}
            value={draft[key] ?? ''} disabled={busy}
            onChange={(event) => {
              setDraft((current) => ({ ...current, [key]: event.target.value }));
              if (!optional && key !== 'nome_organizacao') setSelectedPreset('Personalizado');
              setMessage(null);
            }}
            className="block mt-1 w-full h-10 px-3 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium focus:bg-white" />
        </label>
      ))}
    </div>
  );

  return (
    <div className="bg-white p-4 sm:p-5 rounded-2xl border border-slate-200/80 shadow-xs space-y-4">
      <div>
        <h2 className="font-black text-slate-900 text-lg">Configuração da organização</h2>
        <p className="text-sm text-slate-500 mt-1">Escolha um modelo ou personalize os termos. As alterações só são aplicadas ao salvar.</p>
      </div>
      <form onSubmit={save} className="space-y-5">
        <section className="space-y-3">
          <h3 className="font-bold text-slate-900">Modelo & Identidade Institucional</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2" aria-label="Modelos de organização">
            {presets.map((preset) => (
              <button key={preset.nome} type="button" disabled={busy}
                onClick={() => {
                  setDraft((current) => ({ ...current, ...(preset.valores ?? { tipo_organizacao: 'Personalizado' }) }));
                  setSelectedPreset(preset.nome);
                  setMessage(null);
                }}
                aria-pressed={selectedPreset === preset.nome}
                className={`px-3 py-2.5 rounded-xl border text-left font-bold text-sm disabled:opacity-50 ${selectedPreset === preset.nome ? 'border-emerald-500 bg-emerald-50 text-emerald-900' : 'border-slate-200 hover:bg-slate-50'}`}>
                {preset.nome}
              </button>
            ))}
          </div>
          {renderFields(identityFields)}
        </section>
        <section className="space-y-3">
          <h3 className="font-bold text-slate-900">Vocabulário & Plurais</h3>
          {renderFields(vocabularyFields)}
          <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-700" aria-label="Pré-visualização em tempo real">
            <p className="font-bold text-slate-900">Pré-visualização em tempo real</p>
            <p className="mt-2 font-bold">{draft.termo_assistido_plural} · {draft.termo_atendente_plural} · {draft.termo_atividade_plural} · {draft.alias_evento_plural}</p>
            <div className="mt-3 flex flex-wrap gap-2">
              {[draft.termo_assistido, draft.termo_atendente, draft.termo_atividade, draft.alias_evento].map((term, index) => (
                <span key={index} className="rounded-lg bg-emerald-700 px-3 py-2 text-xs font-bold text-white">+ {term}</span>
              ))}
            </div>
          </div>
        </section>
        <section className="space-y-3">
          <h3 className="font-bold text-slate-900">Regras Operacionais da Casa</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {rules.map(({ key, label }) => (
              <label key={key} className="flex items-center gap-3 text-sm font-bold text-slate-700">
                <input type="checkbox" checked={draft[key]} disabled={busy}
                  onChange={(event) => {
                    setDraft((current) => ({ ...current, [key]: event.target.checked }));
                    setSelectedPreset('Personalizado');
                    setMessage(null);
                  }}
                  className="h-4 w-4 accent-emerald-600" />
                {label}
              </label>
            ))}
          </div>
        </section>
        {message && <p role={message.error ? 'alert' : 'status'} className={message.error ? 'text-sm text-rose-700' : 'text-sm text-emerald-700'}>{message.text}</p>}
        <button type="submit" disabled={busy} className="h-11 px-6 bg-slate-900 text-white font-bold text-sm rounded-xl disabled:opacity-50">
          {busy ? 'Salvando...' : 'Salvar'}
        </button>
      </form>
    </div>
  );
}
