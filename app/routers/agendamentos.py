# app/routers/agendamentos.py

from fastapi import APIRouter, Depends, status, HTTPException
from typing import List
import sys
import os
from datetime import datetime

# Adiciona o diretório 'src' para imports modulares
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

# Importa Services e Schemas
from src.utils.dependencies import DBDependency
from src.modules.agendamento import AgendamentoService
from src.modules.relatorio import RelatorioService
from src.utils.schemas import AgendamentoUpdateStatus

# Cria o Router
router = APIRouter(
    prefix="/agendamentos",
    tags=["Logística e Atendimento (Agendamentos)"]
)

# ------------------------------------------------------------------
# ENDPOINT: LISTAR AGENDAMENTOS PENDENTES
# ------------------------------------------------------------------

@router.get("/pendentes", status_code=status.HTTP_200_OK)
def listar_agendamentos_pendentes_detalhado(db: DBDependency):
    """
    Lista todos os agendamentos pendentes com detalhes de NOME (usando lógica de JOIN do RelatorioService).
    """
    relatorio_service = RelatorioService(db)
    
    # Chama a função de relatório que já faz o JOIN com Pessoa e Usuario
    agendamentos_detalhado = relatorio_service.gerar_detalhe_agendamentos_pendentes()
    
    if not agendamentos_detalhado:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nenhum agendamento pendente encontrado.")
        
    # Os dados já vêm como List[Dict] formatada para o JSON
    return agendamentos_detalhado


@router.patch("/{id_agendamento}/confirmar", status_code=status.HTTP_200_OK)
def confirmar_presenca(id_agendamento: int, status_update: AgendamentoUpdateStatus, db: DBDependency):
    """
    Endpoint para o recepcionista confirmar a presença ('Sim' ou 'Não') do consulente.
    """
    agendamento_service = AgendamentoService(db)
    
    # Chama o service para atualizar a coluna
    sucesso = agendamento_service.confirmar_comparecimento(
        id_agendamento, 
        status_update.compareceu # Pydantic garante que seja 'Sim' ou 'Não'
    )
    
    if not sucesso:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Falha ao atualizar presença. Verifique o ID do agendamento."
        )
        
    return {
        "message": "Status de comparecimento atualizado com sucesso.", 
        "id_agendamento": id_agendamento, 
        "novo_status": status_update.compareceu
    }