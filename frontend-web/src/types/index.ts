export interface Usuario {
  id: number;
  nome: string;
  email: string;
  funcao?: string;
  role: 'Administrador' | 'Operador' | 'Recepcionista' | 'Vendedor';
  status: 'Ativo' | 'Inativo';
  require_password_change?: boolean;
  permissoes: string[] | null;
}

export interface Categoria {
  id: number;
  nome: string;
  descricao?: string;
  status: string;
}

export interface Item {
  id: number;
  nome: string;
  valor_compra: number | null;
  valor_venda: number;
  id_categoria?: number;
  status: string;
  estoque_minimo: number;
}

export interface Facilitador {
  id: number;
  nome: string;
  especialidade?: string | null;
  observacoes?: string | null;
  status: 'Ativo' | 'Inativo';
}

export interface Atividade {
  id: number;
  nome: string;
  descricao?: string | null;
  status: 'Ativo' | 'Inativo';
}

export interface Evento {
  id: number;
  nome: string;
  data_evento: string;
  tipo: string;
  status: 'Aberto' | 'Fechado' | 'Agendado' | string;
}

export interface Caixa {
  id: number;
  nome: string;
  descricao?: string;
  status: string;
}

export interface MovimentoCaixa {
  id: number;
  id_caixa: number;
  id_usuario_abertura: number;
  valor_abertura: number;
  status: 'Aberto' | 'Fechado';
  data_abertura: string;
  data_fechamento?: string;
  id_evento?: number;
}

export interface Pessoa {
  id: number;
  nome: string;
  telefone?: string;
  documento?: string;
  preferencial: boolean;
  observacoes?: string;
  data_cadastro: string;
}

export interface Agendamento {
  id: number;
  id_pessoa: number;
  pessoa?: string;
  telefone?: string;
  documento?: string;
  id_evento: number;
  id_facilitador?: number;
  facilitador?: string;
  id_atividade?: number | null;
  atividade?: string | null;
  data_hora: string;
  tipo_servico: string;
  status: 'Aguardando' | 'Chamado' | 'Atendido' | 'Ausente' | string;
  compareceu: 'Pendente' | 'Sim' | 'Nao';
  numero_senha?: string;
  preferencial: boolean;
  ordem_chegada: number;
  observacoes?: string;
}

export interface OrganizacaoConfig {
  nome_organizacao: string;
  tipo_organizacao: string;
  subtitulo?: string;
  registro?: string;
  cidade_uf?: string;
  telefone_contato?: string;
  termo_assistido: string;
  termo_assistido_plural: string;
  termo_atendente: string;
  termo_atendente_plural: string;
  termo_servico: string;
  termo_atividade: string;
  termo_atividade_plural: string;
  alias_evento: string;
  alias_evento_plural: string;
  habilitar_pdv: boolean;
  habilitar_atendimentos: boolean;
  habilitar_doacoes: boolean;
  exigir_documento_atendimento: boolean;
}

export interface CartItem {
  id_item: number;
  nome: string;
  quantidade: number;
  valor_unitario: number;
}
