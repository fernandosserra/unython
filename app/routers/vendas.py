from fastapi import APIRouter, Depends, status, HTTPException
from typing import List, Optional
from decimal import Decimal

from src.utils.dependencies import DBDependency
from src.utils.schemas import VendaCreate, VendaResponse
from src.modules.venda import VendaService
from src.modules.caixas import CaixaService
from src.modules.estoque import EstoqueService
from src.modules.usuario import UsuarioService
from src.utils.models import Venda, ItemVenda, Caixa

router = APIRouter(
    prefix="/vendas",
    tags=["Vendas"]
)


def _obter_movimento_caixa(db, responsavel_id: int, caixa_id: Optional[int], id_evento: int, valor_abertura: Decimal = Decimal("0.00")) -> int:
    """Garante um movimento de caixa aberto para o evento e retorna o id_movimento."""
    caixa_service = CaixaService(db)
    if caixa_id:
        cid = caixa_id
    else:
        caixa = caixa_service.buscar_caixa_por_nome("Caixa API")
        cid = caixa.id if caixa else caixa_service.registrar_caixa(
            Caixa(nome="Caixa API", descricao="Caixa padrão para API")
        )
    mov = caixa_service.buscar_movimento_ativo(cid)
    if mov:
        return mov.id
    return caixa_service.abrir_movimento(cid, responsavel_id, valor_abertura, id_evento)


@router.post("/", status_code=status.HTTP_201_CREATED)
def registrar_venda_completa(venda_data: VendaCreate, db: DBDependency):
    estoque_service = EstoqueService(db)
    caixa_service = CaixaService(db)
    venda_service = VendaService(db, estoque_service, caixa_service)

    if not venda_data.id_evento:
        raise HTTPException(status_code=400, detail="id_evento é obrigatório.")

    movimento_id = venda_data.id_movimento_caixa
    if not movimento_id:
        movimento_id = _obter_movimento_caixa(db, venda_data.responsavel_id, venda_data.id_caixa, venda_data.id_evento)

    cabecalho = Venda(
        id_pessoa=venda_data.id_pessoa,
        responsavel=str(venda_data.responsavel_id),
        id_evento=venda_data.id_evento,
        id_movimento_caixa=movimento_id,
    )

    detalhes = [
        ItemVenda(
            id_item=item.item_id,
            quantidade=item.quantidade,
            valor_unitario=Decimal(str(item.valor_unitario)),
            id_venda=0,
        )
        for item in venda_data.itens
    ]

    id_venda = venda_service.registrar_venda_completa(cabecalho, detalhes)

    if id_venda is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A transação falhou. Estoque insuficiente ou dados inválidos.",
        )

    return {"message": "Venda registrada com sucesso.", "id_venda": id_venda}


@router.get("/", response_model=List[VendaResponse], status_code=status.HTTP_200_OK)
def listar_vendas(db: DBDependency):
    estoque_service = EstoqueService(db)
    caixa_service = CaixaService(db)
    venda_service = VendaService(db, estoque_service, caixa_service)
    vendas = venda_service.buscar_vendas()
    if not vendas:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nenhuma venda registrada.")
    return vendas


@router.get("/ultimas", response_model=List[VendaResponse], status_code=status.HTTP_200_OK)
def listar_ultimas_vendas(db: DBDependency, limite: int = 10):
    estoque_service = EstoqueService(db)
    caixa_service = CaixaService(db)
    venda_service = VendaService(db, estoque_service, caixa_service)
    usuario_service = UsuarioService(db)
    users = {u.id: u.nome for u in usuario_service.buscar_usuarios()}
    vendas = venda_service.buscar_ultimas_vendas(limite)
    # Enriquecer responsavel com nome, se for id numérico
    enriched = []
    for v in vendas:
        try:
            rid = int(v.responsavel)
            nome = users.get(rid, v.responsavel)
        except Exception:
            nome = v.responsavel
        data = v.__dict__.copy()
        data["responsavel"] = nome
        enriched.append(data)
    return enriched
