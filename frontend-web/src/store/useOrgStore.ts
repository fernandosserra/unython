import { create } from 'zustand';
import { apiClient } from '../api/client';
import type { OrganizacaoConfig } from '../types';

export const defaultOrgConfig: OrganizacaoConfig = {
  nome_organizacao: 'Terreiro Caboclo Pena Branca',
  tipo_organizacao: 'Terreiro de Umbanda / Centro Espírita',
  termo_assistido: 'Consulente',
  termo_assistido_plural: 'Consulentes',
  termo_atendente: 'Médium / Cambone',
  termo_servico: 'Passe / Consulta',
  termo_atividade: 'Entidade / Serviço',
  alias_evento: 'Evento',
};

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
      set({ config: { ...defaultOrgConfig, ...data } });
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
    if (!data?.config || data.config.alias_evento !== config.alias_evento) {
      throw new Error('A configuração foi enviada, mas o servidor não confirmou o termo de evento. Recarregue antes de tentar novamente.');
    }
    set({ config: { ...defaultOrgConfig, ...data.config } });
  },
}));
