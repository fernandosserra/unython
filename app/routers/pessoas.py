# app/routers/pessoas.py

from fastapi import APIRouter, HTTPException, status, Query
from typing import List, Optional
from src.utils.dependencies import DBDependency
from src.modules.pessoa import PessoaService
from src.utils.models import Pessoa
from src.utils.schemas import PessoaCreate, PessoaResponse

router = APIRouter(prefix="/pessoas", tags=["Pessoas e Assistidos"])


@router.get("/", response_model=List[PessoaResponse])
def listar_pessoas(
    termo: Optional[str] = Query(None, description="Busca por nome, telefone ou documento"),
    db: DBDependency = None,
):
    """Lista ou busca pessoas/assistidos cadastrados."""
    service = PessoaService(db)
    pessoas = service.buscar_pessoas(termo)
    return [
        PessoaResponse(
            id=p.id,
            nome=p.nome,
            telefone=p.telefone,
            documento=p.documento,
            preferencial=p.preferencial,
            observacoes=p.observacoes,
            data_cadastro=p.data_cadastro,
        )
        for p in pessoas
    ]


@router.post("/", response_model=PessoaResponse, status_code=status.HTTP_201_CREATED)
def criar_pessoa(payload: PessoaCreate, db: DBDependency):
    """Cadastra uma nova pessoa/assistido."""
    service = PessoaService(db)
    nova_pessoa = Pessoa(
        nome=payload.nome,
        telefone=payload.telefone,
        documento=payload.documento,
        preferencial=payload.preferencial,
        observacoes=payload.observacoes,
    )
    novo_id = service.registrar_pessoa(nova_pessoa)
    if not novo_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não foi possível cadastrar a pessoa.",
        )
    p = service.buscar_por_id(novo_id)
    return PessoaResponse(
        id=p.id,
        nome=p.nome,
        telefone=p.telefone,
        documento=p.documento,
        preferencial=p.preferencial,
        observacoes=p.observacoes,
        data_cadastro=p.data_cadastro,
    )
