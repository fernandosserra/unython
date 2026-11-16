# src/modules/agendamento.py
"""
Módulo de Acolhimento, Atendimentos e Gestão de Filas.
Suporta senhas sequenciais (G-01, P-01), filas preferenciais e comuns,
chamada, baixa (atendido), marcação de ausência e reativação.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from src.utils.database_manager import DatabaseManager
from src.utils.models import Agendamento


class AgendamentoService:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def registrar_agendamento(self, agendamento: Agendamento) -> Optional[int]:
        """Registra agendamento legado direto."""
        query = """
            INSERT INTO agendamentos 
            (id_pessoa, id_facilitador, data_hora, tipo_servico, status, id_evento, compareceu, numero_senha, preferencial, ordem_chegada, observacoes) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
        """
        params = (
            agendamento.id_pessoa,
            agendamento.id_facilitador,
            agendamento.data_hora,
            agendamento.tipo_servico,
            agendamento.status or 'Aguardando',
            agendamento.id_evento,
            agendamento.compareceu or 'Pendente',
            agendamento.numero_senha,
            bool(agendamento.preferencial),
            agendamento.ordem_chegada or 1,
            agendamento.observacoes,
        )
        return self.db.execute_query(query, params, commit=True)

    def registrar_acolhimento(
        self,
        id_evento: int,
        id_pessoa: int,
        preferencial: bool = False,
        tipo_servico: str = "Passe / Consulta",
        id_facilitador: Optional[int] = None,
        observacoes: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Cadastra o acolhido no evento ativo, gerando automaticamente a senha cronológica
        (ex: P-01 para preferencial, G-01 para geral) e ordem de chegada.
        """
        # 1. Determina a ordem de chegada no evento
        query_ordem = "SELECT COALESCE(MAX(ordem_chegada), 0) + 1 FROM agendamentos WHERE id_evento = %s"
        _, res_ordem = self.db.execute_query(query_ordem, (id_evento,), fetch_one=True)
        ordem_chegada = res_ordem[0] if res_ordem else 1

        # 2. Gera a numeração da senha de acordo com a fila
        prefixo = "P" if preferencial else "G"
        query_senha = """
            SELECT COUNT(*) + 1 
            FROM agendamentos 
            WHERE id_evento = %s AND preferencial = %s
        """
        _, res_senha = self.db.execute_query(query_senha, (id_evento, bool(preferencial)), fetch_one=True)
        qtd_fila = res_senha[0] if res_senha else 1
        numero_senha = f"{prefixo}-{qtd_fila:02d}"

        # 3. Insere o atendimento
        agendamento = Agendamento(
            id_pessoa=id_pessoa,
            tipo_servico=tipo_servico or "Atendimento",
            id_evento=id_evento,
            id_facilitador=id_facilitador,
            data_hora=datetime.now(),
            status="Aguardando",
            compareceu="Pendente",
            numero_senha=numero_senha,
            preferencial=bool(preferencial),
            ordem_chegada=ordem_chegada,
            observacoes=observacoes,
        )

        novo_id = self.registrar_agendamento(agendamento)
        if not novo_id:
            return None

        return {
            "id": novo_id,
            "numero_senha": numero_senha,
            "preferencial": bool(preferencial),
            "ordem_chegada": ordem_chegada,
            "status": "Aguardando",
        }

    def pre_agendar(
        self,
        id_evento: int,
        id_pessoa: int,
        preferencial: bool = False,
        tipo_servico: str = "Passe / Consulta",
        id_facilitador: Optional[int] = None,
        observacoes: Optional[str] = None,
    ) -> Optional[int]:
        """
        Registra um agendamento com antecedência para um evento futuro.
        Não gera senha ainda - a senha será gerada no dia do trabalho quando fizer o Check-in.
        """
        agendamento = Agendamento(
            id_pessoa=id_pessoa,
            tipo_servico=tipo_servico or "Atendimento",
            id_evento=id_evento,
            id_facilitador=id_facilitador,
            data_hora=datetime.now(),
            status="PreAgendado",
            compareceu="Pendente",
            numero_senha=None,
            preferencial=bool(preferencial),
            ordem_chegada=0,
            observacoes=observacoes,
        )
        return self.registrar_agendamento(agendamento)

    def fazer_checkin(self, id_agendamento: int) -> Optional[Dict[str, Any]]:
        """
        Quando o assistido chega à casa no dia do evento:
        Gera sua senha sequencial na ordem de chegada física (P-XX ou G-XX)
        e o coloca na Fila Ativa com status 'Aguardando'.
        """
        query_busca = "SELECT id_evento, preferencial FROM agendamentos WHERE id = %s"
        columns, res = self.db.execute_query(query_busca, (id_agendamento,), fetch_one=True)
        if not res:
            return None

        id_evento = res[0]
        preferencial = bool(res[1])

        # 1. Determina a ordem de chegada entre os que já deram entrada
        query_ordem = """
            SELECT COALESCE(MAX(ordem_chegada), 0) + 1 
            FROM agendamentos 
            WHERE id_evento = %s AND numero_senha IS NOT NULL
        """
        _, res_ordem = self.db.execute_query(query_ordem, (id_evento,), fetch_one=True)
        ordem_chegada = res_ordem[0] if res_ordem else 1

        # 2. Gera a senha sequencial do dia
        prefixo = "P" if preferencial else "G"
        query_senha = """
            SELECT COUNT(*) + 1 
            FROM agendamentos 
            WHERE id_evento = %s AND preferencial = %s AND numero_senha IS NOT NULL
        """
        _, res_senha = self.db.execute_query(query_senha, (id_evento, preferencial), fetch_one=True)
        qtd = res_senha[0] if res_senha else 1
        numero_senha = f"{prefixo}-{qtd:02d}"

        # 3. Atualiza o agendamento com a senha e entrada na fila ativa
        query_up = """
            UPDATE agendamentos 
            SET status = 'Aguardando', compareceu = 'Pendente', 
                numero_senha = %s, ordem_chegada = %s, data_hora = NOW()
            WHERE id = %s
        """
        ok = self.db.execute_query(query_up, (numero_senha, ordem_chegada, id_agendamento), commit=True)
        if not ok:
            return None

        return {
            "id": id_agendamento,
            "numero_senha": numero_senha,
            "ordem_chegada": ordem_chegada,
            "preferencial": preferencial,
            "status": "Aguardando",
        }

    def listar_pre_agendados(self, id_evento: int) -> List[Dict[str, Any]]:
        """
        Lista pessoas previamente agendadas para o evento que ainda não fizeram Check-in no dia.
        """
        query = """
            SELECT 
                a.id,
                a.id_pessoa,
                p.nome AS pessoa,
                p.telefone,
                p.documento,
                a.id_evento,
                a.id_facilitador,
                u.nome AS facilitador,
                a.data_hora,
                a.tipo_servico,
                a.status,
                a.compareceu,
                a.numero_senha,
                a.preferencial,
                a.ordem_chegada,
                a.observacoes
            FROM 
                agendamentos a
            INNER JOIN 
                pessoas p ON a.id_pessoa = p.id
            LEFT JOIN 
                usuarios u ON a.id_facilitador = u.id
            WHERE 
                a.id_evento = %s 
                AND (a.status = 'PreAgendado' OR a.numero_senha IS NULL)
            ORDER BY 
                a.id ASC
        """
        try:
            columns, results = self.db.execute_query(query, (id_evento,), fetch_all=True)
            if results:
                return [dict(zip(columns, row)) for row in results]
            return []
        except Exception as e:
            print(f"[agendamento] Erro ao listar pré-agendados do evento {id_evento}: {e}")
            return []

    def listar_fila_evento(self, id_evento: int) -> List[Dict[str, Any]]:
        """
        Retorna a fila ativa do evento (apenas quem já fez Check-in ou foi acolhido no dia).
        """
        query = """
            SELECT 
                a.id,
                a.id_pessoa,
                p.nome AS pessoa,
                p.telefone,
                p.documento,
                a.id_evento,
                a.id_facilitador,
                u.nome AS facilitador,
                a.data_hora,
                a.tipo_servico,
                a.status,
                a.compareceu,
                a.numero_senha,
                a.preferencial,
                a.ordem_chegada,
                a.observacoes
            FROM 
                agendamentos a
            INNER JOIN 
                pessoas p ON a.id_pessoa = p.id
            LEFT JOIN 
                usuarios u ON a.id_facilitador = u.id
            WHERE 
                a.id_evento = %s
                AND a.numero_senha IS NOT NULL
                AND a.status != 'PreAgendado'
            ORDER BY 
                a.ordem_chegada ASC, a.data_hora ASC
        """
        try:
            columns, results = self.db.execute_query(query, (id_evento,), fetch_all=True)
            if results:
                return [dict(zip(columns, row)) for row in results]
            return []
        except Exception as e:
            print(f"[agendamento] Erro ao listar fila do evento {id_evento}: {e}")
            return []

    def atualizar_status(self, id_agendamento: int, novo_status: str) -> bool:
        """
        Atualiza o status operacional do atendimento ('Aguardando', 'Chamado', 'Atendido', 'Ausente').
        Sincroniza automaticamente a coluna compareceu.
        """
        compareceu = "Pendente"
        if novo_status == "Atendido":
            compareceu = "Sim"
        elif novo_status == "Ausente":
            compareceu = "Nao"

        query = """
            UPDATE agendamentos 
            SET status = %s, compareceu = %s 
            WHERE id = %s
        """
        params = (novo_status, compareceu, id_agendamento)
        return bool(self.db.execute_query(query, params, commit=True))

    def reativar_ausente(self, id_agendamento: int) -> bool:
        """
        Remove o assistido da lista de ausentes e o recoloca na fila com status 'Aguardando',
        caso ele não tenha ouvido a chamada de sua senha.
        """
        query = """
            UPDATE agendamentos 
            SET status = 'Aguardando', compareceu = 'Pendente' 
            WHERE id = %s
        """
        return bool(self.db.execute_query(query, (id_agendamento,), commit=True))

    def confirmar_comparecimento(self, id_agendamento: int, presenca: str) -> bool:
        """Compatibilidade com o método legado."""
        status = "Atendido" if presenca == "Sim" else ("Ausente" if presenca == "Nao" else "Aguardando")
        return self.atualizar_status(id_agendamento, status)
