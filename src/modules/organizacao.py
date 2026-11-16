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
            SELECT id, nome_organizacao, tipo_organizacao, termo_assistido, termo_assistido_plural, termo_atendente, termo_servico
            FROM organizacao_config
            WHERE id = 1
            LIMIT 1;
        """
        try:
            columns, results = self.db.execute_query(query, fetch_one=True)
            if results:
                data = dict(zip(columns, results))
                return OrganizacaoConfig(**data)
        except Exception as e:
            print(f"[organizacao] Erro ao obter configurações: {e}")

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
    ) -> bool:
        """Atualiza ou insere as configurações da organização no registro principal (id=1)."""
        query = """
            INSERT INTO organizacao_config 
                (id, nome_organizacao, tipo_organizacao, termo_assistido, termo_assistido_plural, termo_atendente, termo_servico)
            VALUES (1, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                nome_organizacao = EXCLUDED.nome_organizacao,
                tipo_organizacao = EXCLUDED.tipo_organizacao,
                termo_assistido = EXCLUDED.termo_assistido,
                termo_assistido_plural = EXCLUDED.termo_assistido_plural,
                termo_atendente = EXCLUDED.termo_atendente,
                termo_servico = EXCLUDED.termo_servico;
        """
        params = (
            nome_organizacao,
            tipo_organizacao,
            termo_assistido,
            termo_assistido_plural,
            termo_atendente,
            termo_servico,
        )
        return bool(self.db.execute_query(query, params, commit=True))
