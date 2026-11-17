from fastapi import APIRouter, Depends, status, HTTPException, Query, Request
from typing import List, Optional
from decimal import Decimal

from src.utils.audit import record_audit
from src.utils.dependencies import DBDependency, get_current_user, require_module
from src.utils.schemas import VendaCreate, VendaRecenteResponse, VendaResponse
from src.modules.venda import VendaService
from src.modules.caixas import CaixaService
from src.modules.estoque import EstoqueService
from src.modules.usuario import UsuarioService
from src.utils.models import Venda, ItemVenda, Caixa, Usuario

router = APIRouter(
    prefix="/vendas",
    tags=["Vendas"],
    dependencies=[Depends(get_current_user), Depends(require_module("pdv"))],
)


def _obter_movimento_caixa(db, responsavel_id: int, caixa_id: Optional[int], id_evento: int, request_id: str, valor_abertura: Decimal = Decimal("0.00")) -> int:
    """Garante um movimento de caixa aberto para o evento e retorna o id_movimento."""
    caixa_service = CaixaService(db)
    _, evento = db.execute_query("SELECT status FROM eventos WHERE id = %s FOR UPDATE", (id_evento,), fetch_one=True)
    if not evento or evento[0] not in ("Aberto", "Agendado"):
        raise HTTPException(status_code=400, detail="O evento não está aberto nem agendado.")
    if caixa_id:
        cid = caixa_id
    else:
        caixa = caixa_service.buscar_caixa_por_nome("Caixa API")
        cid = caixa.id if caixa else caixa_service.registrar_caixa(
            Caixa(nome="Caixa API", descricao="Caixa padrão para API"), commit=False
        )
    db.execute_query("SELECT id FROM caixas WHERE id = %s FOR UPDATE", (cid,), fetch_one=True)
    mov = caixa_service.buscar_movimento_ativo(cid)
    if mov:
        return mov.id
    mid = caixa_service.abrir_movimento(cid, responsavel_id, valor_abertura, id_evento, commit=False)
    if not mid:
        raise HTTPException(status_code=400, detail="Não foi possível abrir movimento de caixa.")
    record_audit(db, user_id=responsavel_id, acao="abrir_caixa",
                 entidade="movimento_caixa", entidade_id=mid,
                 detalhes={"caixa_id": cid, "evento_id": id_evento,
                           "valor_abertura": str(valor_abertura), "origem": "venda"},
                 request_id=request_id)
    return mid


@router.post("/", status_code=status.HTTP_201_CREATED)
def registrar_venda_completa(venda_data: VendaCreate, db: DBDependency, request: Request, current_user: Usuario = Depends(get_current_user)):
    estoque_service = EstoqueService(db)
    caixa_service = CaixaService(db)
    venda_service = VendaService(db, estoque_service, caixa_service)

    if not venda_data.id_evento:
        raise HTTPException(status_code=400, detail="id_evento é obrigatório.")

    detalhes = [
        ItemVenda(
            id_item=item.item_id,
            quantidade=item.quantidade,
            valor_unitario=Decimal(str(item.valor_unitario)),
            id_venda=0,
        )
        for item in venda_data.itens
    ]

    try:
        movimento_id = venda_data.id_movimento_caixa
        if not movimento_id:
            movimento_id = _obter_movimento_caixa(
                db, current_user.id, venda_data.id_caixa, venda_data.id_evento, request.state.request_id
            )

        cabecalho = Venda(
            id_pessoa=venda_data.id_pessoa,
            responsavel=str(current_user.id),
            id_evento=venda_data.id_evento,
            id_movimento_caixa=movimento_id,
        )

        for det in detalhes:
            saldo = estoque_service.calcular_saldo_item(det.id_item)
            if saldo < det.quantidade:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Estoque insuficiente para o item {det.id_item}. Necessário: {det.quantidade}, Saldo: {saldo}",
                )

        id_venda = venda_service.registrar_venda_completa(cabecalho, detalhes)
        if id_venda is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A transação falhou. Estoque insuficiente ou dados inválidos.",
            )
    except Exception:
        db.conn.rollback()
        raise

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


@router.get("/ultimas", response_model=List[VendaRecenteResponse], status_code=status.HTTP_200_OK)
def listar_ultimas_vendas(db: DBDependency, limite: int = Query(10, ge=1, le=100)):
    estoque_service = EstoqueService(db)
    caixa_service = CaixaService(db)
    venda_service = VendaService(db, estoque_service, caixa_service)
    usuario_service = UsuarioService(db)
    users = {u.id: u.nome for u in usuario_service.buscar_usuarios()}
    vendas = venda_service.buscar_ultimas_vendas_com_itens(limite)
    # Enriquecer responsavel com nome, se for id numérico
    for venda in vendas:
        try:
            rid = int(venda["responsavel"])
            nome = users.get(rid, venda["responsavel"])
        except (TypeError, ValueError):
            nome = venda["responsavel"]
        venda["responsavel"] = nome
    return vendas
