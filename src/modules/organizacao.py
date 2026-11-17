# src/modules/organizacao.py
"""
Módulo para gerenciamento de configurações da organização e vocabulário customizado
(Ex: Terreiro de Umbanda, Igreja Católica, Evangélica, Albergue, Clínica Social).
"""

from typing import Dict, Any, Optional
from src.utils.database_manager import DatabaseManager
from src.utils.models import OrganizacaoConfig


class OrganizacaoService:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def obter_configuracoes(self) -> OrganizacaoConfig:
        """Obtém as configurações ativas da organização."""
        query = """
            SELECT id, nome_organizacao, tipo_organizacao, termo_assistido, termo_assistido_plural,
                   termo_atendente, termo_servico, termo_atividade, alias_evento,
                   subtitulo, registro, cidade_uf, telefone_contato, termo_atendente_plural,
                   termo_atividade_plural, alias_evento_plural, habilitar_pdv,
                   habilitar_atendimentos, habilitar_doacoes, exigir_documento_atendimento
            FROM organizacao_config
            WHERE id = 1
            LIMIT 1;
        """
        columns, results = self.db.execute_query(query, fetch_one=True)
        if results:
            data = dict(zip(columns, results))
            return OrganizacaoConfig(**data)

        # Retorna padrão caso não encontre
        return OrganizacaoConfig()

    def salvar_configuracoes(
        self,
        nome_organizacao: str,
        tipo_organizacao: str,
        termo_assistido: str,
        termo_assistido_plural: str,
        termo_atendente: str,
        termo_servico: str,
        termo_atividade: str = "Entidade / Serviço",
        alias_evento: str = "Evento",
        subtitulo: Optional[str] = None,
        registro: Optional[str] = None,
        cidade_uf: Optional[str] = None,
        telefone_contato: Optional[str] = None,
        termo_atendente_plural: str = "Médiuns / Cambones",
        termo_atividade_plural: str = "Entidades / Serviços",
        alias_evento_plural: str = "Eventos",
        habilitar_pdv: bool = True,
        habilitar_atendimentos: bool = True,
        habilitar_doacoes: bool = True,
        exigir_documento_atendimento: bool = False,
    ) -> bool:
        """Atualiza ou insere as configurações da organização no registro principal (id=1)."""
        query = """
            INSERT INTO organizacao_config 
                (id, nome_organizacao, tipo_organizacao, termo_assistido, termo_assistido_plural,
                 termo_atendente, termo_servico, termo_atividade, alias_evento, subtitulo,
                 registro, cidade_uf, telefone_contato, termo_atendente_plural,
                 termo_atividade_plural, alias_evento_plural, habilitar_pdv,
                 habilitar_atendimentos, habilitar_doacoes, exigir_documento_atendimento)
            VALUES (1, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                nome_organizacao = EXCLUDED.nome_organizacao,
                tipo_organizacao = EXCLUDED.tipo_organizacao,
                termo_assistido = EXCLUDED.termo_assistido,
                termo_assistido_plural = EXCLUDED.termo_assistido_plural,
                termo_atendente = EXCLUDED.termo_atendente,
                termo_servico = EXCLUDED.termo_servico,
                termo_atividade = EXCLUDED.termo_atividade,
                alias_evento = EXCLUDED.alias_evento,
                subtitulo = EXCLUDED.subtitulo,
                registro = EXCLUDED.registro,
                cidade_uf = EXCLUDED.cidade_uf,
                telefone_contato = EXCLUDED.telefone_contato,
                termo_atendente_plural = EXCLUDED.termo_atendente_plural,
                termo_atividade_plural = EXCLUDED.termo_atividade_plural,
                alias_evento_plural = EXCLUDED.alias_evento_plural,
                habilitar_pdv = EXCLUDED.habilitar_pdv,
                habilitar_atendimentos = EXCLUDED.habilitar_atendimentos,
                habilitar_doacoes = EXCLUDED.habilitar_doacoes,
                exigir_documento_atendimento = EXCLUDED.exigir_documento_atendimento;
        """
        params = (
            nome_organizacao,
            tipo_organizacao,
            termo_assistido,
            termo_assistido_plural,
            termo_atendente,
            termo_servico,
            termo_atividade,
            alias_evento,
            subtitulo,
            registro,
            cidade_uf,
            telefone_contato,
            termo_atendente_plural,
            termo_atividade_plural,
            alias_evento_plural,
            habilitar_pdv,
            habilitar_atendimentos,
            habilitar_doacoes,
            exigir_documento_atendimento,
        )
        return bool(self.db.execute_query(query, params, commit=True))
