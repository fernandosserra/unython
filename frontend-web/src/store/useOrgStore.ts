import { create } from 'zustand';
import { apiClient } from '../api/client';
import type { OrganizacaoConfig } from '../types';

export const defaultOrgConfig: OrganizacaoConfig = {
  nome_organizacao: 'Terreiro Caboclo Pena Branca',
  tipo_organizacao: 'Terreiro de Umbanda / Centro Espírita',
  subtitulo: '',
  registro: '',
  cidade_uf: '',
  telefone_contato: '',
  termo_assistido: 'Consulente',
  termo_assistido_plural: 'Consulentes',
  termo_atendente: 'Médium / Cambone',
  termo_atendente_plural: 'Médiuns / Cambones',
  termo_servico: 'Passe / Consulta',
  termo_atividade: 'Entidade / Serviço',
  termo_atividade_plural: 'Entidades / Serviços',
  alias_evento: 'Evento',
  alias_evento_plural: 'Eventos',
  habilitar_pdv: true,
  habilitar_atendimentos: true,
  habilitar_doacoes: true,
  exigir_documento_atendimento: false,
};

const optionalFields = ['subtitulo', 'registro', 'cidade_uf', 'telefone_contato'] as const;
const configFields = Object.keys(defaultOrgConfig) as (keyof OrganizacaoConfig)[];

function normalizeConfig(data: Partial<OrganizacaoConfig>): OrganizacaoConfig {
  const config = { ...defaultOrgConfig, ...data };
  for (const field of optionalFields) {
    config[field] = data[field] ?? '';
  }
  return config;
}

interface OrgState {
  config: OrganizacaoConfig;
  loadConfig: () => Promise<void>;
  saveConfig: (config: OrganizacaoConfig) => Promise<void>;
}

export const useOrgStore = create<OrgState>((set) => ({
  config: { ...defaultOrgConfig },
  loadConfig: async () => {
    try {
      const { data } = await apiClient.get<Partial<OrganizacaoConfig>>('/organizacao/config');
      if (!data || typeof data !== 'object') throw new Error('Resposta inválida');
      set({ config: normalizeConfig(data) });
    } catch (error) {
      throw new Error('Não foi possível carregar a configuração da organização.', { cause: error });
    }
  },
  saveConfig: async (config) => {
    let data: { config?: Partial<OrganizacaoConfig> };
    try {
      ({ data } = await apiClient.put('/organizacao/config', config));
    } catch (error) {
      throw new Error('Não foi possível salvar a configuração da organização.', { cause: error });
    }
    const confirmed = data?.config;
    const unconfirmed = configFields.filter((field) => {
      if (!confirmed || !Object.hasOwn(confirmed, field)) return true;
      if (optionalFields.some((optionalField) => optionalField === field)) {
        return (confirmed[field] ?? '') !== (config[field] ?? '');
      }
      return confirmed[field] !== config[field];
    });
    if (unconfirmed.length) {
      throw new Error(`A configuração foi enviada, mas o servidor não confirmou todos os campos (${unconfirmed.join(', ')}). Recarregue antes de tentar novamente.`);
    }
    set({ config: normalizeConfig(confirmed!) });
  },
}));
