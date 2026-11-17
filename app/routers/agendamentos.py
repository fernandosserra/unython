# app/routers/agendamentos.py

from fastapi import APIRouter, Depends, status, HTTPException
from typing import List, Optional
from datetime import datetime

from src.utils.dependencies import DBDependency
from src.modules.agendamento import AgendamentoService
from src.modules.pessoa import PessoaService
from src.modules.relatorio import RelatorioService
from src.modules.organizacao import OrganizacaoService
from src.utils.models import Pessoa
from src.utils.schemas import (
    AgendamentoUpdateStatus,
    AgendamentoStatusUpdateRequest,
    AcolhimentoCreateRequest,
    AgendamentoFilaItem,
)

router = APIRouter(
    prefix="/agendamentos",
    tags=["Logística, Acolhimento e Atendimentos"]
)


def validar_facilitador(db: DBDependency, facilitador_id: Optional[int]):
    if facilitador_id is not None:
        _, row = db.execute_query(
            "SELECT id FROM facilitadores WHERE id = %s AND status = 'Ativo'",
            (facilitador_id,), fetch_one=True,
        )
        if not row:
            raise HTTPException(status_code=400, detail="Atendente não encontrado ou inativo.")


def validar_atividade(db: DBDependency, atividade_id: Optional[int]):
    if atividade_id is not None:
        _, row = db.execute_query(
            "SELECT nome FROM atividades_atendimento WHERE id = %s AND status = 'Ativo'",
            (atividade_id,), fetch_one=True,
        )
        if not row:
            raise HTTPException(status_code=400, detail="Cadastro não encontrado ou inativo.")
        return row[0]
    return None


@router.get("/fila/{id_evento}", response_model=List[AgendamentoFilaItem])
def listar_fila_do_evento(id_evento: int, db: DBDependency):
    """
    Retorna a fila de acolhimento do evento ativo em ordem cronológica de chegada,
    com distinção de fila Geral/Comum e Preferencial.
    """
    service = AgendamentoService(db)
    fila = service.listar_fila_evento(id_evento)
    return [AgendamentoFilaItem(**item) for item in fila]


@router.get("/pre-agendados/{id_evento}", response_model=List[AgendamentoFilaItem])
def listar_pre_agendados_do_evento(id_evento: int, db: DBDependency):
    """
    Retorna a lista de pessoas pré-agendadas com antecedência para o evento,
    que ainda não fizeram o Check-in no dia.
    """
    service = AgendamentoService(db)
    lista = service.listar_pre_agendados(id_evento)
    return [AgendamentoFilaItem(**item) for item in lista]


@router.post("/pre-agendar", status_code=status.HTTP_201_CREATED)
def agendar_com_antecedencia(payload: AcolhimentoCreateRequest, db: DBDependency):
    """
    Registra um agendamento com antecedência para um evento futuro.
    A senha de atendimento será emitida no dia do evento quando o consulente fizer o Check-in.
    """
    validar_facilitador(db, payload.id_facilitador)
    atividade = validar_atividade(db, payload.id_atividade)
    tipo_servico = payload.tipo_servico or atividade or OrganizacaoService(db).obter_configuracoes().termo_servico
    pessoa_service = PessoaService(db)
    agendamento_service = AgendamentoService(db)

    id_pessoa = payload.id_pessoa
    if not id_pessoa:
        if not payload.nome:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Informe uma pessoa existente ou o nome para novo cadastro.",
            )
        nova_pessoa = Pessoa(
            nome=payload.nome,
            telefone=payload.telefone,
            documento=payload.documento,
            preferencial=payload.preferencial,
            observacoes=payload.observacoes,
        )
        id_pessoa = pessoa_service.registrar_pessoa(nova_pessoa)
        if not id_pessoa:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Falha ao cadastrar pessoa.",
            )

    agendamento_id = agendamento_service.pre_agendar(
        id_evento=payload.id_evento,
        id_pessoa=id_pessoa,
        preferencial=payload.preferencial,
        tipo_servico=tipo_servico,
        id_facilitador=payload.id_facilitador,
        id_atividade=payload.id_atividade,
        observacoes=payload.observacoes,
    )

    if not agendamento_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não foi possível realizar o agendamento prévio.",
        )

    return {
        "message": "Agendamento com antecedência realizado com sucesso!",
        "id": agendamento_id,
        "id_evento": payload.id_evento,
        "id_pessoa": id_pessoa,
        "status": "PreAgendado",
    }


@router.post("/{id_agendamento}/checkin", status_code=status.HTTP_200_OK)
def realizar_checkin(id_agendamento: int, db: DBDependency):
    """
    Realiza o Check-in de uma pessoa pré-agendada no dia do evento:
    Gera a senha sequencial da noite e insere na fila ativa de chamada.
    """
    service = AgendamentoService(db)
    resultado = service.fazer_checkin(id_agendamento)
    if not resultado:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não foi possível realizar o check-in do agendamento.",
        )
    return {
        "message": "Check-in realizado com sucesso! Senha emitida.",
        **resultado,
    }


@router.post("/acolher", status_code=status.HTTP_201_CREATED)
def acolher_pessoa_no_evento(payload: AcolhimentoCreateRequest, db: DBDependency):
    """
    Registra um acolhido na fila do evento.
    Se for fornecido id_pessoa, utiliza a pessoa existente.
    Se for fornecido nome, cadastra automaticamente a nova pessoa e a coloca na fila.
    Gera senha sequencial cronológica (P-01 para preferencial, G-01 para comum).
    """
    validar_facilitador(db, payload.id_facilitador)
    atividade = validar_atividade(db, payload.id_atividade)
    tipo_servico = payload.tipo_servico or atividade or OrganizacaoService(db).obter_configuracoes().termo_servico
    pessoa_service = PessoaService(db)
    agendamento_service = AgendamentoService(db)

    id_pessoa = payload.id_pessoa

    # Se não passou id_pessoa mas passou nome, cria a pessoa primeiro
    if not id_pessoa:
        if not payload.nome:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Informe uma pessoa existente ou o nome para novo cadastro.",
            )
        nova_pessoa = Pessoa(
            nome=payload.nome,
            telefone=payload.telefone,
            documento=payload.documento,
            preferencial=payload.preferencial,
            observacoes=payload.observacoes,
        )
        id_pessoa = pessoa_service.registrar_pessoa(nova_pessoa)
        if not id_pessoa:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Falha ao cadastrar pessoa.",
            )

    # Registra o acolhimento na fila do evento com senha gerada
    resultado = agendamento_service.registrar_acolhimento(
        id_evento=payload.id_evento,
        id_pessoa=id_pessoa,
        preferencial=payload.preferencial,
        tipo_servico=tipo_servico,
        id_facilitador=payload.id_facilitador,
        id_atividade=payload.id_atividade,
        observacoes=payload.observacoes,
    )

    if not resultado:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não foi possível incluir a pessoa na fila do evento.",
        )

    return {
        "message": "Acolhimento registrado na fila com sucesso!",
        **resultado,
    }


@router.patch("/{id_agendamento}/status", status_code=status.HTTP_200_OK)
def atualizar_status_atendimento(
    id_agendamento: int,
    payload: AgendamentoStatusUpdateRequest,
    db: DBDependency,
):
    """
    Atualiza o status do atendimento ('Aguardando', 'Chamado', 'Atendido', 'Ausente').
    """
    service = AgendamentoService(db)
    sucesso = service.atualizar_status(id_agendamento, payload.status)
    if not sucesso:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Falha ao atualizar status do atendimento.",
        )
    return {
        "message": f"Status atualizado para '{payload.status}'.",
        "id_agendamento": id_agendamento,
        "novo_status": payload.status,
    }


@router.patch("/{id_agendamento}/reativar", status_code=status.HTTP_200_OK)
def reativar_ausente(id_agendamento: int, db: DBDependency):
    """
    Remove o acolhido da lista de ausentes e retorna para a fila de espera ('Aguardando').
    Útil quando a pessoa não ouviu a chamada da sua senha e retorna ao balcão.
    """
    service = AgendamentoService(db)
    sucesso = service.reativar_ausente(id_agendamento)
    if not sucesso:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não foi possível reativar o atendimento.",
        )
    return {
        "message": "Atendimento reativado e retornado para a fila de espera com sucesso!",
        "id_agendamento": id_agendamento,
        "novo_status": "Aguardando",
    }


# --- Endpoints de compatibilidade ---

@router.get("/pendentes", status_code=status.HTTP_200_OK)
def listar_agendamentos_pendentes_detalhado(db: DBDependency):
    """Endpoint legado mantido para compatibilidade."""
    relatorio_service = RelatorioService(db)
    agendamentos_detalhado = relatorio_service.gerar_detalhe_agendamentos_pendentes()
    return agendamentos_detalhado or []


@router.patch("/{id_agendamento}/confirmar", status_code=status.HTTP_200_OK)
def confirmar_presenca(
    id_agendamento: int,
    status_update: AgendamentoUpdateStatus,
    db: DBDependency,
):
    """Endpoint legado mantido para compatibilidade."""
    agendamento_service = AgendamentoService(db)
    sucesso = agendamento_service.confirmar_comparecimento(
        id_agendamento,
        status_update.compareceu,
    )
    if not sucesso:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Falha ao atualizar presença.",
        )
    return {
        "message": "Status atualizado com sucesso.",
        "id_agendamento": id_agendamento,
        "novo_status": status_update.compareceu,
    }
